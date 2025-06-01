"""
Item System - Comprehensive item management infrastructure for the engine studio
Provides a unified API for creating, managing, and working with all item types
"""
import os
import json
import pygame
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile
import subprocess
import sys

# ============================================================================
# CORE ITEM DEFINITIONS AND ENUMS
# ============================================================================

class ItemCategory(Enum):
    """Enumeration of all item categories"""
    RESOURCE = "resource"
    FOOD = "food"
    WATER = "water"
    TOOL = "tool"
    WEAPON = "weapon"
    SCHEMATIC = "schematic"
    SPECIAL = "special"

class ToolType(Enum):
    """Enumeration of tool types"""
    AXE = "axe"
    PICKAXE = "pickaxe"
    SWORD = "sword"
    HOE = "hoe"
    HAMMER = "hammer"

class StructureType(Enum):
    """Enumeration of structure types for schematics"""
    HOUSE = "house"
    CAMPFIRE = "campfire"
    WORKSHOP = "workshop"
    FARM = "farm"
    WALL = "wall"
    BRIDGE = "bridge"

@dataclass
class ItemProperties:
    """Base properties for all items"""
    item_id: str
    name: str
    description: str
    category: ItemCategory
    icon_path: Optional[str] = None
    max_stack: int = 1
    rarity: str = "common"
    value: int = 0
    weight: float = 1.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class ConsumableProperties(ItemProperties):
    """Properties specific to consumable items"""
    effect_value: int = 0
    effect_type: str = "health"
    duration: float = 0.0
    cooldown: float = 0.0

@dataclass
class ToolProperties(ItemProperties):
    """Properties specific to tool items"""
    tool_type: ToolType = ToolType.AXE
    durability: int = 100
    effectiveness: float = 1.0
    repair_material: Optional[str] = None
    enchantments: List[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.enchantments is None:
            self.enchantments = []
        self.max_stack = 1  # Tools typically don't stack

@dataclass
class SchematicProperties(ItemProperties):
    """Properties specific to schematic items"""
    structure_type: StructureType = StructureType.HOUSE
    width: int = 1
    height: int = 1
    required_materials: Dict[str, int] = None
    build_time: float = 0.0
    skill_required: str = "construction"
    skill_level: int = 1
    
    def __post_init__(self):
        super().__post_init__()
        if self.required_materials is None:
            self.required_materials = {}
        self.max_stack = 5  # Schematics have limited stacking

# ============================================================================
# ITEM BASE CLASSES
# ============================================================================

class ItemInstance:
    """Represents an actual item instance in the game world"""
    
    def __init__(self, properties: ItemProperties, quantity: int = 1, durability: Optional[int] = None):
        self.properties = properties
        self.quantity = quantity
        self.durability = durability if durability is not None else getattr(properties, 'durability', None)
        self.current_durability = self.durability
        self.icon_surface = None
        self._load_icon()
    
    def _load_icon(self):
        """Load the item's icon surface"""
        if not pygame.get_init() or not self.properties.icon_path:
            return
            
        try:
            # Construct full path
            if not os.path.isabs(self.properties.icon_path):
                project_root = self._get_project_root()
                if self.properties.icon_path.startswith("items/"):
                    full_path = os.path.join(project_root, "assets", self.properties.icon_path)
                else:
                    full_path = os.path.join(project_root, "assets", "items", self.properties.icon_path)
            else:
                full_path = self.properties.icon_path
            
            if os.path.exists(full_path):
                self.icon_surface = pygame.image.load(full_path).convert_alpha()
                # Ensure 16x16 size
                if self.icon_surface.get_size() != (16, 16):
                    self.icon_surface = pygame.transform.scale(self.icon_surface, (16, 16))
            else:
                self.icon_surface = self._create_placeholder_icon()
        except Exception as e:
            print(f"Error loading icon for {self.properties.item_id}: {e}")
            self.icon_surface = self._create_placeholder_icon()
    
    def _create_placeholder_icon(self):
        """Create a placeholder icon"""
        surface = pygame.Surface((16, 16), pygame.SRCALPHA)
        
        # Color based on category
        color_map = {
            ItemCategory.RESOURCE: (139, 69, 19),    # Brown
            ItemCategory.FOOD: (255, 165, 0),        # Orange
            ItemCategory.WATER: (0, 191, 255),       # Blue
            ItemCategory.TOOL: (169, 169, 169),      # Gray
            ItemCategory.WEAPON: (220, 20, 60),      # Red
            ItemCategory.SCHEMATIC: (255, 255, 0),   # Yellow
            ItemCategory.SPECIAL: (138, 43, 226)     # Purple
        }
        
        color = color_map.get(self.properties.category, (128, 128, 128))
        surface.fill(color)
        pygame.draw.rect(surface, (0, 0, 0), (0, 0, 16, 16), 1)
        
        return surface
    
    def _get_project_root(self):
        """Get the project root directory"""
        current_file = os.path.abspath(__file__)
        # Navigate up from engine/systems/item_system.py to project root
        return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    def can_stack_with(self, other: 'ItemInstance') -> bool:
        """Check if this item can stack with another"""
        if self.properties.item_id != other.properties.item_id:
            return False
        
        # Items with durability generally don't stack unless at full durability
        if self.durability is not None:
            return (self.current_durability == self.durability and 
                   other.current_durability == other.durability)
        
        return True
    
    def split(self, amount: int) -> Optional['ItemInstance']:
        """Split this stack into two"""
        if amount <= 0 or amount >= self.quantity:
            return None
        
        new_instance = ItemInstance(self.properties, amount, self.durability)
        new_instance.current_durability = self.current_durability
        self.quantity -= amount
        
        return new_instance
    
    def stack_with(self, other: 'ItemInstance') -> int:
        """Stack with another item, returns overflow"""
        if not self.can_stack_with(other):
            return other.quantity
        
        space_available = self.properties.max_stack - self.quantity
        amount_to_add = min(other.quantity, space_available)
        
        self.quantity += amount_to_add
        return other.quantity - amount_to_add
    
    def use(self, user=None, world=None, **kwargs) -> bool:
        """Use this item"""
        # This will be handled by the item system's use handlers
        return False
    
    def reduce_durability(self, amount: int = 1) -> bool:
        """Reduce durability, returns True if item is still usable"""
        if self.current_durability is None:
            return True
        
        self.current_durability = max(0, self.current_durability - amount)
        return self.current_durability > 0
    
    def repair(self, amount: int) -> None:
        """Repair the item"""
        if self.current_durability is not None and self.durability is not None:
            self.current_durability = min(self.durability, self.current_durability + amount)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        data = {
            "item_id": self.properties.item_id,
            "quantity": self.quantity
        }
        
        if self.current_durability is not None:
            data["durability"] = self.current_durability
        
        return data

# ============================================================================
# ASEPRITE INTEGRATION
# ============================================================================

class AsepriteIntegration:
    """Handles integration with Aseprite for sprite editing"""
    
    def __init__(self, aseprite_path: Optional[str] = None):
        self.aseprite_path = aseprite_path or self._find_aseprite()
        self.available = self.aseprite_path is not None
        
        if not self.available:
            print("Warning: Aseprite not found. Icon editing features will be disabled.")
    
    def _find_aseprite(self) -> Optional[str]:
        """Try to find Aseprite executable"""
        common_paths = []
        
        if sys.platform == "win32":
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            common_paths.extend([
                os.path.join(program_files, "Aseprite", "Aseprite.exe"),
                os.path.join(program_files_x86, "Aseprite", "Aseprite.exe"),
                os.path.join(program_files, "Steam", "steamapps", "common", "Aseprite", "Aseprite.exe"),
            ])
        elif sys.platform == "darwin":
            common_paths.extend([
                "/Applications/Aseprite.app/Contents/MacOS/aseprite",
                os.path.expanduser("~/Applications/Aseprite.app/Contents/MacOS/aseprite"),
                os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Aseprite/Aseprite.app/Contents/MacOS/aseprite")
            ])
        else:  # Linux
            common_paths.extend([
                "/usr/bin/aseprite",
                "/usr/local/bin/aseprite",
                os.path.expanduser("~/.steam/steam/steamapps/common/Aseprite/aseprite")
            ])
        
        # Check PATH
        try:
            from shutil import which
            aseprite_in_path = which("aseprite")
            if aseprite_in_path:
                common_paths.insert(0, aseprite_in_path)
        except ImportError:
            pass
        
        for path in common_paths:
            if os.path.exists(path) and os.path.isfile(path):
                return path
        
        return None
    
    def create_new_sprite(self, width: int = 16, height: int = 16, save_path: Optional[str] = None) -> Optional[str]:
        """Create a new sprite with Aseprite"""
        if not self.available:
            return None
        
        if save_path is None:
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, f"temp_sprite_{os.getpid()}.png")
        
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        
        try:
            # Create blank PNG
            if pygame.get_init():
                surface = pygame.Surface((width, height), pygame.SRCALPHA)
                surface.fill((255, 255, 255, 255))
                pygame.image.save(surface, save_path)
            
            # Open in Aseprite
            subprocess.Popen([self.aseprite_path, save_path])
            return save_path
        except Exception as e:
            print(f"Error creating sprite: {e}")
            return None
    
    def edit_sprite(self, sprite_path: str) -> bool:
        """Open sprite in Aseprite for editing"""
        if not self.available or not os.path.exists(sprite_path):
            return False
        
        try:
            subprocess.Popen([self.aseprite_path, sprite_path])
            return True
        except Exception as e:
            print(f"Error opening sprite: {e}")
            return False

# ============================================================================
# ITEM FACTORY AND REGISTRY
# ============================================================================

class ItemRegistry:
    """Central registry for all item definitions"""
    
    def __init__(self):
        self._definitions: Dict[str, ItemProperties] = {}
        self._use_handlers: Dict[str, Callable] = {}
        self._categories: Dict[ItemCategory, List[str]] = {cat: [] for cat in ItemCategory}
    
    def register_item(self, properties: ItemProperties, use_handler: Optional[Callable] = None) -> None:
        """Register an item definition"""
        self._definitions[properties.item_id] = properties
        self._categories[properties.category].append(properties.item_id)
        
        if use_handler:
            self._use_handlers[properties.item_id] = use_handler
    
    def get_item_properties(self, item_id: str) -> Optional[ItemProperties]:
        """Get item properties by ID"""
        return self._definitions.get(item_id)
    
    def get_items_by_category(self, category: ItemCategory) -> List[ItemProperties]:
        """Get all items in a category"""
        return [self._definitions[item_id] for item_id in self._categories[category] 
                if item_id in self._definitions]
    
    def get_all_items(self) -> List[ItemProperties]:
        """Get all registered items"""
        return list(self._definitions.values())
    
    def get_use_handler(self, item_id: str) -> Optional[Callable]:
        """Get the use handler for an item"""
        return self._use_handlers.get(item_id)
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item from the registry"""
        if item_id in self._definitions:
            properties = self._definitions[item_id]
            del self._definitions[item_id]
            
            if item_id in self._categories[properties.category]:
                self._categories[properties.category].remove(item_id)
            
            if item_id in self._use_handlers:
                del self._use_handlers[item_id]
            
            return True
        return False

class ItemFactory:
    """Factory for creating item instances"""
    
    def __init__(self, registry: ItemRegistry):
        self.registry = registry
    
    def create_item(self, item_id: str, quantity: int = 1, durability: Optional[int] = None) -> Optional[ItemInstance]:
        """Create an item instance from registered properties"""
        properties = self.registry.get_item_properties(item_id)
        if not properties:
            print(f"Unknown item ID: {item_id}")
            return None
        
        return ItemInstance(properties, quantity, durability)
    
    def create_from_dict(self, data: Dict[str, Any]) -> Optional[ItemInstance]:
        """Create item instance from serialized data"""
        item_id = data.get("item_id")
        if not item_id:
            return None
        
        quantity = data.get("quantity", 1)
        durability = data.get("durability")
        
        return self.create_item(item_id, quantity, durability)

# ============================================================================
# ITEM PERSISTENCE AND DATA MANAGEMENT
# ============================================================================

class ItemDataManager:
    """Manages saving and loading item definitions"""
    
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)
    
    def save_item_definition(self, properties: ItemProperties) -> bool:
        """Save an item definition to file"""
        try:
            category_file = os.path.join(self.data_directory, f"{properties.category.value}_items.json")
            
            # Load existing items in category
            items = []
            if os.path.exists(category_file):
                with open(category_file, 'r') as f:
                    items = json.load(f)
            
            # Update or add the item
            item_dict = self._properties_to_dict(properties)
            
            # Find and replace existing item or add new one
            found = False
            for i, item in enumerate(items):
                if item.get("id") == properties.item_id:
                    items[i] = item_dict
                    found = True
                    break
            
            if not found:
                items.append(item_dict)
            
            # Save back to file
            with open(category_file, 'w') as f:
                json.dump(items, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving item definition: {e}")
            return False
    
    def load_item_definitions(self) -> List[ItemProperties]:
        """Load all item definitions from files"""
        items = []
        
        for category_file in os.listdir(self.data_directory):
            if category_file.endswith("_items.json"):
                try:
                    with open(os.path.join(self.data_directory, category_file), 'r') as f:
                        file_items = json.load(f)
                        
                    for item_data in file_items:
                        properties = self._dict_to_properties(item_data)
                        if properties:
                            items.append(properties)
                            
                except Exception as e:
                    print(f"Error loading {category_file}: {e}")
        
        return items
    
    def delete_item_definition(self, item_id: str, category: ItemCategory) -> bool:
        """Delete an item definition"""
        try:
            category_file = os.path.join(self.data_directory, f"{category.value}_items.json")
            
            if not os.path.exists(category_file):
                return False
            
            with open(category_file, 'r') as f:
                items = json.load(f)
            
            # Remove the item
            items = [item for item in items if item.get("id") != item_id]
            
            # Save back or delete file if empty
            if items:
                with open(category_file, 'w') as f:
                    json.dump(items, f, indent=2)
            else:
                os.remove(category_file)
            
            return True
        except Exception as e:
            print(f"Error deleting item definition: {e}")
            return False
    
    def _properties_to_dict(self, properties: ItemProperties) -> Dict[str, Any]:
        """Convert item properties to dictionary"""
        data = asdict(properties)
        
        # Convert enums to strings
        data["category"] = properties.category.value
        
        if isinstance(properties, ToolProperties):
            data["tool_type"] = properties.tool_type.value
            data["type"] = "tool"
        elif isinstance(properties, SchematicProperties):
            data["structure_type"] = properties.structure_type.value
            data["type"] = "schematic"
        elif isinstance(properties, ConsumableProperties):
            if properties.effect_type == "hunger":
                data["type"] = "food"
            elif properties.effect_type == "thirst":
                data["type"] = "water"
            else:
                data["type"] = "consumable"
        else:
            data["type"] = properties.category.value
        
        # Rename item_id to id for consistency
        data["id"] = data.pop("item_id")
        
        return data
    
    def _dict_to_properties(self, data: Dict[str, Any]) -> Optional[ItemProperties]:
        """Convert dictionary to item properties"""
        try:
            item_type = data.get("type", "resource")
            item_id = data.get("id", "")
            
            if not item_id:
                return None
            
            # Determine category
            category_map = {
                "resource": ItemCategory.RESOURCE,
                "food": ItemCategory.FOOD,
                "water": ItemCategory.WATER,
                "tool": ItemCategory.TOOL,
                "weapon": ItemCategory.WEAPON,
                "schematic": ItemCategory.SCHEMATIC,
                "special": ItemCategory.SPECIAL,
                "consumable": ItemCategory.FOOD  # Default consumables to food
            }
            
            category = category_map.get(item_type, ItemCategory.RESOURCE)
            
            # Create appropriate properties object
            if item_type == "tool":
                tool_type_str = data.get("tool_type", "axe")
                tool_type = ToolType(tool_type_str) if tool_type_str in [t.value for t in ToolType] else ToolType.AXE
                
                return ToolProperties(
                    item_id=item_id,
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    category=category,
                    icon_path=data.get("icon"),
                    max_stack=data.get("max_stack", 1),
                    rarity=data.get("rarity", "common"),
                    value=data.get("value", 0),
                    weight=data.get("weight", 1.0),
                    tags=data.get("tags", []),
                    tool_type=tool_type,
                    durability=data.get("durability", 100),
                    effectiveness=data.get("effectiveness", 1.0),
                    repair_material=data.get("repair_material"),
                    enchantments=data.get("enchantments", [])
                )
            
            elif item_type == "schematic":
                structure_type_str = data.get("structure_type", "house")
                structure_type = StructureType(structure_type_str) if structure_type_str in [s.value for s in StructureType] else StructureType.HOUSE
                
                return SchematicProperties(
                    item_id=item_id,
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    category=category,
                    icon_path=data.get("icon"),
                    max_stack=data.get("max_stack", 5),
                    rarity=data.get("rarity", "common"),
                    value=data.get("value", 0),
                    weight=data.get("weight", 1.0),
                    tags=data.get("tags", []),
                    structure_type=structure_type,
                    width=data.get("width", 1),
                    height=data.get("height", 1),
                    required_materials=data.get("required_materials", {}),
                    build_time=data.get("build_time", 0.0),
                    skill_required=data.get("skill_required", "construction"),
                    skill_level=data.get("skill_level", 1)
                )
            
            elif item_type in ["food", "water", "consumable"]:
                effect_type = "hunger" if item_type == "food" else "thirst" if item_type == "water" else data.get("effect_type", "health")
                
                return ConsumableProperties(
                    item_id=item_id,
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    category=category,
                    icon_path=data.get("icon"),
                    max_stack=data.get("max_stack", 16),
                    rarity=data.get("rarity", "common"),
                    value=data.get("value", 0),
                    weight=data.get("weight", 1.0),
                    tags=data.get("tags", []),
                    effect_value=data.get("hunger_value", data.get("thirst_value", data.get("effect_value", 2))),
                    effect_type=effect_type,
                    duration=data.get("duration", 0.0),
                    cooldown=data.get("cooldown", 0.0)
                )
            
            else:
                # Basic item properties
                return ItemProperties(
                    item_id=item_id,
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    category=category,
                    icon_path=data.get("icon"),
                    max_stack=data.get("max_stack", 64),
                    rarity=data.get("rarity", "common"),
                    value=data.get("value", 0),
                    weight=data.get("weight", 1.0),
                    tags=data.get("tags", [])
                )
                
        except Exception as e:
            print(f"Error converting dict to properties: {e}")
            return None

# ============================================================================
# ICON AND ASSET MANAGEMENT
# ============================================================================

class IconManager:
    """Manages item icons and asset creation"""
    
    def __init__(self, assets_directory: str):
        self.assets_directory = assets_directory
        self.items_directory = os.path.join(assets_directory, "items")
        os.makedirs(self.items_directory, exist_ok=True)
        
        self.aseprite = AsepriteIntegration()
    
    def create_placeholder_icon(self, item_id: str, category: ItemCategory, size: Tuple[int, int] = (16, 16)) -> str:
        """Create a placeholder icon for an item"""
        filename = f"{item_id}.png"
        file_path = os.path.join(self.items_directory, filename)
        
        if os.path.exists(file_path):
            return f"items/{filename}"
        
        if not pygame.get_init():
            return f"items/{filename}"
        
        try:
            surface = pygame.Surface(size, pygame.SRCALPHA)
            
            # Color based on category
            color_map = {
                ItemCategory.RESOURCE: (139, 69, 19),
                ItemCategory.FOOD: (255, 165, 0),
                ItemCategory.WATER: (0, 191, 255),
                ItemCategory.TOOL: (169, 169, 169),
                ItemCategory.WEAPON: (220, 20, 60),
                ItemCategory.SCHEMATIC: (255, 255, 0),
                ItemCategory.SPECIAL: (138, 43, 226)
            }
            
            color = color_map.get(category, (128, 128, 128))
            surface.fill(color)
            pygame.draw.rect(surface, (0, 0, 0), (0, 0, size[0], size[1]), 1)
            
            # Add category-specific details
            self._add_icon_details(surface, category, size)
            
            pygame.image.save(surface, file_path)
            print(f"Created placeholder icon: {file_path}")
            
        except Exception as e:
            print(f"Error creating placeholder icon: {e}")
        
        return f"items/{filename}"
    
    def _add_icon_details(self, surface: pygame.Surface, category: ItemCategory, size: Tuple[int, int]):
        """Add category-specific details to placeholder icons"""
        w, h = size
        
        if category == ItemCategory.FOOD:
            # Add a bite mark
            pygame.draw.circle(surface, (0, 0, 0, 0), (w - 4, 4), 3)
        elif category == ItemCategory.WATER:
            # Add water level indicator
            pygame.draw.rect(surface, (50, 100, 200), (3, h - 6, w - 6, 3))
        elif category == ItemCategory.TOOL:
            # Add tool handle
            pygame.draw.line(surface, (100, 50, 0), (w//2, 2), (w//2, h - 2), 2)
        elif category == ItemCategory.SCHEMATIC:
            # Add blueprint lines
            pygame.draw.line(surface, (0, 0, 0), (2, h//3), (w - 2, h//3), 1)
            pygame.draw.line(surface, (0, 0, 0), (2, 2*h//3), (w - 2, 2*h//3), 1)
    
    def create_new_icon(self, item_id: str, size: Tuple[int, int] = (16, 16)) -> Optional[str]:
        """Create a new icon using Aseprite"""
        if not self.aseprite.available:
            return None
        
        filename = f"{item_id}.png"
        file_path = os.path.join(self.items_directory, filename)
        
        sprite_path = self.aseprite.create_new_sprite(size[0], size[1], file_path)
        if sprite_path:
            return f"items/{filename}"
        
        return None
    
    def edit_icon(self, icon_path: str) -> bool:
        """Edit an existing icon with Aseprite"""
        if not self.aseprite.available:
            return False
        
        if not icon_path.startswith("items/"):
            icon_path = f"items/{icon_path}"
        
        full_path = os.path.join(self.assets_directory, icon_path)
        return self.aseprite.edit_sprite(full_path)
    
    def get_icon_path(self, item_id: str) -> str:
        """Get the icon path for an item"""
        filename = f"{item_id}.png"
        full_path = os.path.join(self.items_directory, filename)
        
        if os.path.exists(full_path):
            return f"items/{filename}"
        
        return None

# ============================================================================
# USE HANDLERS FOR DIFFERENT ITEM TYPES
# ============================================================================

class ItemUseHandlers:
    """Collection of use handlers for different item types"""
    
    @staticmethod
    def create_consumable_handler(effect_type: str, effect_value: int) -> Callable:
        """Create a use handler for consumable items"""
        def use_consumable(item_instance: ItemInstance, user=None, world=None, **kwargs) -> bool:
            if not user or not hasattr(user, effect_type):
                return False
            
            # Get current and max values
            current_value = getattr(user, effect_type)
            max_attr = f"max_{effect_type}"
            max_value = getattr(user, max_attr, 10)
            
            # Apply effect
            new_value = min(current_value + effect_value, max_value)
            setattr(user, effect_type, new_value)
            
            # Reduce quantity
            item_instance.quantity -= 1
            
            print(f"Used {item_instance.properties.name}, {effect_type}: {current_value} -> {new_value}")
            return True
        
        return use_consumable
    
    @staticmethod
    def create_tool_handler(tool_type: ToolType, effectiveness: float) -> Callable:
        """Create a use handler for tool items"""
        def use_tool(item_instance: ItemInstance, user=None, world=None, **kwargs) -> bool:
            if not user or not world:
                return False
            
            # Get target position based on user facing direction
            if not hasattr(user, 'grid_x') or not hasattr(user, 'grid_y') or not hasattr(user, 'facing'):
                return False
            
            dx, dy = 0, 0
            if user.facing == 'up':
                dy = -1
            elif user.facing == 'down':
                dy = 1
            elif user.facing == 'left':
                dx = -1
            elif user.facing == 'right':
                dx = 1
            
            target_x, target_y = user.grid_x + dx, user.grid_y + dy
            
            # Handle different tool types
            success = False
            if tool_type == ToolType.AXE:
                success = ItemUseHandlers._use_axe(world, target_x, target_y, effectiveness)
            elif tool_type == ToolType.PICKAXE:
                success = ItemUseHandlers._use_pickaxe(world, target_x, target_y, effectiveness)
            elif tool_type == ToolType.HOE:
                success = ItemUseHandlers._use_hoe(world, target_x, target_y, effectiveness)
            
            if success:
                # Reduce durability
                if not item_instance.reduce_durability(1):
                    print(f"{item_instance.properties.name} broke!")
                    return False
            
            return success
        
        return use_tool
    
    @staticmethod
    def create_schematic_handler(structure_type: StructureType) -> Callable:
        """Create a use handler for schematic items"""
        def use_schematic(item_instance: ItemInstance, user=None, world=None, **kwargs) -> bool:
            if not user or not world:
                return False
            
            # Get placement position
            if not hasattr(user, 'grid_x') or not hasattr(user, 'grid_y') or not hasattr(user, 'facing'):
                return False
            
            x, y = user.grid_x, user.grid_y
            if user.facing == 'up':
                y -= 1
            elif user.facing == 'down':
                y += 1
            elif user.facing == 'left':
                x -= 1
            elif user.facing == 'right':
                x += 1
            
            # Place structure based on type
            success = False
            if structure_type == StructureType.HOUSE and hasattr(world, 'add_house'):
                success = world.add_house(x, y) is not None
            elif structure_type == StructureType.CAMPFIRE and hasattr(world, 'add_campfire'):
                success = world.add_campfire(x, y) is not None
            
            if success:
                item_instance.quantity -= 1
                print(f"Placed {structure_type.value} at ({x}, {y})")
            
            return success
        
        return use_schematic
    
    @staticmethod
    def _use_axe(world, x: int, y: int, effectiveness: float) -> bool:
        """Handle axe usage on trees"""
        if hasattr(world, 'entity_tile_manager'):
            entity_tile = world.entity_tile_manager.get_entity_tile_at(x, y)
            if entity_tile and hasattr(entity_tile, 'tile_type') and entity_tile.tile_type == 'tree':
                print(f"Chopped tree at ({x}, {y}) with effectiveness {effectiveness}")
                return True
        return False
    
    @staticmethod
    def _use_pickaxe(world, x: int, y: int, effectiveness: float) -> bool:
        """Handle pickaxe usage on rocks/mountains"""
        tile = world.get_tile(x, y) if hasattr(world, 'get_tile') else None
        if tile and hasattr(tile, 'type') and tile.type == "mountain":
            print(f"Mined mountain at ({x}, {y}) with effectiveness {effectiveness}")
            return True
        return False
    
    @staticmethod
    def _use_hoe(world, x: int, y: int, effectiveness: float) -> bool:
        """Handle hoe usage for farming"""
        tile = world.get_tile(x, y) if hasattr(world, 'get_tile') else None
        if tile and hasattr(tile, 'type') and tile.type in ["grass", "dirt"]:
            print(f"Tilled soil at ({x}, {y}) with effectiveness {effectiveness}")
            return True
        return False

# ============================================================================
# MAIN ITEM SYSTEM CLASS
# ============================================================================

class ItemSystem:
    """Main item system that orchestrates all item functionality"""
    
    def __init__(self, project_root: str, aseprite_path: Optional[str] = None):
        """Initialize the item system
        
        Args:
            project_root: Path to the project root directory
            aseprite_path: Optional path to Aseprite executable
        """
        self.project_root = project_root
        self.data_directory = os.path.join(project_root, "data", "items")
        self.assets_directory = os.path.join(project_root, "assets")
        
        # Initialize components
        self.registry = ItemRegistry()
        self.factory = ItemFactory(self.registry)
        self.data_manager = ItemDataManager(self.data_directory)
        self.icon_manager = IconManager(self.assets_directory)
        
        # Override Aseprite path if provided
        if aseprite_path:
            self.icon_manager.aseprite.aseprite_path = aseprite_path
            self.icon_manager.aseprite.available = os.path.exists(aseprite_path)
        
        # Load existing items
        self._load_all_items()
        
        # Create default items if none exist
        if not self.registry.get_all_items():
            self._create_default_items()
    
    def _load_all_items(self):
        """Load all item definitions from storage"""
        items = self.data_manager.load_item_definitions()
        
        for properties in items:
            # Create appropriate use handler
            use_handler = self._create_use_handler(properties)
            self.registry.register_item(properties, use_handler)
        
        print(f"Loaded {len(items)} item definitions")
    
    def _create_use_handler(self, properties: ItemProperties) -> Optional[Callable]:
        """Create appropriate use handler for item properties"""
        if isinstance(properties, ConsumableProperties):
            return ItemUseHandlers.create_consumable_handler(
                properties.effect_type, properties.effect_value
            )
        elif isinstance(properties, ToolProperties):
            return ItemUseHandlers.create_tool_handler(
                properties.tool_type, properties.effectiveness
            )
        elif isinstance(properties, SchematicProperties):
            return ItemUseHandlers.create_schematic_handler(
                properties.structure_type
            )
        
        return None
    
    def _create_default_items(self):
        """Create default items if none exist"""
        print("Creating default items...")
        
        # Resources
        self.create_resource_item(
            "stone", "Stone", "A common building material",
            max_stack=64, value=1
        )
        
        self.create_resource_item(
            "branch", "Branch", "Collected from trees",
            max_stack=64, value=1
        )
        
        self.create_resource_item(
            "fiber", "Plant Fiber", "Used for crafting",
            max_stack=64, value=1
        )
        
        # Food items
        self.create_food_item(
            "apple", "Apple", "A juicy red apple",
            hunger_value=2, max_stack=16, value=5
        )
        
        self.create_food_item(
            "berries", "Berries", "Small wild berries",
            hunger_value=1, max_stack=32, value=2
        )
        
        # Water items
        self.create_water_item(
            "water_bottle", "Water Bottle", "A bottle of fresh water",
            thirst_value=2, max_stack=16, value=3
        )
        
        self.create_water_item(
            "canteen", "Canteen", "A large water container",
            thirst_value=4, max_stack=4, value=10
        )
        
        # Tools
        self.create_tool_item(
            "stone_axe", "Stone Axe", "A crude axe made of stone",
            ToolType.AXE, durability=50, effectiveness=0.8, value=25
        )
        
        self.create_tool_item(
            "stone_pickaxe", "Stone Pickaxe", "A crude pickaxe made of stone",
            ToolType.PICKAXE, durability=50, effectiveness=0.8, value=25
        )
        
        # Schematics
        self.create_schematic_item(
            "house_schematic", "House Schematic", "Blueprint for a simple house",
            StructureType.HOUSE, width=2, height=2, value=50
        )
        
        self.create_schematic_item(
            "campfire_schematic", "Campfire Schematic", "Blueprint for a campfire",
            StructureType.CAMPFIRE, width=1, height=1, value=20
        )
        
        print(f"Created {len(self.registry.get_all_items())} default items")
    
    # ========================================================================
    # PUBLIC API METHODS
    # ========================================================================
    
    def create_item_instance(self, item_id: str, quantity: int = 1, durability: Optional[int] = None) -> Optional[ItemInstance]:
        """Create an item instance"""
        return self.factory.create_item(item_id, quantity, durability)
    
    def create_resource_item(self, item_id: str, name: str, description: str, 
                           max_stack: int = 64, value: int = 0, weight: float = 1.0,
                           tags: List[str] = None, icon_path: Optional[str] = None) -> ItemProperties:
        """Create a new resource item"""
        if icon_path is None:
            icon_path = self.icon_manager.create_placeholder_icon(item_id, ItemCategory.RESOURCE)
        
        properties = ItemProperties(
            item_id=item_id,
            name=name,
            description=description,
            category=ItemCategory.RESOURCE,
            icon_path=icon_path,
            max_stack=max_stack,
            value=value,
            weight=weight,
            tags=tags or []
        )
        
        self.registry.register_item(properties)
        self.data_manager.save_item_definition(properties)
        
        return properties
    
    def create_food_item(self, item_id: str, name: str, description: str,
                        hunger_value: int = 2, max_stack: int = 16, value: int = 0,
                        duration: float = 0.0, cooldown: float = 0.0,
                        tags: List[str] = None, icon_path: Optional[str] = None) -> ConsumableProperties:
        """Create a new food item"""
        if icon_path is None:
            icon_path = self.icon_manager.create_placeholder_icon(item_id, ItemCategory.FOOD)
        
        properties = ConsumableProperties(
            item_id=item_id,
            name=name,
            description=description,
            category=ItemCategory.FOOD,
            icon_path=icon_path,
            max_stack=max_stack,
            value=value,
            tags=tags or [],
            effect_value=hunger_value,
            effect_type="hunger",
            duration=duration,
            cooldown=cooldown
        )
        
        use_handler = ItemUseHandlers.create_consumable_handler("hunger", hunger_value)
        self.registry.register_item(properties, use_handler)
        self.data_manager.save_item_definition(properties)
        
        return properties
    
    def create_water_item(self, item_id: str, name: str, description: str,
                         thirst_value: int = 2, max_stack: int = 16, value: int = 0,
                         duration: float = 0.0, cooldown: float = 0.0,
                         tags: List[str] = None, icon_path: Optional[str] = None) -> ConsumableProperties:
        """Create a new water item"""
        if icon_path is None:
            icon_path = self.icon_manager.create_placeholder_icon(item_id, ItemCategory.WATER)
        
        properties = ConsumableProperties(
            item_id=item_id,
            name=name,
            description=description,
            category=ItemCategory.WATER,
            icon_path=icon_path,
            max_stack=max_stack,
            value=value,
            tags=tags or [],
            effect_value=thirst_value,
            effect_type="thirst",
            duration=duration,
            cooldown=cooldown
        )
        
        use_handler = ItemUseHandlers.create_consumable_handler("thirst", thirst_value)
        self.registry.register_item(properties, use_handler)
        self.data_manager.save_item_definition(properties)
        
        return properties
    
    def create_tool_item(self, item_id: str, name: str, description: str,
                        tool_type: ToolType, durability: int = 100, effectiveness: float = 1.0,
                        value: int = 0, repair_material: Optional[str] = None,
                        enchantments: List[str] = None, tags: List[str] = None,
                        icon_path: Optional[str] = None) -> ToolProperties:
        """Create a new tool item"""
        if icon_path is None:
            icon_path = self.icon_manager.create_placeholder_icon(item_id, ItemCategory.TOOL)
        
        properties = ToolProperties(
            item_id=item_id,
            name=name,
            description=description,
            category=ItemCategory.TOOL,
            icon_path=icon_path,
            max_stack=1,
            value=value,
            tags=tags or [],
            tool_type=tool_type,
            durability=durability,
            effectiveness=effectiveness,
            repair_material=repair_material,
            enchantments=enchantments or []
        )
        
        use_handler = ItemUseHandlers.create_tool_handler(tool_type, effectiveness)
        self.registry.register_item(properties, use_handler)
        self.data_manager.save_item_definition(properties)
        
        return properties
    
    def create_schematic_item(self, item_id: str, name: str, description: str,
                             structure_type: StructureType, width: int = 1, height: int = 1,
                             value: int = 0, required_materials: Dict[str, int] = None,
                             build_time: float = 0.0, skill_required: str = "construction",
                             skill_level: int = 1, tags: List[str] = None,
                             icon_path: Optional[str] = None) -> SchematicProperties:
        """Create a new schematic item"""
        if icon_path is None:
            icon_path = self.icon_manager.create_placeholder_icon(item_id, ItemCategory.SCHEMATIC)
        
        properties = SchematicProperties(
            item_id=item_id,
            name=name,
            description=description,
            category=ItemCategory.SCHEMATIC,
            icon_path=icon_path,
            max_stack=5,
            value=value,
            tags=tags or [],
            structure_type=structure_type,
            width=width,
            height=height,
            required_materials=required_materials or {},
            build_time=build_time,
            skill_required=skill_required,
            skill_level=skill_level
        )
        
        use_handler = ItemUseHandlers.create_schematic_handler(structure_type)
        self.registry.register_item(properties, use_handler)
        self.data_manager.save_item_definition(properties)
        
        return properties
    
    def create_custom_item(self, properties: ItemProperties, use_handler: Optional[Callable] = None) -> ItemProperties:
        """Create a custom item with specific properties"""
        if properties.icon_path is None:
            properties.icon_path = self.icon_manager.create_placeholder_icon(
                properties.item_id, properties.category
            )
        
        self.registry.register_item(properties, use_handler)
        self.data_manager.save_item_definition(properties)
        
        return properties
    
    def update_item(self, properties: ItemProperties, use_handler: Optional[Callable] = None) -> bool:
        """Update an existing item"""
        if properties.item_id not in self.registry._definitions:
            return False
        
        self.registry.register_item(properties, use_handler)
        return self.data_manager.save_item_definition(properties)
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item"""
        properties = self.registry.get_item_properties(item_id)
        if not properties:
            return False
        
        success = self.data_manager.delete_item_definition(item_id, properties.category)
        if success:
            self.registry.remove_item(item_id)
        
        return success
    
    def get_item_properties(self, item_id: str) -> Optional[ItemProperties]:
        """Get item properties by ID"""
        return self.registry.get_item_properties(item_id)
    
    def get_items_by_category(self, category: ItemCategory) -> List[ItemProperties]:
        """Get all items in a category"""
        return self.registry.get_items_by_category(category)
    
    def get_all_items(self) -> List[ItemProperties]:
        """Get all registered items"""
        return self.registry.get_all_items()
    
    def use_item(self, item_instance: ItemInstance, user=None, world=None, **kwargs) -> bool:
        """Use an item instance"""
        use_handler = self.registry.get_use_handler(item_instance.properties.item_id)
        if use_handler:
            return use_handler(item_instance, user, world, **kwargs)
        
        return item_instance.use(user, world, **kwargs)
    
    def create_new_icon(self, item_id: str, size: Tuple[int, int] = (16, 16)) -> Optional[str]:
        """Create a new icon using Aseprite"""
        return self.icon_manager.create_new_icon(item_id, size)
    
    def edit_icon(self, item_id: str) -> bool:
        """Edit an item's icon with Aseprite"""
        properties = self.get_item_properties(item_id)
        if not properties or not properties.icon_path:
            return False
        
        return self.icon_manager.edit_icon(properties.icon_path)
    
    def get_icon_surface(self, item_id: str) -> Optional[pygame.Surface]:
        """Get the icon surface for an item"""
        instance = self.create_item_instance(item_id)
        return instance.icon_surface if instance else None
    
    def export_item_definitions(self, file_path: str) -> bool:
        """Export all item definitions to a single JSON file"""
        try:
            all_items = []
            for properties in self.get_all_items():
                all_items.append(self.data_manager._properties_to_dict(properties))
            
            with open(file_path, 'w') as f:
                json.dump(all_items, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting item definitions: {e}")
            return False
    
    def import_item_definitions(self, file_path: str) -> int:
        """Import item definitions from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                items_data = json.load(f)
            
            imported_count = 0
            for item_data in items_data:
                properties = self.data_manager._dict_to_properties(item_data)
                if properties:
                    use_handler = self._create_use_handler(properties)
                    self.registry.register_item(properties, use_handler)
                    self.data_manager.save_item_definition(properties)
                    imported_count += 1
            
            return imported_count
        except Exception as e:
            print(f"Error importing item definitions: {e}")
            return 0
    
    def validate_item_assets(self) -> Dict[str, List[str]]:
        """Validate that all items have their required assets"""
        missing_icons = []
        invalid_paths = []
        
        for properties in self.get_all_items():
            if properties.icon_path:
                if properties.icon_path.startswith("items/"):
                    full_path = os.path.join(self.assets_directory, properties.icon_path)
                else:
                    full_path = os.path.join(self.assets_directory, "items", properties.icon_path)
                
                if not os.path.exists(full_path):
                    missing_icons.append(properties.item_id)
            else:
                invalid_paths.append(properties.item_id)
        
        return {
            "missing_icons": missing_icons,
            "invalid_paths": invalid_paths
        }
    
    def create_missing_assets(self) -> int:
        """Create placeholder assets for items that are missing them"""
        validation_result = self.validate_item_assets()
        created_count = 0
        
        for item_id in validation_result["missing_icons"] + validation_result["invalid_paths"]:
            properties = self.get_item_properties(item_id)
            if properties:
                icon_path = self.icon_manager.create_placeholder_icon(item_id, properties.category)
                properties.icon_path = icon_path
                self.data_manager.save_item_definition(properties)
                created_count += 1
        
        return created_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the item system"""
        all_items = self.get_all_items()
        
        category_counts = {}
        for category in ItemCategory:
            category_counts[category.value] = len(self.get_items_by_category(category))
        
        validation_result = self.validate_item_assets()
        
        return {
            "total_items": len(all_items),
            "category_counts": category_counts,
            "missing_assets": len(validation_result["missing_icons"]) + len(validation_result["invalid_paths"]),
            "aseprite_available": self.icon_manager.aseprite.available,
            "data_directory": self.data_directory,
            "assets_directory": self.assets_directory
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_item_system(project_root: str, aseprite_path: Optional[str] = None) -> ItemSystem:
    """Create and initialize an item system"""
    return ItemSystem(project_root, aseprite_path)

def serialize_item_instance(item_instance: ItemInstance) -> Dict[str, Any]:
    """Serialize an item instance to dictionary"""
    return item_instance.to_dict()

def deserialize_item_instance(data: Dict[str, Any], item_system: ItemSystem) -> Optional[ItemInstance]:
    """Deserialize an item instance from dictionary"""
    return item_system.factory.create_from_dict(data)

def batch_create_items(item_system: ItemSystem, items_data: List[Dict[str, Any]]) -> List[ItemProperties]:
    """Batch create multiple items from data"""
    created_items = []
    
    for item_data in items_data:
        try:
            item_type = item_data.get("type", "resource")
            
            if item_type == "resource":
                properties = item_system.create_resource_item(
                    item_data["id"],
                    item_data["name"],
                    item_data["description"],
                    item_data.get("max_stack", 64),
                    item_data.get("value", 0),
                    item_data.get("weight", 1.0),
                    item_data.get("tags", []),
                    item_data.get("icon")
                )
            elif item_type == "food":
                properties = item_system.create_food_item(
                    item_data["id"],
                    item_data["name"],
                    item_data["description"],
                    item_data.get("hunger_value", 2),
                    item_data.get("max_stack", 16),
                    item_data.get("value", 0),
                    item_data.get("duration", 0.0),
                    item_data.get("cooldown", 0.0),
                    item_data.get("tags", []),
                    item_data.get("icon")
                )
            elif item_type == "water":
                properties = item_system.create_water_item(
                    item_data["id"],
                    item_data["name"],
                    item_data["description"],
                    item_data.get("thirst_value", 2),
                    item_data.get("max_stack", 16),
                    item_data.get("value", 0),
                    item_data.get("duration", 0.0),
                    item_data.get("cooldown", 0.0),
                    item_data.get("tags", []),
                    item_data.get("icon")
                )
            elif item_type == "tool":
                tool_type = ToolType(item_data.get("tool_type", "axe"))
                properties = item_system.create_tool_item(
                    item_data["id"],
                    item_data["name"],
                    item_data["description"],
                    tool_type,
                    item_data.get("durability", 100),
                    item_data.get("effectiveness", 1.0),
                    item_data.get("value", 0),
                    item_data.get("repair_material"),
                    item_data.get("enchantments", []),
                    item_data.get("tags", []),
                    item_data.get("icon")
                )
            elif item_type == "schematic":
                structure_type = StructureType(item_data.get("structure_type", "house"))
                properties = item_system.create_schematic_item(
                    item_data["id"],
                    item_data["name"],
                    item_data["description"],
                    structure_type,
                    item_data.get("width", 1),
                    item_data.get("height", 1),
                    item_data.get("value", 0),
                    item_data.get("required_materials", {}),
                    item_data.get("build_time", 0.0),
                    item_data.get("skill_required", "construction"),
                    item_data.get("skill_level", 1),
                    item_data.get("tags", []),
                    item_data.get("icon")
                )
            
            created_items.append(properties)
            
        except Exception as e:
            print(f"Error creating item {item_data.get('id', 'unknown')}: {e}")
    
    return created_items

# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

if __name__ == "__main__":
    # Example usage of the item system
    import pygame
    pygame.init()
    
    # Create item system
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    item_system = create_item_system(project_root)
    
    # Get statistics
    stats = item_system.get_statistics()
    print("Item System Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Create a custom item
    custom_properties = ItemProperties(
        item_id="magic_crystal",
        name="Magic Crystal",
        description="A mysterious crystal that glows with inner light",
        category=ItemCategory.SPECIAL,
        max_stack=1,
        rarity="legendary",
        value=1000,
        weight=0.5,
        tags=["magic", "rare", "glowing"]
    )
    
    item_system.create_custom_item(custom_properties)
    
    # Create an item instance
    crystal_instance = item_system.create_item_instance("magic_crystal")
    if crystal_instance:
        print(f"Created item: {crystal_instance.properties.name}")
    
    # Test batch creation
    batch_data = [
        {
            "type": "food",
            "id": "bread",
            "name": "Bread",
            "description": "Fresh baked bread",
            "hunger_value": 3,
            "value": 8
        },
        {
            "type": "tool",
            "id": "iron_sword",
            "name": "Iron Sword",
            "description": "A sharp iron sword",
            "tool_type": "sword",
            "durability": 200,
            "effectiveness": 1.5,
            "value": 100
        }
    ]
    
    batch_created = batch_create_items(item_system, batch_data)
    print(f"Batch created {len(batch_created)} items")
    
    # Validate assets
    validation = item_system.validate_item_assets()
    print(f"Asset validation: {validation}")
    
    # Create missing assets
    created_assets = item_system.create_missing_assets()
    print(f"Created {created_assets} missing assets")
    
    pygame.quit()

# ============================================================================
# INTEGRATION HELPERS FOR EXISTING CODEBASE
# ============================================================================

class LegacyItemAdapter:
    """Adapter to help integrate with existing item classes"""
    
    def __init__(self, item_system: ItemSystem):
        self.item_system = item_system
    
    def convert_legacy_item_to_properties(self, legacy_item) -> Optional[ItemProperties]:
        """Convert a legacy item instance to ItemProperties"""
        try:
            # Determine category based on class type
            category = ItemCategory.RESOURCE
            if hasattr(legacy_item, '__class__'):
                class_name = legacy_item.__class__.__name__.lower()
                if 'food' in class_name:
                    category = ItemCategory.FOOD
                elif 'water' in class_name or 'bottle' in class_name:
                    category = ItemCategory.WATER
                elif 'tool' in class_name or 'axe' in class_name or 'pickaxe' in class_name:
                    category = ItemCategory.TOOL
                elif 'schematic' in class_name:
                    category = ItemCategory.SCHEMATIC
            
            # Create appropriate properties based on category
            if category == ItemCategory.FOOD:
                return ConsumableProperties(
                    item_id=getattr(legacy_item, 'item_id', 'unknown'),
                    name=getattr(legacy_item, 'name', 'Unknown'),
                    description=getattr(legacy_item, 'description', ''),
                    category=category,
                    icon_path=getattr(legacy_item, 'icon_path', None),
                    max_stack=getattr(legacy_item, 'max_stack', 16),
                    effect_value=getattr(legacy_item, 'effect_value', 2),
                    effect_type="hunger"
                )
            elif category == ItemCategory.WATER:
                return ConsumableProperties(
                    item_id=getattr(legacy_item, 'item_id', 'unknown'),
                    name=getattr(legacy_item, 'name', 'Unknown'),
                    description=getattr(legacy_item, 'description', ''),
                    category=category,
                    icon_path=getattr(legacy_item, 'icon_path', None),
                    max_stack=getattr(legacy_item, 'max_stack', 16),
                    effect_value=getattr(legacy_item, 'effect_value', 2),
                    effect_type="thirst"
                )
            elif category == ItemCategory.TOOL:
                tool_type_str = getattr(legacy_item, 'tool_type', 'axe')
                tool_type = ToolType.AXE
                try:
                    tool_type = ToolType(tool_type_str)
                except ValueError:
                    pass
                
                return ToolProperties(
                    item_id=getattr(legacy_item, 'item_id', 'unknown'),
                    name=getattr(legacy_item, 'name', 'Unknown'),
                    description=getattr(legacy_item, 'description', ''),
                    category=category,
                    icon_path=getattr(legacy_item, 'icon_path', None),
                    tool_type=tool_type,
                    durability=getattr(legacy_item, 'max_durability', 100),
                    effectiveness=getattr(legacy_item, 'effectiveness', 1.0)
                )
            elif category == ItemCategory.SCHEMATIC:
                structure_type_str = getattr(legacy_item, 'structure_type', 'house')
                structure_type = StructureType.HOUSE
                try:
                    structure_type = StructureType(structure_type_str)
                except ValueError:
                    pass
                
                return SchematicProperties(
                    item_id=getattr(legacy_item, 'item_id', 'unknown'),
                    name=getattr(legacy_item, 'name', 'Unknown'),
                    description=getattr(legacy_item, 'description', ''),
                    category=category,
                    icon_path=getattr(legacy_item, 'icon_path', None),
                    structure_type=structure_type,
                    width=getattr(legacy_item, 'width', 1),
                    height=getattr(legacy_item, 'height', 1)
                )
            else:
                return ItemProperties(
                    item_id=getattr(legacy_item, 'item_id', 'unknown'),
                    name=getattr(legacy_item, 'name', 'Unknown'),
                    description=getattr(legacy_item, 'description', ''),
                    category=category,
                    icon_path=getattr(legacy_item, 'icon_path', None),
                    max_stack=getattr(legacy_item, 'max_stack', 64)
                )
        
        except Exception as e:
            print(f"Error converting legacy item: {e}")
            return None
    
    def migrate_legacy_items(self, legacy_items: List) -> int:
        """Migrate a list of legacy items to the new system"""
        migrated_count = 0
        
        for legacy_item in legacy_items:
            properties = self.convert_legacy_item_to_properties(legacy_item)
            if properties:
                try:
                    self.item_system.create_custom_item(properties)
                    migrated_count += 1
                except Exception as e:
                    print(f"Error migrating item {getattr(legacy_item, 'item_id', 'unknown')}: {e}")
        
        return migrated_count

def migrate_from_legacy_system(item_system: ItemSystem, legacy_item_manager=None, legacy_factory=None) -> Dict[str, int]:
    """Migrate items from the legacy item system"""
    adapter = LegacyItemAdapter(item_system)
    migration_stats = {
        "migrated_definitions": 0,
        "migrated_templates": 0,
        "errors": 0
    }
    
    # Migrate from legacy item manager if provided
    if legacy_item_manager and hasattr(legacy_item_manager, 'get_all_items'):
        try:
            legacy_definitions = legacy_item_manager.get_all_items()
            for definition in legacy_definitions:
                try:
                    # Convert legacy definition to new format
                    if hasattr(definition, 'category'):
                        category_map = {
                            "resource": ItemCategory.RESOURCE,
                            "food": ItemCategory.FOOD,
                            "water": ItemCategory.WATER,
                            "tool": ItemCategory.TOOL,
                            "schematic": ItemCategory.SCHEMATIC
                        }
                        
                        category = category_map.get(definition.category, ItemCategory.RESOURCE)
                        
                        if category == ItemCategory.FOOD:
                            properties = ConsumableProperties(
                                item_id=definition.item_id,
                                name=definition.name,
                                description=definition.description,
                                category=category,
                                icon_path=definition.icon_path,
                                max_stack=definition.properties.get("max_stack", 16),
                                effect_value=definition.properties.get("hunger_value", 2),
                                effect_type="hunger"
                            )
                        elif category == ItemCategory.WATER:
                            properties = ConsumableProperties(
                                item_id=definition.item_id,
                                name=definition.name,
                                description=definition.description,
                                category=category,
                                icon_path=definition.icon_path,
                                max_stack=definition.properties.get("max_stack", 16),
                                effect_value=definition.properties.get("thirst_value", 2),
                                effect_type="thirst"
                            )
                        elif category == ItemCategory.TOOL:
                            tool_type_str = definition.properties.get("tool_type", "axe")
                            tool_type = ToolType.AXE
                            try:
                                tool_type = ToolType(tool_type_str)
                            except ValueError:
                                pass
                            
                            properties = ToolProperties(
                                item_id=definition.item_id,
                                name=definition.name,
                                description=definition.description,
                                category=category,
                                icon_path=definition.icon_path,
                                tool_type=tool_type,
                                durability=definition.properties.get("durability", 100),
                                effectiveness=definition.properties.get("effectiveness", 1.0)
                            )
                        elif category == ItemCategory.SCHEMATIC:
                            structure_type_str = definition.properties.get("structure_type", "house")
                            structure_type = StructureType.HOUSE
                            try:
                                structure_type = StructureType(structure_type_str)
                            except ValueError:
                                pass
                            
                            properties = SchematicProperties(
                                item_id=definition.item_id,
                                name=definition.name,
                                description=definition.description,
                                category=category,
                                icon_path=definition.icon_path,
                                structure_type=structure_type,
                                width=definition.properties.get("width", 1),
                                height=definition.properties.get("height", 1),
                                required_materials=definition.properties.get("required_materials", {})
                            )
                        else:
                            properties = ItemProperties(
                                item_id=definition.item_id,
                                name=definition.name,
                                description=definition.description,
                                category=category,
                                icon_path=definition.icon_path,
                                max_stack=definition.properties.get("max_stack", 64)
                            )
                        
                        item_system.create_custom_item(properties)
                        migration_stats["migrated_definitions"] += 1
                        
                except Exception as e:
                    print(f"Error migrating definition {getattr(definition, 'item_id', 'unknown')}: {e}")
                    migration_stats["errors"] += 1
                    
        except Exception as e:
            print(f"Error accessing legacy item manager: {e}")
            migration_stats["errors"] += 1
    
    # Migrate from legacy factory if provided
    if legacy_factory and hasattr(legacy_factory, '_templates'):
        try:
            for item_id, template in legacy_factory._templates.items():
                try:
                    properties = adapter.convert_legacy_item_to_properties(template)
                    if properties:
                        item_system.create_custom_item(properties)
                        migration_stats["migrated_templates"] += 1
                except Exception as e:
                    print(f"Error migrating template {item_id}: {e}")
                    migration_stats["errors"] += 1
                    
        except Exception as e:
            print(f"Error accessing legacy factory: {e}")
            migration_stats["errors"] += 1
    
    return migration_stats

# ============================================================================
# EXPORT FOR ENGINE STUDIO
# ============================================================================

# Main classes and functions that should be available to the engine studio
__all__ = [
    # Core classes
    'ItemSystem',
    'ItemInstance',
    'ItemProperties',
    'ConsumableProperties',
    'ToolProperties',
    'SchematicProperties',
    
    # Enums
    'ItemCategory',
    'ToolType',
    'StructureType',
    
    # Factory and registry
    'ItemRegistry',
    'ItemFactory',
    
    # Managers
    'ItemDataManager',
    'IconManager',
    
    # Integration
    'AsepriteIntegration',
    'LegacyItemAdapter',
    
    # Utility functions
    'create_item_system',
    'serialize_item_instance',
    'deserialize_item_instance',
    'batch_create_items',
    'migrate_from_legacy_system',
    
    # Use handlers
    'ItemUseHandlers'
]

# Configuration for engine studio integration
ENGINE_STUDIO_CONFIG = {
    "system_name": "Item System",
    "version": "1.0.0",
    "description": "Comprehensive item management system for game engines",
    "dependencies": ["pygame"],
    "optional_dependencies": ["aseprite"],
    "data_formats": ["json"],
    "asset_formats": ["png", "jpg", "bmp"],
    "categories": [category.value for category in ItemCategory],
    "tool_types": [tool_type.value for tool_type in ToolType],
    "structure_types": [structure_type.value for structure_type in StructureType]
}

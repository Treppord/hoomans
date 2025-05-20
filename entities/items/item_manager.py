"""
Item Manager - Central system for managing game items
Provides a streamlined workflow for creating and managing different item types
"""
import os
import json
import pygame
from typing import Dict, List, Optional, Any, Tuple, Callable

from entities.items.item_base import Item
from entities.items.consumable import FoodItem, WaterBottleItem, ConsumableItem
from entities.items.tool import ToolItem, AxeItem, PickaxeItem
from entities.items.item_factory import ItemFactory

# Define item categories
ITEM_CATEGORIES = {
    "resource": "Basic resources like stones, wood, etc.",
    "food": "Consumable items that restore hunger",
    "water": "Consumable items that restore thirst",
    "tool": "Tools like axes, pickaxes, etc.",
    "weapon": "Weapons for combat",
    "schematic": "Building plans for structures",
    "special": "Special or unique items"
}

class ItemDefinition:
    """Represents a complete item definition that can be saved/loaded"""
    
    def __init__(self, 
                 item_id: str, 
                 name: str, 
                 description: str, 
                 category: str,
                 icon_path: str = None,
                 properties: Dict[str, Any] = None):
        """
        Initialize an item definition
        
        Args:
            item_id: Unique identifier for this item
            name: Display name
            description: Item description
            category: Item category (resource, food, tool, etc.)
            icon_path: Path to item icon
            properties: Additional properties specific to this item type
        """
        self.item_id = item_id
        self.name = name
        self.description = description
        self.category = category
        self.icon_path = icon_path
        self.properties = properties or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.item_id,
            "name": self.name,
            "description": self.description,
            "type": self.category,
            "icon": self.icon_path,
            **self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItemDefinition':
        """Create from dictionary"""
        # Extract basic properties
        item_id = data.get("id", "")
        name = data.get("name", "")
        description = data.get("description", "")
        category = data.get("type", "resource")
        icon_path = data.get("icon", "")
        
        # Extract additional properties based on category
        properties = {k: v for k, v in data.items() 
                     if k not in ["id", "name", "description", "type", "icon"]}
        
        return cls(item_id, name, description, category, icon_path, properties)


class ItemManager:
    """Central manager for all game items"""
    
    def __init__(self):
        """Initialize the item manager"""
        self.items: Dict[str, ItemDefinition] = {}
        self.categories: Dict[str, List[str]] = {category: [] for category in ITEM_CATEGORIES}
        self.data_dir = self._get_data_dir()
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load all items
        self.load_all_items()
    
    def _get_data_dir(self) -> str:
        """Get the path to the data directory"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, "data", "items")
    
    def load_all_items(self) -> None:
        """Load all item definitions from JSON files"""
        # Clear existing items
        self.items = {}
        self.categories = {category: [] for category in ITEM_CATEGORIES}
        
        # Load all JSON files in the data directory
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                        # Handle both single items and arrays of items
                        if isinstance(data, list):
                            for item_data in data:
                                self._register_item_from_dict(item_data)
                        else:
                            self._register_item_from_dict(data)
                            
                    print(f"Loaded items from {filename}")
                except Exception as e:
                    print(f"Error loading items from {filename}: {e}")
    
    def _register_item_from_dict(self, data: Dict[str, Any]) -> None:
        """Register an item from dictionary data"""
        try:
            item_def = ItemDefinition.from_dict(data)
            self.items[item_def.item_id] = item_def
            
            # Add to category list
            category = item_def.category
            if category in self.categories:
                self.categories[category].append(item_def.item_id)
            else:
                self.categories[category] = [item_def.item_id]
                
            # Register with ItemFactory
            self._register_with_factory(item_def)
        except Exception as e:
            print(f"Error registering item {data.get('id', 'unknown')}: {e}")
    
    def _register_with_factory(self, item_def: ItemDefinition) -> None:
        """Register an item with the ItemFactory"""
        # Create the appropriate item type based on category
        if item_def.category == "food":
            item = FoodItem(
                item_id=item_def.item_id,
                name=item_def.name,
                description=item_def.description,
                icon_path=item_def.icon_path,
                max_stack=item_def.properties.get("max_stack", 16),
                hunger_value=item_def.properties.get("hunger_value", 2)
            )
            ItemFactory.register_template(item)
            
        elif item_def.category == "water":
            item = WaterBottleItem(
                item_id=item_def.item_id,
                name=item_def.name,
                description=item_def.description,
                icon_path=item_def.icon_path,
                max_stack=item_def.properties.get("max_stack", 16),
                thirst_value=item_def.properties.get("thirst_value", 2)
            )
            ItemFactory.register_template(item)
            
        elif item_def.category == "tool" and item_def.properties.get("tool_type") == "axe":
            item = AxeItem(
                item_id=item_def.item_id,
                name=item_def.name,
                description=item_def.description,
                icon_path=item_def.icon_path,
                durability=item_def.properties.get("durability", 100),
                effectiveness=item_def.properties.get("effectiveness", 1.0)
            )
            ItemFactory.register_template(item)
            
        elif item_def.category == "tool" and item_def.properties.get("tool_type") == "pickaxe":
            item = PickaxeItem(
                item_id=item_def.item_id,
                name=item_def.name,
                description=item_def.description,
                icon_path=item_def.icon_path,
                durability=item_def.properties.get("durability", 100),
                effectiveness=item_def.properties.get("effectiveness", 1.0)
            )
            ItemFactory.register_template(item)
            
        elif item_def.category == "resource":
            # Basic resource item
            item = Item(
                item_id=item_def.item_id,
                name=item_def.name,
                description=item_def.description,
                icon_path=item_def.icon_path,
                max_stack=item_def.properties.get("max_stack", 64)
            )
            ItemFactory.register_template(item)
            
        elif item_def.category == "schematic":
            # Properly handle schematic items
            structure_type = item_def.properties.get("structure_type", "generic")
            
            # Create the appropriate schematic item based on structure type
            if structure_type == "house":
                from entities.items.schematic import HouseSchematicItem
                item = HouseSchematicItem(
                    item_id=item_def.item_id,
                    name=item_def.name,
                    description=item_def.description,
                    icon_path=item_def.icon_path,
                    max_stack=item_def.properties.get("max_stack", 5)
                )
            elif structure_type == "campfire":
                from entities.items.schematic import CampfireSchematicItem
                item = CampfireSchematicItem(
                    item_id=item_def.item_id,
                    name=item_def.name,
                    description=item_def.description,
                    icon_path=item_def.icon_path,
                    max_stack=item_def.properties.get("max_stack", 5)
                )
            else:
                # Generic schematic
                from entities.items.schematic import SchematicItem
                item = SchematicItem(
                    item_id=item_def.item_id,
                    name=item_def.name,
                    description=item_def.description,
                    icon_path=item_def.icon_path,
                    max_stack=item_def.properties.get("max_stack", 5),
                    structure_type=structure_type,
                    width=item_def.properties.get("width", 1),
                    height=item_def.properties.get("height", 1)
                )
            
            ItemFactory.register_template(item)
    
    def create_item(self, item_def: ItemDefinition) -> None:
        """Create a new item definition and save it"""
        # Add to memory
        self.items[item_def.item_id] = item_def
        
        # Add to category list
        category = item_def.category
        if category in self.categories:
            self.categories[category].append(item_def.item_id)
        else:
            self.categories[category] = [item_def.item_id]
        
        # Register with ItemFactory
        self._register_with_factory(item_def)
        
        # Save to file
        self.save_category(category)
    
    def update_item(self, item_def: ItemDefinition) -> None:
        """Update an existing item definition"""
        old_item = self.items.get(item_def.item_id)
        if old_item:
            # Remove from old category if changed
            if old_item.category != item_def.category:
                if old_item.category in self.categories and item_def.item_id in self.categories[old_item.category]:
                    self.categories[old_item.category].remove(item_def.item_id)
                
                # Add to new category
                if item_def.category in self.categories:
                    self.categories[item_def.category].append(item_def.item_id)
                else:
                    self.categories[item_def.category] = [item_def.item_id]
            
            # Update in memory
            self.items[item_def.item_id] = item_def
            
            # Re-register with ItemFactory
            self._register_with_factory(item_def)
            
            # Save both categories if changed
            if old_item.category != item_def.category:
                self.save_category(old_item.category)
            self.save_category(item_def.category)
        else:
            # If item doesn't exist, create it
            self.create_item(item_def)
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item definition"""
        if item_id in self.items:
            item_def = self.items[item_id]
            category = item_def.category
            
            # Remove from memory
            del self.items[item_id]
            
            # Remove from category list
            if category in self.categories and item_id in self.categories[category]:
                self.categories[category].remove(item_id)
            
            # Save category file
            self.save_category(category)
            return True
        return False
    
    def save_category(self, category: str) -> None:
        """Save all items in a category to a JSON file"""
        if category not in self.categories:
            return
            
        # Get all items in this category
        items_in_category = [self.items[item_id] for item_id in self.categories[category] 
                            if item_id in self.items]
        
        if not items_in_category:
            # If no items in category, delete the file if it exists
            file_path = os.path.join(self.data_dir, f"{category}_items.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # Convert to dictionaries
        item_dicts = [item.to_dict() for item in items_in_category]
        
        # Save to file
        file_path = os.path.join(self.data_dir, f"{category}_items.json")
        try:
            with open(file_path, 'w') as f:
                json.dump(item_dicts, f, indent=2)
            print(f"Saved {len(items_in_category)} items to {file_path}")
        except Exception as e:
            print(f"Error saving items to {file_path}: {e}")
    
    def save_all_items(self) -> None:
        """Save all items to their respective category files"""
        for category in self.categories:
            self.save_category(category)
    
    def get_item(self, item_id: str) -> Optional[ItemDefinition]:
        """Get an item definition by ID"""
        return self.items.get(item_id)
    
    def get_items_in_category(self, category: str) -> List[ItemDefinition]:
        """Get all items in a category"""
        if category not in self.categories:
            return []
        
        return [self.items[item_id] for item_id in self.categories[category] 
                if item_id in self.items]
    
    def get_all_items(self) -> List[ItemDefinition]:
        """Get all item definitions"""
        return list(self.items.values())
    
    def create_resource_item(self, item_id: str, name: str, description: str, 
                           icon_path: str = None, max_stack: int = 64) -> ItemDefinition:
        """Helper function to create a resource item"""
        properties = {
            "max_stack": max_stack
        }
        
        item_def = ItemDefinition(
            item_id=item_id,
            name=name,
            description=description,
            category="resource",
            icon_path=icon_path,
            properties=properties
        )
        
        self.create_item(item_def)
        return item_def
    
    def create_food_item(self, item_id: str, name: str, description: str, 
                        icon_path: str = None, max_stack: int = 16, 
                        hunger_value: int = 2) -> ItemDefinition:
        """Helper function to create a food item"""
        properties = {
            "max_stack": max_stack,
            "hunger_value": hunger_value
        }
        
        item_def = ItemDefinition(
            item_id=item_id,
            name=name,
            description=description,
            category="food",
            icon_path=icon_path,
            properties=properties
        )
        
        self.create_item(item_def)
        return item_def
    
    def create_water_item(self, item_id: str, name: str, description: str, 
                         icon_path: str = None, max_stack: int = 16, 
                         thirst_value: int = 2) -> ItemDefinition:
        """Helper function to create a water item"""
        properties = {
            "max_stack": max_stack,
            "thirst_value": thirst_value
        }
        
        item_def = ItemDefinition(
            item_id=item_id,
            name=name,
            description=description,
            category="water",
            icon_path=icon_path,
            properties=properties
        )
        
        self.create_item(item_def)
        return item_def
    
    def create_tool_item(self, item_id: str, name: str, description: str, 
                        tool_type: str, icon_path: str = None, 
                        durability: int = 100, effectiveness: float = 1.0) -> ItemDefinition:
        """Helper function to create a tool item"""
        properties = {
            "tool_type": tool_type,
            "durability": durability,
            "effectiveness": effectiveness,
            "max_stack": 1  # Tools typically don't stack
        }
        
        item_def = ItemDefinition(
            item_id=item_id,
            name=name,
            description=description,
            category="tool",
            icon_path=icon_path,
            properties=properties
        )
        
        self.create_item(item_def)
        return item_def
    
    def create_schematic_item(self, item_id: str, name: str, description: str, 
                            structure_type: str, icon_path: str = None, 
                            width: int = 1, height: int = 1) -> ItemDefinition:
        """Helper function to create a schematic item for building structures"""
        properties = {
            "structure_type": structure_type,
            "max_stack": 5,  # Schematics typically don't stack much
            "width": width,
            "height": height
        }
        
        item_def = ItemDefinition(
            item_id=item_id,
            name=name,
            description=description,
            category="schematic",
            icon_path=icon_path,
            properties=properties
        )
        
        self.create_item(item_def)
        return item_def

    def create_default_items(self) -> None:
        """Create a set of default items if none exist"""
        # Only create defaults if no items exist
        if self.items:
            return
            
        print("Creating default items...")
        
        # Create some basic resources
        self.create_resource_item(
            "stone", "Stone", "A common building material",
            icon_path="items/stone.png", max_stack=64
        )
        
        self.create_resource_item(
            "branch", "Branch", "Collected from trees, useful for crafting",
            icon_path="items/branch.png", max_stack=64
        )
        
        self.create_resource_item(
            "fiber", "Plant Fiber", "Used for crafting basic items",
            icon_path="items/fiber.png", max_stack=64
        )
        
        # Create some food items
        self.create_food_item(
            "apple", "Apple", "A juicy red apple that restores hunger",
            icon_path="items/apple.png", hunger_value=2
        )
        
        self.create_food_item(
            "berries", "Berries", "Small wild berries, slightly filling",
            icon_path="items/berries.png", hunger_value=1, max_stack=32
        )
        
        # Create water items
        self.create_water_item(
            "water_bottle", "Water Bottle", "A bottle of fresh water",
            icon_path="items/water_bottle.png", thirst_value=2
        )
        
        self.create_water_item(
            "canteen", "Canteen", "A large container for water",
            icon_path="items/canteen.png", thirst_value=4, max_stack=4
        )
        
        # Create tools
        self.create_tool_item(
            "stone_axe", "Stone Axe", "A crude axe made of stone",
            tool_type="axe", icon_path="items/stone_axe.png", 
            durability=50, effectiveness=0.8
        )
        
        self.create_tool_item(
            "stone_pickaxe", "Stone Pickaxe", "A crude pickaxe made of stone",
            tool_type="pickaxe", icon_path="items/stone_pickaxe.png", 
            durability=50, effectiveness=0.8
        )
        
        # Create schematics
        self.create_schematic_item(
            "house_schematic", "House Schematic", 
            "A blueprint for building a simple house",
            structure_type="house", icon_path="items/house_schematic.png"
        )
        
        self.create_schematic_item(
            "campfire_schematic", "Campfire Schematic", 
            "A blueprint for building a campfire",
            structure_type="campfire", icon_path="items/campfire_schematic.png"
        )
        
        print(f"Created {len(self.items)} default items")


# Helper functions for creating item icons

def create_placeholder_icon(name: str, color: Tuple[int, int, int]) -> str:
    """Create a placeholder icon for an item and return the path"""
    # Get the path to the assets directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    items_dir = os.path.join(project_root, "assets", "items")
    
    # Create the items directory if it doesn't exist
    if not os.path.exists(items_dir):
        os.makedirs(items_dir)
    
    # Create the icon filename
    filename = f"{name}.png"
    file_path = os.path.join(items_dir, filename)
    
    # Skip if the file already exists
    if os.path.exists(file_path):
        return f"items/{filename}"
    
    # Create a placeholder icon
    if pygame.get_init():
        surface = pygame.Surface((16, 16), pygame.SRCALPHA)
        
        # Fill with base color
        surface.fill(color)
        
        # Add a border
        pygame.draw.rect(surface, (0, 0, 0), (0, 0, 16, 16), 1)
        
        # Save the image
        pygame.image.save(surface, file_path)
        print(f"Created placeholder icon at {file_path}")
    else:
        print(f"Cannot create placeholder icon - pygame not initialized")
    
    return f"items/{filename}"


# Usage example and utility functions

def initialize_item_system():
    """Initialize the item system and ensure default items exist"""
    # Create the item manager
    manager = ItemManager()
    
    # Create default items if none exist
    manager.create_default_items()
    
    # Register all items with the ItemFactory
    for item_def in manager.get_all_items():
        manager._register_with_factory(item_def)
    
    return manager


def add_item_to_player(player, item_id: str, quantity: int = 1) -> bool:
    """Helper function to add an item to a player's inventory"""
    if not hasattr(player, 'inventory'):
        print(f"Player has no inventory")
        return False
    
    item = ItemFactory.create_item(item_id, quantity)
    if not item:
        print(f"Failed to create item {item_id}")
        return False
    
    result = player.inventory.add_item(item)
    print(f"Added {quantity}x {item_id} to player inventory: {result}")
    return result


def create_schematic_handler(structure_type: str) -> Callable:
    """Create a handler function for using a schematic item"""
    def use_schematic(user, world):
        """Use a schematic to place a structure"""
        if not world:
            print("No world available to place structure")
            return False
        
        # Get the position in front of the player based on facing direction
        x, y = user.grid_x, user.grid_y
        if user.facing == 'up':
            y -= 1
        elif user.facing == 'down':
            y += 1
        elif user.facing == 'left':
            x -= 1
        elif user.facing == 'right':
            x += 1
        
        # Place the structure
        if structure_type == "house":
            if hasattr(world, 'add_house'):
                house = world.add_house(x, y)
                return house is not None
        elif structure_type == "campfire":
            if hasattr(world, 'add_campfire'):
                campfire = world.add_campfire(x, y)
                return campfire is not None
        
        print(f"Cannot place structure of type {structure_type}")
        return False
    
    return use_schematic

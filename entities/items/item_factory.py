"""Factory for creating items from templates or definitions"""
import json
import os
from typing import Dict, Optional, List
from entities.items.item_base import Item
from entities.items.consumable import FoodItem, WaterBottleItem
from entities.items.tool import AxeItem, PickaxeItem
import pygame

class ItemFactory:
    """Factory for creating game items"""
    
    # Dictionary of registered item templates
    _templates = {}
    
    @classmethod
    def register_item_templates(cls):
        """Register all built-in item templates"""
        # Register consumables
        cls.register_template(FoodItem.create_template())
        cls.register_template(WaterBottleItem.create_template())
        
        # Register tools
        cls.register_template(AxeItem.create_template())
        cls.register_template(PickaxeItem.create_template())
        
        # Load custom items from JSON if available
        cls.load_custom_items()
    
    @classmethod
    def register_template(cls, item):
        """Register an item template"""
        cls._templates[item.item_id] = item
    
    @classmethod
    def create_item(cls, item_id, quantity=1) -> Optional[Item]:
        """Create a new item instance from a template"""
        print(f"DEBUG: ItemFactory.create_item called for {item_id} x{quantity}")
        
        # Make sure templates are registered
        if not cls._templates:
            print("DEBUG: Templates not registered, registering now...")
            cls.register_item_templates()
            
        if item_id not in cls._templates:
            print(f"WARNING: Unknown item type {item_id}")
            print(f"DEBUG: Available item types: {list(cls._templates.keys())}")
            return None
            
        # Create a new instance from the template
        template = cls._templates[item_id]
        print(f"DEBUG: Found template for {item_id}: {template.__class__.__name__}")
        
        try:
            item = template.create_instance()
            item.quantity = quantity
            print(f"DEBUG: Created item instance: {item.name} x{item.quantity}")
            
            # Ensure icon is loaded if pygame is initialized
            if item and pygame.get_init():
                item.ensure_icon_loaded()
                
            return item
        except Exception as e:
            print(f"ERROR: Failed to create item instance for {item_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    
    @classmethod
    def load_custom_items(cls):
        """Load custom item definitions from JSON files"""
        # Get the path to the items directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        items_path = os.path.join(project_root, "data", "items")
        
        # Create directory if it doesn't exist
        if not os.path.exists(items_path):
            os.makedirs(items_path)
            # Create a sample item definition
            cls._create_sample_item_definition(items_path)
            return
        
        # Load all JSON files in the items directory
        for filename in os.listdir(items_path):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(items_path, filename), 'r') as f:
                        item_data = json.load(f)
                        if isinstance(item_data, list):
                            # Handle array of items
                            for item_def in item_data:
                                cls._create_item_from_definition(item_def)
                        else:
                            # Handle single item
                            cls._create_item_from_definition(item_data)
                except Exception as e:
                    print(f"Error loading item definition from {filename}: {e}")
    
    @classmethod
    def _create_item_from_definition(cls, item_data):
        """Create an item from a JSON definition"""
        item_type = item_data.get("type", "")
        item_id = item_data.get("id", "")
        
        if not item_id:
            print("Warning: Item definition missing id")
            return
        
        # Ensure icon path is properly formatted
        icon_path = item_data.get("icon", "")
        if icon_path and not icon_path.startswith("items/"):
            icon_path = f"items/{icon_path}"
        
        # Create the appropriate item type
        if item_type == "food":
            item = FoodItem(
                item_id=item_id,
                name=item_data.get("name", "Unknown Food"),
                description=item_data.get("description", ""),
                icon_path=icon_path or "items/food_generic.png",
                max_stack=item_data.get("max_stack", 16),
                hunger_value=item_data.get("hunger_value", 2)
            )
            cls.register_template(item)
            
        elif item_type == "water":
            item = WaterBottleItem(
                item_id=item_id,
                name=item_data.get("name", "Unknown Water"),
                description=item_data.get("description", ""),
                icon_path=icon_path or "items/water_bottle.png",
                max_stack=item_data.get("max_stack", 16),
                thirst_value=item_data.get("thirst_value", 2)
            )
            cls.register_template(item)
            
        elif item_type == "axe":
            item = AxeItem(
                item_id=item_id,
                name=item_data.get("name", "Unknown Axe"),
                description=item_data.get("description", ""),
                icon_path=icon_path or "items/axe.png",
                durability=item_data.get("durability", 100),
                effectiveness=item_data.get("effectiveness", 1.0)
            )
            cls.register_template(item)
            
        elif item_type == "pickaxe":
            item = PickaxeItem(
                item_id=item_id,
                name=item_data.get("name", "Unknown Pickaxe"),
                description=item_data.get("description", ""),
                icon_path=icon_path or "items/pickaxe.png",
                durability=item_data.get("durability", 100),
                effectiveness=item_data.get("effectiveness", 1.0)
            )
            cls.register_template(item)
            
        else:
            print(f"Warning: Unknown item type '{item_type}' in definition")
    
    @classmethod
    def _create_sample_item_definition(cls, items_path):
        """Create a sample item definition file"""
        sample_items = [
            {
                "type": "food",
                "id": "apple",
                "name": "Apple",
                "description": "A juicy red apple that restores hunger.",
                "icon": "apple.png",
                "max_stack": 16,
                "hunger_value": 2
            },
            {
                "type": "water",
                "id": "canteen",
                "name": "Canteen",
                "description": "A canteen filled with fresh water.",
                "icon": "canteen.png",
                "max_stack": 4,
                "thirst_value": 4
            },
            {
                "type": "axe",
                "id": "stone_axe",
                "name": "Stone Axe",
                "description": "A crude axe made of stone.",
                "icon": "stone_axe.png",
                "durability": 50,
                "effectiveness": 0.8
            }
        ]
        
        try:
            with open(os.path.join(items_path, "sample_items.json"), 'w') as f:
                json.dump(sample_items, f, indent=2)
                print("Created sample item definitions file")
        except Exception as e:
            print(f"Error creating sample item definitions: {e}")
    
    @classmethod
    def ensure_item_assets_exist(cls):
        """Ensure that basic item assets exist, creating placeholders if needed"""
        # Get the path to the assets directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        items_dir = os.path.join(project_root, "assets", "items")
        
        # Create the items directory if it doesn't exist
        if not os.path.exists(items_dir):
            os.makedirs(items_dir)
            print(f"Created items directory at {items_dir}")
        
        # Define basic items that should have assets
        basic_items = {
            "food_generic.png": (255, 200, 100),  # Orange/brown for food
            "water_bottle.png": (100, 200, 255),  # Blue for water
            "axe.png": (150, 150, 150),           # Gray for axe
            "pickaxe.png": (180, 180, 180)        # Light gray for pickaxe
        }
        
        # Create placeholder assets if they don't exist
        for filename, color in basic_items.items():
            file_path = os.path.join(items_dir, filename)
            if not os.path.exists(file_path):
                try:
                    # Create a 16x16 placeholder image
                    if pygame.get_init():
                        surface = pygame.Surface((16, 16), pygame.SRCALPHA)
                        
                        # Fill with base color
                        surface.fill(color)
                        
                        # Add a border
                        pygame.draw.rect(surface, (0, 0, 0), (0, 0, 16, 16), 1)
                        
                        # Add some detail based on the item type
                        if "food" in filename:
                            # Draw a bite mark
                            pygame.draw.circle(surface, (0, 0, 0, 0), (12, 4), 4)
                        elif "water" in filename:
                            # Draw water level
                            pygame.draw.rect(surface, (50, 100, 200), (3, 8, 10, 5))
                        elif "axe" in filename:
                            # Draw axe head and handle
                            pygame.draw.line(surface, (100, 50, 0), (8, 2), (8, 14), 2)
                            pygame.draw.polygon(surface, (200, 200, 200), [(8, 4), (14, 2), (14, 6)])
                        elif "pickaxe" in filename:
                            # Draw pickaxe head and handle
                            pygame.draw.line(surface, (100, 50, 0), (8, 2), (8, 14), 2)
                            pygame.draw.line(surface, (200, 200, 200), (8, 3), (14, 6), 2)
                            pygame.draw.line(surface, (200, 200, 200), (8, 3), (2, 6), 2)
                        
                        # Save the image
                        pygame.image.save(surface, file_path)
                        print(f"Created placeholder item image: {file_path}")
                    else:
                        print(f"Cannot create placeholder for {filename} - pygame not initialized")
                except Exception as e:
                    print(f"Error creating placeholder for {filename}: {e}")

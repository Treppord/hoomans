"""
Item Creator Tool - In-engine tool for creating and editing game items
Integrates with Aseprite API for sprite creation and editing
"""
import os
import sys
import json
import subprocess
import tempfile
import pygame
import pygame_gui
from pygame_gui.elements import (
    UIWindow, UIButton, UITextEntryLine, UIDropDownMenu, 
    UILabel, UIPanel, UITextBox, UIImage, UISelectionList
)
from typing import Dict, List, Optional, Any, Tuple, Callable

# Add the project root to the Python path if running as standalone
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

from entities.items.item_manager import ItemManager, ItemDefinition, ITEM_CATEGORIES, create_placeholder_icon
from entities.items.item_factory import ItemFactory

class AsepriteIntegration:
    """Handles integration with Aseprite for sprite editing"""
    
    def __init__(self, aseprite_path=None):
        """Initialize Aseprite integration
        
        Args:
            aseprite_path: Path to Aseprite executable
        """
        # Use provided path if given
        if aseprite_path:
            self.aseprite_path = aseprite_path
        else:
            # Try to find Aseprite
            self.aseprite_path = self._find_aseprite()
            
            # Check for Mac Steam installation
            if not self.aseprite_path and sys.platform == "darwin":
                steam_path = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common")
                if os.path.exists(steam_path):
                    for item in os.listdir(steam_path):
                        if "Aseprite" in item:
                            possible_path = os.path.join(steam_path, item, "Aseprite.app", "Contents", "MacOS", "aseprite")
                            if os.path.exists(possible_path):
                                self.aseprite_path = possible_path
                                break
        
        self.available = self.aseprite_path is not None
        
        if not self.available:
            print("Warning: Aseprite not found. Some features will be disabled.")
            print("To enable Aseprite integration, set the correct path to Aseprite executable.")
        else:
            print(f"Found Aseprite at: {self.aseprite_path}")
    
    def _find_aseprite(self) -> Optional[str]:
        """Try to find Aseprite executable in common locations"""
        # Common paths for different operating systems
        common_paths = []
        
        # Windows
        if sys.platform == "win32":
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            
            common_paths.extend([
                os.path.join(program_files, "Aseprite", "Aseprite.exe"),
                os.path.join(program_files_x86, "Aseprite", "Aseprite.exe"),
                os.path.join(program_files, "Steam", "steamapps", "common", "Aseprite", "Aseprite.exe"),
                "C:\\Aseprite\\Aseprite.exe"
            ])
        
        # macOS
        elif sys.platform == "darwin":
            common_paths.extend([
                "/Applications/Aseprite.app/Contents/MacOS/aseprite",
                os.path.expanduser("~/Applications/Aseprite.app/Contents/MacOS/aseprite"),
                os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Aseprite/Aseprite.app/Contents/MacOS/aseprite")
            ])
        
        # Linux
        else:
            common_paths.extend([
                "/usr/bin/aseprite",
                "/usr/local/bin/aseprite",
                os.path.expanduser("~/.steam/steam/steamapps/common/Aseprite/aseprite")
            ])
        
        # Check if aseprite exists in PATH
        try:
            from shutil import which
            aseprite_in_path = which("aseprite")
            if aseprite_in_path:
                common_paths.insert(0, aseprite_in_path)
        except ImportError:
            pass
        
        # Check each path
        for path in common_paths:
            if os.path.exists(path) and os.path.isfile(path):
                return path
        
        return None
    
    def create_new_sprite(self, width=16, height=16, save_path=None) -> Optional[str]:
        """Create a new sprite with Aseprite
        
        Args:
            width: Sprite width in pixels
            height: Sprite height in pixels
            save_path: Path to save the sprite to
                
        Returns:
            Path to the saved sprite, or None if canceled or failed
        """
        if not self.available:
            print("Aseprite not available")
            return None
        
        # Create a temporary file if no save path provided
        if save_path is None:
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, f"temp_sprite_{os.getpid()}.png")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        
        # Create a simple PNG file using pygame
        try:
            # Create a blank surface
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            surface.fill((255, 255, 255, 255))  # White, fully opaque
            
            # Save as PNG
            pygame.image.save(surface, save_path)
            
            # Now open the PNG in Aseprite
            cmd = [self.aseprite_path, save_path]
            subprocess.Popen(cmd)
            
            return save_path
        except Exception as e:
            print(f"Error creating new sprite: {e}")
            return None



    
    def edit_sprite(self, sprite_path: str) -> bool:
        """Open a sprite in Aseprite for editing
        
        Args:
            sprite_path: Path to the sprite file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            print("Aseprite not available")
            return False
        
        if not os.path.exists(sprite_path):
            print(f"Sprite file not found: {sprite_path}")
            return False
        
        try:
            # Open the sprite in Aseprite
            cmd = [self.aseprite_path, sprite_path]
            subprocess.Popen(cmd)  # Use Popen to not block
            return True
        except Exception as e:
            print(f"Error opening sprite in Aseprite: {e}")
            return False
    
    def export_sprite(self, sprite_path: str, output_path: str, scale: int = 1) -> bool:
        """Export a sprite to PNG
        
        Args:
            sprite_path: Path to the sprite file
            output_path: Path to save the PNG to
            scale: Scale factor for export
            
        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            print("Aseprite not available")
            return False
        
        if not os.path.exists(sprite_path):
            print(f"Sprite file not found: {sprite_path}")
            return False
        
        # If the sprite is already a PNG, just copy it
        if sprite_path.lower().endswith('.png'):
            try:
                import shutil
                shutil.copy2(sprite_path, output_path)
                return os.path.exists(output_path)
            except Exception as e:
                print(f"Error copying PNG: {e}")
                return False
        
        # Otherwise, try to export using Aseprite
        try:
            # Export the sprite to PNG
            cmd = [
                self.aseprite_path,
                "-b",  # Batch mode
                sprite_path,
                "--scale", str(scale),  # Scale factor
                "--save-as", output_path  # Save to path
            ]
            subprocess.run(cmd, check=True)
            return os.path.exists(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error exporting sprite: {e}")
            return False



class ItemCreatorTool:
    """In-engine tool for creating and editing game items"""
    
    def __init__(self, screen_size=(1024, 768), item_manager=None):
        """Initialize the item creator tool
        
        Args:
            screen_size: Size of the tool window
            item_manager: Optional ItemManager instance
        """
        # Initialize pygame if not already initialized
        if not pygame.get_init():
            pygame.init()
        
        # Set up the display
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
        pygame.display.set_caption("Item Creator Tool")
        
        # Set up pygame_gui - use a default theme instead of loading from file
        self.ui_manager = pygame_gui.UIManager(screen_size)
        self.clock = pygame.time.Clock()
        
        # Initialize Aseprite integration with the path you provided
        aseprite_path = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Aseprite/Aseprite.app/Contents/MacOS/aseprite")
        self.aseprite = AsepriteIntegration(aseprite_path)
        
        # Initialize or get item manager
        if item_manager is None:
            from entities.items.item_manager import initialize_item_system
            self.item_manager = initialize_item_system()
        else:
            self.item_manager = item_manager
        
        # Current item being edited
        self.current_item = None
        self.current_sprite_path = None
    
        # Add file monitoring for icon updates
        self.icon_last_modified = 0
        self.icon_check_interval = 1.0  # Check every second
        self.icon_check_timer = 0
        
        # Set up UI elements
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI elements"""
        # Main layout
        self.main_panel = UIPanel(
            relative_rect=pygame.Rect((0, 0), self.screen_size),
            manager=self.ui_manager
        )
        
        # Left panel - Item list
        left_panel_width = 250
        self.left_panel = UIPanel(
            relative_rect=pygame.Rect((10, 10), (left_panel_width, self.screen_size[1] - 20)),
            manager=self.ui_manager,
            container=self.main_panel
        )
        
        # Category dropdown
        self.category_label = UILabel(
            relative_rect=pygame.Rect((10, 10), (left_panel_width - 20, 20)),
            text="Category:",
            manager=self.ui_manager,
            container=self.left_panel
        )
        
        # Fix for pygame_gui API - it uses different parameters
        self.category_dropdown = UIDropDownMenu(
            relative_rect=pygame.Rect((10, 35), (left_panel_width - 20, 30)),
            options_list=list(ITEM_CATEGORIES.keys()),
            starting_option="resource",
            manager=self.ui_manager,
            container=self.left_panel
        )
        
        # Item list
        self.item_list_label = UILabel(
            relative_rect=pygame.Rect((10, 75), (left_panel_width - 20, 20)),
            text="Items:",
            manager=self.ui_manager,
            container=self.left_panel
        )
        
        self.item_list = UISelectionList(
            relative_rect=pygame.Rect((10, 100), (left_panel_width - 20, 300)),
            item_list=[],
            manager=self.ui_manager,
            container=self.left_panel
        )
        
        # Buttons for item management
        button_width = (left_panel_width - 30) // 2
        
        self.new_item_button = UIButton(
            relative_rect=pygame.Rect((10, 410), (button_width, 30)),
            text="New Item",
            manager=self.ui_manager,
            container=self.left_panel
        )
        
        self.delete_item_button = UIButton(
            relative_rect=pygame.Rect((20 + button_width, 410), (button_width, 30)),
            text="Delete Item",
            manager=self.ui_manager,
            container=self.left_panel
        )
        
        # Right panel - Item editor
        right_panel_width = self.screen_size[0] - left_panel_width - 30
        self.right_panel = UIPanel(
            relative_rect=pygame.Rect((left_panel_width + 20, 10), (right_panel_width, self.screen_size[1] - 20)),
            manager=self.ui_manager,
            container=self.main_panel
        )
        
        # Item properties
        self.properties_label = UILabel(
            relative_rect=pygame.Rect((10, 10), (right_panel_width - 20, 20)),
            text="Item Properties:",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Item ID
        self.id_label = UILabel(
            relative_rect=pygame.Rect((10, 40), (100, 20)),
            text="Item ID:",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        self.id_entry = UITextEntryLine(
            relative_rect=pygame.Rect((120, 40), (right_panel_width - 140, 20)),
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Item Name
        self.name_label = UILabel(
            relative_rect=pygame.Rect((10, 70), (100, 20)),
            text="Name:",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        self.name_entry = UITextEntryLine(
            relative_rect=pygame.Rect((120, 70), (right_panel_width - 140, 20)),
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Item Description
        self.desc_label = UILabel(
            relative_rect=pygame.Rect((10, 100), (100, 20)),
            text="Description:",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        self.desc_entry = UITextEntryLine(
            relative_rect=pygame.Rect((120, 100), (right_panel_width - 140, 20)),
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Item Category
        self.item_category_label = UILabel(
            relative_rect=pygame.Rect((10, 130), (100, 20)),
            text="Category:",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Fix for pygame_gui API
        self.item_category_dropdown = UIDropDownMenu(
            relative_rect=pygame.Rect((120, 130), (right_panel_width - 140, 30)),
            options_list=list(ITEM_CATEGORIES.keys()),
            starting_option="resource",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Item Icon
        self.icon_label = UILabel(
            relative_rect=pygame.Rect((10, 170), (100, 20)),
            text="Icon:",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        self.icon_preview = UIPanel(
            relative_rect=pygame.Rect((120, 170), (64, 64)),
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        self.edit_icon_button = UIButton(
            relative_rect=pygame.Rect((194, 170), (150, 30)),
            text="Edit in Aseprite",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        self.create_icon_button = UIButton(
            relative_rect=pygame.Rect((194, 204), (150, 30)),
            text="Create New Icon",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Dynamic properties section
        self.properties_section_label = UILabel(
            relative_rect=pygame.Rect((10, 250), (right_panel_width - 20, 20)),
            text="Category-Specific Properties:",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # This will be populated dynamically based on the selected category
        self.property_widgets = {}
        self.property_labels = {}
        
        # Save button
        self.save_button = UIButton(
            relative_rect=pygame.Rect((right_panel_width - 100, self.screen_size[1] - 80), (90, 30)),
            text="Save Item",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Status message
        self.status_label = UILabel(
            relative_rect=pygame.Rect((10, self.screen_size[1] - 80), (right_panel_width - 120, 30)),
            text="",
            manager=self.ui_manager,
            container=self.right_panel
        )
        
        # Populate the item list
        self._update_item_list()
    
    def _update_item_list(self):
        """Update the item list based on the selected category"""
        category = self.category_dropdown.selected_option
        
        # Ensure category is a string
        if isinstance(category, tuple):
            category = category[0]
        
        items = self.item_manager.get_items_in_category(category)
        
        # Create a list of item names with their IDs
        item_list = [f"{item.name} ({item.item_id})" for item in items]
        
        # Update the selection list
        self.item_list.set_item_list(item_list)

    def _create_property_widgets(self):
        """Create property widgets based on the selected category"""
        # Clear existing property widgets
        for widget in self.property_widgets.values():
            widget.kill()
        for label in self.property_labels.values():
            label.kill()
        
        self.property_widgets = {}
        self.property_labels = {}
        
        # Get the selected category
        category = self.item_category_dropdown.selected_option
        
        # Define properties for each category
        properties = {}
        
        if category == "resource":
            properties = {
                "max_stack": {"type": "int", "default": 64, "label": "Max Stack Size"}
            }
        elif category == "food":
            properties = {
                "max_stack": {"type": "int", "default": 16, "label": "Max Stack Size"},
                "hunger_value": {"type": "int", "default": 2, "label": "Hunger Value"}
            }
        elif category == "water":
            properties = {
                "max_stack": {"type": "int", "default": 16, "label": "Max Stack Size"},
                "thirst_value": {"type": "int", "default": 2, "label": "Thirst Value"}
            }
        elif category == "tool":
            properties = {
                "tool_type": {"type": "dropdown", "options": ["axe", "pickaxe"], "default": "axe", "label": "Tool Type"},
                "durability": {"type": "int", "default": 100, "label": "Durability"},
                "effectiveness": {"type": "float", "default": 1.0, "label": "Effectiveness"}
            }
        elif category == "schematic":
            properties = {
                "structure_type": {"type": "dropdown", "options": ["house", "campfire"], "default": "house", "label": "Structure Type"}
            }
        
        # Create widgets for each property
        y_offset = 280
        for prop_name, prop_info in properties.items():
            # Create label
            label = UILabel(
                relative_rect=pygame.Rect((10, y_offset), (150, 20)),
                text=prop_info["label"] + ":",
                manager=self.ui_manager,
                container=self.right_panel
            )
            self.property_labels[prop_name] = label
            
            # Create widget based on property type
            if prop_info["type"] == "int" or prop_info["type"] == "float":
                widget = UITextEntryLine(
                    relative_rect=pygame.Rect((170, y_offset), (150, 20)),
                    manager=self.ui_manager,
                    container=self.right_panel
                )
                widget.set_text(str(prop_info["default"]))
            elif prop_info["type"] == "dropdown":
                # Fix for pygame_gui API
                widget = UIDropDownMenu(
                    relative_rect=pygame.Rect((170, y_offset), (150, 30)),
                    options_list=prop_info["options"],
                    starting_option=prop_info["default"],
                    manager=self.ui_manager,
                    container=self.right_panel
                )
            
            self.property_widgets[prop_name] = widget
            y_offset += 40
    
    def _get_property_values(self):
        """Get the values of all property widgets"""
        values = {}
        
        for prop_name, widget in self.property_widgets.items():
            if isinstance(widget, UITextEntryLine):
                # Try to convert to appropriate type
                try:
                    if "float" in prop_name or prop_name == "effectiveness":
                        values[prop_name] = float(widget.get_text())
                    else:
                        values[prop_name] = int(widget.get_text())
                except ValueError:
                    # Default to string if conversion fails
                    values[prop_name] = widget.get_text()
            elif isinstance(widget, UIDropDownMenu):
                values[prop_name] = widget.selected_option
        
        return values
    
    def _set_property_values(self, properties):
        """Set the values of property widgets from a dictionary"""
        for prop_name, value in properties.items():
            if prop_name in self.property_widgets:
                widget = self.property_widgets[prop_name]
                if isinstance(widget, UITextEntryLine):
                    widget.set_text(str(value))
                elif isinstance(widget, UIDropDownMenu):
                    if value in widget.options_list:
                        widget.selected_option = value
    
    def _load_item(self, item_id):
        """Load an item for editing"""
        item = self.item_manager.get_item(item_id)
        if not item:
            self.status_label.set_text(f"Error: Item {item_id} not found")
            return
        
        # Set current item
        self.current_item = item
        
        # Update UI with item properties
        self.id_entry.set_text(item.item_id)
        self.name_entry.set_text(item.name)
        self.desc_entry.set_text(item.description)
        self.item_category_dropdown.selected_option = item.category
        
        # Create property widgets for this category
        self._create_property_widgets()
        
        # Set property values
        self._set_property_values(item.properties)
        
        # Load icon preview
        self._load_icon_preview(item.icon_path)
        
        self.status_label.set_text(f"Loaded item: {item.name}")
    
    def _check_icon_updates(self, time_delta):
        """Check if the current icon file has been modified and reload if needed"""
        if not self.current_sprite_path or not os.path.exists(self.current_sprite_path):
            return
            
        # Update timer
        self.icon_check_timer += time_delta
        if self.icon_check_timer < self.icon_check_interval:
            return
            
        # Reset timer
        self.icon_check_timer = 0
        
        # Check if file has been modified
        try:
            modified_time = os.path.getmtime(self.current_sprite_path)
            if modified_time > self.icon_last_modified:
                # File has been modified, reload icon
                self.icon_last_modified = modified_time
                self._reload_icon_preview()
        except Exception as e:
            print(f"Error checking icon modification time: {e}")

    def _reload_icon_preview(self):
        """Reload the current icon preview"""
        if not self.current_sprite_path or not os.path.exists(self.current_sprite_path):
            return
            
        try:
            # Kill existing image if any
            if hasattr(self, 'icon_image') and self.icon_image:
                self.icon_image.kill()
            
            # Load the image directly from file
            image_surface = pygame.image.load(self.current_sprite_path)
            
            # Create a new image
            self.icon_image = UIImage(
                relative_rect=pygame.Rect((0, 0), (64, 64)),
                image_surface=image_surface,
                manager=self.ui_manager,
                container=self.icon_preview
            )
            
            print(f"Reloaded icon from {self.current_sprite_path}")
        except Exception as e:
            print(f"Error reloading icon: {e}")

    def _load_icon_preview(self, icon_path):
        """Load and display the item icon"""
        if not icon_path:
            return
        
        # Get the full path to the icon
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if icon_path.startswith("items/"):
            icon_path = os.path.join(project_root, "assets", icon_path)
        else:
            icon_path = os.path.join(project_root, "assets", "items", icon_path)
        
        # Check if the file exists
        if not os.path.exists(icon_path):
            print(f"Warning: Item icon not found: {icon_path}")
            return
        
        # Store the current sprite path
        self.current_sprite_path = icon_path
        
        # Store the last modified time
        try:
            self.icon_last_modified = os.path.getmtime(icon_path)
        except Exception:
            self.icon_last_modified = 0
        
        # Load the icon
        try:
            # Kill existing image if any
            if hasattr(self, 'icon_image') and self.icon_image:
                self.icon_image.kill()
            
            # Create a new image
            self.icon_image = UIImage(
                relative_rect=pygame.Rect((0, 0), (64, 64)),
                image_surface=pygame.image.load(icon_path),
                manager=self.ui_manager,
                container=self.icon_preview
            )
        except Exception as e:
            print(f"Error loading icon: {e}")


    
    def _create_new_item(self):
        """Create a new item"""
        # Generate a unique ID
        base_id = "new_item"
        item_id = base_id
        counter = 1
        
        while self.item_manager.get_item(item_id):
            item_id = f"{base_id}_{counter}"
            counter += 1
        
        # Get the selected category as a string
        category = self.category_dropdown.selected_option
        if isinstance(category, tuple):
            category = category[0]  # Take the first element if it's a tuple
        
        # Create a new item definition
        item = ItemDefinition(
            item_id=item_id,
            name="New Item",
            description="A new item",
            category=category,
            icon_path=None,
            properties={}
        )
        
        # Set as current item
        self.current_item = item
        
        # Update UI
        self.id_entry.set_text(item.item_id)
        self.name_entry.set_text(item.name)
        self.desc_entry.set_text(item.description)
        self.item_category_dropdown.selected_option = category
        
        # Create property widgets
        self._create_property_widgets()
        
        # Clear icon preview
        if hasattr(self, 'icon_image') and self.icon_image:
            self.icon_image.kill()
            self.icon_image = None
        
        self.current_sprite_path = None
        
        self.status_label.set_text("Created new item")
    
    def _save_current_item(self):
        """Save the current item"""
        if not self.current_item:
            self.status_label.set_text("No item to save")
            return
        
        # Get values from UI
        item_id = self.id_entry.get_text()
        name = self.name_entry.get_text()
        description = self.desc_entry.get_text()
        category = self.item_category_dropdown.selected_option
        
        # Ensure category is a string
        if isinstance(category, tuple):
            category = category[0]
        
        # Validate
        if not item_id or not name:
            self.status_label.set_text("Error: Item ID and Name are required")
            return
        
        # Check if ID changed and already exists
        if item_id != self.current_item.item_id and self.item_manager.get_item(item_id):
            self.status_label.set_text(f"Error: Item ID {item_id} already exists")
            return
        
        # Get icon path
        icon_path = self.current_item.icon_path
        if self.current_sprite_path:
            # Extract relative path for storage
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            assets_dir = os.path.join(project_root, "assets")
            
            if self.current_sprite_path.startswith(assets_dir):
                rel_path = os.path.relpath(self.current_sprite_path, assets_dir)
                icon_path = rel_path.replace("\\", "/")  # Normalize path separators
            else:
                icon_path = os.path.basename(self.current_sprite_path)
                if not icon_path.startswith("items/"):
                    icon_path = f"items/{icon_path}"
        
        # Get property values
        properties = self._get_property_values()
        
        # Create or update item definition
        item_def = ItemDefinition(
            item_id=item_id,
            name=name,
            description=description,
            category=category,
            icon_path=icon_path,
            properties=properties
        )
        
        # Save to item manager
        if item_id == self.current_item.item_id:
            self.item_manager.update_item(item_def)
        else:
            # If ID changed, delete old item
            if self.item_manager.get_item(self.current_item.item_id):
                self.item_manager.delete_item(self.current_item.item_id)
            
            # Create new item
            self.item_manager.create_item(item_def)
        
        # Update current item
        self.current_item = item_def
        
        # Update item list
        self._update_item_list()
        
        # Update status
        self.status_label.set_text(f"Saved item: {name}")

    
    def _delete_current_item(self):
        """Delete the current item"""
        if not self.current_item:
            self.status_label.set_text("No item to delete")
            return
        
        # Confirm deletion
        # In a real implementation, you'd show a confirmation dialog
        # For simplicity, we'll just delete without confirmation
        
        item_id = self.current_item.item_id
        item_name = self.current_item.name
        
        # Delete from item manager
        if self.item_manager.delete_item(item_id):
            self.status_label.set_text(f"Deleted item: {item_name}")
            
            # Clear current item
            self.current_item = None
            
            # Clear UI
            self.id_entry.set_text("")
            self.name_entry.set_text("")
            self.desc_entry.set_text("")
            
            # Clear icon preview
            if hasattr(self, 'icon_image') and self.icon_image:
                self.icon_image.kill()
                self.icon_image = None
            
            self.current_sprite_path = None
            
            # Update item list
            self._update_item_list()
        else:
            self.status_label.set_text(f"Error: Failed to delete item {item_id}")
    
    def _edit_icon_in_aseprite(self):
        """Edit the current item's icon in Aseprite"""
        if not self.aseprite.available:
            self.status_label.set_text("Error: Aseprite not available")
            return
        
        if not self.current_item:
            self.status_label.set_text("No item selected")
            return
        
        # If we have a current sprite path, edit it
        if self.current_sprite_path and os.path.exists(self.current_sprite_path):
            self.aseprite.edit_sprite(self.current_sprite_path)
            self.status_label.set_text(f"Editing icon in Aseprite: {os.path.basename(self.current_sprite_path)}")
            return
        
        # Otherwise, create a new icon
        self._create_new_icon()
    
    def _create_new_icon(self):
        """Create a new icon for the current item"""
        if not self.aseprite.available:
            self.status_label.set_text("Error: Aseprite not available")
            return
        
        if not self.current_item:
            self.status_label.set_text("No item selected")
            return
        
        # Create a filename based on item ID
        item_id = self.id_entry.get_text() or self.current_item.item_id
        filename = f"{item_id}.png"
        
        # Get the path to save the icon
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        items_dir = os.path.join(project_root, "assets", "items")
        
        # Create the directory if it doesn't exist
        os.makedirs(items_dir, exist_ok=True)
        
        # Full path to the icon
        icon_path = os.path.join(items_dir, filename)
        
        # Create a new sprite directly in the assets directory
        try:
            # Create a blank surface
            surface = pygame.Surface((16, 16), pygame.SRCALPHA)
            surface.fill((255, 255, 255, 255))  # White, fully opaque
            
            # Save as PNG
            pygame.image.save(surface, icon_path)
            
            # Now open the PNG in Aseprite
            cmd = [self.aseprite.aseprite_path, icon_path]
            subprocess.Popen(cmd)
            
            # Update current sprite path
            self.current_sprite_path = icon_path
            
            # Update icon preview
            self._load_icon_preview(f"items/{filename}")
            
            # Update item icon path
            self.current_item.icon_path = f"items/{filename}"
            
            self.status_label.set_text(f"Created new icon: {filename}")
        except Exception as e:
            print(f"Error creating new icon: {e}")
            self.status_label.set_text(f"Error creating icon: {str(e)}")


    
    def _handle_category_change(self):
        """Handle category change in the item list"""
        self._update_item_list()
    
    def _handle_item_category_change(self):
        """Handle category change in the item editor"""
        # Ensure we have a string category
        category = self.item_category_dropdown.selected_option
        if isinstance(category, tuple):
            category = category[0]
            self.item_category_dropdown.selected_option = category
        
        self._create_property_widgets()

    
    def _handle_item_selection(self, selected_item):
        """Handle item selection from the list"""
        if not selected_item:
            return
        
        # Extract item ID from the selection text
        # Format is "Item Name (item_id)"
        item_text = selected_item
        start_idx = item_text.rfind("(") + 1
        end_idx = item_text.rfind(")")
        
        if start_idx > 0 and end_idx > start_idx:
            item_id = item_text[start_idx:end_idx]
            self._load_item(item_id)
    
    def run(self):
        """Run the item creator tool"""
        running = True
        
        while running:
            time_delta = self.clock.tick(60) / 1000.0
            
            self._check_icon_updates(time_delta)

            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.VIDEORESIZE:
                    self.screen_size = event.size
                    self.screen = pygame.display.set_mode(self.screen_size, pygame.RESIZABLE)
                    self.ui_manager.set_window_resolution(self.screen_size)
                
                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_element == self.new_item_button:
                            self._create_new_item()
                        elif event.ui_element == self.delete_item_button:
                            self._delete_current_item()
                        elif event.ui_element == self.save_button:
                            self._save_current_item()
                        elif event.ui_element == self.edit_icon_button:
                            self._edit_icon_in_aseprite()
                        elif event.ui_element == self.create_icon_button:
                            self._create_new_icon()
                    
                    elif event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                        if event.ui_element == self.category_dropdown:
                            self._handle_category_change()
                        elif event.ui_element == self.item_category_dropdown:
                            self._handle_item_category_change()
                    
                    elif event.user_type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                        if event.ui_element == self.item_list:
                            self._handle_item_selection(event.text)
                
                self.ui_manager.process_events(event)
            
            self.ui_manager.update(time_delta)
            
            self.screen.fill((30, 30, 30))
            self.ui_manager.draw_ui(self.screen)
            
            pygame.display.update()
        
        # Save all items before exiting
        self.item_manager.save_all_items()
        
        # Sync with ItemFactory if it exists
        if hasattr(ItemFactory, 'sync_with_item_manager'):
            ItemFactory.sync_with_item_manager(self.item_manager)
        
        pygame.quit()


class SchematicItemHandler:
    """Handler for schematic items that create structures in the world"""
    
    @staticmethod
    def register_schematic_handlers():
        """Register handlers for all schematic items"""
        # Get the item manager
        from entities.items.item_manager import initialize_item_system
        item_manager = initialize_item_system()
        
        # Get all schematic items
        schematic_items = item_manager.get_items_in_category("schematic")
        
        # Register a handler for each schematic
        for item in schematic_items:
            structure_type = item.properties.get("structure_type")
            if structure_type:
                SchematicItemHandler.register_handler(item.item_id, structure_type)
    
    @staticmethod
    def register_handler(item_id, structure_type):
        """Register a handler for a specific schematic item"""
        # Get the item template from ItemFactory
        if item_id not in ItemFactory._templates:
            print(f"Warning: Item {item_id} not found in ItemFactory templates")
            return
        
        # Create a handler function
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
        
        # Assign the handler to the item template
        template = ItemFactory._templates[item_id]
        template.use = use_schematic
        
        print(f"Registered handler for schematic item: {item_id} ({structure_type})")


def launch_item_creator():
    """Launch the item creator tool"""
    # Initialize pygame if not already initialized
    if not pygame.get_init():
        pygame.init()
    
    # Create and run the tool
    tool = ItemCreatorTool()
    tool.run()


if __name__ == "__main__":
    # Run the tool as a standalone application
    launch_item_creator()

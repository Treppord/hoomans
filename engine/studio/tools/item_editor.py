"""
Item Editor Tool - Embedded tool for editing game items
"""
import pygame
import pygame_gui
import os
import sys
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from typing import Dict, Any, Optional, List
from engine.studio.studio_tools import EmbeddedTool

class ItemEditor(EmbeddedTool):
    """Embedded item editor for the studio"""
    
    def __init__(self, studio_instance, ui_manager=None):
        super().__init__(studio_instance, "item_editor", ui_manager)
        
        # Current item data
        self.current_item = {
            "id": "",
            "name": "",
            "description": "",
            "type": "consumable",
            "value": 1,
            "stackable": True,
            "max_stack": 10,
            "icon": "",
            "properties": {}
        }
        
        # Available item types
        self.item_types = ["consumable", "tool", "weapon", "material", "quest"]
        
        # UI elements
        self.main_panel = None
        self.item_list = None
        self.properties_panel = None
        
        # Items will be loaded after UI is created
        self.items = {}
    
    def _create_ui(self):
        """Create the item editor UI"""
        if not self.ui_manager:
            return
        
        # Main panel - positioned to be clearly on top
        panel_width = 1000
        panel_height = 700
        panel_x = (self.studio.screen_size[0] - panel_width) // 2
        panel_y = 80  # Start below the studio menu bar
        
        self.main_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.ui_manager
        )
        self.ui_elements.append(self.main_panel)
        
        # Title
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, panel_width - 120, 30),
            text="Item Editor",
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(title_label)
        
        # Close button
        close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_width - 100, 10, 80, 30),
            text="Close",
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(close_button)
        
        # Item list (left side)
        list_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(10, 50, 200, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(list_panel)
        
        list_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 180, 25),
            text="Items:",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(list_label)
        
        # Item list - start with empty list
        self.item_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 40, 180, 400),
            item_list=["Loading..."],
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(self.item_list)
        
        # Action buttons
        new_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 450, 80, 30),
            text="New",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(new_button)
        
        delete_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 450, 80, 30),
            text="Delete",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(delete_button)
        
        save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 490, 80, 30),
            text="Save",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(save_button)
        
        load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 490, 80, 30),
            text="Load",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(load_button)
        
        # Properties panel (right side)
        self.properties_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(220, 50, 770, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.properties_panel)
        
        # Create property fields
        self._create_property_fields()
        
        # Now load items after UI is created
        self._load_items()

    def _create_property_fields(self):
        """Create property input fields"""
        y_offset = 10
        field_height = 30
        spacing = 40
        
        # Item ID
        id_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Item ID:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(id_label)
        
        self.id_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(120, y_offset, 200, field_height),
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.id_input)
        y_offset += spacing
        
        # Item Name
        name_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Name:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(name_label)
        
        self.name_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(120, y_offset, 200, field_height),
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.name_input)
        y_offset += spacing
        
        # Description
        desc_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Description:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(desc_label)
        
        self.desc_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(120, y_offset, 400, field_height),
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.desc_input)
        y_offset += spacing
        
        # Item Type
        type_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Type:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(type_label)
        
        self.type_dropdown = pygame_gui.elements.UIDropDownMenu(
            relative_rect=pygame.Rect(120, y_offset, 150, field_height),
            options_list=self.item_types,
            starting_option="consumable",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.type_dropdown)
        y_offset += spacing
        
        # Icon section with preview
        icon_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Icon:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(icon_label)
        
        # Icon preview panel
        self.icon_preview_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(120, y_offset, 64, 64),
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.icon_preview_panel)
        
        # Icon path input
        self.icon_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(194, y_offset, 200, field_height),
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.icon_input)
        
        # Browse button
        browse_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(404, y_offset, 80, field_height),
            text="Browse",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(browse_button)
        
        # Create icon button
        create_icon_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(494, y_offset, 100, field_height),
            text="Create Icon",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(create_icon_button)
        
        y_offset += 80  # Extra space for icon
        
        # Value
        value_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Value:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(value_label)
        
        self.value_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(120, y_offset, 100, field_height),
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.value_input)
        y_offset += spacing
        
        # Stackable checkbox
        self.stackable_checkbox = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset, 150, field_height),
            text="☐ Stackable",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.stackable_checkbox)
        
        # Max stack
        stack_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(170, y_offset, 80, 25),
            text="Max Stack:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(stack_label)
        
        self.stack_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(260, y_offset, 80, field_height),
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.stack_input)
        y_offset += spacing
        
        # Properties text area
        props_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 200, 25),
            text="Custom Properties (JSON):",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(props_label)
        y_offset += 30
        
        self.properties_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, y_offset, 500, 100),
            html_text="{}",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.properties_text)
        
        # Apply button
        apply_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(520, y_offset + 70, 100, 30),
            text="Apply Changes",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(apply_button)
        
        # Load current item data into fields
        self._load_item_into_fields()

    def _load_icon_preview(self, icon_path):
        """Load and display the item icon"""
        if not icon_path:
            return
        
        # Get the full path to the icon
        if icon_path.startswith("items/"):
            full_icon_path = os.path.join(project_root, "assets", icon_path)
        else:
            full_icon_path = os.path.join(project_root, "assets", "items", icon_path)
        
        # Check if the file exists
        if not os.path.exists(full_icon_path):
            print(f"Warning: Item icon not found: {full_icon_path}")
            return
        
        try:
            # Kill existing image if any
            if hasattr(self, 'icon_image') and self.icon_image:
                self.icon_image.kill()
            
            # Load and scale the image
            icon_surface = pygame.image.load(full_icon_path)
            # Scale to fit the preview panel (64x64)
            icon_surface = pygame.transform.scale(icon_surface, (60, 60))
            
            # Create a new image element
            self.icon_image = pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(2, 2, 60, 60),
                image_surface=icon_surface,
                manager=self.ui_manager,
                container=self.icon_preview_panel
            )
            
            print(f"Loaded icon preview: {icon_path}")
            
        except Exception as e:
            print(f"Error loading icon preview: {e}")



    def _create_new_icon(self):
        """Create a new icon for the current item"""
        if not self.current_item:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text("No item selected")
            return
        
        # Create a simple placeholder icon
        item_id = self.id_input.get_text() or self.current_item.get("id", "new_item")
        filename = f"{item_id}.png"
        
        # Get the path to save the icon
        items_dir = os.path.join(project_root, "assets", "items")
        os.makedirs(items_dir, exist_ok=True)
        
        icon_path = os.path.join(items_dir, filename)
        
        try:
            # Create a simple colored square as placeholder
            icon_surface = pygame.Surface((16, 16))
            icon_surface.fill((100, 150, 200))  # Light blue
            pygame.draw.rect(icon_surface, (255, 255, 255), (1, 1, 14, 14), 1)  # White border
            
            # Save the icon
            pygame.image.save(icon_surface, icon_path)
            
            # Update the icon input and preview
            relative_path = f"items/{filename}"
            self.icon_input.set_text(relative_path)
            self.current_item["icon"] = relative_path
            self._load_icon_preview(relative_path)
            
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Created icon: {filename}")
                
        except Exception as e:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Error creating icon: {e}")
    
    def _load_item_into_fields(self):
        """Load current item data into the input fields"""
        if not hasattr(self, 'id_input') or not self.id_input:
            return  # UI not ready yet
            
        self.id_input.set_text(self.current_item.get("id", ""))
        self.name_input.set_text(self.current_item.get("name", ""))
        self.desc_input.set_text(self.current_item.get("description", ""))
        self.value_input.set_text(str(self.current_item.get("value", 1)))
        self.stack_input.set_text(str(self.current_item.get("max_stack", 10)))
        self.icon_input.set_text(self.current_item.get("icon", ""))
        
        # Update stackable checkbox
        stackable = self.current_item.get("stackable", True)
        self.stackable_checkbox.text = "☑ Stackable" if stackable else "☐ Stackable"
        
        # Update properties text
        props_json = json.dumps(self.current_item.get("properties", {}), indent=2)
        self.properties_text.html_text = f"<font face='monospace'>{props_json}</font>"
        self.properties_text.rebuild()
    
    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, 'text'):
                if event.ui_element.text == "Close":
                    self.close()
                elif event.ui_element.text == "New":
                    self._create_new_item()
                elif event.ui_element.text == "Delete":
                    self._delete_current_item()
                elif event.ui_element.text == "Save":
                    self._save_items()
                elif event.ui_element.text == "Load":
                    self._load_items()
                elif event.ui_element.text == "Apply Changes":
                    self._apply_changes()
                elif event.ui_element.text == "Browse":
                    self._browse_icon()
                elif event.ui_element.text == "Create Icon":
                    self._create_new_icon()
                elif "Stackable" in event.ui_element.text:
                    self._toggle_stackable()
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.item_list:
                self._load_selected_item(event.text)
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.type_dropdown:
                self.current_item["type"] = event.text
        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == self.icon_input:
                # Update icon preview when path changes
                icon_path = event.text.strip()
                if icon_path:
                    self._load_icon_preview(icon_path)
    
    def _create_new_item(self):
        """Create a new item"""
        self.current_item = {
            "id": "new_item",
            "name": "New Item",
            "description": "A new item",
            "type": "consumable",
            "value": 1,
            "stackable": True,
            "max_stack": 10,
            "icon": "",
            "properties": {}
        }
        self._load_item_into_fields()
        
        if hasattr(self.studio, 'status_label'):
            self.studio.status_label.set_text("Created new item")
    
    def _delete_current_item(self):
        """Delete the currently selected item"""
        item_id = self.current_item.get("id", "")
        if item_id and item_id in self.items:
            del self.items[item_id]
            self._refresh_item_list()
            self._create_new_item()  # Load empty item
            
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Deleted item: {item_id}")
    
    def _apply_changes(self):
        """Apply changes from the input fields to the current item"""
        try:
            # Get values from input fields
            item_id = self.id_input.get_text().strip()
            if not item_id:
                if hasattr(self.studio, 'status_label'):
                    self.studio.status_label.set_text("Error: Item ID cannot be empty")
                return
            
            # Remove old item if ID changed
            old_id = self.current_item.get("id", "")
            if old_id and old_id != item_id and old_id in self.items:
                del self.items[old_id]
            
            # Update current item
            self.current_item["id"] = item_id
            self.current_item["name"] = self.name_input.get_text().strip()
            self.current_item["description"] = self.desc_input.get_text().strip()
            self.current_item["type"] = self.type_dropdown.selected_option
            self.current_item["value"] = int(self.value_input.get_text() or "1")
            self.current_item["max_stack"] = int(self.stack_input.get_text() or "10")
            self.current_item["icon"] = self.icon_input.get_text().strip()
            
            # Parse properties JSON
            try:
                props_text = self.properties_text.html_text.replace('<font face=\'monospace\'>', '').replace('</font>', '')
                self.current_item["properties"] = json.loads(props_text)
            except json.JSONDecodeError:
                self.current_item["properties"] = {}
            
            # Add to items dictionary
            self.items[item_id] = self.current_item.copy()
            
            # Refresh item list
            self._refresh_item_list()
            
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Applied changes to: {item_id}")
                
        except ValueError as e:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Error: Invalid number format")
        except Exception as e:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Error applying changes: {e}")
    
    def _toggle_stackable(self):
        """Toggle the stackable property"""
        current_stackable = self.current_item.get("stackable", True)
        new_stackable = not current_stackable
        self.current_item["stackable"] = new_stackable
        self.stackable_checkbox.text = "☑ Stackable" if new_stackable else "☐ Stackable"
    
    def _browse_icon(self):
        """Browse for an icon file"""
        # For now, just show a placeholder message
        if hasattr(self.studio, 'status_label'):
            self.studio.status_label.set_text("Icon browser not implemented yet")
    
    def _load_selected_item(self, item_name):
        """Load the selected item from the list"""
        if item_name in self.items:
            self.current_item = self.items[item_name].copy()
            self._load_item_into_fields()
            
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Loaded item: {item_name}")
    
    def _refresh_item_list(self):
        """Refresh the item list UI"""
        if not self.item_list:
            return  # UI not ready yet
            
        item_names = list(self.items.keys()) if self.items else ["No items"]
        self.item_list.set_item_list(item_names)
    
    def _load_items(self):
        """Load items from file"""
        items_file = os.path.join(project_root, "data", "items.json")
        
        if os.path.exists(items_file):
            try:
                with open(items_file, 'r') as f:
                    self.items = json.load(f)
                
                self._refresh_item_list()
                
                if hasattr(self.studio, 'status_label'):
                    self.studio.status_label.set_text("Items loaded successfully")
                    
            except Exception as e:
                if hasattr(self.studio, 'status_label'):
                    self.studio.status_label.set_text(f"Error loading items: {e}")
        else:
            # Create default items
            self.items = {
                "apple": {
                    "id": "apple",
                    "name": "Apple",
                    "description": "A fresh red apple",
                    "type": "consumable",
                    "value": 2,
                    "stackable": True,
                    "max_stack": 10,
                    "icon": "assets/items/apple.png",
                    "properties": {"nutrition": 5}
                },
                "water_bottle": {
                    "id": "water_bottle",
                    "name": "Water Bottle",
                    "description": "A bottle of clean water",
                    "type": "consumable",
                    "value": 3,
                    "stackable": True,
                    "max_stack": 5,
                    "icon": "assets/items/water_bottle.png",
                    "properties": {"hydration": 3}
                }
            }
            self._refresh_item_list()
        
        return self.items
    
    def _save_items(self):
        """Save items to file"""
        try:
            # Ensure data directory exists
            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir, exist_ok=True)
            
            items_file = os.path.join(data_dir, "items.json")
            with open(items_file, 'w') as f:
                json.dump(self.items, f, indent=2)
            
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text("Items saved successfully")
                
        except Exception as e:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Error saving items: {e}")

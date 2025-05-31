"""
New Game Dialog - Dialog for creating new game configurations
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

import pygame
import pygame_gui
from typing import Optional, Callable
from config.game_config import GameConfig, SystemConfig, EntityConfig, WorldItemConfig

class NewGameDialog:
    """Dialog for creating new game configurations"""
    
    def __init__(self, ui_manager, screen_size, callback: Optional[Callable] = None):
        self.ui_manager = ui_manager
        self.screen_size = screen_size
        self.callback = callback
        self.visible = False
        self.ui_elements = []
        
        # Dialog data
        self.game_name = ""
        self.game_description = ""
        self.world_width = 256
        self.world_height = 256
        self.template = "default"
    
    def show(self):
        """Show the dialog"""
        if self.visible:
            return
        
        self.visible = True
        self._create_ui()
    
    def hide(self):
        """Hide the dialog"""
        if not self.visible:
            return
        
        self.visible = False
        self._destroy_ui()
    
    def _create_ui(self):
        """Create the dialog UI"""
        # Dialog panel
        dialog_width = 500
        dialog_height = 400
        dialog_x = (self.screen_size[0] - dialog_width) // 2
        dialog_y = (self.screen_size[1] - dialog_height) // 2
        
        self.dialog_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height),
            manager=self.ui_manager
        )
        self.ui_elements.append(self.dialog_panel)
        
        # Title
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, dialog_width - 20, 30),
            text="Create New Game Configuration",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(title_label)
        
        # Game name
        name_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 50, 100, 25),
            text="Game Name:",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(name_label)
        
        self.name_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(120, 50, 350, 25),
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.name_input.set_text("My New Game")
        self.ui_elements.append(self.name_input)
        
        # Description
        desc_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 85, 100, 25),
            text="Description:",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(desc_label)
        
        self.desc_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(120, 85, 350, 25),
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.desc_input.set_text("A new game configuration")
        self.ui_elements.append(self.desc_input)
        
        # Template selection
        template_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 120, 100, 25),
            text="Template:",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(template_label)
        
        self.template_dropdown = pygame_gui.elements.UIDropDownMenu(
            relative_rect=pygame.Rect(120, 120, 200, 25),
            options_list=["default", "minimal", "survival", "custom"],
            starting_option="default",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(self.template_dropdown)
        
        # World size
        world_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 155, 100, 25),
            text="World Size:",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(world_label)
        
        # Width
        width_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(120, 155, 50, 25),
            text="Width:",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(width_label)
        
        self.width_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(175, 155, 80, 25),
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.width_input.set_text("256")
        self.ui_elements.append(self.width_input)
        
        # Height
        height_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(270, 155, 50, 25),
            text="Height:",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(height_label)
        
        self.height_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(325, 155, 80, 25),
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.height_input.set_text("256")
        self.ui_elements.append(self.height_input)
        
        # Preview area
        preview_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 190, 100, 25),
            text="Preview:",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(preview_label)
        
        self.preview_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, 220, dialog_width - 20, 120),
            html_text="Configuration preview will appear here...",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(self.preview_text)
        
        # Buttons
        self.create_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(dialog_width - 180, dialog_height - 40, 80, 30),
            text="Create",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(self.create_button)
        
        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(dialog_width - 90, dialog_height - 40, 80, 30),
            text="Cancel",
            manager=self.ui_manager,
            container=self.dialog_panel
        )
        self.ui_elements.append(self.cancel_button)
        
        # Update preview
        self._update_preview()
    
    def _destroy_ui(self):
        """Destroy UI elements"""
        for element in self.ui_elements:
            element.kill()
        self.ui_elements.clear()
    
    def handle_event(self, event):
        """Handle dialog events"""
        if not self.visible:
            return False
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.create_button:
                self._create_game()
                return True
            elif event.ui_element == self.cancel_button:
                self.hide()
                return True
        
        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element in [self.name_input, self.desc_input, self.width_input, self.height_input]:
                self._update_preview()
        
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.template_dropdown:
                self._update_preview()
        
        return False
    
    def _update_preview(self):
        """Update the configuration preview"""
        try:
            name = self.name_input.get_text() if hasattr(self, 'name_input') else "My New Game"
            desc = self.desc_input.get_text() if hasattr(self, 'desc_input') else "A new game"
            template = self.template_dropdown.selected_option if hasattr(self, 'template_dropdown') else "default"
            width = int(self.width_input.get_text()) if hasattr(self, 'width_input') else 256
            height = int(self.height_input.get_text()) if hasattr(self, 'height_input') else 256
            
            preview_html = f"""
            <b>Name:</b> {name}<br>
            <b>Description:</b> {desc}<br>
            <b>Template:</b> {template}<br>
            <b>World Size:</b> {width}x{height}<br>
            <br>
            <b>Features based on template:</b><br>
            """
            
            if template == "default":
                preview_html += "• Standard game systems<br>• Player + 2 NPCs<br>• 30 food entities<br>• Basic items"
            elif template == "minimal":
                preview_html += "• Basic systems only<br>• Player + 5 food entities<br>• Minimal items"
            elif template == "survival":
                preview_html += "• Enhanced survival systems<br>• Player + 3 NPCs<br>• 100 food entities<br>• Extended item set"
            elif template == "custom":
                preview_html += "• Empty configuration<br>• Customize everything<br>• No default entities"
            
            if hasattr(self, 'preview_text'):
                self.preview_text.html_text = preview_html
                self.preview_text.rebuild()
                
        except ValueError:
            # Handle invalid number input
            if hasattr(self, 'preview_text'):
                self.preview_text.html_text = "<font color='#ff0000'>Invalid world size values</font>"
                self.preview_text.rebuild()
    
    def _create_game(self):
        """Create the new game configuration"""
        try:
            # Get values from inputs
            name = self.name_input.get_text()
            desc = self.desc_input.get_text()
            template = self.template_dropdown.selected_option
            width = int(self.width_input.get_text())
            height = int(self.height_input.get_text())
            
            # Validate inputs
            if not name.strip():
                self._show_error("Game name cannot be empty")
                return
            
            if width <= 0 or height <= 0:
                self._show_error("World size must be positive")
                return
            
            # Create configuration based on template
            config = self._create_config_from_template(name, desc, template, width, height)
            
            # Call callback if provided
            if self.callback:
                self.callback(config, template)
            
            # Hide dialog
            self.hide()
            
        except ValueError:
            self._show_error("Invalid world size values")
        except Exception as e:
            self._show_error(f"Error creating configuration: {e}")
    
    def _create_config_from_template(self, name: str, desc: str, template: str, width: int, height: int) -> GameConfig:
        """Create a game configuration from template"""
        if template == "minimal":
            return GameConfig(
                name=name,
                description=desc,
                world_width=width,
                world_height=height,
                systems=[
                    SystemConfig(name="entity_manager", enabled=True),
                    SystemConfig(name="world_map", enabled=True, config={"width": width, "height": height})
                ],
                entities=[
                    EntityConfig(entity_type="player", grid_x=width//2, grid_y=height//2, color=(255, 0, 0), speed=1),
                    EntityConfig(entity_type="food_npcs", count=5)
                ],
                world_items=[]
            )
        
        elif template == "survival":
            return GameConfig(
                name=name,
                description=desc,
                world_width=width,
                world_height=height,
                systems=[
                    SystemConfig(name="sound_system", enabled=True),
                    SystemConfig(name="entity_manager", enabled=True),
                    SystemConfig(name="item_system", enabled=True),
                    SystemConfig(name="world_map", enabled=True, config={"width": width, "height": height}),
                    SystemConfig(name="world_cache", enabled=True),
                    SystemConfig(name="ai_universe", enabled=True)
                ],
                entities=[
                    EntityConfig(entity_type="player", grid_x=width//2, grid_y=height//2, color=(255, 0, 0), speed=1),
                    EntityConfig(entity_type="npc", grid_x=width//2+10, grid_y=height//2+10, color=(0, 255, 0), speed=1),
                    EntityConfig(entity_type="npc", grid_x=width//2-10, grid_y=height//2-10, color=(0, 0, 255), speed=1),
                    EntityConfig(entity_type="npc", grid_x=width//2-10, grid_y=height//2-10, color=(0, 0, 255), speed=1),
                    EntityConfig(entity_type="food_npcs", count=100)
                ],
                world_items=[
                    WorldItemConfig(item_type="apple", x=width//2+5, y=width//2+5, quantity=3),
                    WorldItemConfig(item_type="water_bottle", x=width//2-5, y=width//2-5, quantity=2)
                ]
            )
        
        elif template == "custom":
            return GameConfig(
                name=name,
                description=desc,
                world_width=width,
                world_height=height,
                systems=[],
                entities=[],
                world_items=[]
            )
        
        else:  # default template
            return GameConfig(
                name=name,
                description=desc,
                world_width=width,
                world_height=height,
                systems=[
                    SystemConfig(name="sound_system", enabled=True),
                    SystemConfig(name="entity_manager", enabled=True),
                    SystemConfig(name="item_system", enabled=True),
                    SystemConfig(name="world_map", enabled=True, config={"width": width, "height": height}),
                    SystemConfig(name="world_cache", enabled=True),
                    SystemConfig(name="ai_universe", enabled=True)
                ],
                entities=[
                    EntityConfig(entity_type="player", grid_x=width//2, grid_y=height//2, color=(255, 0, 0), speed=1),
                    EntityConfig(entity_type="npc", grid_x=width//2+5, grid_y=width//2+5, color=(0, 255, 0), speed=1),
                    EntityConfig(entity_type="npc", grid_x=width//2-5, grid_y=width//2-5, color=(0, 0, 255), speed=1),
                    EntityConfig(entity_type="food_npcs", count=30)
                ],
                world_items=[
                    WorldItemConfig(item_type="apple", x=width//2+3, y=width//2+3, quantity=3),
                    WorldItemConfig(item_type="berries", x=width//2-3, y=width//2-3, quantity=1),
                    WorldItemConfig(item_type="water_bottle", x=width//2, y=width//2+5, quantity=2)
                ]
            )
    
    def _show_error(self, message: str):
        """Show an error message in the preview area"""
        if hasattr(self, 'preview_text'):
            self.preview_text.html_text = f"<font color='#ff0000'>Error: {message}</font>"
            self.preview_text.rebuild()
    
    def is_visible(self) -> bool:
        """Check if dialog is visible"""
        return self.visible

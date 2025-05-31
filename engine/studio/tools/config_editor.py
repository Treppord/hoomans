"""
Configuration Editor Tool - Embedded tool for editing game configurations
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
from config.game_loader import GameConfigLoader

class ConfigEditor(EmbeddedTool):
    """Embedded configuration editor for the studio"""
    
    def __init__(self, studio_instance, ui_manager=None):
        super().__init__(studio_instance, "config_editor", ui_manager)
        
        self.config_loader = GameConfigLoader()
        self.current_config = None
        self.current_config_name = ""
        
        # UI elements
        self.main_panel = None
        self.config_list = None
        self.properties_panel = None
    
    def _create_ui(self):
        """Create the config editor UI"""
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
            text="Configuration Editor",
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
        
        # Config list (left side)
        list_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(10, 50, 200, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(list_panel)
        
        list_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 180, 25),
            text="Configurations:",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(list_label)
        
        # Config list
        config_names = self.config_loader.list_available_games()
        self.config_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 40, 180, 400),
            item_list=config_names,
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(self.config_list)
        
        # Action buttons
        new_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 450, 80, 30),
            text="New",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(new_button)
        
        duplicate_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 450, 80, 30),
            text="Duplicate",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(duplicate_button)
        
        save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 490, 80, 30),
            text="Save",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(save_button)
        
        validate_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 490, 80, 30),
            text="Validate",
            manager=self.ui_manager,
            container=list_panel
        )
        self.ui_elements.append(validate_button)
        
        # Properties panel (right side)
        self.properties_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(220, 50, 770, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.properties_panel)
        
        # Properties display
        props_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 200, 25),
            text="Configuration Properties:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(props_label)
        
        self.properties_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, 40, 750, 550),
            html_text="Select a configuration to view properties",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.properties_text)

    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, 'text'):
                if event.ui_element.text == "Close":
                    self.close()
                elif event.ui_element.text == "New":
                    self._create_new_config()
                elif event.ui_element.text == "Duplicate":
                    self._duplicate_config()
                elif event.ui_element.text == "Save":
                    self._save_config()
                elif event.ui_element.text == "Validate":
                    self._validate_config()
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.config_list:
                self._load_selected_config(event.text)
    
    def _load_selected_config(self, config_name):
        """Load the selected configuration"""
        try:
            self.current_config = self.config_loader.get_game_config(config_name)
            self.current_config_name = config_name
            
            # Display config properties
            config_info = self.config_loader.get_game_info(config_name)
            
            html_text = f"""
            <b>Configuration: {config_name}</b><br><br>
            <b>Name:</b> {config_info['name']}<br>
            <b>Description:</b> {config_info['description']}<br>
            <b>World Size:</b> {config_info['world_size']}<br>
            <b>Entities:</b> {config_info['entity_count']}<br>
            <b>Systems:</b> {config_info['system_count']}<br><br>
            <b>Systems:</b><br>
            """
            
            # Add system details
            for system in self.current_config.systems:
                status = "Enabled" if system.enabled else "Disabled"
                html_text += f"  • {system.name}: {status}<br>"
            
            html_text += "<br><b>Entities:</b><br>"
            
            # Add entity details
            for entity in self.current_config.entities:
                if entity.entity_type == "food_npcs":
                    html_text += f"  • {entity.count}x Food NPCs<br>"
                else:
                    pos = f"({entity.grid_x}, {entity.grid_y})" if entity.grid_x is not None else "Random"
                    html_text += f"  • {entity.entity_type} at {pos}<br>"
            
            html_text += "<br><b>World Items:</b><br>"
            
            # Add world item details
            for item in self.current_config.world_items:
                html_text += f"  • {item.quantity}x {item.item_type} at ({item.x}, {item.y})<br>"
            
            self.properties_text.html_text = html_text
            self.properties_text.rebuild()
            
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Loaded config: {config_name}")
                
        except Exception as e:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Error loading config: {e}")
    
    def _create_new_config(self):
        """Create a new configuration"""
        if hasattr(self.studio, 'status_label'):
            self.studio.status_label.set_text("New config creation not implemented yet")
    
    def _duplicate_config(self):
        """Duplicate the current configuration"""
        if hasattr(self.studio, 'status_label'):
            self.studio.status_label.set_text("Config duplication not implemented yet")
    
    def _save_config(self):
        """Save the current configuration"""
        if hasattr(self.studio, 'status_label'):
            self.studio.status_label.set_text("Config saving not implemented yet")
    
    def _validate_config(self):
        """Validate the current configuration"""
        if not self.current_config:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text("No config selected for validation")
            return
        
        try:
            from tools.config_validator import ConfigValidator
            validator = ConfigValidator()
            is_valid = validator.validate_config(self.current_config)
            
            report = validator.get_validation_report()
            
            # Display validation results
            html_text = f"<b>Validation Results for {self.current_config_name}:</b><br><br>"
            html_text += f"<b>Status:</b> {'Valid' if is_valid else 'Invalid'}<br><br>"
            html_text += report.replace('\n', '<br>')
            
            self.properties_text.html_text = html_text
            self.properties_text.rebuild()
            
            status = "Config is valid" if is_valid else "Config has errors"
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(status)
                
        except ImportError:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text("Config validator not available")
        except Exception as e:
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Validation error: {e}")

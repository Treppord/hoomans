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
        
        # Work with the currently loaded game
        self.current_config = studio_instance.current_game
        self.current_config_name = self._get_current_game_name()
        
        # UI elements
        self.main_panel = None
        self.properties_panel = None
        self.config_tree = None
        self.value_editor = None
        self.selected_property = None
    
    def _create_ui(self):
        """Create the config editor UI"""
        if not self.ui_manager:
            return
        
        # Main panel
        panel_width = 1200
        panel_height = 800
        panel_x = (self.studio.screen_size[0] - panel_width) // 2
        panel_y = 80
        
        self.main_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.ui_manager
        )
        self.ui_elements.append(self.main_panel)
        
        # Title with current game name
        title_text = f"Configuration Editor - {self.current_config_name}" if self.current_config else "Configuration Editor - No Game Loaded"
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, panel_width - 120, 30),
            text=title_text,
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
        
        if not self.current_config:
            # Show message if no game is loaded
            no_game_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(50, 100, panel_width - 100, 50),
                text="No game loaded. Please load a game first.",
                manager=self.ui_manager,
                container=self.main_panel
            )
            self.ui_elements.append(no_game_label)
            return
        
        # Configuration tree (left side)
        tree_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(10, 50, 400, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(tree_panel)
        
        tree_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 380, 25),
            text="Configuration Properties:",
            manager=self.ui_manager,
            container=tree_panel
        )
        self.ui_elements.append(tree_label)
        
        # Create property list
        property_items = self._build_property_list()
        self.config_tree = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 40, 380, 500),
            item_list=property_items,
            manager=self.ui_manager,
            container=tree_panel
        )
        self.ui_elements.append(self.config_tree)
        
        # Action buttons
        save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 550, 80, 30),
            text="Save",
            manager=self.ui_manager,
            container=tree_panel
        )
        self.ui_elements.append(save_button)
        
        validate_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 550, 80, 30),
            text="Validate",
            manager=self.ui_manager,
            container=tree_panel
        )
        self.ui_elements.append(validate_button)
        
        reset_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(190, 550, 80, 30),
            text="Reset",
            manager=self.ui_manager,
            container=tree_panel
        )
        self.ui_elements.append(reset_button)
        
        # Value editor panel (right side)
        self.properties_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(420, 50, 770, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.properties_panel)
        
        # Properties display
        props_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 200, 25),
            text="Property Editor:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(props_label)
        
        self.value_editor = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, 40, 750, 650),
            html_text="Select a property to edit its value",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.value_editor)
    
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
    

    



    def _get_current_game_name(self):
        """Get the name of the currently loaded game"""
        if not self.current_config:
            return "No Game Loaded"
        
        # Find the game name from the config loader
        for name in self.studio.config_loader.list_available_games():
            try:
                config = self.studio.config_loader.get_game_config(name)
                if config.name == self.current_config.name:
                    return name
            except:
                continue
        return self.current_config.name



    def _build_property_list(self):
        """Build a list of editable properties"""
        if not self.current_config:
            return []
        
        properties = []
        
        # Basic config properties
        properties.append("📋 Basic Settings")
        properties.append("  • Name")
        properties.append("  • Description")
        properties.append("  • World Width")
        properties.append("  • World Height")
        
        # Systems
        properties.append("⚙️ Systems")
        for i, system in enumerate(self.current_config.systems):
            status = "✅" if system.enabled else "❌"
            properties.append(f"  • {status} {system.name}")
        
        # Entities
        properties.append("👤 Entities")
        for i, entity in enumerate(self.current_config.entities):
            if entity.entity_type == "food_npcs":
                properties.append(f"  • {entity.count}x {entity.entity_type}")
            else:
                pos = f"({entity.grid_x}, {entity.grid_y})" if entity.grid_x is not None else "Random"
                properties.append(f"  • {entity.entity_type} at {pos}")
        
        # World Items
        properties.append("🎒 World Items")
        for i, item in enumerate(self.current_config.world_items):
            properties.append(f"  • {item.quantity}x {item.item_type} at ({item.x}, {item.y})")
        
        return properties

    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, 'text'):
                if event.ui_element.text == "Close":
                    self.close()
                elif event.ui_element.text == "Save":
                    self._save_config()
                elif event.ui_element.text == "Validate":
                    self._validate_config()
                elif event.ui_element.text == "Reset":
                    self._reset_config()
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.config_tree:
                self._edit_selected_property(event.text)

    def _edit_selected_property(self, property_text):
        """Edit the selected property"""
        if not self.current_config:
            return
        
        self.selected_property = property_text.strip()
        
        # Parse the property and show editor
        if "Name" in property_text and "📋" not in property_text:
            self._show_text_editor("Game Name", self.current_config.name, "name")
        elif "Description" in property_text:
            self._show_text_editor("Game Description", self.current_config.description, "description")
        elif "World Width" in property_text:
            self._show_number_editor("World Width", self.current_config.world_width, "world_width")
        elif "World Height" in property_text:
            self._show_number_editor("World Height", self.current_config.world_height, "world_height")
        elif "⚙️" in property_text or "👤" in property_text or "🎒" in property_text:
            # Category headers - show info
            self._show_category_info(property_text)
        elif any(symbol in property_text for symbol in ["✅", "❌"]):
            # System toggle
            self._show_system_editor(property_text)
        elif "x " in property_text and ("entity" in property_text or "item" in property_text):
            # Entity or item editor
            self._show_entity_item_editor(property_text)
        else:
            self.value_editor.html_text = f"<b>Selected:</b> {property_text}<br><br>This property is not yet editable."
            self.value_editor.rebuild()

    def _show_text_editor(self, title, current_value, property_key):
        """Show text editor for string properties"""
        html_text = f"""
        <b>{title}</b><br><br>
        <b>Current Value:</b> {current_value}<br><br>
        <b>Instructions:</b><br>
        This property can be edited by modifying the configuration file directly.<br>
        Property key: <code>{property_key}</code><br><br>
        <b>Example:</b><br>
        <code>config.{property_key} = "New Value"</code>
        """
        self.value_editor.html_text = html_text
        self.value_editor.rebuild()

    def _show_number_editor(self, title, current_value, property_key):
        """Show number editor for numeric properties"""
        html_text = f"""
        <b>{title}</b><br><br>
        <b>Current Value:</b> {current_value}<br><br>
        <b>Instructions:</b><br>
        This numeric property can be edited by modifying the configuration file.<br>
        Property key: <code>{property_key}</code><br><br>
        <b>Example:</b><br>
        <code>config.{property_key} = {current_value + 50}</code><br><br>
        <b>Valid Range:</b> 1 - 1000
        """
        self.value_editor.html_text = html_text
        self.value_editor.rebuild()

    def _show_system_editor(self, system_text):
        """Show system enable/disable editor"""
        # Extract system name
        system_name = system_text.split(" ", 2)[-1] if len(system_text.split(" ")) > 2 else "Unknown"
        
        # Find the system
        target_system = None
        for system in self.current_config.systems:
            if system.name == system_name:
                target_system = system
                break
        
        if target_system:
            status = "Enabled" if target_system.enabled else "Disabled"
            html_text = f"""
            <b>System: {system_name}</b><br><br>
            <b>Current Status:</b> {status}<br><br>
            <b>Instructions:</b><br>
            To toggle this system, modify the configuration file:<br><br>
            <b>Find the system in the systems list:</b><br>
            <code>SystemConfig(name="{system_name}", enabled={str(target_system.enabled)})</code><br><br>
            <b>Change enabled to:</b><br>
            <code>SystemConfig(name="{system_name}", enabled={str(not target_system.enabled)})</code>
            """
        else:
            html_text = f"<b>System not found:</b> {system_name}"
        
        self.value_editor.html_text = html_text
        self.value_editor.rebuild()

    def _show_category_info(self, category_text):
        """Show information about a category"""
        if "📋" in category_text:
            html_text = """
            <b>Basic Settings</b><br><br>
            Configure fundamental game properties:<br>
            • <b>Name:</b> Display name of the game<br>
            • <b>Description:</b> Game description<br>
            • <b>World Width:</b> Width of the game world in tiles<br>
            • <b>World Height:</b> Height of the game world in tiles<br><br>
            Select a specific property to edit it.
            """
        elif "⚙️" in category_text:
            enabled_count = len([s for s in self.current_config.systems if s.enabled])
            total_count = len(self.current_config.systems)
            html_text = f"""
            <b>Systems Configuration</b><br><br>
            <b>Status:</b> {enabled_count}/{total_count} systems enabled<br><br>
            <b>Available Systems:</b><br>
            """
            for system in self.current_config.systems:
                status = "✅ Enabled" if system.enabled else "❌ Disabled"
                html_text += f"• <b>{system.name}:</b> {status}<br>"
            html_text += "<br>Click on a system to toggle it."
        elif "👤" in category_text:
            html_text = f"""
            <b>Entities Configuration</b><br><br>
            <b>Total Entities:</b> {len(self.current_config.entities)}<br><br>
            <b>Entity List:</b><br>
            """
            for entity in self.current_config.entities:
                if entity.entity_type == "food_npcs":
                    html_text += f"• <b>{entity.entity_type}:</b> {entity.count} instances<br>"
                else:
                    pos = f"({entity.grid_x}, {entity.grid_y})" if entity.grid_x is not None else "Random position"
                    html_text += f"• <b>{entity.entity_type}:</b> at {pos}<br>"
        elif "🎒" in category_text:
            html_text = f"""
            <b>World Items Configuration</b><br><br>
            <b>Total Items:</b> {len(self.current_config.world_items)}<br><br>
            <b>Item List:</b><br>
            """
            for item in self.current_config.world_items:
                html_text += f"• <b>{item.item_type}:</b> {item.quantity}x at ({item.x}, {item.y})<br>"
        else:
            html_text = f"<b>Category:</b> {category_text}<br><br>Select a specific item to edit."
        
        self.value_editor.html_text = html_text
        self.value_editor.rebuild()

    def _show_entity_item_editor(self, item_text):
        """Show editor for entities or items"""
        html_text = f"""
        <b>Selected Item:</b> {item_text}<br><br>
        <b>Instructions:</b><br>
        To edit this item, you need to modify the configuration file directly.<br><br>
        <b>For Entities:</b><br>
        • Modify position: <code>grid_x</code> and <code>grid_y</code><br>
        • Change color: <code>color=(R, G, B)</code><br>
        • Adjust speed: <code>speed=value</code><br>
        • For food_npcs: <code>count=number</code><br><br>
        <b>For World Items:</b><br>
        • Change position: <code>x</code> and <code>y</code><br>
        • Modify quantity: <code>quantity=number</code><br>
        • Change type: <code>item_type="new_type"</code><br><br>
        <b>Note:</b> Direct editing will be available in future updates.
        """
        self.value_editor.html_text = html_text
        self.value_editor.rebuild()


    def _save_config(self):
        """Save the current configuration"""
        if not self.current_config:
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text("No config to save")
            return
        
        try:
            # For now, show instructions on how to save
            html_text = f"""
            <b>Save Configuration</b><br><br>
            <b>Current Game:</b> {self.current_config_name}<br><br>
            <b>Instructions:</b><br>
            To save changes, you need to modify the configuration file located at:<br>
            <code>config/games/{self.current_config_name}_game.py</code><br><br>
            <b>Backup Recommendation:</b><br>
            Always create a backup before making changes:<br>
            <code>cp {self.current_config_name}_game.py {self.current_config_name}_game.py.backup</code><br><br>
            <b>Auto-save feature coming soon!</b>
            """
            
            self.value_editor.html_text = html_text
            self.value_editor.rebuild()
            
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text("Save instructions displayed")
                
        except Exception as e:
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text(f"Save error: {e}")

    def _validate_config(self):
        """Validate the current configuration"""
        if not self.current_config:
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text("No config to validate")
            return
        
        try:
            # Basic validation
            validation_results = []
            
            # Check basic properties
            if not self.current_config.name or len(self.current_config.name.strip()) == 0:
                validation_results.append("❌ Game name is empty")
            else:
                validation_results.append("✅ Game name is valid")
            
            if not self.current_config.description:
                validation_results.append("⚠️ Game description is empty")
            else:
                validation_results.append("✅ Game description is present")
            
            # Check world size
            if self.current_config.world_width <= 0 or self.current_config.world_height <= 0:
                validation_results.append("❌ Invalid world dimensions")
            else:
                validation_results.append(f"✅ World size: {self.current_config.world_width}x{self.current_config.world_height}")
            
            # Check systems
            enabled_systems = [s for s in self.current_config.systems if s.enabled]
            if len(enabled_systems) == 0:
                validation_results.append("❌ No systems enabled")
            else:
                validation_results.append(f"✅ {len(enabled_systems)} systems enabled")
            
            # Check entities
            if len(self.current_config.entities) == 0:
                validation_results.append("⚠️ No entities defined")
            else:
                validation_results.append(f"✅ {len(self.current_config.entities)} entities defined")
                
                # Check for player entity
                has_player = any(e.entity_type == "player" for e in self.current_config.entities)
                if not has_player:
                    validation_results.append("⚠️ No player entity found")
                else:
                    validation_results.append("✅ Player entity present")
            
            # Check world items
            if len(self.current_config.world_items) == 0:
                validation_results.append("⚠️ No world items defined")
            else:
                validation_results.append(f"✅ {len(self.current_config.world_items)} world items defined")
            
            # Display results
            is_valid = not any("❌" in result for result in validation_results)
            status = "✅ Configuration is valid" if is_valid else "❌ Configuration has errors"
            
            html_text = f"""
            <b>Validation Results for {self.current_config_name}</b><br><br>
            <b>Overall Status:</b> {status}<br><br>
            <b>Detailed Results:</b><br>
            """
            
            for result in validation_results:
                html_text += f"{result}<br>"
            
            html_text += "<br><b>Legend:</b><br>"
            html_text += "✅ = Valid/Good<br>"
            html_text += "⚠️ = Warning (not critical)<br>"
            html_text += "❌ = Error (needs fixing)<br>"
            
            self.value_editor.html_text = html_text
            self.value_editor.rebuild()
            
            status_msg = "Config is valid" if is_valid else "Config has errors"
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text(status_msg)
                
        except Exception as e:
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text(f"Validation error: {e}")

    def _reset_config(self):
        """Reset to original configuration"""
        if not self.current_config:
            return
        
        try:
            # Reload the original config
            original_config = self.studio.config_loader.get_game_config(self.current_config_name)
            self.current_config = original_config
            self.studio.current_game = original_config
            
            # Refresh the property list
            property_items = self._build_property_list()
            self.config_tree.set_item_list(property_items)
            self.config_tree.rebuild()
            
            self.value_editor.html_text = """
            <b>Configuration Reset</b><br><br>
            The configuration has been reset to its original values.<br>
            Any unsaved changes have been lost.<br><br>
            Select a property to continue editing.
            """
            self.value_editor.rebuild()
            
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text("Config reset to original")
                
        except Exception as e:
            if hasattr(self.studio, 'status_label') and self.studio.status_label:
                self.studio.status_label.set_text(f"Reset error: {e}")
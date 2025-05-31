"""
Hoomans Game Engine Studio - Main UI Platform
"""
import pygame
import pygame_gui
import sys
import os
from typing import Dict, Any, Optional
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from engine.studio.studio_tools import StudioToolManager, GameLauncher, ProjectManager
from config.game_loader import GameConfigLoader

class EngineStudio:
    """Main game engine studio interface"""
        
    def __init__(self):
        pygame.init()
        self.screen_size = (1400, 900)
        self.screen = pygame.display.set_mode(self.screen_size, pygame.RESIZABLE)
        pygame.display.set_caption("Hoomans Game Engine Studio")
        
        # Load UI theme
        self._load_ui_theme()
        
        # Get theme path
        theme_path = os.path.join(project_root, "engine", "studio", "theme.json")
        
        # Main UI manager for studio interface
        try:
            self.ui_manager = pygame_gui.UIManager(self.screen_size, theme_path=theme_path)
        except:
            self.ui_manager = pygame_gui.UIManager(self.screen_size)
        
        # Separate UI manager for tools (higher layer)
        try:
            self.tools_ui_manager = pygame_gui.UIManager(self.screen_size, theme_path=theme_path)
        except:
            self.tools_ui_manager = pygame_gui.UIManager(self.screen_size)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize managers
        self.config_loader = GameConfigLoader()
        self.tool_manager = StudioToolManager(self)
        self.game_launcher = GameLauncher(self)
        self.project_manager = ProjectManager(self)
        
        # UI elements
        self.status_label = None
        self.workspace_label = None
        self.config_list = None
        self.properties_text = None
        
        print("=== Hoomans Game Engine Studio ===")
        print("Starting Hoomans Game Engine Studio...")
        print("Available tools: Map Editor, Config Editor, Asset Browser")
        print("Click 'New Game' to create a new game configuration")
        
        self._setup_ui()

    def _load_ui_theme(self):
        """Load UI theme for the studio"""
        theme_path = os.path.join(project_root, "engine", "studio", "theme.json")
        
        # Create default theme if it doesn't exist
        if not os.path.exists(theme_path):
            default_theme = {
                "defaults": {
                    "colours": {
                        "normal_bg": "#25292e",
                        "hovered_bg": "#35393e",
                        "disabled_bg": "#25292e",
                        "selected_bg": "#193784",
                        "dark_bg": "#15191e",
                        "normal_text": "#c5cbd8",
                        "hovered_text": "#FFFFFF",
                        "selected_text": "#FFFFFF",
                        "disabled_text": "#6d736f",
                        "normal_border": "#DDDDDD",
                        "hovered_border": "#B0B0B0",
                        "disabled_border": "#808080",
                        "selected_border": "#8080B0"
                    }
                }
            }
            
            os.makedirs(os.path.dirname(theme_path), exist_ok=True)
            with open(theme_path, 'w') as f:
                json.dump(default_theme, f, indent=4)
            
    def _create_default_theme(self, theme_path):
        """Create default UI theme"""
        theme_data = {
            "defaults": {
                "colours": {
                    "normal_bg": "#2c3e50",
                    "hovered_bg": "#34495e",
                    "selected_bg": "#3498db",
                    "normal_text": "#ecf0f1",
                    "selected_text": "#ffffff"
                }
            },
            "#menu_panel": {
                "colours": {
                    "normal_bg": "#34495e"
                }
            },
            "#sidebar_panel": {
                "colours": {
                    "normal_bg": "#2c3e50"
                }
            },
            "#workspace_panel": {
                "colours": {
                    "normal_bg": "#ecf0f1"
                }
            }
        }
        
        os.makedirs(os.path.dirname(theme_path), exist_ok=True)
        import json
        with open(theme_path, 'w') as f:
            json.dump(theme_data, f, indent=2)

    def _setup_ui(self):
        """Setup the main studio UI"""
        # Define modern color scheme
        button_style = {
            'normal_bg': pygame.Color('#4a90e2'),
            'hovered_bg': pygame.Color('#357abd'),
            'selected_bg': pygame.Color('#2968a3'),
            'normal_text': pygame.Color('#ffffff'),
            'font_size': 14
        }
        
        # Main menu bar with gradient background
        self.menu_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, self.screen_size[0], 60),
            manager=self.ui_manager,
            element_id='menu_panel'
        )
        
        # Menu buttons with improved styling
        button_width = 120
        button_height = 40
        button_y = 10
        button_spacing = 10
        
        buttons_data = [
            ("New Game", 10),
            ("Load Game", 140),
            ("Map Editor", 270),
            ("Item Editor", 400),
            ("Config Editor", 530),
            ("Asset Browser", 660),
            ("Play Game", 790)
        ]
        
        self.buttons = {}
        for text, x_pos in buttons_data:
            btn_id = text.lower().replace(' ', '_') + '_btn'
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, button_y, button_width, button_height),
                text=text,
                manager=self.ui_manager,
                container=self.menu_panel,
                object_id=f'#{btn_id}'
            )
            setattr(self, btn_id, button)
            self.buttons[text] = button
        
        # Status bar with better styling
        self.status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.screen_size[0] - 300, button_y, 280, button_height),
            text="Ready",
            manager=self.ui_manager,
            container=self.menu_panel,
            object_id='#status_label'
        )
        
        # Rest of the UI setup...
        self._setup_content_area()
        
    def _setup_content_area(self):
        """Setup the main content area"""
        content_y = 70
        content_height = self.screen_size[1] - content_y - 10
        
        # Left sidebar with improved styling
        self.sidebar_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(10, content_y, 320, content_height),
            manager=self.ui_manager,
            object_id='#sidebar_panel'
        )
        
        # Project section
        self.project_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 300, 30),
            text="Game Configurations",
            manager=self.ui_manager,
            container=self.sidebar_panel,
            object_id='#section_header'
        )
        
        # Game config list with better styling
        game_configs = self.config_loader.list_available_games()
        self.config_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 50, 300, 250),
            item_list=game_configs,
            manager=self.ui_manager,
            container=self.sidebar_panel,
            object_id='#config_list'
        )
        
        # Properties section
        self.properties_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 310, 300, 30),
            text="Properties",
            manager=self.ui_manager,
            container=self.sidebar_panel,
            object_id='#section_header'
        )
        
        self.properties_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, 350, 300, 200),
            html_text="<p>Select a game configuration to view properties</p>",
            manager=self.ui_manager,
            container=self.sidebar_panel,
            object_id='#properties_text'
        )
        
        # Main workspace
        workspace_x = 340
        workspace_width = self.screen_size[0] - workspace_x - 10
        
        self.workspace_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(workspace_x, content_y, workspace_width, content_height),
            manager=self.ui_manager,
            object_id='#workspace_panel'
        )
        
        self.workspace_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(20, 20, workspace_width - 40, 40),
            text="Workspace - Select a tool or game to begin",
            manager=self.ui_manager,
            container=self.workspace_panel,
            object_id='#workspace_header'
        )
    
    def handle_events(self):
        """Handle UI events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.VIDEORESIZE:
                self.screen_size = event.size
                self.screen = pygame.display.set_mode(self.screen_size, pygame.RESIZABLE)
                self.ui_manager.set_window_resolution(self.screen_size)
                self.tools_ui_manager.set_window_resolution(self.screen_size)
                self._resize_ui()
            
            # Let tool manager handle events first (higher priority)
            if self.tool_manager.handle_event(event):
                continue
            
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    self._handle_button_press(event.ui_element)
                elif event.user_type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                    if event.ui_element == self.config_list:
                        self._handle_config_selection(event.text)
            
            # Process events for both UI managers
            self.tools_ui_manager.process_events(event)
            self.ui_manager.process_events(event)
    
    def _handle_button_press(self, button):
        """Handle button press events"""
        button_text = button.text
        
        if button_text == "New Game":
            self._create_new_game()
        elif button_text == "Load Game":
            self._load_game()
        elif button_text == "Map Editor":
            self._open_map_editor()
        elif button_text == "Item Editor":
            self._open_item_editor()
        elif button_text == "Config Editor":
            self._open_config_editor()
        elif button_text == "Asset Browser":
            self._open_asset_browser()
        elif button_text == "Play Game":
            self._play_current_game()
            
            
    def _open_config_editor(self):
        """Open the configuration editor tool"""
        try:
            success = self.tool_manager.launch_tool("config_editor")
            if success:
                self.workspace_label.set_text("Configuration Editor - Opened successfully")
                self.status_label.set_text("Config Editor opened")
            else:
                self.status_label.set_text("Failed to open Config Editor")
        except Exception as e:
            self.status_label.set_text(f"Error: {e}")

    def _open_asset_browser(self):
        """Open the asset browser tool"""
        try:
            success = self.tool_manager.launch_tool("asset_browser")
            if success:
                self.workspace_label.set_text("Asset Browser - Opened successfully")
                self.status_label.set_text("Asset Browser opened")
            else:
                self.status_label.set_text("Failed to open Asset Browser")
        except Exception as e:
            self.status_label.set_text(f"Error: {e}")
            
    def _handle_config_selection(self, config_name):
        """Handle game configuration selection"""
        try:
            config = self.config_loader.get_game_config(config_name)
            info = self.config_loader.get_game_info(config_name)
            
            properties_html = f"""
            <b>Name:</b> {info['name']}<br>
            <b>Description:</b> {info['description']}<br>
            <b>World Size:</b> {info['world_size']}<br>
            <b>Entities:</b> {info['entity_count']}<br>
            <b>Systems:</b> {info['system_count']}<br>
            """
            
            self.properties_text.html_text = properties_html
            self.properties_text.rebuild()
            
            self.status_label.set_text(f"Selected: {config_name}")
            
        except Exception as e:
            self.properties_text.html_text = f"Error loading config: {e}"
            self.properties_text.rebuild()
            self.status_label.set_text(f"Error: {e}")
    
    def _create_new_game(self):
        """Create a new game configuration"""
        self.workspace_label.set_text("Creating new game configuration...")
        self.status_label.set_text("New game dialog not implemented yet")
        
        # TODO: Open new game dialog
        # For now, just show a message
        print("New game creation not implemented yet")
    
    def _load_game(self):
        """Load an existing game"""
        selected = self.config_list.get_single_selection()
        if selected:
            try:
                config = self.config_loader.get_game_config(selected)
                self.workspace_label.set_text(f"Loaded game: {config.name}")
                self.status_label.set_text(f"Loaded: {selected}")
            except Exception as e:
                self.workspace_label.set_text(f"Error loading game: {e}")
                self.status_label.set_text(f"Error: {e}")
        else:
            self.status_label.set_text("No game configuration selected")
    
    def _open_map_editor(self):
        """Open the map editor tool"""
        try:
            success = self.tool_manager.launch_tool("map_editor")
            if success:
                self.workspace_label.set_text("Map Editor - Opened successfully")
                self.status_label.set_text("Map Editor opened")
            else:
                self.workspace_label.set_text("Map Editor - Failed to open")
                self.status_label.set_text("Failed to open Map Editor")
        except Exception as e:
            self.workspace_label.set_text(f"Map Editor - Error: {e}")
            self.status_label.set_text(f"Error: {e}")
    
    def _open_item_editor(self):
        """Open the item editor tool"""
        try:
            success = self.tool_manager.launch_tool("item_editor")
            if success:
                self.workspace_label.set_text("Item Editor - Opened successfully")
                self.status_label.set_text("Item Editor opened")
            else:
                self.workspace_label.set_text("Item Editor - Failed to open")
                self.status_label.set_text("Failed to open Item Editor")
        except Exception as e:
            self.workspace_label.set_text(f"Item Editor - Error: {e}")
            self.status_label.set_text(f"Error: {e}")
    
    def _play_current_game(self):
        """Play the currently selected game"""
        selected = self.config_list.get_single_selection()
        if selected:
            try:
                self.workspace_label.set_text(f"Starting game: {selected}")
                self.status_label.set_text("Launching game...")
                
                # Launch game with skip menu option
                success = self.game_launcher.launch_game(
                    selected,
                    skip_menu=True,
                    width=1024,
                    height=768
                )
                
                if success:
                    self.status_label.set_text(f"Game launched: {selected}")
                else:
                    self.status_label.set_text("Failed to launch game")
                
            except Exception as e:
                self.workspace_label.set_text(f"Error starting game: {e}")
                self.status_label.set_text(f"Launch error: {e}")
        else:
            self.workspace_label.set_text("Please select a game configuration first")
            self.status_label.set_text("No configuration selected")
    
    def _resize_ui(self):
        """Resize UI elements when window is resized"""
        # Update menu panel
        self.menu_panel.relative_rect.width = self.screen_size[0]
        
        # Update status label position
        self.status_label.relative_rect.x = self.screen_size[0] - 300
        
        # Update content area
        content_y = 70
        content_height = self.screen_size[1] - content_y
        
        # Update sidebar
        self.sidebar_panel.relative_rect.height = content_height - 20
        
        # Update workspace
        workspace_x = 320
        workspace_width = self.screen_size[0] - workspace_x - 10
        self.workspace_panel.relative_rect.width = workspace_width
        self.workspace_panel.relative_rect.height = content_height - 20
        
        # Update workspace label
        self.workspace_label.relative_rect.width = workspace_width - 20
        
        # Rebuild UI
        self.ui_manager.clear_and_reset()
        self._setup_ui()
    
    def update(self):
        """Update the studio"""
        time_delta = self.clock.tick(60) / 1000.0
        
        # Update both UI managers
        self.ui_manager.update(time_delta)
        self.tools_ui_manager.update(time_delta)
        
        # Update tool manager
        self.tool_manager.update(time_delta)

    def render(self):
        """Render the studio"""
        self.screen.fill((30, 30, 30))
        
        # Draw main studio UI first (background layer)
        self.ui_manager.draw_ui(self.screen)
        
        # Draw tools UI on top
        self.tools_ui_manager.draw_ui(self.screen)
        
        # Render embedded tools
        self.tool_manager.render(self.screen)
        
        pygame.display.flip()
        
        
    
    def run(self):
        """Run the studio main loop"""
        print("Studio is running. Use the interface to:")
        print("- Open Map Editor or Item Editor")
        print("- Select a game configuration and click Play Game")
        print("- Create new game configurations")
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up studio...")
        self._save_studio_settings()
        self.tool_manager.cleanup()
        self.game_launcher.cleanup()
        pygame.quit()
        sys.exit()

    def _load_studio_settings(self):
        """Load studio settings and recent projects"""
        settings_path = os.path.join(project_root, 'engine', 'studio', 'settings.json')
        if os.path.exists(settings_path):
            try:
                import json
                with open(settings_path, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = self._get_default_settings()
        else:
            self.settings = self._get_default_settings()
            self._save_studio_settings()

    def _get_default_settings(self):
        """Get default studio settings"""
        return {
            "recent_configs": [],
            "window_size": [1400, 900],
            "last_opened_config": None,
            "auto_save": True
        }
        
    def _save_studio_settings(self):
        """Save studio settings"""
        settings_path = os.path.join(project_root, 'engine', 'studio', 'settings.json')
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        # Update current settings
        self.settings["window_size"] = list(self.screen_size)
        
        import json
        with open(settings_path, 'w') as f:
            json.dump(self.settings, f, indent=2)
        

def main():
    """Main entry point for the studio"""
    try:
        studio = EngineStudio()
        studio.run()
    except KeyboardInterrupt:
        print("\nStudio interrupted by user")
    except Exception as e:
        print(f"Fatal error in Studio: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

"""
Studio Tools Manager - Handles launching and managing development tools
"""
import sys
import os
import subprocess
from typing import Dict, Any, List, Optional
import pygame

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

class StudioToolManager:
    """Manages development tools within the studio"""
    
    def __init__(self, studio_instance):
        self.studio = studio_instance
        self.active_tools = {}
        self.tool_processes = {}
        
        # Define available tools
        self.tools = {
            "map_editor": {
                "name": "Map Editor",
                "type": "embedded",
                "class": "engine.studio.tools.map_editor.MapEditor",
                "description": "Visual map editor for creating game worlds"
            },
            "item_editor": {
                "name": "Item Editor", 
                "type": "embedded",
                "class": "engine.studio.tools.item_editor.ItemEditor",
                "description": "Editor for creating and modifying game items"
            },
            "config_editor": {
                "name": "Configuration Editor",
                "type": "embedded",
                "class": "engine.studio.tools.config_editor.ConfigEditor",
                "description": "Edit game configurations and settings"
            },
            "asset_browser": {
                "name": "Asset Browser",
                "type": "embedded", 
                "class": "engine.studio.tools.asset_browser.AssetBrowser",
                "description": "Browse and manage game assets"
            }
        }
        
        print("Available tools:", ", ".join([tool["name"] for tool in self.tools.values()]))

    
    def launch_tool(self, tool_name: str, **kwargs) -> bool:
        """Launch a development tool"""
        if tool_name not in self.tools:
            print(f"Unknown tool: {tool_name}")
            return False
        
        tool_info = self.tools[tool_name]
        
        if tool_info["type"] == "external":
            return self._launch_external_tool(tool_name, **kwargs)
        elif tool_info["type"] == "embedded":
            return self._launch_embedded_tool(tool_name, **kwargs)
        else:
            print(f"Unknown tool type: {tool_info['type']}")
            return False
    
    def _launch_external_tool(self, tool_name: str, **kwargs) -> bool:
        """Launch an external tool as a separate process"""
        tool_info = self.tools[tool_name]
        script_path = os.path.join(project_root, tool_info["script"])
        
        if not os.path.exists(script_path):
            print(f"Tool script not found: {script_path}")
            return False
        
        try:
            # Build command
            cmd = [sys.executable, script_path]
            
            # Add any additional arguments
            for key, value in kwargs.items():
                if isinstance(value, bool) and value:
                    cmd.append(f"--{key.replace('_', '-')}")  # Convert underscores to hyphens
                elif not isinstance(value, bool):
                    cmd.extend([f"--{key.replace('_', '-')}", str(value)])
            
            # Launch process
            process = subprocess.Popen(cmd)
            self.tool_processes[tool_name] = process
            
            print(f"Launched external tool: {tool_name}")
            return True
            
        except Exception as e:
            print(f"Error launching {tool_name}: {e}")
            return False
        
    def _launch_embedded_tool(self, tool_name: str, **kwargs) -> bool:
        """Launch an embedded tool within the studio"""
        try:
            # Close existing tool if open
            if tool_name in self.active_tools:
                self.active_tools[tool_name].close()
                del self.active_tools[tool_name]
            
            # Import and create the tool with tools UI manager
            if tool_name == "map_editor":
                from engine.studio.tools.map_editor import MapEditor
                self.active_tools[tool_name] = MapEditor(self.studio, self.studio.tools_ui_manager)
                self.active_tools[tool_name].show()
                return True
                
            elif tool_name == "item_editor":
                from engine.studio.tools.item_editor import ItemEditor
                self.active_tools[tool_name] = ItemEditor(self.studio, self.studio.tools_ui_manager)
                self.active_tools[tool_name].show()
                return True
                
            elif tool_name == "config_editor":
                from engine.studio.tools.config_editor import ConfigEditor
                self.active_tools[tool_name] = ConfigEditor(self.studio, self.studio.tools_ui_manager)
                self.active_tools[tool_name].show()
                return True
                
            elif tool_name == "asset_browser":
                from engine.studio.tools.asset_browser import AssetBrowser
                self.active_tools[tool_name] = AssetBrowser(self.studio, self.studio.tools_ui_manager)
                self.active_tools[tool_name].show()
                return True
                
            else:
                print(f"Unknown embedded tool: {tool_name}")
                return False
                
        except Exception as e:
            print(f"Error launching embedded tool {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    
    def close_tool(self, tool_name: str) -> bool:
        """Close a running tool"""
        # Close embedded tool
        if tool_name in self.active_tools:
            self.active_tools[tool_name].close()
            del self.active_tools[tool_name]
            return True
        
        # Terminate external process
        if tool_name in self.tool_processes:
            process = self.tool_processes[tool_name]
            if process.poll() is None:  # Still running
                process.terminate()
            del self.tool_processes[tool_name]
            return True
        
        return False
    
    def is_tool_running(self, tool_name: str) -> bool:
        """Check if a tool is currently running"""
        # Check embedded tools
        if tool_name in self.active_tools:
            return self.active_tools[tool_name].is_visible()
        
        # Check external processes
        if tool_name in self.tool_processes:
            return self.tool_processes[tool_name].poll() is None
        
        return False
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available tools"""
        return self.tools.copy()
    
    def handle_event(self, event):
        """Handle events for active embedded tools"""
        for tool in self.active_tools.values():
            if tool.is_visible() and hasattr(tool, 'handle_event'):
                if tool.handle_event(event):
                    return True
        return False
    
    def update(self, time_delta):
        """Update active embedded tools"""
        for tool in self.active_tools.values():
            if tool.is_visible() and hasattr(tool, 'update'):
                tool.update(time_delta)
    
    def render(self, surface):
        """Render active embedded tools"""
        for tool in self.active_tools.values():
            if tool.is_visible() and hasattr(tool, 'render'):
                tool.render(surface)
    
    def cleanup(self):
        """Clean up all running tools"""
        # Close embedded tools
        for tool_name in list(self.active_tools.keys()):
            self.close_tool(tool_name)
        
        # Terminate external processes
        for tool_name in list(self.tool_processes.keys()):
            self.close_tool(tool_name)

class EmbeddedTool:
    """Base class for embedded studio tools"""
    
    def __init__(self, studio_instance, tool_name: str, ui_manager=None):
        self.studio = studio_instance
        self.tool_name = tool_name
        self.visible = False
        self.ui_elements = []
        # Use tools UI manager if provided, otherwise fall back to main UI manager
        self.ui_manager = ui_manager if ui_manager else studio_instance.ui_manager
    
    def show(self):
        """Show the tool"""
        if not self.visible:
            self.visible = True
            self._create_ui()
            print(f"Showing {self.tool_name}")
    
    def hide(self):
        """Hide the tool"""
        if self.visible:
            self.visible = False
            self._destroy_ui()
            print(f"Hiding {self.tool_name}")
    
    def close(self):
        """Close the tool"""
        self.hide()
        print(f"Closing {self.tool_name}")
    
    def is_visible(self) -> bool:
        """Check if tool is visible"""
        return self.visible
    
    def _create_ui(self):
        """Create UI elements - override in subclasses"""
        pass
    
    def _destroy_ui(self):
        """Destroy UI elements"""
        for element in self.ui_elements:
            if hasattr(element, 'kill'):
                try:
                    element.kill()
                except:
                    pass
        self.ui_elements.clear()
    
    def handle_event(self, event):
        """Handle events - override in subclasses"""
        if not self.visible:
            return False
        return False
    
    def update(self, time_delta):
        """Update tool - override in subclasses"""
        pass
    
    def render(self, surface):
        """Render tool - override in subclasses"""
        pass



class GameLauncher:
    """Handles launching games from the studio"""
    
    def __init__(self, studio_instance):
        self.studio = studio_instance
        self.running_games = {}
    
    def launch_game(self, config_name: str, **launch_args) -> bool:
        """Launch a game with specified configuration"""
        try:
            # Build launch command
            cmd = [sys.executable, os.path.join(project_root, "game_engine.py")]
            cmd.extend(["--game-config", config_name])
            
            # Add launch arguments - convert underscores to hyphens
            for key, value in launch_args.items():
                arg_name = key.replace('_', '-')  # Convert skip_menu to skip-menu
                if isinstance(value, bool) and value:
                    cmd.append(f"--{arg_name}")
                elif not isinstance(value, bool):
                    cmd.extend([f"--{arg_name}", str(value)])
            
            print(f"Launching game with command: {' '.join(cmd)}")
            
            # Launch game process
            process = subprocess.Popen(cmd)
            self.running_games[config_name] = process
            
            print(f"Launched game: {config_name}")
            return True
            
        except Exception as e:
            print(f"Error launching game {config_name}: {e}")
            return False
    
    def stop_game(self, config_name: str) -> bool:
        """Stop a running game"""
        if config_name in self.running_games:
            process = self.running_games[config_name]
            if process.poll() is None:  # Still running
                process.terminate()
            del self.running_games[config_name]
            return True
        return False
    
    def is_game_running(self, config_name: str) -> bool:
        """Check if a game is currently running"""
        if config_name in self.running_games:
            return self.running_games[config_name].poll() is None
        return False
    
    def get_running_games(self) -> list:
        """Get list of currently running games"""
        running = []
        for config_name, process in list(self.running_games.items()):
            if process.poll() is None:
                running.append(config_name)
            else:
                # Clean up finished processes
                del self.running_games[config_name]
        return running
    
    def cleanup(self):
        """Clean up all running games"""
        for config_name in list(self.running_games.keys()):
            self.stop_game(config_name)

class ProjectManager:
    """Manages studio projects and configurations"""
    
    def __init__(self, studio_instance):
        self.studio = studio_instance
        self.current_project = None
        self.project_path = os.path.join(project_root, "projects")
        
        # Ensure projects directory exists
        os.makedirs(self.project_path, exist_ok=True)
    
    def create_project(self, project_name: str, template: str = "default") -> bool:
        """Create a new project"""
        try:
            project_dir = os.path.join(self.project_path, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # Create project structure
            subdirs = ["maps", "items", "configs", "assets", "scripts"]
            for subdir in subdirs:
                os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)
            
            # Create project file
            project_file = os.path.join(project_dir, f"{project_name}.hproject")
            project_data = {
                "name": project_name,
                "template": template,
                "created": str(pygame.time.get_ticks()),
                "version": "1.0.0"
            }
            
            import json
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            print(f"Created project: {project_name}")
            return True
            
        except Exception as e:
            print(f"Error creating project {project_name}: {e}")
            return False
    
    def load_project(self, project_name: str) -> bool:
        """Load an existing project"""
        try:
            project_file = os.path.join(self.project_path, project_name, f"{project_name}.hproject")
            
            if not os.path.exists(project_file):
                print(f"Project file not found: {project_file}")
                return False
            
            import json
            with open(project_file, 'r') as f:
                project_data = json.load(f)
            
            self.current_project = project_data
            print(f"Loaded project: {project_name}")
            return True
            
        except Exception as e:
            print(f"Error loading project {project_name}: {e}")
            return False
    
    def get_projects(self) -> list:
        """Get list of available projects"""
        projects = []
        if os.path.exists(self.project_path):
            for item in os.listdir(self.project_path):
                project_dir = os.path.join(self.project_path, item)
                if os.path.isdir(project_dir):
                    project_file = os.path.join(project_dir, f"{item}.hproject")
                    if os.path.exists(project_file):
                        projects.append(item)
        return projects
    
    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """Get current project data"""
        return self.current_project
    
    def save_project(self) -> bool:
        """Save current project"""
        if not self.current_project:
            return False
        
        try:
            project_name = self.current_project["name"]
            project_file = os.path.join(self.project_path, project_name, f"{project_name}.hproject")
            
            import json
            with open(project_file, 'w') as f:
                json.dump(self.current_project, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving project: {e}")
            return False

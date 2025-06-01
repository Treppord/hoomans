"""
Game Configuration Loader
Manages loading different game configurations
"""
import importlib
from typing import Dict, List
from config.game_config import GameConfig
import os
import glob


class GameConfigLoader:
    """Loads and manages game configurations"""
    
    def __init__(self):
        self.available_games = {}
        self._load_available_games()
    
        
    def _load_available_games(self):
        """Load all available game configurations"""
        # Auto-discover game configuration files
        games_dir = os.path.join(os.path.dirname(__file__), "games")
        
        if os.path.exists(games_dir):
            # Find all Python files in the games directory
            game_files = glob.glob(os.path.join(games_dir, "*_game.py"))
            
            for game_file in game_files:
                filename = os.path.basename(game_file)
                if filename.startswith("__"):
                    continue
                    
                # Extract game name (remove _game.py suffix)
                game_name = filename[:-3]  # Remove .py
                if game_name.endswith("_game"):
                    game_name = game_name[:-5]  # Remove _game
                
                module_path = f"config.games.{filename[:-3]}"
                function_name = f"get_{game_name}_game_config"
                
                # Try to register the game
                try:
                    self._register_game(game_name, module_path, function_name)
                except Exception as e:
                    print(f"Failed to register game {game_name}: {e}")
    
    def _register_game(self, name: str, module_path: str, function_name: str):
        """Register a game configuration"""
        self.available_games[name] = {
            "module_path": module_path,
            "function_name": function_name
        }
    
    def get_game_config(self, game_name: str) -> GameConfig:
        """Load a specific game configuration"""
        if game_name not in self.available_games:
            raise ValueError(f"Game configuration '{game_name}' not found. Available: {list(self.available_games.keys())}")
        
        game_info = self.available_games[game_name]
        
        try:
            # Import the module
            module = importlib.import_module(game_info["module_path"])
            
            # Get the configuration function
            config_function = getattr(module, game_info["function_name"])
            
            # Call the function to get the configuration
            return config_function()
            
        except Exception as e:
            raise RuntimeError(f"Failed to load game configuration '{game_name}': {e}")
    
    def list_available_games(self) -> List[str]:
        """Get list of available game configurations"""
        return list(self.available_games.keys())
    
    def register_custom_game(self, name: str, module_path: str, function_name: str):
        """Register a custom game configuration"""
        self._register_game(name, module_path, function_name)
    
    def get_game_info(self, game_name: str) -> Dict[str, str]:
        """Get information about a game configuration without loading it"""
        if game_name not in self.available_games:
            return None
        
        try:
            config = self.get_game_config(game_name)
            return {
                "name": config.name,
                "description": config.description,
                "world_size": f"{config.world_width}x{config.world_height}",
                "entity_count": len(config.entities),
                "system_count": len([s for s in config.systems if s.enabled])
            }
        except Exception as e:
            return {
                "name": game_name,
                "description": f"Error loading: {e}",
                "world_size": "Unknown",
                "entity_count": "Unknown",
                "system_count": "Unknown"
            }
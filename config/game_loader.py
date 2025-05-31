"""
Game Configuration Loader
Manages loading different game configurations
"""
import importlib
from typing import Dict, List
from config.game_config import GameConfig

class GameConfigLoader:
    """Loads and manages game configurations"""
    
    def __init__(self):
        self.available_games = {}
        self._load_available_games()
    
    def _load_available_games(self):
        """Load all available game configurations"""
        # Register built-in game configurations
        self._register_game("default", "config.games.default_game", "get_default_game_config")
        self._register_game("minimal", "config.games.minimal_game", "get_minimal_game_config")
        self._register_game("survival", "config.games.survival_game", "get_survival_game_config")
    
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
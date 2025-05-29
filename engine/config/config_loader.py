"""Configuration loading and management"""
import json
import os
import pygame
from typing import Dict, Any, List, Optional

class ConfigLoader:
    """Handles loading and accessing configuration files"""
    
    def __init__(self, config_dir=None):
        """Initialize the config loader"""
        if config_dir is None:
            # Default to config directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(current_dir, '..', '..', 'config')
        
        self.config_dir = os.path.abspath(config_dir)
        self.configs = {}
        
        # Load all configuration files
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all JSON configuration files from the config directory"""
        if not os.path.exists(self.config_dir):
            print(f"Warning: Config directory not found: {self.config_dir}")
            return
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                config_name = filename[:-5]  # Remove .json extension
                file_path = os.path.join(self.config_dir, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        self.configs[config_name] = json.load(f)
                    print(f"Loaded config: {config_name}")
                except Exception as e:
                    print(f"Error loading config {filename}: {e}")
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """Get a complete configuration by name"""
        return self.configs.get(config_name, {})
    
    def get_setting(self, config_name: str, *path: str, default=None) -> Any:
        """Get a specific setting using a path (e.g., 'display', 'width')"""
        config = self.get_config(config_name)
        
        current = config
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_pygame_keys(self, key_path: str) -> List[int]:
        """Convert key names to pygame key constants
        
        Args:
            key_path: Dot-separated path to the key configuration (e.g., 'input_mappings.movement.up')
        
        Returns:
            List of pygame key constants
        """
        # Split the path and get the key names
        path_parts = key_path.split('.')
        
        # Get the key names from the config
        key_names = self.get_setting(*path_parts, default=[])
        
        if not isinstance(key_names, list):
            key_names = [key_names] if key_names else []
        
        # Convert key names to pygame constants
        pygame_keys = []
        for key_name in key_names:
            # Handle different key name formats
            pygame_key = None
            
            # Try direct pygame constant (e.g., "K_UP")
            if hasattr(pygame, key_name):
                pygame_key = getattr(pygame, key_name)
            # Try with K_ prefix (e.g., "UP" -> "K_UP")
            elif hasattr(pygame, f'K_{key_name}'):
                pygame_key = getattr(pygame, f'K_{key_name}')
            # Try lowercase with K_ prefix (e.g., "up" -> "K_UP")
            elif hasattr(pygame, f'K_{key_name.upper()}'):
                pygame_key = getattr(pygame, f'K_{key_name.upper()}')
            # Try removing K_ and making uppercase (e.g., "K_up" -> "K_UP")
            elif key_name.startswith('K_') and hasattr(pygame, key_name.upper()):
                pygame_key = getattr(pygame, key_name.upper())
            
            if pygame_key is not None:
                pygame_keys.append(pygame_key)
                print(f"Mapped key '{key_name}' to pygame constant {pygame_key}")
            else:
                print(f"Warning: Could not map key name: {key_name}")
        
        return pygame_keys
    
    def reload_config(self, config_name: str):
        """Reload a specific configuration file"""
        file_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    self.configs[config_name] = json.load(f)
                print(f"Reloaded config: {config_name}")
                return True
            except Exception as e:
                print(f"Error reloading config {config_name}: {e}")
                return False
        else:
            print(f"Config file not found: {file_path}")
            return False
    
    def save_config(self, config_name: str, config_data: Dict[str, Any]):
        """Save configuration data to a file"""
        file_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Update in-memory config
            self.configs[config_name] = config_data
            print(f"Saved config: {config_name}")
            return True
        except Exception as e:
            print(f"Error saving config {config_name}: {e}")
            return False

# Global config loader instance
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """Get the global config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def initialize_config_loader(config_dir=None) -> ConfigLoader:
    """Initialize the global config loader with a custom directory"""
    global _config_loader
    _config_loader = ConfigLoader(config_dir)
    return _config_loader

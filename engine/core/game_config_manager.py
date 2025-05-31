"""
Game Configuration Manager
Integrates with the engine to manage dynamic configurations
"""
from typing import Dict, Any, Optional
from config.game_config import GameConfig

class GameConfigManager:
    """Manages game configuration within the engine"""
    
    def __init__(self, engine):
        self.engine = engine
        self.current_config: Optional[GameConfig] = None
        self.runtime_overrides: Dict[str, Any] = {}
    
    def set_config(self, config: GameConfig):
        """Set the current game configuration"""
        self.current_config = config
        print(f"Game configuration set: {config.name}")
    
    def get_config(self) -> Optional[GameConfig]:
        """Get the current game configuration"""
        return self.current_config
    
    def override_setting(self, key: str, value: Any):
        """Override a configuration setting at runtime"""
        self.runtime_overrides[key] = value
        print(f"Configuration override: {key} = {value}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting with runtime override support"""
        # Check runtime overrides first
        if key in self.runtime_overrides:
            return self.runtime_overrides[key]
        
        # Check current configuration
        if self.current_config:
            # Navigate through nested configuration
            keys = key.split('.')
            value = self.current_config
            
            try:
                for k in keys:
                    if hasattr(value, k):
                        value = getattr(value, k)
                    elif isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                return value
            except (AttributeError, KeyError, TypeError):
                pass
        
        return default
    
    def reload_config(self, new_config: GameConfig):
        """Reload configuration (useful for hot-reloading during development)"""
        print(f"Reloading configuration: {new_config.name}")
        self.current_config = new_config
        
        # Trigger reconfiguration of systems that support it
        self._reconfigure_systems()
    
    def _reconfigure_systems(self):
        """Reconfigure systems that support hot-reloading"""
        if not self.current_config:
            return
        
        # Reconfigure camera if settings changed
        if hasattr(self.engine, 'camera'):
            # Example: Update camera settings
            pass
        
        # Reconfigure UI if settings changed
        if hasattr(self.engine, 'ui'):
            # Example: Update UI theme or layout
            pass
        
        print("Systems reconfigured")
    
    def export_current_state(self) -> Dict[str, Any]:
        """Export current configuration state for debugging"""
        return {
            "config_name": self.current_config.name if self.current_config else None,
            "config_description": self.current_config.description if self.current_config else None,
            "runtime_overrides": self.runtime_overrides.copy(),
            "world_size": f"{self.current_config.world_width}x{self.current_config.world_height}" if self.current_config else None,
            "enabled_systems": [s.name for s in self.current_config.systems if s.enabled] if self.current_config else [],
            "entity_count": len(self.current_config.entities) if self.current_config else 0
        }

"""
Configuration Validator
Validates game configurations for correctness
"""
from typing import List, Dict, Any
from config.game_config import GameConfig, SystemConfig, EntityConfig, WorldItemConfig

class ConfigValidator:
    """Validates game configurations"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_config(self, config: GameConfig) -> bool:
        """Validate a complete game configuration"""
        self.errors.clear()
        self.warnings.clear()
        
        # Validate basic properties
        self._validate_basic_properties(config)
        
        # Validate systems
        self._validate_systems(config.systems)
        
        # Validate entities
        self._validate_entities(config.entities)
        
        # Validate world items
        self._validate_world_items(config.world_items)
        
        # Validate world size
        self._validate_world_size(config)
        
        # Check for logical consistency
        self._validate_logical_consistency(config)
        
        return len(self.errors) == 0
    
    def _validate_basic_properties(self, config: GameConfig):
        """Validate basic configuration properties"""
        if not config.name or not config.name.strip():
            self.errors.append("Configuration name cannot be empty")
        
        if not config.description or not config.description.strip():
            self.warnings.append("Configuration description is empty")
        
        if config.world_width <= 0 or config.world_height <= 0:
            self.errors.append("World dimensions must be positive")
        
        if config.world_width > 2048 or config.world_height > 2048:
            self.warnings.append("Large world size may impact performance")
    
    def _validate_systems(self, systems: List[SystemConfig]):
        """Validate system configurations"""
        system_names = set()
        
        for system in systems:
            if not system.name or not system.name.strip():
                self.errors.append("System name cannot be empty")
                continue
            
            if system.name in system_names:
                self.errors.append(f"Duplicate system name: {system.name}")
            
            system_names.add(system.name)
            
            # Validate specific system requirements
            self._validate_system_specific(system)
    
    def _validate_system_specific(self, system: SystemConfig):
        """Validate system-specific requirements"""
        if system.name == "sound_system" and system.enabled:
            config = system.config
            for volume_key in ["master_volume", "sfx_volume", "music_volume"]:
                if volume_key in config:
                    volume = config[volume_key]
                    if not 0.0 <= volume <= 1.0:
                        self.errors.append(f"Sound volume {volume_key} must be between 0.0 and 1.0")
        
        elif system.name == "world_map" and system.enabled:
            config = system.config
            if "width" in config and config["width"] <= 0:
                self.errors.append("World map width must be positive")
            if "height" in config and config["height"] <= 0:
                self.errors.append("World map height must be positive")
    
    def _validate_entities(self, entities: List[EntityConfig]):
        """Validate entity configurations"""
        player_count = 0
        
        for entity in entities:
            if not entity.entity_type or not entity.entity_type.strip():
                self.errors.append("Entity type cannot be empty")
                continue
            
            if entity.entity_type == "player":
                player_count += 1
            
            # Validate coordinates
            if entity.grid_x < 0 or entity.grid_y < 0:
                self.errors.append(f"Entity coordinates must be non-negative: {entity.entity_type}")
            
            # Validate color
            if len(entity.color) != 3:
                self.errors.append(f"Entity color must be RGB tuple: {entity.entity_type}")
            else:
                for component in entity.color:
                    if not 0 <= component <= 255:
                        self.errors.append(f"Color components must be 0-255: {entity.entity_type}")
            
            # Validate speed
            if entity.speed <= 0:
                self.errors.append(f"Entity speed must be positive: {entity.entity_type}")
        
        # Check player count
        if player_count == 0:
            self.warnings.append("No player entity defined")
        elif player_count > 1:
            self.warnings.append("Multiple player entities defined")
    
    def _validate_world_items(self, world_items: List[WorldItemConfig]):
        """Validate world item configurations"""
        for item in world_items:
            if not item.item_type or not item.item_type.strip():
                self.errors.append("World item type cannot be empty")
            
            if item.x < 0 or item.y < 0:
                self.errors.append(f"World item coordinates must be non-negative: {item.item_type}")
            
            if item.quantity <= 0:
                self.errors.append(f"World item quantity must be positive: {item.item_type}")
    
    def _validate_world_size(self, config: GameConfig):
        """Validate world size against entity and item positions"""
        max_entity_x = max_entity_y = 0
        max_item_x = max_item_y = 0
        
        # Check entity positions
        for entity in config.entities:
            if entity.entity_type != "food_npcs":  # Skip food NPCs as they're spawned randomly
                max_entity_x = max(max_entity_x, entity.grid_x)
                max_entity_y = max(max_entity_y, entity.grid_y)
        
        # Check item positions
        for item in config.world_items:
            max_item_x = max(max_item_x, item.x)
            max_item_y = max(max_item_y, item.y)
        
        # Validate against world size
        if max_entity_x >= config.world_width:
            self.errors.append(f"Entity position ({max_entity_x}) exceeds world width ({config.world_width})")
        
        if max_entity_y >= config.world_height:
            self.errors.append(f"Entity position ({max_entity_y}) exceeds world height ({config.world_height})")
        
        if max_item_x >= config.world_width:
            self.errors.append(f"Item position ({max_item_x}) exceeds world width ({config.world_width})")
        
        if max_item_y >= config.world_height:
            self.errors.append(f"Item position ({max_item_y}) exceeds world height ({config.world_height})")
    
    def _validate_logical_consistency(self, config: GameConfig):
        """Validate logical consistency between systems"""
        enabled_systems = {s.name for s in config.systems if s.enabled}
        
        # Check dependencies
        if "world_cache" in enabled_systems and "world_map" not in enabled_systems:
            self.warnings.append("World cache enabled but world map disabled")
        
        if "ai_universe" in enabled_systems and "entity_manager" not in enabled_systems:
            self.warnings.append("AI universe enabled but entity manager disabled")
        
        # Check if item system is needed
        if config.world_items and "item_system" not in enabled_systems:
            self.warnings.append("World items defined but item system disabled")
    
    def get_validation_report(self) -> str:
        """Get a formatted validation report"""
        report = []
        
        if self.errors:
            report.append("ERRORS:")
            for error in self.errors:
                report.append(f"  - {error}")
        
        if self.warnings:
            if report:
                report.append("")
            report.append("WARNINGS:")
            for warning in self.warnings:
                report.append(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            report.append("Configuration is valid!")
        
        return "\n".join(report)
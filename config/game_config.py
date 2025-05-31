"""
Game Configuration System
Defines what gets loaded and initialized for different game modes
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable

@dataclass
class EntityConfig:
    """Configuration for entity creation"""
    entity_type: str
    grid_x: Optional[int] = None  # Make optional
    grid_y: Optional[int] = None  # Make optional
    color: tuple = (255, 255, 255)
    speed: int = 1
    cna_filename: Optional[str] = None
    count: int = 1
    extra_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorldItemConfig:
    """Configuration for world item spawning"""
    item_type: str
    x: int
    y: int
    quantity: int = 1

@dataclass
class SystemConfig:
    """Configuration for game systems"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GameConfig:
    """Complete game configuration"""
    name: str
    description: str
    
    # World settings
    world_width: int = 256
    world_height: int = 256
    
    # Systems to initialize
    systems: List[SystemConfig] = field(default_factory=list)
    
    # Entities to create
    entities: List[EntityConfig] = field(default_factory=list)
    
    # World items to spawn
    world_items: List[WorldItemConfig] = field(default_factory=list)
    
    # Custom initialization hooks
    pre_init_hooks: List[str] = field(default_factory=list)
    post_init_hooks: List[str] = field(default_factory=list)
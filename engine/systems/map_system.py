"""
Comprehensive Map System for Custom Game Engine
Encapsulates all map-related functionality as callable components for the engine studio

This system provides:
- Tile management and rendering
- Entity tile system (trees, houses, etc.)
- Procedural map generation with biomes
- Map serialization and loading
- Performance optimization
- Extensible architecture for studio integration
"""

import os
import gzip
import json
import random
import math
import time
import pygame
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import threading
from concurrent.futures import ThreadPoolExecutor

# ============================================================================
# CORE ENUMS AND DATA STRUCTURES
# ============================================================================

class TileType(Enum):
    """Enumeration of all tile types"""
    EMPTY = "empty"
    WALL = "wall"
    GRASS = "grass"
    WATER = "water"
    SAND = "sand"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    DEEP_WATER = "deep_water"
    SHALLOW_WATER = "shallow_water"
    ROCK = "rock"
    PATH = "path"
    SNOW = "snow"

class BiomeType(Enum):
    """Enumeration of biome types"""
    OCEAN = "ocean"
    LAKE = "lake"
    RIVER = "river"
    BEACH = "beach"
    PLAINS = "plains"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    SNOW = "snow"
    SWAMP = "swamp"

class EntityTileType(Enum):
    """Enumeration of entity tile types"""
    TREE = "tree"
    HOUSE = "house"
    ROCK_FORMATION = "rock_formation"
    BRIDGE = "bridge"
    TOWER = "tower"
    FENCE = "fence"

class MapGenerationType(Enum):
    """Map generation algorithms"""
    PROCEDURAL = "procedural"
    PERLIN_NOISE = "perlin_noise"
    CELLULAR_AUTOMATA = "cellular_automata"
    WAVE_FUNCTION_COLLAPSE = "wave_function_collapse"
    CUSTOM = "custom"

@dataclass
class TileProperties:
    """Properties for a tile type"""
    tile_type: TileType
    name: str
    description: str
    walkable: bool = True
    swimmable: bool = False
    buildable: bool = True
    base_color: Tuple[int, int, int] = (255, 255, 255)
    texture_path: Optional[str] = None
    texture_variations: List[str] = None
    movement_cost: float = 1.0
    opacity: float = 1.0
    animated: bool = False
    animation_frames: int = 1
    animation_speed: int = 200
    sound_effects: Dict[str, str] = None
    particle_effects: Dict[str, Any] = None
    custom_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.texture_variations is None:
            self.texture_variations = []
        if self.sound_effects is None:
            self.sound_effects = {}
        if self.particle_effects is None:
            self.particle_effects = {}
        if self.custom_properties is None:
            self.custom_properties = {}

@dataclass
class EntityTileProperties:
    """Properties for entity tiles (structures)"""
    entity_type: EntityTileType
    name: str
    description: str
    width: int = 1
    height: int = 1
    walkable_components: List[Tuple[int, int]] = None
    interactable: bool = True
    destructible: bool = False
    health: int = 100
    texture_path: Optional[str] = None
    construction_cost: Dict[str, int] = None
    construction_time: float = 0.0
    provides_shelter: bool = False
    storage_capacity: int = 0
    custom_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.walkable_components is None:
            self.walkable_components = []
        if self.construction_cost is None:
            self.construction_cost = {}
        if self.custom_properties is None:
            self.custom_properties = {}

@dataclass
class BiomeRule:
    """Defines biome generation rules"""
    biome_type: BiomeType
    primary_tile: TileType
    secondary_tiles: List[TileType]
    allowed_neighbors: Set[BiomeType]
    elevation_range: Tuple[float, float]
    moisture_range: Tuple[float, float]
    temperature_range: Tuple[float, float]
    min_region_size: int = 4
    spawn_probability: float = 1.0
    entity_spawn_rules: Dict[EntityTileType, float] = None
    
    def __post_init__(self):
        if self.entity_spawn_rules is None:
            self.entity_spawn_rules = {}

@dataclass
class MapGenerationConfig:
    """Configuration for map generation"""
    width: int
    height: int
    seed: Optional[int] = None
    generation_type: MapGenerationType = MapGenerationType.PROCEDURAL
    biome_rules: Dict[BiomeType, BiomeRule] = None
    noise_settings: Dict[str, Any] = None
    post_processing: List[str] = None
    entity_generation: bool = True
    border_type: Optional[TileType] = TileType.WALL
    ensure_water_access: bool = True
    
    def __post_init__(self):
        if self.biome_rules is None:
            self.biome_rules = {}
        if self.noise_settings is None:
            self.noise_settings = {}
        if self.post_processing is None:
            self.post_processing = []

# ============================================================================
# TILE SYSTEM
# ============================================================================

class TileRegistry:
    """Registry for all tile types and their properties"""
    
    def __init__(self):
        self.tile_definitions: Dict[TileType, TileProperties] = {}
        self.texture_cache: Dict[str, pygame.Surface] = {}
        self.tileset_cache: Dict[str, List[pygame.Surface]] = {}
        self._initialize_default_tiles()
    
    def _initialize_default_tiles(self):
        """Initialize default tile definitions"""
        default_tiles = [
            TileProperties(
                TileType.EMPTY, "Empty", "Empty space",
                walkable=True, base_color=(0, 0, 0)
            ),
            TileProperties(
                TileType.WALL, "Wall", "Solid wall",
                walkable=False, buildable=False, base_color=(100, 100, 100)
            ),
            TileProperties(
                TileType.GRASS, "Grass", "Green grass",
                walkable=True, base_color=(0, 150, 0)
            ),
            TileProperties(
                TileType.WATER, "Water", "Deep water",
                walkable=False, swimmable=True, buildable=False, base_color=(0, 0, 200)
            ),
            TileProperties(
                TileType.SAND, "Sand", "Sandy ground",
                walkable=True, base_color=(194, 178, 128)
            ),
            TileProperties(
                TileType.FOREST, "Forest", "Dense forest",
                walkable=True, movement_cost=1.5, base_color=(0, 100, 0)
            ),
            TileProperties(
                TileType.MOUNTAIN, "Mountain", "Rocky mountain",
                walkable=False, buildable=False, base_color=(120, 100, 80)
            ),
            TileProperties(
                TileType.DEEP_WATER, "Deep Water", "Very deep water",
                walkable=False, swimmable=True, buildable=False, base_color=(0, 0, 150)
            ),
            TileProperties(
                TileType.SHALLOW_WATER, "Shallow Water", "Shallow water",
                walkable=True, swimmable=True, movement_cost=2.0, base_color=(65, 105, 225)
            ),
            TileProperties(
                TileType.ROCK, "Rock", "Rocky ground",
                walkable=True, movement_cost=1.2, base_color=(150, 150, 150)
            ),
            TileProperties(
                TileType.PATH, "Path", "Dirt path",
                walkable=True, movement_cost=0.8, base_color=(153, 136, 119)
            ),
            TileProperties(
                TileType.SNOW, "Snow", "Snow-covered ground",
                walkable=True, movement_cost=1.3, base_color=(250, 250, 250)
            )
        ]
        
        for tile_props in default_tiles:
            self.register_tile(tile_props)
    
    def register_tile(self, tile_properties: TileProperties):
        """Register a new tile type"""
        self.tile_definitions[tile_properties.tile_type] = tile_properties
    
    def get_tile_properties(self, tile_type: TileType) -> Optional[TileProperties]:
        """Get properties for a tile type"""
        return self.tile_definitions.get(tile_type)
    
    def load_tileset(self, filename: str, tile_width: int = 16, tile_height: int = 16) -> List[pygame.Surface]:
        """Load a tileset and split into individual tiles"""
        if filename in self.tileset_cache:
            return self.tileset_cache[filename]
        
        try:
            tileset = pygame.image.load(filename).convert_alpha()
            tileset_width, tileset_height = tileset.get_size()
            
            cols = tileset_width // tile_width
            rows = tileset_height // tile_height
            
            tiles = []
            for row in range(rows):
                for col in range(cols):
                    x = col * tile_width
                    y = row * tile_height
                    tile = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
                    tile.blit(tileset, (0, 0), (x, y, tile_width, tile_height))
                    tiles.append(tile)
            
            self.tileset_cache[filename] = tiles
            return tiles
        except Exception as e:
            print(f"Error loading tileset {filename}: {e}")
            return []
    
    def load_texture(self, texture_path: str) -> Optional[pygame.Surface]:
        """Load a single texture"""
        if texture_path in self.texture_cache:
            return self.texture_cache[texture_path]
        
        try:
            texture = pygame.image.load(texture_path).convert_alpha()
            self.texture_cache[texture_path] = texture
            return texture
        except Exception as e:
            print(f"Error loading texture {texture_path}: {e}")
            return None
    
    def create_custom_tile(self, tile_type: TileType, **properties) -> TileProperties:
        """Create a custom tile with specified properties"""
        base_props = self.get_tile_properties(tile_type)
        if base_props:
            # Create a copy and update with custom properties
            custom_props = TileProperties(**asdict(base_props))
            for key, value in properties.items():
                if hasattr(custom_props, key):
                    setattr(custom_props, key, value)
            return custom_props
        return None

class Tile:
    """Individual tile instance"""
    
    SIZE = 16  # Default tile size in pixels
    
    def __init__(self, tile_type: TileType, properties: TileProperties = None, 
                 variation: int = 0, custom_data: Dict[str, Any] = None):
        self.tile_type = tile_type
        self.properties = properties
        self.variation = variation
        self.custom_data = custom_data or {}
        self.selected_texture = None
        self.animation_frame = 0
        self.last_animation_update = 0
        
        # Cache frequently accessed properties
        self._walkable = properties.walkable if properties else True
        self._movement_cost = properties.movement_cost if properties else 1.0
        self._base_color = properties.base_color if properties else (255, 255, 255)
    
    @property
    def type(self) -> str:
        """Legacy compatibility property"""
        return self.tile_type.value
    
    def is_walkable(self) -> bool:
        """Check if this tile is walkable"""
        return self._walkable
    
    def is_water(self) -> bool:
        """Check if this tile is water"""
        return self.tile_type in [TileType.WATER, TileType.DEEP_WATER, TileType.SHALLOW_WATER]
    
    def get_movement_cost(self) -> float:
        """Get movement cost for this tile"""
        return self._movement_cost
    
    def update_animation(self, current_time: int):
        """Update tile animation"""
        if (self.properties and self.properties.animated and 
            current_time - self.last_animation_update > self.properties.animation_speed):
            self.animation_frame = (self.animation_frame + 1) % self.properties.animation_frames
            self.last_animation_update = current_time
    
    def render(self, screen: pygame.Surface, x: int, y: int, width: int, height: int):
        """Render the tile"""
        if self.selected_texture:
            scaled_texture = pygame.transform.scale(self.selected_texture, (width, height))
            screen.blit(scaled_texture, (x, y))
        else:
            # Fallback to color rendering
            color = self._base_color
            if self.properties and self.properties.opacity < 1.0:
                # Create surface with alpha
                surface = pygame.Surface((width, height), pygame.SRCALPHA)
                alpha = int(255 * self.properties.opacity)
                color_with_alpha = (*color, alpha)
                surface.fill(color_with_alpha)
                screen.blit(surface, (x, y))
            else:
                pygame.draw.rect(screen, color, (x, y, width, height))

# ============================================================================
# ENTITY TILE SYSTEM
# ============================================================================

class EntityTileRegistry:
    """Registry for entity tile types"""
    
    def __init__(self):
        self.entity_definitions: Dict[EntityTileType, EntityTileProperties] = {}
        self.texture_cache: Dict[str, pygame.Surface] = {}
        self._initialize_default_entity_tiles()
    
    def _initialize_default_entity_tiles(self):
        """Initialize default entity tile definitions"""
        default_entities = [
            EntityTileProperties(
                EntityTileType.TREE, "Tree", "A tall tree",
                width=1, height=2, walkable_components=[(0, 0)],
                destructible=True, health=50
            ),
            EntityTileProperties(
                EntityTileType.HOUSE, "House", "A residential building",
                width=2, height=2, walkable_components=[],
                provides_shelter=True, storage_capacity=100,
                construction_cost={"wood": 20, "stone": 10}
            ),
            EntityTileProperties(
                EntityTileType.ROCK_FORMATION, "Rock Formation", "Large rocks",
                width=2, height=2, walkable_components=[],
                destructible=True, health=100
            ),
            EntityTileProperties(
                EntityTileType.BRIDGE, "Bridge", "Wooden bridge over water",
                width=1, height=1, walkable_components=[(0, 0)],
                construction_cost={"wood": 5}
            ),
            EntityTileProperties(
                EntityTileType.TOWER, "Tower", "Defensive tower",
                width=2, height=3, walkable_components=[(0, 0), (1, 0)],
                provides_shelter=True, health=200,
                construction_cost={"stone": 50, "wood": 20}
            ),
            EntityTileProperties(
                EntityTileType.FENCE, "Fence", "Wooden fence",
                width=1, height=1, walkable_components=[],
                destructible=True, health=25,
                construction_cost={"wood": 2}
            )
        ]
        
        for entity_props in default_entities:
            self.register_entity_tile(entity_props)
    
    def register_entity_tile(self, entity_properties: EntityTileProperties):
        """Register a new entity tile type"""
        self.entity_definitions[entity_properties.entity_type] = entity_properties
    
    def get_entity_properties(self, entity_type: EntityTileType) -> Optional[EntityTileProperties]:
        """Get properties for an entity tile type"""
        return self.entity_definitions.get(entity_type)
    
    def create_custom_entity_tile(self, entity_type: EntityTileType, **properties) -> EntityTileProperties:
        """Create a custom entity tile with specified properties"""
        base_props = self.get_entity_properties(entity_type)
        if base_props:
            custom_props = EntityTileProperties(**asdict(base_props))
            for key, value in properties.items():
                if hasattr(custom_props, key):
                    setattr(custom_props, key, value)
            return custom_props
        return None

class EntityTile:
    """Individual entity tile instance"""
    
    def __init__(self, entity_type: EntityTileType, x: int, y: int, 
                 properties: EntityTileProperties = None, custom_data: Dict[str, Any] = None):
        self.entity_type = entity_type
        self.x = x
        self.y = y
        self.properties = properties
        self.custom_data = custom_data or {}
        self.current_health = properties.health if properties else 100
        self.construction_progress = 1.0  # 1.0 = fully constructed
        self.last_interaction_time = 0
        self.stored_items = {}  # For storage-capable structures
        self.occupants = []  # For shelter-providing structures
        
        # Cache frequently accessed properties
        self._width = properties.width if properties else 1
        self._height = properties.height if properties else 1
        self._interactable = properties.interactable if properties else True
    
    @property
    def tile_type(self) -> str:
        """Legacy compatibility property"""
        return self.entity_type.value
    
    def get_occupied_tiles(self) -> List[Tuple[int, int]]:
        """Get all tiles occupied by this entity"""
        occupied = []
        for dy in range(self._height):
            for dx in range(self._width):
                occupied.append((self.x + dx, self.y + dy))
        return occupied
    
    def is_walkable_at(self, local_x: int, local_y: int) -> bool:
        """Check if a specific position within the entity is walkable"""
        if not self.properties:
            return False
        return (local_x, local_y) in self.properties.walkable_components
    
    def can_interact(self) -> bool:
        """Check if this entity can be interacted with"""
        return self._interactable and self.construction_progress >= 1.0
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to the entity, returns True if destroyed"""
        if not self.properties or not self.properties.destructible:
            return False
        
        self.current_health = max(0, self.current_health - damage)
        return self.current_health <= 0
    
    def repair(self, amount: int):
        """Repair the entity"""
        if self.properties:
            self.current_health = min(self.properties.health, self.current_health + amount)
    
    def add_stored_item(self, item_id: str, quantity: int) -> bool:
        """Add items to storage if this entity has storage capacity"""
        if not self.properties or self.properties.storage_capacity <= 0:
            return False
        
        current_total = sum(self.stored_items.values())
        if current_total + quantity <= self.properties.storage_capacity:
            self.stored_items[item_id] = self.stored_items.get(item_id, 0) + quantity
            return True
        return False
    
    def remove_stored_item(self, item_id: str, quantity: int) -> int:
        """Remove items from storage, returns actual amount removed"""
        if item_id not in self.stored_items:
            return 0
        
        available = self.stored_items[item_id]
        removed = min(available, quantity)
        self.stored_items[item_id] -= removed
        
        if self.stored_items[item_id] <= 0:
            del self.stored_items[item_id]
        
        return removed
    
    def render(self, screen: pygame.Surface, x: int, y: int, tile_size: int):
        """Render the entity tile"""
        width = self._width * tile_size
        height = self._height * tile_size
        
        # Default rendering based on entity type
        color_map = {
            EntityTileType.TREE: (0, 100, 0),
            EntityTileType.HOUSE: (139, 69, 19),
            EntityTileType.ROCK_FORMATION: (128, 128, 128),
            EntityTileType.BRIDGE: (160, 82, 45),
            EntityTileType.TOWER: (105, 105, 105),
            EntityTileType.FENCE: (101, 67, 33)
        }
        
        color = color_map.get(self.entity_type, (255, 0, 255))
        
        # Adjust color based on health
        if self.properties and self.properties.destructible:
            health_ratio = self.current_health / self.properties.health
            color = tuple(int(c * health_ratio) for c in color)
        
        pygame.draw.rect(screen, color, (x, y, width, height))
        
        # Draw border
        pygame.draw.rect(screen, (0, 0, 0), (x, y, width, height), 1)
        
        # Draw construction progress if not complete
        if self.construction_progress < 1.0:
            progress_height = int(height * self.construction_progress)
            pygame.draw.rect(screen, (255, 255, 0), 
                           (x, y + height - progress_height, width, progress_height))

class EntityTileManager:
    """Manages all entity tiles on the map"""
    
    def __init__(self, map_width: int, map_height: int):
        self.map_width = map_width
        self.map_height = map_height
        self.entity_tiles: Dict[Tuple[int, int], EntityTile] = {}
        self.entity_grid: List[List[Optional[EntityTile]]] = [
            [None for _ in range(map_width)] for _ in range(map_height)
        ]
    
    def add_entity_tile(self, entity_tile: EntityTile) -> bool:
        """Add an entity tile to the map"""
        # Check if the area is clear
        for dy in range(entity_tile._height):
            for dx in range(entity_tile._width):
                x, y = entity_tile.x + dx, entity_tile.y + dy
                if (x < 0 or x >= self.map_width or 
                    y < 0 or y >= self.map_height or
                    self.entity_grid[y][x] is not None):
                    return False
        
        # Place the entity
        for dy in range(entity_tile._height):
            for dx in range(entity_tile._width):
                x, y = entity_tile.x + dx, entity_tile.y + dy
                self.entity_grid[y][x] = entity_tile
        
        self.entity_tiles[(entity_tile.x, entity_tile.y)] = entity_tile
        return True
    
    def remove_entity_tile(self, x: int, y: int) -> Optional[EntityTile]:
        """Remove an entity tile from the map"""
        entity_tile = self.get_entity_tile_at(x, y)
        if not entity_tile:
            return None
        
        # Clear all occupied positions
        for dy in range(entity_tile._height):
            for dx in range(entity_tile._width):
                ex, ey = entity_tile.x + dx, entity_tile.y + dy
                if 0 <= ex < self.map_width and 0 <= ey < self.map_height:
                    self.entity_grid[ey][ex] = None
        
        # Remove from main dictionary
        if (entity_tile.x, entity_tile.y) in self.entity_tiles:
            del self.entity_tiles[(entity_tile.x, entity_tile.y)]
        
        return entity_tile
    
    def get_entity_tile_at(self, x: int, y: int) -> Optional[EntityTile]:
        """Get entity tile at position"""
        if 0 <= x < self.map_width and 0 <= y < self.map_height:
            return self.entity_grid[y][x]
        return None
    
    def is_position_blocked(self, x: int, y: int) -> bool:
        """Check if position is blocked by an entity tile"""
        entity_tile = self.get_entity_tile_at(x, y)
        if not entity_tile:
            return False
        
        # Calculate local position within the entity
        local_x = x - entity_tile.x
        local_y = y - entity_tile.y
        
        return not entity_tile.is_walkable_at(local_x, local_y)
    
    def get_all_entity_tiles(self) -> List[EntityTile]:
        """Get all entity tiles"""
        return list(self.entity_tiles.values())
    
    def get_entities_in_area(self, x: int, y: int, width: int, height: int) -> List[EntityTile]:
        """Get all entity tiles in a rectangular area"""
        entities = set()
        for dy in range(height):
            for dx in range(width):
                entity = self.get_entity_tile_at(x + dx, y + dy)
                if entity:
                    entities.add(entity)
        return list(entities)

# ============================================================================
# BIOME SYSTEM
# ============================================================================

class BiomeRegistry:
    """Registry for biome definitions and rules"""
    
    def __init__(self):
        self.biome_rules: Dict[BiomeType, BiomeRule] = {}
        self._initialize_default_biomes()
    
    def _initialize_default_biomes(self):
        """Initialize default biome rules"""
        default_biomes = [
            BiomeRule(
                BiomeType.OCEAN,
                TileType.DEEP_WATER,
                [TileType.WATER],
                {BiomeType.BEACH, BiomeType.LAKE},
                elevation_range=(-1.0, 0.2),
                moisture_range=(0.8, 1.0),
                temperature_range=(-1.0, 1.0),
                min_region_size=20
            ),
            BiomeRule(
                BiomeType.BEACH,
                TileType.SAND,
                [TileType.SHALLOW_WATER, TileType.GRASS],
                {BiomeType.OCEAN, BiomeType.PLAINS, BiomeType.FOREST},
                elevation_range=(0.1, 0.3),
                moisture_range=(0.3, 0.7),
                temperature_range=(0.2, 0.8),
                min_region_size=5
            ),
            BiomeRule(
                BiomeType.PLAINS,
                TileType.GRASS,
                [TileType.PATH, TileType.ROCK],
                {BiomeType.FOREST, BiomeType.BEACH, BiomeType.DESERT, BiomeType.MOUNTAIN},
                elevation_range=(0.2, 0.6),
                moisture_range=(0.3, 0.8),
                temperature_range=(0.3, 0.7),
                min_region_size=10,
                entity_spawn_rules={EntityTileType.TREE: 0.1}
            ),
            BiomeRule(
                BiomeType.FOREST,
                TileType.FOREST,
                [TileType.GRASS, TileType.ROCK],
                {BiomeType.PLAINS, BiomeType.MOUNTAIN, BiomeType.SWAMP},
                elevation_range=(0.3, 0.8),
                moisture_range=(0.6, 1.0),
                temperature_range=(0.2, 0.8),
                min_region_size=15,
                entity_spawn_rules={EntityTileType.TREE: 0.4}
            ),
            BiomeRule(
                BiomeType.MOUNTAIN,
                TileType.MOUNTAIN,
                [TileType.ROCK, TileType.SNOW],
                {BiomeType.FOREST, BiomeType.PLAINS, BiomeType.SNOW},
                elevation_range=(0.7, 1.0),
                moisture_range=(0.2, 0.8),
                temperature_range=(-0.5, 0.5),
                min_region_size=8,
                entity_spawn_rules={EntityTileType.ROCK_FORMATION: 0.2}
            ),
            BiomeRule(
                BiomeType.DESERT,
                TileType.SAND,
                [TileType.ROCK],
                {BiomeType.PLAINS},
                elevation_range=(0.2, 0.7),
                moisture_range=(0.0, 0.3),
                temperature_range=(0.5, 1.0),
                min_region_size=12
            ),
            BiomeRule(
                BiomeType.SNOW,
                TileType.SNOW,
                [TileType.ROCK, TileType.MOUNTAIN],
                {BiomeType.MOUNTAIN},
                elevation_range=(0.8, 1.0),
                moisture_range=(0.4, 1.0),
                temperature_range=(-1.0, 0.0),
                min_region_size=6
            ),
            BiomeRule(
                BiomeType.SWAMP,
                TileType.SHALLOW_WATER,
                [TileType.GRASS, TileType.FOREST],
                {BiomeType.FOREST, BiomeType.LAKE},
                elevation_range=(0.1, 0.4),
                moisture_range=(0.8, 1.0),
                temperature_range=(0.3, 0.8),
                min_region_size=8,
                entity_spawn_rules={EntityTileType.TREE: 0.2}
            ),
            BiomeRule(
                BiomeType.LAKE,
                TileType.WATER,
                [TileType.SHALLOW_WATER, TileType.GRASS],
                {BiomeType.PLAINS, BiomeType.FOREST, BiomeType.SWAMP},
                elevation_range=(0.0, 0.3),
                moisture_range=(0.9, 1.0),
                temperature_range=(0.0, 0.9),
                min_region_size=5
            ),
            BiomeRule(
                BiomeType.RIVER,
                TileType.SHALLOW_WATER,
                [TileType.WATER, TileType.GRASS],
                {BiomeType.PLAINS, BiomeType.FOREST, BiomeType.LAKE, BiomeType.OCEAN},
                elevation_range=(0.1, 0.5),
                moisture_range=(0.8, 1.0),
                temperature_range=(0.0, 0.8),
                min_region_size=3
            )
        ]
        
        for biome_rule in default_biomes:
            self.register_biome(biome_rule)
    
    def register_biome(self, biome_rule: BiomeRule):
        """Register a biome rule"""
        self.biome_rules[biome_rule.biome_type] = biome_rule
    
    def get_biome_rule(self, biome_type: BiomeType) -> Optional[BiomeRule]:
        """Get biome rule for a biome type"""
        return self.biome_rules.get(biome_type)
    
    def get_suitable_biome(self, elevation: float, moisture: float, temperature: float) -> Optional[BiomeType]:
        """Find the most suitable biome for given environmental parameters"""
        best_biome = None
        best_score = -1
        
        for biome_type, rule in self.biome_rules.items():
            # Check if parameters are within range
            if (rule.elevation_range[0] <= elevation <= rule.elevation_range[1] and
                rule.moisture_range[0] <= moisture <= rule.moisture_range[1] and
                rule.temperature_range[0] <= temperature <= rule.temperature_range[1]):
                
                # Calculate suitability score (closer to center of ranges = better)
                elev_score = 1 - abs(elevation - (rule.elevation_range[0] + rule.elevation_range[1]) / 2)
                moist_score = 1 - abs(moisture - (rule.moisture_range[0] + rule.moisture_range[1]) / 2)
                temp_score = 1 - abs(temperature - (rule.temperature_range[0] + rule.temperature_range[1]) / 2)
                
                total_score = (elev_score + moist_score + temp_score) / 3 * rule.spawn_probability
                
                if total_score > best_score:
                    best_score = total_score
                    best_biome = biome_type
        
        return best_biome

# ============================================================================
# NOISE GENERATION SYSTEM
# ============================================================================

class NoiseGenerator:
    """Generates various types of noise for map generation"""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(0, 2**32 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)
    
    def perlin_noise_2d(self, width: int, height: int, scale: float = 0.1, 
                       octaves: int = 4, persistence: float = 0.5, 
                       lacunarity: float = 2.0) -> np.ndarray:
        """Generate 2D Perlin noise"""
        noise_map = np.zeros((height, width))
        
        for octave in range(octaves):
            frequency = scale * (lacunarity ** octave)
            amplitude = persistence ** octave
            
            # Simple noise generation (in a real implementation, you'd use a proper Perlin noise library)
            octave_noise = self._simple_noise_2d(width, height, frequency)
            noise_map += octave_noise * amplitude
        
        # Normalize to [-1, 1]
        noise_map = (noise_map - np.min(noise_map)) / (np.max(noise_map) - np.min(noise_map))
        noise_map = noise_map * 2 - 1
        
        return noise_map
    
    def _simple_noise_2d(self, width: int, height: int, frequency: float) -> np.ndarray:
        """Simple noise generation (placeholder for proper Perlin noise)"""
        noise = np.random.random((height, width))
        
        # Apply some smoothing
        from scipy import ndimage
        try:
            noise = ndimage.gaussian_filter(noise, sigma=1/frequency)
        except ImportError:
            # Fallback if scipy is not available
            pass
        
        return noise
    
    def cellular_automata(self, width: int, height: int, initial_density: float = 0.45,
                         iterations: int = 5, birth_limit: int = 4, death_limit: int = 3) -> np.ndarray:
        """Generate map using cellular automata"""
        # Initialize random map
        cell_map = np.random.random((height, width)) < initial_density
        
        for _ in range(iterations):
            new_map = np.zeros_like(cell_map, dtype=bool)
            
            for y in range(height):
                for x in range(width):
                    neighbors = self._count_neighbors(cell_map, x, y)
                    
                    if cell_map[y, x]:  # Cell is alive
                        new_map[y, x] = neighbors >= death_limit
                    else:  # Cell is dead
                        new_map[y, x] = neighbors > birth_limit
            
            cell_map = new_map
        
        return cell_map.astype(float)
    
    def _count_neighbors(self, cell_map: np.ndarray, x: int, y: int) -> int:
        """Count living neighbors for cellular automata"""
        count = 0
        height, width = cell_map.shape
        
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                
                # Treat out-of-bounds as walls
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    count += 1
                elif cell_map[ny, nx]:
                    count += 1
        
        return count
    
    def diamond_square(self, size: int, roughness: float = 0.5) -> np.ndarray:
        """Generate heightmap using diamond-square algorithm"""
        # Size must be power of 2 + 1
        actual_size = 2 ** int(math.log2(size - 1)) + 1
        heightmap = np.zeros((actual_size, actual_size))
        
        # Initialize corners
        heightmap[0, 0] = random.uniform(-1, 1)
        heightmap[0, actual_size-1] = random.uniform(-1, 1)
        heightmap[actual_size-1, 0] = random.uniform(-1, 1)
        heightmap[actual_size-1, actual_size-1] = random.uniform(-1, 1)
        
        step_size = actual_size - 1
        scale = roughness
        
        while step_size > 1:
            half_step = step_size // 2
            
            # Diamond step
            for y in range(half_step, actual_size, step_size):
                for x in range(half_step, actual_size, step_size):
                    avg = (heightmap[y - half_step, x - half_step] +
                           heightmap[y - half_step, x + half_step] +
                           heightmap[y + half_step, x - half_step] +
                           heightmap[y + half_step, x + half_step]) / 4
                    
                    heightmap[y, x] = avg + random.uniform(-scale, scale)
            
            # Square step
            for y in range(0, actual_size, half_step):
                for x in range((y + half_step) % step_size, actual_size, step_size):
                    neighbors = []
                    
                    if y - half_step >= 0:
                        neighbors.append(heightmap[y - half_step, x])
                    if y + half_step < actual_size:
                        neighbors.append(heightmap[y + half_step, x])
                    if x - half_step >= 0:
                        neighbors.append(heightmap[y, x - half_step])
                    if x + half_step < actual_size:
                        neighbors.append(heightmap[y, x + half_step])
                    
                    if neighbors:
                        avg = sum(neighbors) / len(neighbors)
                        heightmap[y, x] = avg + random.uniform(-scale, scale)
            
            step_size //= 2
            scale *= roughness
        
        # Resize to requested size if different
        if actual_size != size:
            # Simple resize (in practice, you'd use proper interpolation)
            heightmap = heightmap[:size, :size]
        
        return heightmap

# ============================================================================
# MAP GENERATION SYSTEM
# ============================================================================

class MapGenerator:
    """Generates maps using various algorithms"""
    
    def __init__(self, tile_registry: TileRegistry, biome_registry: BiomeRegistry,
                 entity_registry: EntityTileRegistry):
        self.tile_registry = tile_registry
        self.biome_registry = biome_registry
        self.entity_registry = entity_registry
        self.noise_generator = NoiseGenerator()
    
    def generate_map(self, config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Generate a complete map based on configuration"""
        if config.seed:
            self.noise_generator = NoiseGenerator(config.seed)
        
        # Generate base terrain
        if config.generation_type == MapGenerationType.PROCEDURAL:
            terrain, biomes = self._generate_procedural_map(config)
        elif config.generation_type == MapGenerationType.PERLIN_NOISE:
            terrain, biomes = self._generate_perlin_map(config)
        elif config.generation_type == MapGenerationType.CELLULAR_AUTOMATA:
            terrain, biomes = self._generate_cellular_map(config)
        else:
            terrain, biomes = self._generate_simple_map(config)
        
        # Apply post-processing
        for process in config.post_processing:
            terrain, biomes = self._apply_post_processing(terrain, biomes, process, config)
        
        # Add borders if specified
        if config.border_type:
            terrain = self._add_borders(terrain, config.border_type)
        
        return terrain, biomes
    
    def _generate_procedural_map(self, config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Generate map using procedural generation with multiple noise layers"""
        width, height = config.width, config.height
        
        # Generate noise maps
        elevation = self.noise_generator.perlin_noise_2d(width, height, scale=0.05, octaves=4)
        moisture = self.noise_generator.perlin_noise_2d(width, height, scale=0.08, octaves=3)
        temperature = self.noise_generator.perlin_noise_2d(width, height, scale=0.06, octaves=3)
        
        # Create terrain and biome maps
        terrain = [[None for _ in range(width)] for _ in range(height)]
        biomes = [[None for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                elev = elevation[y, x]
                moist = moisture[y, x]
                temp = temperature[y, x]
                
                # Determine biome
                biome_type = self.biome_registry.get_suitable_biome(elev, moist, temp)
                biomes[y][x] = biome_type
                
                # Get tile type from biome
                if biome_type:
                    biome_rule = self.biome_registry.get_biome_rule(biome_type)
                    if biome_rule:
                        # Choose primary or secondary tile
                        if random.random() < 0.7:  # 70% chance for primary tile
                            tile_type = biome_rule.primary_tile
                        else:
                            tile_type = random.choice(biome_rule.secondary_tiles) if biome_rule.secondary_tiles else biome_rule.primary_tile
                    else:
                        tile_type = TileType.GRASS
                else:
                    tile_type = TileType.GRASS
                
                # Create tile
                tile_props = self.tile_registry.get_tile_properties(tile_type)
                terrain[y][x] = Tile(tile_type, tile_props)
        
        return terrain, biomes
    
    def _generate_perlin_map(self, config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Generate map using primarily Perlin noise"""
        width, height = config.width, config.height
        
        # Get noise settings
        noise_settings = config.noise_settings
        scale = noise_settings.get('scale', 0.1)
        octaves = noise_settings.get('octaves', 4)
        
        # Generate heightmap
        heightmap = self.noise_generator.perlin_noise_2d(width, height, scale, octaves)
        
        terrain = [[None for _ in range(width)] for _ in range(height)]
        biomes = [[None for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                height_value = heightmap[y, x]
                
                # Simple height-based terrain assignment
                if height_value < -0.5:
                    tile_type = TileType.DEEP_WATER
                    biome_type = BiomeType.OCEAN
                elif height_value < -0.2:
                    tile_type = TileType.WATER
                    biome_type = BiomeType.LAKE
                elif height_value < 0.0:
                    tile_type = TileType.SHALLOW_WATER
                    biome_type = BiomeType.BEACH
                elif height_value < 0.3:
                    tile_type = TileType.GRASS
                    biome_type = BiomeType.PLAINS
                elif height_value < 0.6:
                    tile_type = TileType.FOREST
                    biome_type = BiomeType.FOREST
                else:
                    tile_type = TileType.MOUNTAIN
                    biome_type = BiomeType.MOUNTAIN
                
                tile_props = self.tile_registry.get_tile_properties(tile_type)
                terrain[y][x] = Tile(tile_type, tile_props)
                biomes[y][x] = biome_type
        
        return terrain, biomes
    
    def _generate_cellular_map(self, config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Generate map using cellular automata"""
        width, height = config.width, config.height
        
        # Get cellular automata settings
        ca_settings = config.noise_settings
        initial_density = ca_settings.get('initial_density', 0.45)
        iterations = ca_settings.get('iterations', 5)
        
        # Generate cellular automata map
        cell_map = self.noise_generator.cellular_automata(width, height, initial_density, iterations)
        
        terrain = [[None for _ in range(width)] for _ in range(height)]
        biomes = [[None for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                if cell_map[y, x]:
                    tile_type = TileType.WALL
                    biome_type = BiomeType.MOUNTAIN
                else:
                    tile_type = TileType.GRASS
                    biome_type = BiomeType.PLAINS
                
                tile_props = self.tile_registry.get_tile_properties(tile_type)
                terrain[y][x] = Tile(tile_type, tile_props)
                biomes[y][x] = biome_type
        
        return terrain, biomes
    
    def _generate_simple_map(self, config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Generate a simple map with basic patterns"""
        width, height = config.width, config.height
        
        terrain = [[None for _ in range(width)] for _ in range(height)]
        biomes = [[None for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                # Simple pattern: grass with some water and mountains
                if random.random() < 0.1:
                    tile_type = TileType.WATER
                    biome_type = BiomeType.LAKE
                elif random.random() < 0.05:
                    tile_type = TileType.MOUNTAIN
                    biome_type = BiomeType.MOUNTAIN
                else:
                    tile_type = TileType.GRASS
                    biome_type = BiomeType.PLAINS
                
                tile_props = self.tile_registry.get_tile_properties(tile_type)
                terrain[y][x] = Tile(tile_type, tile_props)
                biomes[y][x] = biome_type
        
        return terrain, biomes
    
    def _apply_post_processing(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]], 
                              process: str, config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Apply post-processing effects to the map"""
        if process == "smooth":
            return self._smooth_terrain(terrain, biomes)
        elif process == "add_rivers":
            return self._add_rivers(terrain, biomes, config)
        elif process == "add_paths":
            return self._add_paths(terrain, biomes, config)
        elif process == "ensure_connectivity":
            return self._ensure_connectivity(terrain, biomes)
        
        return terrain, biomes
    
    def _smooth_terrain(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]]) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Smooth terrain by reducing isolated tiles"""
        height, width = len(terrain), len(terrain[0])
        new_terrain = [[None for _ in range(width)] for _ in range(height)]
        new_biomes = [[None for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                # Count neighboring tile types
                tile_counts = {}
                biome_counts = {}
                
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            tile_type = terrain[ny][nx].tile_type
                            biome_type = biomes[ny][nx]
                            
                            tile_counts[tile_type] = tile_counts.get(tile_type, 0) + 1
                            biome_counts[biome_type] = biome_counts.get(biome_type, 0) + 1
                
                # Choose most common tile and biome
                most_common_tile = max(tile_counts, key=tile_counts.get)
                most_common_biome = max(biome_counts, key=biome_counts.get)
                
                tile_props = self.tile_registry.get_tile_properties(most_common_tile)
                new_terrain[y][x] = Tile(most_common_tile, tile_props)
                new_biomes[y][x] = most_common_biome
        
        return new_terrain, new_biomes
    
    def _add_rivers(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]], 
                   config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Add rivers to the map"""
        height, width = len(terrain), len(terrain[0])
        
        # Find high elevation points as river sources
        sources = []
        for y in range(height):
            for x in range(width):
                if terrain[y][x].tile_type == TileType.MOUNTAIN and random.random() < 0.1:
                    sources.append((x, y))
        
        # Generate rivers from sources
        for source_x, source_y in sources:
            self._generate_river_path(terrain, biomes, source_x, source_y, width, height)
        
        return terrain, biomes
    
    def _generate_river_path(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]], 
                           start_x: int, start_y: int, width: int, height: int):
        """Generate a single river path"""
        current_x, current_y = start_x, start_y
        visited = set()
        
        while (current_x, current_y) not in visited and 0 <= current_x < width and 0 <= current_y < height:
            visited.add((current_x, current_y))
            
            # Place river tile
            if terrain[current_y][current_x].tile_type not in [TileType.WATER, TileType.DEEP_WATER]:
                tile_props = self.tile_registry.get_tile_properties(TileType.SHALLOW_WATER)
                terrain[current_y][current_x] = Tile(TileType.SHALLOW_WATER, tile_props)
                biomes[current_y][current_x] = BiomeType.RIVER
            
            # Find next position (move towards lower elevation or water)
            best_next = None
            best_score = float('inf')
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                next_x, next_y = current_x + dx, current_y + dy
                
                if (0 <= next_x < width and 0 <= next_y < height and 
                    (next_x, next_y) not in visited):
                    
                    # Score based on tile type (prefer moving towards water/lower elevation)
                    tile_type = terrain[next_y][next_x].tile_type
                    if tile_type in [TileType.WATER, TileType.DEEP_WATER]:
                        best_next = (next_x, next_y)
                        break
                    elif tile_type in [TileType.GRASS, TileType.SAND]:
                        score = random.random()
                        if score < best_score:
                            best_score = score
                            best_next = (next_x, next_y)
            
            if best_next:
                current_x, current_y = best_next
            else:
                break
    
    def _add_paths(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]], 
                  config: MapGenerationConfig) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Add paths connecting important locations"""
        # This is a simplified implementation
        # In practice, you'd use pathfinding algorithms to connect settlements
        return terrain, biomes
    
    def _ensure_connectivity(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]]) -> Tuple[List[List[Tile]], List[List[BiomeType]]]:
        """Ensure all walkable areas are connected"""
        # This would implement flood-fill to find disconnected regions
        # and add connections between them
        return terrain, biomes
    
    def _add_borders(self, terrain: List[List[Tile]], border_type: TileType) -> List[List[Tile]]:
        """Add borders around the map"""
        height, width = len(terrain), len(terrain[0])
        border_props = self.tile_registry.get_tile_properties(border_type)
        
        for y in range(height):
            for x in range(width):
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    terrain[y][x] = Tile(border_type, border_props)
        
        return terrain
    
    def generate_entity_tiles(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]], 
                            entity_manager: EntityTileManager) -> List[EntityTile]:
        """Generate entity tiles based on biome rules"""
        height, width = len(terrain), len(terrain[0])
        generated_entities = []
        
        for y in range(height):
            for x in range(width):
                biome_type = biomes[y][x]
                biome_rule = self.biome_registry.get_biome_rule(biome_type)
                
                if biome_rule and biome_rule.entity_spawn_rules:
                    for entity_type, spawn_chance in biome_rule.entity_spawn_rules.items():
                        if random.random() < spawn_chance:
                            entity_props = self.entity_registry.get_entity_properties(entity_type)
                            if entity_props:
                                # Check if there's space for the entity
                                can_place = True
                                for dy in range(entity_props.height):
                                    for dx in range(entity_props.width):
                                        check_x, check_y = x + dx, y + dy
                                        if (check_x >= width or check_y >= height or
                                            entity_manager.get_entity_tile_at(check_x, check_y) is not None):
                                            can_place = False
                                            break
                                    if not can_place:
                                        break
                                
                                if can_place:
                                    entity_tile = EntityTile(entity_type, x, y, entity_props)
                                    if entity_manager.add_entity_tile(entity_tile):
                                        generated_entities.append(entity_tile)
        
        return generated_entities

# ============================================================================
# MAP SERIALIZATION SYSTEM
# ============================================================================

class MapSerializer:
    """Handles saving and loading of maps"""
    
    def __init__(self, tile_registry: TileRegistry, entity_registry: EntityTileRegistry):
        self.tile_registry = tile_registry
        self.entity_registry = entity_registry
    
    def _compress_terrain_data(self, terrain: List[List[Tile]]) -> List[List[Any]]:
        """Compress terrain data by removing redundant information"""
        compressed = []
        for row in terrain:
            compressed_row = []
            for tile in row:
                # Store only essential data
                tile_data = [
                    tile.tile_type.value,
                    tile.variation if tile.variation != 0 else None,
                    tile.custom_data if tile.custom_data else None
                ]
                # Remove trailing None values
                while len(tile_data) > 1 and tile_data[-1] is None:
                    tile_data.pop()
                
                # If only tile type, store as string
                if len(tile_data) == 1:
                    compressed_row.append(tile_data[0])
                else:
                    compressed_row.append(tile_data)
            compressed.append(compressed_row)
        return compressed
    
    def _decompress_terrain_data(self, compressed_terrain: List[List[Any]]) -> List[List[Tile]]:
        """Decompress terrain data back to Tile objects"""
        terrain = []
        for row in compressed_terrain:
            terrain_row = []
            for tile_data in row:
                if isinstance(tile_data, str):
                    # Simple tile type only
                    tile_type = TileType(tile_data)
                    variation = 0
                    custom_data = {}
                else:
                    # Full tile data
                    tile_type = TileType(tile_data[0])
                    variation = tile_data[1] if len(tile_data) > 1 and tile_data[1] is not None else 0
                    custom_data = tile_data[2] if len(tile_data) > 2 and tile_data[2] is not None else {}
                
                tile_props = self.tile_registry.get_tile_properties(tile_type)
                tile = Tile(tile_type, tile_props, variation, custom_data)
                terrain_row.append(tile)
            terrain.append(terrain_row)
        return terrain
    
    def _compress_biome_data(self, biomes: List[List[BiomeType]]) -> List[str]:
        """Compress biome data using run-length encoding"""
        flat_biomes = []
        for row in biomes:
            for biome in row:
                flat_biomes.append(biome.value if biome else 'null')
        
        # Run-length encoding
        compressed = []
        if flat_biomes:
            current_biome = flat_biomes[0]
            count = 1
            
            for biome in flat_biomes[1:]:
                if biome == current_biome:
                    count += 1
                else:
                    compressed.append(f"{current_biome}:{count}" if count > 1 else current_biome)
                    current_biome = biome
                    count = 1
            
            # Add the last run
            compressed.append(f"{current_biome}:{count}" if count > 1 else current_biome)
        
        return compressed
    
    def _decompress_biome_data(self, compressed_biomes: List[str], width: int, height: int) -> List[List[BiomeType]]:
        """Decompress biome data from run-length encoding"""
        # Decode run-length encoding
        flat_biomes = []
        for item in compressed_biomes:
            if ':' in item:
                biome_value, count = item.split(':')
                count = int(count)
                flat_biomes.extend([biome_value] * count)
            else:
                flat_biomes.append(item)
        
        # Convert back to 2D array
        biomes = []
        for y in range(height):
            row = []
            for x in range(width):
                idx = y * width + x
                if idx < len(flat_biomes):
                    biome_value = flat_biomes[idx]
                    biome = BiomeType(biome_value) if biome_value != 'null' else None
                    row.append(biome)
                else:
                    row.append(None)
            biomes.append(row)
        
        return biomes
    
    def _compress_entity_data(self, entity_tiles: List[EntityTile]) -> List[List[Any]]:
        """Compress entity data by removing default values"""
        compressed = []
        for entity in entity_tiles:
            entity_data = [
                entity.entity_type.value,
                entity.x,
                entity.y
            ]
            
            # Add optional fields only if they differ from defaults
            optional_data = {}
            if entity.current_health != (entity.properties.health if entity.properties else 100):
                optional_data['h'] = entity.current_health
            if entity.construction_progress != 1.0:
                optional_data['c'] = entity.construction_progress
            if entity.custom_data:
                optional_data['d'] = entity.custom_data
            if entity.stored_items:
                optional_data['s'] = entity.stored_items
            
            if optional_data:
                entity_data.append(optional_data)
            
            compressed.append(entity_data)
        
        return compressed
    
    def _decompress_entity_data(self, compressed_entities: List[List[Any]]) -> List[EntityTile]:
        """Decompress entity data back to EntityTile objects"""
        entities = []
        for entity_data in compressed_entities:
            entity_type = EntityTileType(entity_data[0])
            x = entity_data[1]
            y = entity_data[2]
            
            entity_props = self.entity_registry.get_entity_properties(entity_type)
            entity = EntityTile(entity_type, x, y, entity_props)
            
            # Restore optional data
            if len(entity_data) > 3:
                optional_data = entity_data[3]
                entity.current_health = optional_data.get('h', entity.current_health)
                entity.construction_progress = optional_data.get('c', 1.0)
                entity.custom_data = optional_data.get('d', {})
                entity.stored_items = optional_data.get('s', {})
            
            entities.append(entity)
        
        return entities

    def serialize_map(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]], 
                     entity_tiles: List[EntityTile], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Serialize map data to a compressed dictionary"""
        height, width = len(terrain), len(terrain[0])
        
        # Compress data
        compressed_terrain = self._compress_terrain_data(terrain)
        compressed_biomes = self._compress_biome_data(biomes)
        compressed_entities = self._compress_entity_data(entity_tiles)
        
        # Create complete map data
        map_data = {
            'version': '1.1',  # Updated version for compressed format
            'width': width,
            'height': height,
            'terrain': compressed_terrain,
            'biomes': compressed_biomes,
            'entities': compressed_entities,
            'metadata': metadata or {}
        }
        
        return map_data
    
    def deserialize_map(self, map_data: Dict[str, Any]) -> Tuple[List[List[Tile]], List[List[BiomeType]], List[EntityTile]]:
        """Deserialize map data from a compressed dictionary"""
        width = map_data['width']
        height = map_data['height']
        version = map_data.get('version', '1.0')
        
        if version == '1.1':
            # New compressed format
            terrain = self._decompress_terrain_data(map_data['terrain'])
            biomes = self._decompress_biome_data(map_data['biomes'], width, height)
            entity_tiles = self._decompress_entity_data(map_data['entities'])
        else:
            # Legacy format - fallback to old deserialization
            terrain = self._deserialize_legacy_terrain(map_data['terrain'])
            biomes = self._deserialize_legacy_biomes(map_data['biomes'])
            entity_tiles = self._deserialize_legacy_entities(map_data['entities'])
        
        return terrain, biomes, entity_tiles
    
    def _deserialize_legacy_terrain(self, terrain_data: List[List[Dict]]) -> List[List[Tile]]:
        """Deserialize legacy terrain format"""
        terrain = []
        for row in terrain_data:
            terrain_row = []
            for tile_data in row:
                tile_type = TileType(tile_data['type'])
                tile_props = self.tile_registry.get_tile_properties(tile_type)
                tile = Tile(
                    tile_type, 
                    tile_props, 
                    variation=tile_data.get('variation', 0),
                    custom_data=tile_data.get('custom_data', {})
                )
                terrain_row.append(tile)
            terrain.append(terrain_row)
        return terrain
    
    def _deserialize_legacy_biomes(self, biome_data: List[List[str]]) -> List[List[BiomeType]]:
        """Deserialize legacy biome format"""
        biomes = []
        for row in biome_data:
            biome_row = []
            for biome_value in row:
                biome = BiomeType(biome_value) if biome_value else None
                biome_row.append(biome)
            biomes.append(biome_row)
        return biomes
    
    def _deserialize_legacy_entities(self, entity_data: List[Dict]) -> List[EntityTile]:
        """Deserialize legacy entity format"""
        entities = []
        for entity_dict in entity_data:
            entity_type = EntityTileType(entity_dict['type'])
            entity_props = self.entity_registry.get_entity_properties(entity_type)
            
            entity = EntityTile(
                entity_type,
                entity_dict['x'],
                entity_dict['y'],
                entity_props,
                custom_data=entity_dict.get('custom_data', {})
            )
            
            entity.current_health = entity_dict.get('health', entity.current_health)
            entity.construction_progress = entity_dict.get('construction_progress', 1.0)
            entity.stored_items = entity_dict.get('stored_items', {})
            
            entities.append(entity)
        
        return entities

    def save_map_to_file(self, filepath: str, terrain: List[List[Tile]], 
                        biomes: List[List[BiomeType]], entity_tiles: List[EntityTile], 
                        metadata: Dict[str, Any] = None):
        """Save map to a compressed JSON file"""
        map_data = self.serialize_map(terrain, biomes, entity_tiles, metadata)
        
        try:
            if not filepath:
                filepath = "default_map.json"
            
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Save as compressed JSON
            json_str = json.dumps(map_data, separators=(',', ':'))  # Compact JSON
            
            with gzip.open(filepath + '.gz', 'wt', encoding='utf-8') as f:
                f.write(json_str)
            
            print(f"Compressed map saved to {filepath}.gz")
        except Exception as e:
            print(f"Error saving map to {filepath}: {e}")
    
    def load_map_from_file(self, filepath: str) -> Optional[Tuple[List[List[Tile]], List[List[BiomeType]], List[EntityTile], Dict[str, Any]]]:
        """Load map from a compressed JSON file"""
        try:
            # Try compressed file first
            if os.path.exists(filepath + '.gz'):
                with gzip.open(filepath + '.gz', 'rt', encoding='utf-8') as f:
                    map_data = json.load(f)
            elif os.path.exists(filepath):
                # Fallback to uncompressed file
                with open(filepath, 'r') as f:
                    map_data = json.load(f)
            else:
                print(f"Map file not found: {filepath}")
                return None
            
            terrain, biomes, entity_tiles = self.deserialize_map(map_data)
            metadata = map_data.get('metadata', {})
            
            print(f"Map loaded from {filepath}")
            return terrain, biomes, entity_tiles, metadata
        except Exception as e:
            print(f"Error loading map from {filepath}: {e}")
            return None
    
    def export_map_image(self, filepath: str, terrain: List[List[Tile]], 
                        tile_size: int = 4, show_biomes: bool = False, 
                        biomes: List[List[BiomeType]] = None):
        """Export map as an image for visualization"""
        if not pygame.get_init():
            pygame.init()
        
        height, width = len(terrain), len(terrain[0])
        image_width = width * tile_size
        image_height = height * tile_size
        
        surface = pygame.Surface((image_width, image_height))
        
        for y in range(height):
            for x in range(width):
                tile = terrain[y][x]
                
                if show_biomes and biomes:
                    # Use biome colors
                    biome = biomes[y][x]
                    color = self._get_biome_color(biome)
                else:
                    # Use tile colors
                    color = tile._base_color
                
                rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                pygame.draw.rect(surface, color, rect)
        
        try:
            pygame.image.save(surface, filepath)
            print(f"Map image exported to {filepath}")
        except Exception as e:
            print(f"Error exporting map image: {e}")
    
    def _get_biome_color(self, biome: BiomeType) -> Tuple[int, int, int]:
        """Get color for biome visualization"""
        biome_colors = {
            BiomeType.OCEAN: (0, 0, 139),
            BiomeType.LAKE: (0, 0, 255),
            BiomeType.RIVER: (65, 105, 225),
            BiomeType.BEACH: (238, 203, 173),
            BiomeType.PLAINS: (124, 252, 0),
            BiomeType.FOREST: (34, 139, 34),
            BiomeType.MOUNTAIN: (139, 137, 137),
            BiomeType.DESERT: (238, 203, 173),
            BiomeType.SNOW: (255, 250, 250),
            BiomeType.SWAMP: (107, 142, 35)
        }
        return biome_colors.get(biome, (255, 0, 255))

# ============================================================================
# PERFORMANCE OPTIMIZATION SYSTEM
# ============================================================================

class MapChunk:
    """Represents a chunk of the map for efficient loading/unloading"""
    
    def __init__(self, chunk_x: int, chunk_y: int, chunk_size: int):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.chunk_size = chunk_size
        self.terrain: List[List[Tile]] = []
        self.biomes: List[List[BiomeType]] = []
        self.entity_tiles: List[EntityTile] = []
        self.loaded = False
        self.dirty = False  # Needs to be saved
        self.last_access_time = time.time()
    
    def get_world_bounds(self) -> Tuple[int, int, int, int]:
        """Get world coordinates of this chunk"""
        start_x = self.chunk_x * self.chunk_size
        start_y = self.chunk_y * self.chunk_size
        end_x = start_x + self.chunk_size
        end_y = start_y + self.chunk_size
        return start_x, start_y, end_x, end_y
    
    def contains_point(self, world_x: int, world_y: int) -> bool:
        """Check if world coordinates are within this chunk"""
        start_x, start_y, end_x, end_y = self.get_world_bounds()
        return start_x <= world_x < end_x and start_y <= world_y < end_y
    
    def get_local_coordinates(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to local chunk coordinates"""
        start_x, start_y, _, _ = self.get_world_bounds()
        return world_x - start_x, world_y - start_y

class ChunkedMapManager:
    """Manages map chunks for large worlds"""
    
    def __init__(self, chunk_size: int = 64, max_loaded_chunks: int = 9):
        self.chunk_size = chunk_size
        self.max_loaded_chunks = max_loaded_chunks
        self.chunks: Dict[Tuple[int, int], MapChunk] = {}
        self.chunk_cache_dir = "data/chunks"
        self.serializer = None  # Will be set by MapSystem
        
        # Create cache directory
        os.makedirs(self.chunk_cache_dir, exist_ok=True)
    
    def get_chunk_coordinates(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Get chunk coordinates for world position"""
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        return chunk_x, chunk_y
    
    def get_chunk(self, chunk_x: int, chunk_y: int) -> Optional[MapChunk]:
        """Get a chunk, loading it if necessary"""
        chunk_key = (chunk_x, chunk_y)
        
        if chunk_key in self.chunks:
            chunk = self.chunks[chunk_key]
            chunk.last_access_time = time.time()
            return chunk
        
        # Try to load chunk from disk
        chunk = self._load_chunk_from_disk(chunk_x, chunk_y)
        if chunk:
            self.chunks[chunk_key] = chunk
            self._manage_chunk_memory()
            return chunk
        
        return None
    
    def create_chunk(self, chunk_x: int, chunk_y: int, terrain: List[List[Tile]], 
                    biomes: List[List[BiomeType]], entity_tiles: List[EntityTile]) -> MapChunk:
        """Create a new chunk with given data"""
        chunk = MapChunk(chunk_x, chunk_y, self.chunk_size)
        chunk.terrain = terrain
        chunk.biomes = biomes
        chunk.entity_tiles = entity_tiles
        chunk.loaded = True
        chunk.dirty = True
        
        chunk_key = (chunk_x, chunk_y)
        self.chunks[chunk_key] = chunk
        
        self._manage_chunk_memory()
        return chunk
    
    def save_chunk(self, chunk: MapChunk):
        """Save a chunk to compressed disk storage"""
        if not self.serializer or not chunk.dirty:
            return
        
        filename = f"chunk_{chunk.chunk_x}_{chunk.chunk_y}.json"
        filepath = os.path.join(self.chunk_cache_dir, filename)
        
        try:
            self.serializer.save_map_to_file(filepath, chunk.terrain, chunk.biomes, chunk.entity_tiles)
            chunk.dirty = False
        except Exception as e:
            print(f"Error saving chunk {chunk.chunk_x}, {chunk.chunk_y}: {e}")
    
    def _load_chunk_from_disk(self, chunk_x: int, chunk_y: int) -> Optional[MapChunk]:
        """Load a chunk from compressed disk storage"""
        if not self.serializer:
            return None
        
        filename = f"chunk_{chunk_x}_{chunk_y}.json"
        filepath = os.path.join(self.chunk_cache_dir, filename)
        
        # Check for compressed file first, then uncompressed
        if not os.path.exists(filepath + '.gz') and not os.path.exists(filepath):
            return None
        
        try:
            result = self.serializer.load_map_from_file(filepath)
            if result:
                terrain, biomes, entity_tiles, _ = result
                chunk = MapChunk(chunk_x, chunk_y, self.chunk_size)
                chunk.terrain = terrain
                chunk.biomes = biomes
                chunk.entity_tiles = entity_tiles
                chunk.loaded = True
                return chunk
        except Exception as e:
            print(f"Error loading chunk {chunk_x}, {chunk_y}: {e}")
        
        return None
    
    def _manage_chunk_memory(self):
        """Unload least recently used chunks if memory limit exceeded"""
        if len(self.chunks) <= self.max_loaded_chunks:
            return
        
        # Sort chunks by last access time
        sorted_chunks = sorted(self.chunks.items(), 
                             key=lambda x: x[1].last_access_time)
        
        # Unload oldest chunks
        chunks_to_unload = len(self.chunks) - self.max_loaded_chunks
        for i in range(chunks_to_unload):
            chunk_key, chunk = sorted_chunks[i]
            
            # Save chunk if dirty
            if chunk.dirty:
                self.save_chunk(chunk)
            
            # Remove from memory
            del self.chunks[chunk_key]
    
    def get_chunks_in_area(self, world_x: int, world_y: int, width: int, height: int) -> List[MapChunk]:
        """Get all chunks that intersect with the given area"""
        chunks = []
        
        start_chunk_x = world_x // self.chunk_size
        start_chunk_y = world_y // self.chunk_size
        end_chunk_x = (world_x + width - 1) // self.chunk_size
        end_chunk_y = (world_y + height - 1) // self.chunk_size
        
        for chunk_y in range(start_chunk_y, end_chunk_y + 1):
            for chunk_x in range(start_chunk_x, end_chunk_x + 1):
                chunk = self.get_chunk(chunk_x, chunk_y)
                if chunk:
                    chunks.append(chunk)
        
        return chunks

# ============================================================================
# MAIN MAP SYSTEM
# ============================================================================

class MapSystem:
    """Main map system that coordinates all map-related functionality"""
    
    def __init__(self, enable_chunking: bool = False, chunk_size: int = 64):
        # Initialize registries
        self.tile_registry = TileRegistry()
        self.entity_registry = EntityTileRegistry()
        self.biome_registry = BiomeRegistry()
        
        # Initialize subsystems
        self.map_generator = MapGenerator(self.tile_registry, self.biome_registry, self.entity_registry)
        self.serializer = MapSerializer(self.tile_registry, self.entity_registry)
        
        # Chunking system (optional)
        self.enable_chunking = enable_chunking
        if enable_chunking:
            self.chunk_manager = ChunkedMapManager(chunk_size)
            self.chunk_manager.serializer = self.serializer
        else:
            self.chunk_manager = None
        
        # Current map data
        self.current_terrain: List[List[Tile]] = []
        self.current_biomes: List[List[BiomeType]] = []
        self.entity_tile_manager: Optional[EntityTileManager] = None
        self.map_width = 0
        self.map_height = 0
        
        # Rendering cache
        self.render_cache: Dict[str, pygame.Surface] = {}
        self.cache_dirty = True
        
        # Performance monitoring
        self.performance_stats = {
            'generation_time': 0,
            'render_time': 0,
            'tiles_rendered': 0,
            'chunks_loaded': 0
        }
    
    def create_map(self, config: MapGenerationConfig) -> bool:
        """Create a new map using the specified configuration"""
        start_time = time.time()
        
        try:
            # Generate terrain and biomes
            terrain, biomes = self.map_generator.generate_map(config)
            
            # Initialize entity tile manager
            self.entity_tile_manager = EntityTileManager(config.width, config.height)
            
            # Generate entity tiles if enabled
            entity_tiles = []
            if config.entity_generation:
                entity_tiles = self.map_generator.generate_entity_tiles(
                    terrain, biomes, self.entity_tile_manager
                )
            
            # Store map data
            if self.enable_chunking:
                self._store_map_in_chunks(terrain, biomes, entity_tiles, config)
            else:
                self.current_terrain = terrain
                self.current_biomes = biomes
            
            self.map_width = config.width
            self.map_height = config.height
            self.cache_dirty = True
            
            # Update performance stats
            generation_time = time.time() - start_time
            self.performance_stats['generation_time'] = generation_time
            
            print(f"Map generated successfully in {generation_time:.2f} seconds")
            print(f"Map size: {config.width}x{config.height}")
            print(f"Entity tiles: {len(entity_tiles)}")
            
            return True
            
        except Exception as e:
            print(f"Error creating map: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _store_map_in_chunks(self, terrain: List[List[Tile]], biomes: List[List[BiomeType]], 
                           entity_tiles: List[EntityTile], config: MapGenerationConfig):
        """Store map data in chunks for large worlds"""
        if not self.chunk_manager:
            return
        
        chunk_size = self.chunk_manager.chunk_size
        chunks_x = (config.width + chunk_size - 1) // chunk_size
        chunks_y = (config.height + chunk_size - 1) // chunk_size
        
        for chunk_y in range(chunks_y):
            for chunk_x in range(chunks_x):
                # Extract chunk data
                start_x = chunk_x * chunk_size
                start_y = chunk_y * chunk_size
                end_x = min(start_x + chunk_size, config.width)
                end_y = min(start_y + chunk_size, config.height)
                
                # Extract terrain for this chunk
                chunk_terrain = []
                chunk_biomes = []
                
                for y in range(start_y, end_y):
                    terrain_row = []
                    biome_row = []
                    for x in range(start_x, end_x):
                        terrain_row.append(terrain[y][x])
                        biome_row.append(biomes[y][x])
                    chunk_terrain.append(terrain_row)
                    chunk_biomes.append(biome_row)
                
                # Extract entity tiles for this chunk
                chunk_entities = []
                for entity in entity_tiles:
                    if start_x <= entity.x < end_x and start_y <= entity.y < end_y:
                        # Adjust entity coordinates to be relative to chunk
                        adjusted_entity = EntityTile(
                            entity.entity_type,
                            entity.x - start_x,
                            entity.y - start_y,
                            entity.properties,
                            entity.custom_data
                        )
                        adjusted_entity.current_health = entity.current_health
                        adjusted_entity.construction_progress = entity.construction_progress
                        adjusted_entity.stored_items = entity.stored_items.copy()
                        chunk_entities.append(adjusted_entity)
                
                # Create and store chunk
                self.chunk_manager.create_chunk(chunk_x, chunk_y, chunk_terrain, chunk_biomes, chunk_entities)
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get tile at world coordinates"""
        if self.enable_chunking and self.chunk_manager:
            chunk_x, chunk_y = self.chunk_manager.get_chunk_coordinates(x, y)
            chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
            
            if chunk and chunk.loaded:
                local_x, local_y = chunk.get_local_coordinates(x, y)
                if (0 <= local_x < len(chunk.terrain[0]) and 
                    0 <= local_y < len(chunk.terrain)):
                    return chunk.terrain[local_y][local_x]
        else:
            if (0 <= x < self.map_width and 0 <= y < self.map_height and
                self.current_terrain):
                return self.current_terrain[y][x]
        
        return None
    
    def set_tile(self, x: int, y: int, tile: Tile) -> bool:
        """Set tile at world coordinates"""
        if self.enable_chunking and self.chunk_manager:
            chunk_x, chunk_y = self.chunk_manager.get_chunk_coordinates(x, y)
            chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
            
            if chunk and chunk.loaded:
                local_x, local_y = chunk.get_local_coordinates(x, y)
                if (0 <= local_x < len(chunk.terrain[0]) and 
                    0 <= local_y < len(chunk.terrain)):
                    chunk.terrain[local_y][local_x] = tile
                    chunk.dirty = True
                    self.cache_dirty = True
                    return True
        else:
            if (0 <= x < self.map_width and 0 <= y < self.map_height and
                self.current_terrain):
                self.current_terrain[y][x] = tile
                self.cache_dirty = True
                return True
        
        return False
    
    def get_biome(self, x: int, y: int) -> Optional[BiomeType]:
        """Get biome at world coordinates"""
        if self.enable_chunking and self.chunk_manager:
            chunk_x, chunk_y = self.chunk_manager.get_chunk_coordinates(x, y)
            chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
            
            if chunk and chunk.loaded:
                local_x, local_y = chunk.get_local_coordinates(x, y)
                if (0 <= local_x < len(chunk.biomes[0]) and 
                    0 <= local_y < len(chunk.biomes)):
                    return chunk.biomes[local_y][local_x]
        else:
            if (0 <= x < self.map_width and 0 <= y < self.map_height and
                self.current_biomes):
                return self.current_biomes[y][x]
        
        return None
    
    def get_entity_tile(self, x: int, y: int) -> Optional[EntityTile]:
        """Get entity tile at world coordinates"""
        if self.entity_tile_manager:
            return self.entity_tile_manager.get_entity_tile_at(x, y)
        return None
    
    def add_entity_tile(self, entity_tile: EntityTile) -> bool:
        """Add an entity tile to the map"""
        if self.entity_tile_manager:
            success = self.entity_tile_manager.add_entity_tile(entity_tile)
            if success:
                self.cache_dirty = True
                
                # If using chunking, mark relevant chunks as dirty
                if self.enable_chunking and self.chunk_manager:
                    for dy in range(entity_tile._height):
                        for dx in range(entity_tile._width):
                            world_x = entity_tile.x + dx
                            world_y = entity_tile.y + dy
                            chunk_x, chunk_y = self.chunk_manager.get_chunk_coordinates(world_x, world_y)
                            chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
                            if chunk:
                                chunk.dirty = True
            
            return success
        return False
    
    def remove_entity_tile(self, x: int, y: int) -> Optional[EntityTile]:
        """Remove entity tile at world coordinates"""
        if self.entity_tile_manager:
            entity = self.entity_tile_manager.remove_entity_tile(x, y)
            if entity:
                self.cache_dirty = True
                
                # If using chunking, mark relevant chunks as dirty
                if self.enable_chunking and self.chunk_manager:
                    for dy in range(entity._height):
                        for dx in range(entity._width):
                            world_x = entity.x + dx
                            world_y = entity.y + dy
                            chunk_x, chunk_y = self.chunk_manager.get_chunk_coordinates(world_x, world_y)
                            chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
                            if chunk:
                                chunk.dirty = True
            
            return entity
        return None
    
    def is_position_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable"""
        # Check tile walkability
        tile = self.get_tile(x, y)
        if not tile or not tile.is_walkable():
            return False
        
        # Check entity tile walkability
        if self.entity_tile_manager:
            return not self.entity_tile_manager.is_position_blocked(x, y)
        
        return True
    
    def get_tiles_in_area(self, x: int, y: int, width: int, height: int) -> List[List[Optional[Tile]]]:
        """Get all tiles in a rectangular area"""
        tiles = []
        
        for dy in range(height):
            row = []
            for dx in range(width):
                tile = self.get_tile(x + dx, y + dy)
                row.append(tile)
            tiles.append(row)
        
        return tiles
    
    def render_area(self, screen: pygame.Surface, camera_x: int, camera_y: int, 
                   screen_width: int, screen_height: int, tile_size: int) -> None:
        """Render a specific area of the map"""
        start_time = time.time()
        
        # Calculate visible tile range
        tiles_per_screen_x = (screen_width // tile_size) + 2
        tiles_per_screen_y = (screen_height // tile_size) + 2
        
        start_tile_x = max(0, camera_x // tile_size)
        start_tile_y = max(0, camera_y // tile_size)
        end_tile_x = min(self.map_width, start_tile_x + tiles_per_screen_x)
        end_tile_y = min(self.map_height, start_tile_y + tiles_per_screen_y)
        
        tiles_rendered = 0
        
        # Render terrain tiles
        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                tile = self.get_tile(x, y)
                if tile:
                    screen_x = x * tile_size - camera_x
                    screen_y = y * tile_size - camera_y
                    
                    # Only render if on screen
                    if (-tile_size <= screen_x <= screen_width and 
                        -tile_size <= screen_y <= screen_height):
                        tile.render(screen, screen_x, screen_y, tile_size)
                        tiles_rendered += 1
        
        # Render entity tiles
        if self.entity_tile_manager:
            entities_in_view = self.entity_tile_manager.get_entities_in_area(
                start_tile_x, start_tile_y, 
                end_tile_x - start_tile_x, end_tile_y - start_tile_y
            )
            
            for entity in entities_in_view:
                screen_x = entity.x * tile_size - camera_x
                screen_y = entity.y * tile_size - camera_y
                
                # Only render if on screen
                entity_width = entity._width * tile_size
                entity_height = entity._height * tile_size
                
                if (-entity_width <= screen_x <= screen_width and 
                    -entity_height <= screen_y <= screen_height):
                    entity.render(screen, screen_x, screen_y, tile_size)
        
        # Update performance stats
        render_time = time.time() - start_time
        self.performance_stats['render_time'] = render_time
        self.performance_stats['tiles_rendered'] = tiles_rendered
    
    def save_map(self, filepath: str, metadata: Dict[str, Any] = None) -> bool:
        """Save the current map to a file"""
        try:
            if self.enable_chunking and self.chunk_manager:
                # Save all loaded chunks
                for chunk in self.chunk_manager.chunks.values():
                    if chunk.dirty:
                        self.chunk_manager.save_chunk(chunk)
                
                # Save chunk metadata
                chunk_metadata = {
                    'chunk_size': self.chunk_manager.chunk_size,
                    'map_width': self.map_width,
                    'map_height': self.map_height,
                    'chunks': list(self.chunk_manager.chunks.keys())
                }
                
                metadata = metadata or {}
                metadata.update(chunk_metadata)
                
                # Save metadata file
                metadata_path = filepath.replace('.json', '_metadata.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            else:
                # Save entire map
                entity_tiles = self.entity_tile_manager.get_all_entity_tiles() if self.entity_tile_manager else []
                self.serializer.save_map_to_file(filepath, self.current_terrain, self.current_biomes, entity_tiles, metadata)
            
            return True
        except Exception as e:
            print(f"Error saving map: {e}")
            return False
    
    def load_map(self, filepath: str) -> bool:
        """Load a map from a file"""
        try:
            # Check if this is a chunked map
            metadata_path = filepath.replace('.json', '_metadata.json')
            
            if os.path.exists(metadata_path):
                # Load chunked map
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                self.map_width = metadata['map_width']
                self.map_height = metadata['map_height']
                chunk_size = metadata['chunk_size']
                
                if not self.enable_chunking:
                    self.enable_chunking = True
                    self.chunk_manager = ChunkedMapManager(chunk_size)
                    self.chunk_manager.serializer = self.serializer
                
                self.entity_tile_manager = EntityTileManager(self.map_width, self.map_height)
                
            else:
                # Load regular map
                result = self.serializer.load_map_from_file(filepath)
                if not result:
                    return False
                
                terrain, biomes, entity_tiles, metadata = result
                
                self.current_terrain = terrain
                self.current_biomes = biomes
                self.map_width = len(terrain[0]) if terrain else 0
                self.map_height = len(terrain) if terrain else 0
                
                # Initialize entity tile manager
                self.entity_tile_manager = EntityTileManager(self.map_width, self.map_height)
                for entity in entity_tiles:
                    self.entity_tile_manager.add_entity_tile(entity)
            
            self.cache_dirty = True
            return True
            
        except Exception as e:
            print(f"Error loading map: {e}")
            return False
    
    def export_map_image(self, filepath: str, tile_size: int = 4, show_biomes: bool = False) -> bool:
        """Export the current map as an image"""
        try:
            if self.enable_chunking:
                # For chunked maps, we'd need to load all chunks and composite them
                # This is a simplified version
                print("Map image export for chunked maps not fully implemented")
                return False
            else:
                self.serializer.export_map_image(
                    filepath, self.current_terrain, tile_size, show_biomes, self.current_biomes
                )
            return True
        except Exception as e:
            print(f"Error exporting map image: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self.performance_stats.copy()
        
        if self.enable_chunking and self.chunk_manager:
            stats['chunks_loaded'] = len(self.chunk_manager.chunks)
            stats['chunk_cache_size'] = self.chunk_manager.max_loaded_chunks
        
        return stats
    
    def cleanup(self):
        """Clean up resources and save any pending data"""
        if self.enable_chunking and self.chunk_manager:
            # Save all dirty chunks
            for chunk in self.chunk_manager.chunks.values():
                if chunk.dirty:
                    self.chunk_manager.save_chunk(chunk)
        
        # Clear render cache
        self.render_cache.clear()
    
    def register_custom_tile_type(self, tile_type: TileType, properties: TileProperties):
        """Register a custom tile type"""
        self.tile_registry.register_tile(tile_type, properties)
        self.cache_dirty = True
    
    def register_custom_entity_type(self, entity_type: EntityTileType, properties: EntityTileProperties):
        """Register a custom entity tile type"""
        self.entity_registry.register_entity(entity_type, properties)
    
    def register_custom_biome(self, biome_rule: BiomeRule):
        """Register a custom biome"""
        self.biome_registry.register_biome(biome_rule)
    
    def get_map_info(self) -> Dict[str, Any]:
        """Get information about the current map"""
        info = {
            'width': self.map_width,
            'height': self.map_height,
            'chunked': self.enable_chunking,
            'total_tiles': self.map_width * self.map_height
        }
        
        if self.entity_tile_manager:
            info['entity_tiles'] = len(self.entity_tile_manager.get_all_entity_tiles())
        
        if self.enable_chunking and self.chunk_manager:
            info['chunk_size'] = self.chunk_manager.chunk_size
            info['loaded_chunks'] = len(self.chunk_manager.chunks)
        
        return info

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_default_map_config(width: int = 256, height: int = 256, 
                             seed: Optional[int] = None) -> MapGenerationConfig:
    """Create a default map generation configuration"""
    return MapGenerationConfig(
        width=width,
        height=height,
        seed=seed,
        generation_type=MapGenerationType.PROCEDURAL,
        noise_settings={
            'scale': 0.05,
            'octaves': 4,
            'persistence': 0.5,
            'lacunarity': 2.0
        },
        post_processing=['smooth', 'add_rivers'],
        entity_generation=True,
        border_type=None
    )

def create_island_map_config(width: int = 256, height: int = 256, 
                           seed: Optional[int] = None) -> MapGenerationConfig:
    """Create a configuration for generating island maps"""
    return MapGenerationConfig(
        width=width,
        height=height,
        seed=seed,
        generation_type=MapGenerationType.PROCEDURAL,
        noise_settings={
            'scale': 0.03,
            'octaves': 6,
            'persistence': 0.6,
            'lacunarity': 2.0,
            'island_factor': 0.8  # Custom parameter for island generation
        },
        post_processing=['smooth', 'add_rivers', 'ensure_connectivity'],
        entity_generation=True,
        border_type=TileType.DEEP_WATER
    )

def create_dungeon_map_config(width: int = 64, height: int = 64, 
                            seed: Optional[int] = None) -> MapGenerationConfig:
    """Create a configuration for generating dungeon maps"""
    return MapGenerationConfig(
        width=width,
        height=height,
        seed=seed,
        generation_type=MapGenerationType.CELLULAR_AUTOMATA,
        noise_settings={
            'initial_density': 0.45,
            'iterations': 5,
            'birth_limit': 4,
            'death_limit': 3
        },
        post_processing=['smooth', 'ensure_connectivity'],
        entity_generation=False,
        border_type=TileType.WALL
    )

def benchmark_map_generation(config: MapGenerationConfig, iterations: int = 5) -> Dict[str, float]:
    """Benchmark map generation performance"""
    map_system = MapSystem()
    times = []
    
    for i in range(iterations):
        start_time = time.time()
        map_system.create_map(config)
        end_time = time.time()
        times.append(end_time - start_time)
    
    return {
        'average_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times),
        'total_time': sum(times),
        'iterations': iterations
    }

# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

def example_usage():
    """Example of how to use the map system"""
    # Create a map system
    map_system = MapSystem(enable_chunking=False)
    
    # Create a default map configuration
    config = create_default_map_config(128, 128, seed=12345)
    
    # Generate the map
    print("Generating map...")
    success = map_system.create_map(config)
    
    if success:
        print("Map generated successfully!")
        
        # Get some tiles
        tile = map_system.get_tile(64, 64)
        print(f"Tile at (64, 64): {tile.tile_type if tile else 'None'}")
        
        # Check if position is walkable
        walkable = map_system.is_position_walkable(64, 64)
        print(f"Position (64, 64) walkable: {walkable}")
        
        # Get map info
        info = map_system.get_map_info()
        print(f"Map info: {info}")
        
        # Save the map
        print("Saving map...")
        map_system.save_map("test_map.json")
        
        # Export as image
        print("Exporting map image...")
        map_system.export_map_image("test_map.png", tile_size=2)
        
        # Get performance stats
        stats = map_system.get_performance_stats()
        print(f"Performance stats: {stats}")
    
    # Clean up
    map_system.cleanup()

def test_chunked_map():
    """Test chunked map functionality"""
    print("Testing chunked map system...")
    
    # Create a chunked map system
    map_system = MapSystem(enable_chunking=True, chunk_size=32)
    
    # Create a larger map
    config = create_default_map_config(256, 256, seed=54321)
    
    # Generate the map
    success = map_system.create_map(config)
    
    if success:
        print("Chunked map generated successfully!")
        
        # Test accessing tiles from different chunks
        for i in range(0, 256, 64):
            tile = map_system.get_tile(i, i)
            print(f"Tile at ({i}, {i}): {tile.tile_type if tile else 'None'}")
        
        # Get performance stats
        stats = map_system.get_performance_stats()
        print(f"Chunked map stats: {stats}")
    
    # Clean up
    map_system.cleanup()

def test_custom_tiles():
    """Test custom tile registration"""
    print("Testing custom tile registration...")
    
    map_system = MapSystem()
    
    # Register custom tiles - fix the property names to match TileProperties
    lava_props = TileProperties(
        tile_type=TileType.GRASS,  # Use existing enum value for demo
        name="Lava",
        description="Molten rock that burns everything",
        walkable=False,
        base_color=(255, 100, 0),
        movement_cost=float('inf'),
        opacity=0.8  # Use opacity instead of transparent
    )
    
    ice_props = TileProperties(
        tile_type=TileType.GRASS,  # Use existing enum value for demo
        name="Ice", 
        description="Slippery frozen water",
        walkable=True,
        base_color=(200, 200, 255),
        movement_cost=1.5,
        opacity=0.9
    )
    
    print("Custom tile properties created successfully")
    print(f"Lava properties: walkable={lava_props.walkable}, color={lava_props.base_color}")
    print(f"Ice properties: walkable={ice_props.walkable}, color={ice_props.base_color}")

if __name__ == "__main__":
    # Run examples
    print("=== Map System Examples ===")
    
    # Basic usage
    example_usage()
    print()
    
    # Chunked map test
    test_chunked_map()
    print()
    
    # Custom tiles test
    test_custom_tiles()
    print()
    
    # Benchmark different map types
    print("=== Benchmarking ===")
    
    configs = [
        ("Small Procedural", create_default_map_config(64, 64)),
        ("Medium Procedural", create_default_map_config(128, 128)),
        ("Large Procedural", create_default_map_config(256, 256)),
        ("Island Map", create_island_map_config(128, 128)),
        ("Dungeon Map", create_dungeon_map_config(64, 64))
    ]
    
    for name, config in configs:
        print(f"Benchmarking {name}...")
        results = benchmark_map_generation(config, iterations=3)
        print(f"  Average time: {results['average_time']:.3f}s")
        print(f"  Range: {results['min_time']:.3f}s - {results['max_time']:.3f}s")
        print()

"""
Entity Management System
Handles creation, spawning, tracking, updating, and destruction of all game entities
"""

import pygame
import random
import os
from typing import List, Optional, Dict, Any

from entities.rectangle import Rectangle
from entities.npc import NPC
from engine.constants import GameBalanceConstants


class EntityManager:
    """
    Manages all game entities including players, NPCs, and other interactive objects.
    
    Responsibilities:
    - Entity creation and spawning
    - Entity lifecycle management
    - Entity state persistence
    - Entity attribute initialization
    - CNA file loading for entities
    """
    
    def __init__(self, game_engine):
        """
        Initialize the entity manager
        
        Args:
            game_engine: Reference to the main game engine
        """
        self.game_engine = game_engine
        self.entities: List[Any] = []
        self.player: Optional[Rectangle] = None
        
        # Entity tracking
        self.npcs: List[NPC] = []
        self.food_npcs: List[Any] = []  # Will be typed properly when FoodNPC is available
        
        # Configuration
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        print("EntityManager initialized")
    
    def add_entity(self, entity) -> Any:
        """
        Add an entity to the game world
        
        Args:
            entity: The entity to add
            
        Returns:
            The added entity
        """
        self.entities.append(entity)
        
        # Track specific entity types
        if isinstance(entity, NPC):
            self.npcs.append(entity)
        
        # If this is a player-controlled entity, store reference
        if hasattr(entity, 'controllable') and entity.controllable:
            print(f"DEBUG: Player entity added with ID {entity.get_entity_id()}")
            self.player = entity
            
            # Set up camera to follow player
            if hasattr(self.game_engine, 'camera'):
                self.game_engine.camera.set_follow_target(entity)
            
            # Debug inventory
            if hasattr(entity, 'inventory'):
                print(f"DEBUG: Player has inventory with {len(entity.inventory.slots)} slots")
            else:
                print("DEBUG: Player does not have inventory attribute")
        
        # Add to game engine's object list for backward compatibility
        if hasattr(self.game_engine, 'objects'):
            self.game_engine.objects.append(entity)
        
        return entity
    
    def create_player(self, grid_x: int = 25, grid_y: int = 19, 
                     color: tuple = (255, 0, 0), speed: int = 1) -> Rectangle:
        """
        Create and configure the player entity
        
        Args:
            grid_x: Starting X position
            grid_y: Starting Y position
            color: Player color
            speed: Movement speed
            
        Returns:
            The created player entity
        """
        player = Rectangle(
            grid_x=grid_x, 
            grid_y=grid_y, 
            color=color, 
            speed=speed, 
            controllable=True
        )
        
        # Add survival attributes
        player.thirst = GameBalanceConstants.STARTING_THIRST
        player.last_thirst_update = pygame.time.get_ticks()
        player.last_drink_time = 0
        
        player.hunger = GameBalanceConstants.STARTING_HUNGER
        player.last_hunger_update = pygame.time.get_ticks()
        
        # Load CNA file if available
        self._load_entity_cna_file(player, "Alex_Brown.cna")
        
        # Add to entity management
        self.add_entity(player)
        
        print(f"Player created at ({grid_x}, {grid_y}) with ID {player.get_entity_id()}")
        return player
    
    def create_npc(self, grid_x: int, grid_y: int, color: tuple = (0, 255, 0), 
                   speed: int = 1, cna_filename: Optional[str] = None) -> NPC:
        """
        Create and configure an NPC entity
        
        Args:
            grid_x: Starting X position
            grid_y: Starting Y position
            color: NPC color
            speed: Movement speed
            cna_filename: Optional CNA file to load
            
        Returns:
            The created NPC entity
        """
        npc = NPC(grid_x=grid_x, grid_y=grid_y, color=color, speed=speed)
        
        # Load CNA file if specified
        if cna_filename:
            self._load_entity_cna_file(npc, cna_filename)
        
        # Initialize exploration attributes
        self._initialize_npc_exploration_attributes(npc)
        
        # Add to entity management
        self.add_entity(npc)
        
        print(f"NPC created at ({grid_x}, {grid_y}) with ID {npc.get_entity_id()}")
        return npc
    
    def spawn_food_npc(self, x: Optional[int] = None, y: Optional[int] = None, 
                      food_type: Optional[str] = None) -> Optional[Any]:
        """
        Spawn a food NPC at the specified position or a random valid position
        
        Args:
            x: X position (random if None)
            y: Y position (random if None)
            food_type: Type of food (random if None)
            
        Returns:
            The spawned food NPC or None if failed
        """
        try:
            from entities.food_npc import FoodNPC
            from engine.ai import FoodWanderAI
            
            # Find random position if not specified
            if x is None or y is None:
                pos = self._find_random_spawn_position()
                if pos:
                    x, y = pos
                else:
                    x, y = 10, 10  # Fallback position
            
            # Create the food NPC
            food_ai = FoodWanderAI()
            food_npc = FoodNPC(grid_x=x, grid_y=y, ai_controller=food_ai)
            
            # Set specific food type if provided
            if food_type:
                food_npc.food_type = food_type
                food_npc.set_color_by_food_type()
            
            # Track food NPCs separately
            self.food_npcs.append(food_npc)
            
            # Add to entity management
            self.add_entity(food_npc)
            
            return food_npc
            
        except ImportError:
            print("Warning: FoodNPC not available")
            return None
    
    def spawn_multiple_food_npcs(self, count: int = 30) -> List[Any]:
        """
        Spawn multiple food NPCs in the world
        
        Args:
            count: Number of food NPCs to spawn
            
        Returns:
            List of spawned food NPCs
        """
        spawned_npcs = []
        print(f"Spawning {count} food NPCs in the world...")
        
        for _ in range(count):
            food_npc = self.spawn_food_npc()
            if food_npc:
                spawned_npcs.append(food_npc)
        
        print(f"Successfully spawned {len(spawned_npcs)} food NPCs")
        return spawned_npcs
    
    def initialize_all_npc_exploration_attributes(self):
        """
        Initialize exploration attributes for all NPCs in the game
        """
        for entity in self.entities:
            if isinstance(entity, NPC):
                # Load cached position if available
                if hasattr(entity, 'load_position_from_cache'):
                    entity.load_position_from_cache()
                
                # Initialize exploration attributes
                self._initialize_npc_exploration_attributes(entity)
    
    def update_all_entities(self):
        """
        Update all managed entities
        This method ensures all entities get their update() method called
        """
        print(f"DEBUG: Updating {len(self.entities)} entities through EntityManager")
        
        for entity in self.entities:
            if hasattr(entity, 'update'):
                try:
                    entity.update()
                    
                    # Debug output for player thirst updates
                    if (hasattr(entity, 'controllable') and entity.controllable and 
                        hasattr(entity, 'thirst')):
                        # Only print occasionally to avoid spam
                        if pygame.time.get_ticks() % 5000 < 100:  # Every 5 seconds, for 100ms
                            print(f"DEBUG: Player thirst: {entity.thirst}, position: ({entity.grid_x}, {entity.grid_y})")
                            
                except Exception as e:
                    print(f"Error updating entity {entity}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"DEBUG: Entity {entity} has no update method")
    
    def _initialize_npc_exploration_attributes(self, npc: NPC):
        """
        Initialize exploration and AI attributes for an NPC
        
        Args:
            npc: The NPC to initialize
        """
        # Set exploration attributes
        npc.exploration_mode = "idle"
        npc.exploration_target_x = None
        npc.exploration_target_y = None
        npc.last_exploration_time = pygame.time.get_ticks()
        npc.explored_tiles = set()  # Set of (x, y) coordinates that have been explored
        npc.interesting_locations = {}  # Dict of location_type -> list of (x, y) coordinates
        npc.home_location = (npc.grid_x, npc.grid_y)  # Starting position as home base
        npc.curiosity = random.uniform(0.5, 1.0)  # How curious/exploratory this NPC is
        npc.last_memory_record_time = 0  # Time of last memory recording
        npc.memory_cooldown = 10000  # Milliseconds between memory recordings (10 seconds)
        
        # Advice following attributes
        npc.advice_remaining_distance = 0
        npc.advice_direction = None
        
        print(f"DEBUG: Initialized exploration attributes for NPC at ({npc.grid_x}, {npc.grid_y})")
    
    def _load_entity_cna_file(self, entity, filename: str):
        """
        Load CNA file for an entity if it exists
        
        Args:
            entity: The entity to load CNA data for
            filename: Name of the CNA file
        """
        cna_file_path = os.path.join(self.project_root, "cna", "data", filename)
        if os.path.exists(cna_file_path):
            print(f"Loading CNA file: {cna_file_path}")
            entity.load_cna_file(cna_file_path)
        else:
            print(f"CNA file not found: {cna_file_path}")
    
    def _find_random_spawn_position(self) -> Optional[tuple]:
        """
        Find a random valid spawn position on the map
        
        Returns:
            Tuple of (x, y) coordinates or None if no valid position found
        """
        if not hasattr(self.game_engine, 'world_map') or not self.game_engine.world_map:
            return None
        
        world_map = self.game_engine.world_map
        valid_positions = []
        
        # Find valid spawn positions (grass or dirt, not water or walls)
        for y_pos in range(world_map.height):
            for x_pos in range(world_map.width):
                tile = world_map.get_tile(x_pos, y_pos)
                if tile and hasattr(tile, 'is_walkable') and tile.is_walkable():
                    # Don't spawn on water
                    if not (hasattr(tile, 'is_water') and tile.is_water()):
                        valid_positions.append((x_pos, y_pos))
        
        # Choose a random valid position
        if valid_positions:
            return random.choice(valid_positions)
        
        return None
    
    def get_all_entities(self) -> List[Any]:
        """
        Get all managed entities
        
        Returns:
            List of all entities
        """
        return self.entities.copy()
    
    def get_player(self) -> Optional[Rectangle]:
        """
        Get the player entity
        
        Returns:
            Player entity or None if not found
        """
        return self.player
    
    def get_npcs(self) -> List[NPC]:
        """
        Get all NPC entities
        
        Returns:
            List of NPC entities
        """
        return self.npcs.copy()
    
    def get_food_npcs(self) -> List[Any]:
        """
        Get all food NPC entities
        
        Returns:
            List of food NPC entities
        """
        return self.food_npcs.copy()
    
    def remove_entity(self, entity) -> bool:
        """
        Remove an entity from management
        
        Args:
            entity: The entity to remove
            
        Returns:
            True if entity was removed, False otherwise
        """
        try:
            # Remove from main entity list
            if entity in self.entities:
                self.entities.remove(entity)
            
            # Remove from specific type lists
            if isinstance(entity, NPC) and entity in self.npcs:
                self.npcs.remove(entity)
            
            if entity in self.food_npcs:
                self.food_npcs.remove(entity)
            
            # Remove from game engine objects list
            if hasattr(self.game_engine, 'objects') and entity in self.game_engine.objects:
                self.game_engine.objects.remove(entity)
            
            # Clear player reference if this was the player
            if self.player == entity:
                self.player = None
            
            print(f"Entity {entity.get_entity_id()} removed from management")
            return True
            
        except Exception as e:
            print(f"Error removing entity: {e}")
            return False
    
    def get_entity_count(self) -> Dict[str, int]:
        """
        Get count of different entity types
        
        Returns:
            Dictionary with entity type counts
        """
        return {
            'total': len(self.entities),
            'npcs': len(self.npcs),
            'food_npcs': len(self.food_npcs),
            'player': 1 if self.player else 0
        }

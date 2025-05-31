"""
Game Initialization Manager
Handles dynamic loading and initialization of game components
"""
import importlib
from typing import Dict, Any, List
from config.game_config import GameConfig, SystemConfig, EntityConfig, WorldItemConfig
import pygame
import os
from typing import List, Dict, Any, Optional, Callable


class GameInitializer:
    """Manages dynamic game initialization based on configuration"""
    
    def __init__(self, engine):
        self.engine = engine
        self.initialized_systems = {}
        self.initialization_hooks = {}
        
        # Register built-in initialization methods
        self._register_builtin_hooks()
    
    def _register_builtin_hooks(self):
        """Register built-in initialization hooks"""
        self.initialization_hooks.update({
            'sound_system': self._init_sound_system,
            'entity_manager': self._init_entity_manager,
            'item_system': self._init_item_system,
            'world_map': self._init_world_map,
            'world_cache': self._init_world_cache,
            'ai_universe': self._init_ai_universe,
            'sprite_assets': self._init_sprite_assets,
        })
    
    def initialize_game(self, config: GameConfig, args):
        """Initialize game based on configuration"""
        print(f"Initializing game: {config.name}")
        print(f"Description: {config.description}")
        
        # Run pre-initialization hooks
        self._run_hooks(config.pre_init_hooks, config, args)
        
        # Initialize systems
        for system_config in config.systems:
            if system_config.enabled:
                self._initialize_system(system_config, args)
        
        # Initialize world
        self._initialize_world(config, args)
        
        # Create entities
        self._create_entities(config.entities)
        
        # Spawn world items
        self._spawn_world_items(config.world_items)
        
        # Run post-initialization hooks
        self._run_hooks(config.post_init_hooks, config, args)
        
        print("Game initialization complete!")
    
    def _run_hooks(self, hook_names: List[str], config: GameConfig, args):
        """Run initialization hooks"""
        for hook_name in hook_names:
            if hook_name in self.initialization_hooks:
                print(f"Running hook: {hook_name}")
                self.initialization_hooks[hook_name](config, args)
            else:
                print(f"Warning: Hook '{hook_name}' not found")
    
    def _initialize_system(self, system_config: SystemConfig, args):
        """Initialize a game system"""
        system_name = system_config.name
        
        if system_name in self.initialization_hooks:
            print(f"Initializing system: {system_name}")
            result = self.initialization_hooks[system_name](system_config.config, args)
            self.initialized_systems[system_name] = result
        else:
            print(f"Warning: System '{system_name}' not found")
    
    def _initialize_world(self, config: GameConfig, args):
        """Initialize the world map"""
        if 'world_map' in self.initialized_systems:
            world_map = self.initialized_systems['world_map']
            
            # Set world dimensions
            if hasattr(world_map, 'width') and hasattr(world_map, 'height'):
                world_map.width = config.world_width
                world_map.height = config.world_height
            
            # Generate map if skipping menu
            if args.skip_menu:
                world_map.generate_realistic_map(seed=self.engine.map_seed)
            
            # Enable debug mode if requested
            if args.map_debug:
                world_map.enable_debug_mode()
                print("Map debug mode enabled")
    
    def _create_entities(self, entity_configs: List[EntityConfig]):
        """Create entities based on configuration"""
        if not self.engine.entity_manager:
            print("Warning: Entity manager not initialized, skipping entity creation")
            return
        
        print("Creating game entities...")
        
        for entity_config in entity_configs:
            self._create_entity(entity_config)
        
        # Print statistics
        entity_counts = self.engine.entity_manager.get_entity_count()
        print(f"Entity creation complete:")
        print(f"  Total entities: {entity_counts['total']}")
        print(f"  Player: {entity_counts['player']}")
        print(f"  NPCs: {entity_counts['npcs']}")
        print(f"  Food NPCs: {entity_counts['food_npcs']}")
    
    def _create_entity(self, config: EntityConfig):
        """Create a single entity"""
        entity_manager = self.engine.entity_manager
        
        if config.entity_type == "player":
            entity_manager.create_player(
                grid_x=config.grid_x,
                grid_y=config.grid_y,
                color=config.color,
                speed=config.speed
            )
        elif config.entity_type == "npc":
            entity_manager.create_npc(
                grid_x=config.grid_x,
                grid_y=config.grid_y,
                color=config.color,
                speed=config.speed,
                cna_filename=config.cna_filename
            )
        elif config.entity_type == "food_npcs":
            entity_manager.spawn_multiple_food_npcs(count=config.count)
        else:
            print(f"Warning: Unknown entity type '{config.entity_type}'")
    
    def _spawn_world_items(self, item_configs: List[WorldItemConfig]):
        """Spawn world items based on configuration"""
        if not hasattr(self.engine, 'world_map') or not self.engine.world_map:
            print("Warning: World map not initialized, skipping world item spawning")
            return
        
        print("Spawning world items...")
        
        for item_config in item_configs:
            self.engine.world_map.spawn_item(
                item_config.item_type,
                item_config.x,
                item_config.y,
                item_config.quantity
            )
    
    # Built-in system initialization methods
    def _init_sound_system(self, config: Dict[str, Any], args):
        """Initialize sound system"""
        print("Initializing sound system...")
        from sound.sound_manager import initialize_sound_manager
        
        sound_manager = initialize_sound_manager(
            master_volume=config.get('master_volume', 0.7),
            sfx_volume=config.get('sfx_volume', 0.8),
            music_volume=config.get('music_volume', 0.6)
        )
        return sound_manager
    
    def _init_entity_manager(self, config: Dict[str, Any], args):
        """Initialize entity management system"""
        print("Initializing entity management system...")
        from entities.entity_manager import EntityManager
        
        entity_manager = EntityManager(self.engine)
        self.engine.entity_manager = entity_manager
        return entity_manager
    
    def _init_item_system(self, config: Dict[str, Any], args):
        """Initialize item management system"""
        print("Initializing item management system...")
        from entities.items.item_manager import initialize_item_system
        from entities.items.item_factory import ItemFactory
        
        item_manager = initialize_item_system()
        self.engine.item_manager = item_manager
        
        # Initialize item factory
        self.engine.load_item_icons()
        ItemFactory.ensure_item_assets_exist()
        ItemFactory.register_item_templates()
        
        return item_manager
    
    def _init_world_map(self, config: Dict[str, Any], args):
        """Initialize world map"""
        print("Initializing world map...")
        from world.map import WorldMap
        
        world_map = WorldMap(
            config.get('width', 256),
            config.get('height', 256)
        )
        world_map.initialize_entity_tiles()
        world_map.initialize_world_items()
        
        self.engine.set_world_map(world_map)
        return world_map
    
    def _init_world_cache(self, config: Dict[str, Any], args):
        """Initialize world cache system"""
        print("Initializing world cache system...")
        from world.world_cache import WorldCache
        
        world_cache = WorldCache()
        if args.skip_menu:
            world_cache.set_world_seed(self.engine.map_seed)
        
        self.engine.world_cache = world_cache
        
        # Connect to AI universe if available
        if hasattr(self.engine, 'ai_universe') and self.engine.ai_universe:
            self.engine.ai_universe.world_cache = world_cache
        
        # Connect to world map if available
        if hasattr(self.engine, 'world_map') and self.engine.world_map:
            self.engine.world_map.set_world_cache(world_cache)
        
        return world_cache
    
    def _init_ai_universe(self, config: Dict[str, Any], args):
        """Initialize AI Universe Controller"""
        if args.no_ai:
            print("AI Universe Controller disabled (--no-ai flag)")
            return None
        
        print("Initializing AI Universe Controller...")
        import os
        from ai.controllers.ai_universe_controller import AIUniverseController
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(project_root, "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
        
        ai_universe = AIUniverseController(
            use_llm=config.get('use_llm', True),
            use_local_model=config.get('use_local_model', True),
            model_path=model_path
        )
        ai_universe.start()
        self.engine.ai_universe = ai_universe
        
        return ai_universe
    
    def _init_sprite_assets(self, config: Dict[str, Any], args):
        """Initialize sprite assets"""
        print("Initializing sprite assets...")
        import os
        import pygame
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sprite_path = os.path.join(project_root, "assets", "ai_sheet.png")
        walk_sprite_path = os.path.join(project_root, "assets", "ai_walk.png")
        
        # Create placeholder sprites if they don't exist
        self._ensure_sprite_exists(sprite_path, "idle")
        self._ensure_sprite_exists(walk_sprite_path, "walk")
    
    def _ensure_sprite_exists(self, sprite_path: str, sprite_type: str):
        """Ensure a sprite file exists, create placeholder if not"""
        if not os.path.exists(sprite_path):
            print(f"Warning: {sprite_type} sprite sheet not found at {sprite_path}")
            print(f"Creating a placeholder {sprite_type} sprite sheet...")
            
            placeholder = pygame.Surface((32, 16))
            if sprite_type == "idle":
                placeholder.fill((255, 255, 255), rect=(0, 0, 16, 16))
                placeholder.fill((255, 255, 255), rect=(16, 0, 16, 16))
            else:  # walk
                placeholder.fill((240, 240, 240), rect=(0, 0, 16, 16))
                placeholder.fill((240, 240, 240), rect=(16, 0, 16, 16))
                pygame.draw.line(placeholder, (200, 200, 200), (4, 12), (12, 12), 2)
                pygame.draw.line(placeholder, (200, 200, 200), (20, 12), (28, 12), 2)
            
            os.makedirs(os.path.dirname(sprite_path), exist_ok=True)
            pygame.image.save(placeholder, sprite_path)
            print(f"Created placeholder {sprite_type} sprite sheet at {sprite_path}")
    
    def register_hook(self, name: str, hook_function: Callable):
        """Register a custom initialization hook"""
        self.initialization_hooks[name] = hook_function
    
    def get_system(self, name: str):
        """Get an initialized system by name"""
        return self.initialized_systems.get(name)
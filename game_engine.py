from sound.sound_manager import initialize_sound_manager
from engine.core.simple_game_engine import SimpleGameEngine  # Updated import
from engine.config.config_loader import initialize_config_loader  # New import
from entities.entity_manager import EntityManager  # New import
from world.map import WorldMap
from world.world_cache import WorldCache
import random
import os
import pygame
# Add this import
from ai.controllers.ai_universe_controller import AIUniverseController, WorldStateCollector
import argparse
from engine.constants import GameBalanceConstants

from entities.items.item_manager import ItemManager, initialize_item_system
from engine.core.game_state_manager import GameState  # Updated import


# RENDER ORDER
# 1. Terrain tiles
# 2. Entities
# 3. Entity tiles


if __name__ == "__main__":
    # Initialize configuration system first
    print("Initializing configuration system...")
    config_loader = initialize_config_loader()
    
    # Parse command line arguments
    map_seed = 39
    arg_parser = argparse.ArgumentParser(description='Grid-Based Game')
    arg_parser.add_argument('--seed', type=int, help='Seed for map generation')
    arg_parser.add_argument('--fullscreen', action='store_true', help='Start in fullscreen mode')
    arg_parser.add_argument('--borderless', action='store_true', help='Start in borderless fullscreen mode')
    arg_parser.add_argument('--width', type=int, default=800, help='Window width (default: 800)')
    arg_parser.add_argument('--height', type=int, default=600, help='Window height (default: 600)')
    arg_parser.add_argument('--skip-menu', action='store_true', help='Skip main menu and start game directly')
    args = arg_parser.parse_args()

    def debug_cna_data(self, entity, name):
        """Debug function to print CNA data details"""
        if hasattr(entity, 'cna_data') and entity.cna_data:
            print(f"DEBUG: {name} CNA data:")
            print(f"  - Culture: {entity.cna_data.culture} (value: {entity.cna_data.culture.value})")
            print(f"  - Current color: {entity.color}")
        else:
            print(f"DEBUG: {name} has no CNA data")

    # Initialize sound system
    print("Initializing sound system...")
    sound_manager = initialize_sound_manager(
        master_volume=0.7,
        sfx_volume=0.8,
        music_volume=0.6
    )
    
    # Create the main game engine
    engine = SimpleGameEngine(title="Hoomans", width=args.width, height=args.height, map_seed=args.seed)
    
    # Initialize entity management system
    print("Initializing entity management system...")
    entity_manager = EntityManager(engine)
    engine.entity_manager = entity_manager  # Store reference in engine
    
    # Set game state based on arguments
    if args.skip_menu:
        # Use the new game state constants
        game_state = GameState()
        engine.game_state = game_state.RUNNING
        engine.load_item_icons()
    else:
        # Ensure we're in menu state (this should be the default)
        game_state = GameState()
        engine.game_state = game_state.MAIN_MENU
    
    # Handle display mode arguments
    if args.fullscreen:
        engine.toggle_fullscreen()
    elif args.borderless:
        engine.toggle_borderless_fullscreen()

    # Initialize item management system
    print("Initializing item management system...")
    item_manager = initialize_item_system()
    engine.item_manager = item_manager
    
    # Initialize item factory after pygame is initialized
    from entities.items.item_factory import ItemFactory
    engine.load_item_icons()
    ItemFactory.ensure_item_assets_exist()
    ItemFactory.register_item_templates()

    # Initialize sprite assets
    project_root = os.path.dirname(os.path.abspath(__file__))
    sprite_path = os.path.join(project_root, "assets", "ai_sheet.png")
    walk_sprite_path = os.path.join(project_root, "assets", "ai_walk.png")
    
    # Check if sprite sheets exist and create placeholders if needed
    if not os.path.exists(sprite_path):
        print(f"Warning: Idle sprite sheet not found at {sprite_path}")
        print("Creating a placeholder idle sprite sheet...")
        # Create a placeholder sprite sheet
        placeholder = pygame.Surface((32, 16))
        # First frame (left half)
        placeholder.fill((255, 255, 255), rect=(0, 0, 16, 16))
        # Second frame (right half)
        placeholder.fill((255, 255, 255), rect=(16, 0, 16, 16))
        # Save the placeholder
        os.makedirs(os.path.dirname(sprite_path), exist_ok=True)
        pygame.image.save(placeholder, sprite_path)
        print(f"Created placeholder idle sprite sheet at {sprite_path}")
    
    if not os.path.exists(walk_sprite_path):
        print(f"Warning: Walk sprite sheet not found at {walk_sprite_path}")
        print("Creating a placeholder walk sprite sheet...")
        # Create a placeholder walk sprite sheet with slightly different frames
        placeholder = pygame.Surface((32, 16))
        # First frame (left half) - slightly different color to distinguish
        placeholder.fill((240, 240, 240), rect=(0, 0, 16, 16))
        # Second frame (right half) - slightly different color to distinguish
        placeholder.fill((240, 240, 240), rect=(16, 0, 16, 16))
        # Add some walking indicators
        pygame.draw.line(placeholder, (200, 200, 200), (4, 12), (12, 12), 2)
        pygame.draw.line(placeholder, (200, 200, 200), (20, 12), (28, 12), 2)
        # Save the placeholder
        os.makedirs(os.path.dirname(walk_sprite_path), exist_ok=True)
        pygame.image.save(placeholder, walk_sprite_path)
        print(f"Created placeholder walk sprite sheet at {walk_sprite_path}")

    # Initialize AI Universe Controller
    print("Initializing AI Universe Controller...")
    model_path = os.path.join(project_root, "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    ai_universe = AIUniverseController(use_llm=True, use_local_model=True, model_path=model_path)
    ai_universe.start()
    engine.ai_universe = ai_universe
    
    # Initialize world map
    print("Initializing world map...")
    world_map = WorldMap(256, 256)
    world_map.initialize_entity_tiles()

    # Only generate the map if we're skipping the menu
    if args.skip_menu:
        world_map.generate_realistic_map(seed=engine.map_seed)
    
    # Add world structures
    house = world_map.add_house(20, 10)
    engine.set_world_map(world_map)

    # Initialize world cache system
    print("Initializing world cache system...")
    world_cache = WorldCache()
    if args.skip_menu:
        world_cache.set_world_seed(engine.map_seed)
    engine.world_cache = world_cache
    ai_universe.world_cache = world_cache  # Direct reference to the same object
    world_map.set_world_cache(world_cache)

    # Initialize world items
    print("Initializing world items...")
    world_map.initialize_world_items()

    # Load world items from cache if available
    if hasattr(engine, 'world_cache') and engine.world_cache:
        world_map.world_item_manager.load_from_cache(engine.world_cache)

    # Spawn test items in the world
    print("Spawning test items in the world...")
    world_map.spawn_item("apple", 30, 20, 3)  # 3 apples
    world_map.spawn_item("berries", 25, 22, 1)  # 1 berries
    world_map.spawn_item("water_bottle", 35, 15, 2)  # 2 water bottles
    world_map.spawn_item("stone_axe", 28, 22, 1)  # 1 stone axe

    # Update and save world items
    if hasattr(engine.world_map, 'world_item_manager'):
        world_map.update_world_items()

    # Save world items to cache periodically
    if hasattr(engine, 'world_cache') and engine.world_cache:
        world_map.world_item_manager.save_to_cache(engine.world_cache)

    # === ENTITY CREATION USING ENTITY MANAGER ===
    print("Creating game entities...")
    
    # Create player entity
    player = entity_manager.create_player(grid_x=25, grid_y=19, color=(255, 0, 0), speed=1)
    
    # Create NPCs with specific CNA files
    wanderer = entity_manager.create_npc(
        grid_x=6, grid_y=6, 
        color=(0, 255, 0), 
        speed=1,
        cna_filename="Skyler_Smith.cna"
    )
    
    follower = entity_manager.create_npc(
        grid_x=37, grid_y=25, 
        color=(0, 0, 255), 
        speed=1,
        cna_filename="Dakota_Brown.cna"
    )

    # Spawn food NPCs using entity manager
    entity_manager.spawn_multiple_food_npcs(count=30)

    # Initialize exploration attributes for all NPCs
    print("Initializing NPC exploration attributes...")
    entity_manager.initialize_all_npc_exploration_attributes()
    
    # Print entity statistics
    entity_counts = entity_manager.get_entity_count()
    print(f"Entity creation complete:")
    print(f"  Total entities: {entity_counts['total']}")
    print(f"  Player: {entity_counts['player']}")
    print(f"  NPCs: {entity_counts['npcs']}")
    print(f"  Food NPCs: {entity_counts['food_npcs']}")
    
    # Start the main game loop
    print("Starting game loop...")
    engine.run()

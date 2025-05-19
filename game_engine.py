from engine.core import SimpleGameEngine
from entities.rectangle import Rectangle
from entities.npc import NPC
from engine.ai import RandomWanderAI, FollowPlayerAI
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


# RENDER ORDER
# 1. Terrain tiles
# 2. Entities
# 3. Entity tiles




if __name__ == "__main__":
    # Create the game engine
    map_seed = 39
    arg_parser = argparse.ArgumentParser(description='Grid-Based Game')
    arg_parser.add_argument('--seed', type=int, help='Seed for map generation')
    arg_parser.add_argument('--fullscreen', action='store_true', help='Start in fullscreen mode')
    arg_parser.add_argument('--borderless', action='store_true', help='Start in borderless fullscreen mode')
    arg_parser.add_argument('--width', type=int, default=800, help='Window width (default: 800)')
    arg_parser.add_argument('--height', type=int, default=600, help='Window height (default: 600)')
    args = arg_parser.parse_args()

    def debug_cna_data(self, entity, name):
        """Debug function to print CNA data details"""
        if hasattr(entity, 'cna_data') and entity.cna_data:
            print(f"DEBUG: {name} CNA data:")
            print(f"  - Culture: {entity.cna_data.culture} (value: {entity.cna_data.culture.value})")
            print(f"  - Current color: {entity.color}")
        else:
            print(f"DEBUG: {name} has no CNA data")

    engine = SimpleGameEngine(title="Hoomans", width=args.width, height=args.height, map_seed=args.seed)
    

    # Initialize item manager and register default items
    print("Initializing item management system...")
    item_manager = initialize_item_system()
    engine.item_manager = item_manager
    
    # Initialize item factory after pygame is initialized
    from entities.items.item_factory import ItemFactory
    engine.load_item_icons()
    ItemFactory.ensure_item_assets_exist()
    ItemFactory.register_item_templates()

    
    # Toggle fullscreen if requested
    if args.fullscreen:
        engine.toggle_fullscreen()

    elif args.borderless:
        engine.toggle_borderless_fullscreen()

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
    model_path = os.path.join(project_root, "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    ai_universe = AIUniverseController(use_llm=True, use_local_model=True, model_path=model_path)
    ai_universe.start()
    engine.ai_universe = ai_universe
    
    # Create and set up the world map (50x38 tiles for an 800x600 screen)
    world_map = WorldMap(256, 256)
    world_map.initialize_entity_tiles()

    world_map.generate_realistic_map(seed=engine.map_seed)
    # Initialize entity tile manager before adding any entity tiles
    
    # Add a tree and print debug info
    # tree = world_map.add_tree(24, 18)
    house = world_map.add_house(20, 10)
    
    engine.set_world_map(world_map)
    
    
    
    # Initialize world cache with the same seed
    world_cache = WorldCache()
    world_cache.set_world_seed(engine.map_seed)
    engine.world_cache = world_cache
    ai_universe.world_cache = world_cache  # Direct reference to the same object

    # Get absolute path to the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add a player-controlled rectangle (using grid coordinates)
    player = engine.add_object(Rectangle(grid_x=25, grid_y=19, color=(255, 0, 0), speed=1, controllable=True))
    
    # Add thirst attribute to player
    player.thirst = GameBalanceConstants.STARTING_THIRST
    player.last_thirst_update = pygame.time.get_ticks()
    player.last_drink_time = 0
    

    # Add thirst attribute to player
    player.hunger = GameBalanceConstants.STARTING_HUNGER
    player.last_hunger_update = pygame.time.get_ticks()
    player.last_drink_time = 0
    
    # Load CNA file for player if it exists
    cna_file_path = os.path.join(project_root, "cna", "data", "Alex_Brown.cna")
    if os.path.exists(cna_file_path):
        print(f"Loading CNA file: {cna_file_path}")
        player.load_cna_file(cna_file_path)
    else:
        print(f"CNA file not found: {cna_file_path}")
    
    # Add an NPC with AI Universe Controller
    wanderer = engine.add_object(NPC(grid_x=6, grid_y=6, color=(0, 255, 0), speed=1))
    # No need to add a specific AI controller, the universe will handle it
    # engine.add_ai_controller(WaterSeekingAI(wanderer, detection_range=8))
    
    # Load CNA file for wanderer if it exists
    cna_file_path = os.path.join(project_root, "cna", "data", "Skyler_Smith.cna")
    if os.path.exists(cna_file_path):
        print(f"Loading CNA file: {cna_file_path}")
        wanderer.load_cna_file(cna_file_path)
    else:
        print(f"CNA file not found: {cna_file_path}")
    
    # Add an NPC that follows the player
    follower = engine.add_object(NPC(grid_x=37, grid_y=25, color=(0, 0, 255), speed=1))
    # You can still use the built-in AI as a fallback
    # engine.add_ai_controller(FollowPlayerAI(follower, detection_range=8))
    
    # Load CNA file for follower if it exists
    cna_file_path = os.path.join(project_root, "cna", "data", "Dakota_Brown.cna")
    if os.path.exists(cna_file_path):
        print(f"Loading CNA file: {cna_file_path}")
        follower.load_cna_file(cna_file_path)
    else:
        print(f"CNA file not found: {cna_file_path}")
    

    print("Spawning food NPCs in the world...")
    for _ in range(30):  # Spawn 10 food NPCs
        food_npc = engine.spawn_food_npc()






    # Initialize exploration attributes for NPCs
    for obj in engine.objects:
        if isinstance(obj, NPC):
            # Set exploration attributes
            obj.exploration_mode = "idle"
            obj.exploration_target_x = None
            obj.exploration_target_y = None
            obj.last_exploration_time = pygame.time.get_ticks()
            obj.explored_tiles = set()  # Set of (x, y) coordinates that have been explored
            obj.interesting_locations = {}  # Dict of location_type -> list of (x, y) coordinates
            obj.home_location = (obj.grid_x, obj.grid_y)  # Starting position as home base
            obj.curiosity = random.uniform(0.5, 1.0)  # How curious/exploratory this NPC is
            obj.last_memory_record_time = 0  # Time of last memory recording
            obj.memory_cooldown = 10000  # Milliseconds between memory recordings (10 seconds)
            
            # Advice following attributes
            obj.advice_remaining_distance = 0
            obj.advice_direction = None
            
            print(f"DEBUG: Initialized exploration attributes for NPC at ({obj.grid_x}, {obj.grid_y})")

    
    # Start the game loop
    engine.run()

from engine.core import SimpleGameEngine
from entities.rectangle import Rectangle
from entities.npc import NPC
from engine.ai import RandomWanderAI, FollowPlayerAI, WaterSeekingAI
from world.map import WorldMap
import os
import pygame
# Add this import
from ai_universe_controller import AIUniverseController, WorldStateCollector

if __name__ == "__main__":
    # Create the game engine
    engine = SimpleGameEngine(title="Grid-Based Game", width=800, height=600)
    
    project_root = os.path.dirname(os.path.abspath(__file__))

    
    # Initialize AI Universe Controller
    model_path = os.path.join(project_root, "models", "tinyllama-1.1b-chat-v1.0.Q2_K.gguf")
    ai_universe = AIUniverseController(use_llm=True, use_local_model=True, model_path=model_path)
    ai_universe.start()
    engine.ai_universe = ai_universe
    
    # Create and set up the world map (50x38 tiles for an 800x600 screen)
    world_map = WorldMap(256, 256)
    world_map.generate_realistic_map()
    engine.set_world_map(world_map)
    
    # Get absolute path to the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add a player-controlled rectangle (using grid coordinates)
    player = engine.add_object(Rectangle(grid_x=25, grid_y=19, color=(255, 0, 0), speed=1, controllable=True))
    
    # Add thirst attribute to player
    player.thirst = 10
    player.last_thirst_update = pygame.time.get_ticks()
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
    
    # Start the game loop
    engine.run()

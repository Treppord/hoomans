from engine.core import SimpleGameEngine
from entities.rectangle import Rectangle
from entities.npc import NPC
from engine.ai import RandomWanderAI, FollowPlayerAI
from world.map import WorldMap
import os

if __name__ == "__main__":
    # Create the game engine
    engine = SimpleGameEngine(title="Grid-Based Game", width=800, height=600)
    
    # Create and set up the world map (50x38 tiles for an 800x600 screen)
    world_map = WorldMap(50, 38)
    world_map.generate_simple_map()
    engine.set_world_map(world_map)
    
    # Add a player-controlled rectangle (using grid coordinates)
    player = engine.add_object(Rectangle(grid_x=25, grid_y=19, color=(255, 0, 0), speed=0.1, controllable=True))
    
    # Get absolute path to the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Load CNA file for player if it exists
    cna_file_path = os.path.join(project_root, "cna", "data", "Alex_Brown.cna")
    if os.path.exists(cna_file_path):
        print(f"Loading CNA file: {cna_file_path}")
        player.load_cna_file(cna_file_path)
    else:
        print(f"CNA file not found: {cna_file_path}")
    
    # Add an NPC with random wandering AI
    wanderer = engine.add_object(NPC(grid_x=6, grid_y=6, color=(0, 255, 0), speed=0.1))
    engine.add_ai_controller(RandomWanderAI(wanderer))
    
    # Load CNA file for wanderer if it exists
    cna_file_path = os.path.join(project_root, "cna", "data", "Skyler_Smith.cna")
    if os.path.exists(cna_file_path):
        print(f"Loading CNA file: {cna_file_path}")
        wanderer.load_cna_file(cna_file_path)
    else:
        print(f"CNA file not found: {cna_file_path}")
    
    # Add an NPC that follows the player
    follower = engine.add_object(NPC(grid_x=37, grid_y=25, color=(0, 0, 255), speed=0.1))
    engine.add_ai_controller(FollowPlayerAI(follower, detection_range=8))
    
        # Load CNA file for player if it exists
    cna_file_path = os.path.join(project_root, "cna", "data", "Dakota_Brown.cna")
    if os.path.exists(cna_file_path):
        print(f"Loading CNA file: {cna_file_path}")
        follower.load_cna_file(cna_file_path)
    else:
        print(f"CNA file not found: {cna_file_path}")
    
    # Start the game loop
    engine.run()

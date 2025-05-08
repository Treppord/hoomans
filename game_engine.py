from engine.core import SimpleGameEngine
from entities.rectangle import Rectangle
from entities.npc import NPC
from engine.ai import RandomWanderAI, FollowPlayerAI
from world.map import WorldMap

if __name__ == "__main__":
    # Create the game engine
    engine = SimpleGameEngine(title="Grid-Based Game", width=800, height=600)
    
    # Create and set up the world map (50x38 tiles for an 800x600 screen)
    world_map = WorldMap(50, 38)
    world_map.generate_simple_map()
    engine.set_world_map(world_map)
    
    # Add a player-controlled rectangle (using grid coordinates)
    player = engine.add_object(Rectangle(grid_x=25, grid_y=19, color=(255, 0, 0), speed=1, controllable=True))
    
    # Add an NPC with random wandering AI
    wanderer = engine.add_object(NPC(grid_x=6, grid_y=6, color=(0, 255, 0), speed=1))
    engine.add_ai_controller(RandomWanderAI(wanderer))
    
    # Add an NPC that follows the player
    follower = engine.add_object(NPC(grid_x=37, grid_y=25, color=(0, 0, 255), speed=1))
    engine.add_ai_controller(FollowPlayerAI(follower, detection_range=8))
    
    # Start the game loop
    engine.run()

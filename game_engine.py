from engine.core import SimpleGameEngine
from entities.rectangle import Rectangle
from entities.cna_entity import CNAEntity
from engine.ai import RandomWanderAI, FollowPlayerAI
from world.map import WorldMap
import os
import random


# Update the load_cna_files function to add more debugging
def load_cna_files(directory):
    """Load all CNA files from a directory"""
    cna_files = []
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith('.cna'):
                full_path = os.path.join(directory, filename)
                if os.path.isfile(full_path) and os.access(full_path, os.R_OK):
                    cna_files.append(full_path)
                else:
                    print(f"Warning: Cannot read file {full_path}")
    
    if not cna_files:
        print(f"No CNA files found in {directory}")
    else:
        print(f"Found {len(cna_files)} CNA files in {directory}")
        # Print the first few files for debugging
        for i, file in enumerate(cna_files[:5]):
            print(f"  {i+1}. {file}")
        if len(cna_files) > 5:
            print(f"  ... and {len(cna_files) - 5} more")
        
    return cna_files

# In the main section, add more debugging for player creation
if __name__ == "__main__":
    # Create the game engine
    engine = SimpleGameEngine(title="CNA Entity Simulation", width=800, height=600)
    
    # Create and set up the world map
    world_map = WorldMap(50, 38)  # Use a smaller map for testing
    world_map.generate_large_map()
    engine.set_world_map(world_map)
    
    # Create the cna/data directory if it doesn't exist
    os.makedirs("cna/data", exist_ok=True)
    
    # Load available CNA files
    cna_files = load_cna_files("cna/data")
    
    # Add a player-controlled entity
    player_cna_file = cna_files[0] if cna_files else None
    print(f"Using CNA file for player: {player_cna_file}")
    
    player = engine.add_object(CNAEntity(
        grid_x=25, 
        grid_y=19, 
        cna_file=player_cna_file,
        color=(255, 0, 0), 
        speed=1, 
        controllable=True
    ))
    
    # Add CNA entities (just a few for testing)
    num_entities = min(5, len(cna_files) - 1 if cna_files else 5)
    
    for i in range(num_entities):
        # Choose a random position near the center
        grid_x = random.randint(20, 30)
        grid_y = random.randint(15, 25)
        
        # Use a CNA file if available, otherwise generate random
        cna_file = cna_files[i+1] if i+1 < len(cna_files) else None
        print(f"Creating entity {i+1} with CNA file: {cna_file}")
        
        # Create the entity
        entity = engine.add_object(CNAEntity(
            grid_x=grid_x,
            grid_y=grid_y,
            cna_file=cna_file,
            speed=1
        ))
    
    # Start the game loop
    engine.run()

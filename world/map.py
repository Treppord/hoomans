import pygame
from world.tile import Tile
import random
import noise
import math

class WorldMap:
    """Represents the game world as a grid of tiles"""
    
    def __init__(self, width, height):
        """Initialize a map with the given dimensions in tiles"""
        self.width = width
        self.height = height
        self.tiles = [[Tile("empty") for _ in range(width)] for _ in range(height)]
    
    def set_tile(self, x, y, tile_type):
        """Set a tile at the specified position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = Tile(tile_type)
    
    def get_tile(self, x, y):
        """Get the tile at the specified position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None
    
    def render(self, screen, camera):
        """Render the visible portion of the map"""
        # Calculate visible tile range based on camera position and zoom
        screen_width, screen_height = screen.get_size()
        
        # Convert screen boundaries to world coordinates
        world_left, world_top = camera.reverse_apply(0, 0)
        world_right, world_bottom = camera.reverse_apply(screen_width, screen_height)
        
        # Calculate tile range to render
        start_x = max(0, int(world_left / Tile.SIZE))
        start_y = max(0, int(world_top / Tile.SIZE))
        end_x = min(self.width, int(world_right / Tile.SIZE) + 2)
        end_y = min(self.height, int(world_bottom / Tile.SIZE) + 2)
        
        # Render visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Apply camera transformation
                tile_x, tile_y, tile_width, tile_height = camera.apply(
                    x * Tile.SIZE, y * Tile.SIZE, Tile.SIZE, Tile.SIZE
                )
                
                # Only render if the tile is on screen
                if (tile_x + tile_width > 0 and tile_x < screen_width and
                    tile_y + tile_height > 0 and tile_y < screen_height):
                    self.tiles[y][x].render(screen, tile_x, tile_y, tile_width, tile_height)
        
        # Draw grid lines if zoom level is appropriate
        if camera.should_draw_grid():
            grid_color = (50, 50, 50)  # Dark gray
            
            # Draw vertical grid lines
            for x in range(start_x, end_x + 1):
                grid_x, grid_y, _, _ = camera.apply(x * Tile.SIZE, start_y * Tile.SIZE, 0, 0)
                _, grid_bottom, _, _ = camera.apply(x * Tile.SIZE, end_y * Tile.SIZE, 0, 0)
                pygame.draw.line(screen, grid_color, (grid_x, grid_y), (grid_x, grid_bottom), 1)
            
            # Draw horizontal grid lines
            for y in range(start_y, end_y + 1):
                grid_x, grid_y, _, _ = camera.apply(start_x * Tile.SIZE, y * Tile.SIZE, 0, 0)
                grid_right, _, _, _ = camera.apply(end_x * Tile.SIZE, y * Tile.SIZE, 0, 0)
                pygame.draw.line(screen, grid_color, (grid_x, grid_y), (grid_right, grid_y), 1)
                

        
        # Render entity tiles if we have an entity tile manager
        if hasattr(self, 'entity_tile_manager'):
            self.entity_tile_manager.render(screen, camera)
    
    def initialize_entity_tiles(self):
        """Initialize entity tiles manager"""
        from world.entity_tile import EntityTileManager, TreeEntityTile, HouseEntityTile
        self.entity_tile_manager = EntityTileManager(self)
        print("Entity tile manager initialized")
    
    def add_tree(self, x, y):
        """Add a tree entity tile at the specified position"""
        from world.entity_tile import TreeEntityTile
        
        if not hasattr(self, 'entity_tile_manager'):
            self.initialize_entity_tiles()
        
        # Check if the position is valid
        if not (0 <= x < self.width - 1 and 0 <= y < self.height - 2):
            return None
            
        # Check if the tiles are available (not water, mountain, or occupied by another entity tile)
        if (self.get_tile(x, y).is_water() or self.get_tile(x, y).type == "mountain" or
            self.get_tile(x, y+1).is_water() or self.get_tile(x, y+1).type == "mountain"):
            return None
            
        # Check if there's already an entity tile here
        if hasattr(self, 'entity_tile_manager'):
            if self.entity_tile_manager.get_entity_tile_at(x, y) or self.entity_tile_manager.get_entity_tile_at(x, y+1):
                return None
        
        # Create and add the tree
        tree = TreeEntityTile(x, y)
        self.entity_tile_manager.add_entity_tile(tree)
        return tree
    
    def add_house(self, x, y):
        """Add a house entity tile at the specified position"""
        from world.entity_tile import HouseEntityTile
        
        # Check if the position is valid
        if not (0 <= x < self.width - 2 and 0 <= y < self.height - 2):
            return None
            
        # Check if the tiles are available
        for dx in range(2):
            for dy in range(2):
                tile = self.get_tile(x + dx, y + dy)
                if tile.is_water() or tile.type == "mountain":
                    return None
                    
        # Check if there's already an entity tile here
        if hasattr(self, 'entity_tile_manager'):
            for dx in range(2):
                for dy in range(2):
                    if self.entity_tile_manager.get_entity_tile_at(x + dx, y + dy):
                        return None
        
        # Create and add the house
        house = HouseEntityTile(x, y)
        if hasattr(self, 'entity_tile_manager'):
            self.entity_tile_manager.add_entity_tile(house)
        return house
    
    def is_wall(self, x, y):
        """Check if the tile at the specified position is a wall"""
        tile = self.get_tile(x, y)
        return tile and tile.type == "wall"
    
    def is_adjacent_to_water(self, x, y):
        """Check if the given position is adjacent to or on water"""
        # Check the tile itself and adjacent tiles
        for dx, dy in [(0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.width and 0 <= ny < self.height and 
                self.get_tile(nx, ny) and self.get_tile(nx, ny).is_water()):
                return True
        return False

    
    def find_nearest_water(self, start_x, start_y, max_distance=8):
        """Find the nearest water tile within the given distance"""
        if not (0 <= start_x < self.width and 0 <= start_y < self.height):
            return None
            
        # Simple breadth-first search to find nearest water
        visited = set()
        queue = [(start_x, start_y, 0)]  # (x, y, distance)
        
        while queue:
            x, y, distance = queue.pop(0)
            
            # Skip if we've already visited this tile or if it's too far
            if (x, y) in visited or distance > max_distance:
                continue
                
            visited.add((x, y))
            
            # Check if this is a water tile
            if self.get_tile(x, y) and self.get_tile(x, y).is_water():
                return (x, y)
                
            # Add adjacent tiles to the queue
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    (nx, ny) not in visited and
                    self.get_tile(nx, ny) and self.get_tile(nx, ny).is_walkable()):
                    queue.append((nx, ny, distance + 1))
                    
        return None  # No water found within range
    
    def generate_realistic_map(self, scale=100.0, octaves=6, persistence=0.5, lacunarity=2.0, seed=None):
        """Generate a realistic world map using Perlin noise"""
        if seed is None:
            seed = random.randint(0, 1000)
        
        print(f"Generating realistic map with seed: {seed}")
        
        # Generate height map using Perlin noise
        height_map = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Get noise value at this position
                nx = x / scale
                ny = y / scale
                # Use multiple octaves for more natural terrain
                value = noise.pnoise2(nx, ny, octaves=octaves, persistence=persistence, 
                                     lacunarity=lacunarity, repeatx=self.width, repeaty=self.height, base=seed)
                # Normalize to 0-1 range
                value = (value + 1) / 2
                row.append(value)
            height_map.append(row)
        
        # Generate moisture map using different seed
        moisture_map = []
        moisture_seed = seed + 1000
        for y in range(self.height):
            row = []
            for x in range(self.width):
                nx = x / scale
                ny = y / scale
                value = noise.pnoise2(nx, ny, octaves=octaves, persistence=persistence, 
                                     lacunarity=lacunarity, repeatx=self.width, repeaty=self.height, base=moisture_seed)
                value = (value + 1) / 2
                row.append(value)
            moisture_map.append(row)
        
        # Set tiles based on height and moisture
        for y in range(self.height):
            for x in range(self.width):
                height = height_map[y][x]
                moisture = moisture_map[y][x]
                
                # Deep water
                if height < 0.3:
                    self.set_tile(x, y, "deep_water")
                
                # Shallow water
                elif height < 0.4:
                    self.set_tile(x, y, "shallow_water")
                
                # Beach/sand
                elif height < 0.45:
                    self.set_tile(x, y, "sand")
                
                # Grassland/plains
                elif height < 0.7:
                    if moisture > 0.6:
                        self.set_tile(x, y, "forest")
                    else:
                        self.set_tile(x, y, "grass")
                
                # Mountains
                elif height < 0.85:
                    self.set_tile(x, y, "mountain")
                
                # Snow peaks
                else:
                    self.set_tile(x, y, "snow")
        
        
        # Add border walls
        self._add_border_walls()
        
        # Ensure there's at least one accessible water area
        self._ensure_accessible_water()
    
    def add_path(self, start_x, start_y, end_x, end_y):
        """Add a path between two points on the map"""
        # Find a path between the start and end points
        path = self._find_path(start_x, start_y, end_x, end_y)
        
        # Create the path
        for x, y in path:
            # Don't place paths in water
            if not self.get_tile(x, y).is_water():
                self.set_tile(x, y, "path")
        
        return path

    
    def _find_path(self, start_x, start_y, end_x, end_y):
        """Simple A* pathfinding to create natural-looking paths"""
        # Initialize open and closed sets
        open_set = [(start_x, start_y)]
        closed_set = set()
        
        # Track path and costs
        came_from = {}
        g_score = {(start_x, start_y): 0}
        f_score = {(start_x, start_y): self._heuristic(start_x, start_y, end_x, end_y)}
        
        while open_set:
            # Find node with lowest f_score
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            
            # If we reached the end
            if current[0] == end_x and current[1] == end_y:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append((start_x, start_y))
                path.reverse()
                return path
            
            # Move current from open to closed
            open_set.remove(current)
            closed_set.add(current)
            
            # Check neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Skip if out of bounds or in closed set
                if (not (0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height) or
                    neighbor in closed_set):
                    continue
                
                # Get tile type for movement cost
                tile = self.get_tile(neighbor[0], neighbor[1])
                if not tile:
                    continue
                
                # Higher cost for water and mountains (avoid them)
                if tile.type == "mountain":
                    continue  # Don't path through mountains
                elif tile.is_water():
                    movement_cost = 100  # Very high cost for water
                elif tile.type == "forest":
                    movement_cost = 5  # Higher cost for forest
                else:
                    movement_cost = 1  # Normal cost
                
                # Calculate tentative g_score
                tentative_g = g_score.get(current, float('inf')) + movement_cost
                
                # Add to open set if not there
                if neighbor not in open_set:
                    open_set.append(neighbor)
                # Skip if this path is worse
                elif tentative_g >= g_score.get(neighbor, float('inf')):
                    continue
                
                # This is the best path so far
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + self._heuristic(neighbor[0], neighbor[1], end_x, end_y)
        
        # No path found
        return []

    
    def _heuristic(self, x1, y1, x2, y2):
        """Calculate Manhattan distance heuristic"""
        return abs(x1 - x2) + abs(y1 - y2)
    
    def _add_border_walls(self):
        """Add walls around the map border"""
        for x in range(self.width):
            self.set_tile(x, 0, "wall")
            self.set_tile(x, self.height - 1, "wall")
        
        for y in range(self.height):
            self.set_tile(0, y, "wall")
            self.set_tile(self.width - 1, y, "wall")
    
    def _ensure_accessible_water(self):
        """Ensure there's at least one accessible water area"""
        # Find center of map
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Check if there's water within reasonable distance
        water_found = False
        for radius in range(1, min(self.width, self.height) // 4):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) == radius:  # Check perimeter
                        x, y = center_x + dx, center_y + dy
                        if 0 <= x < self.width and 0 <= y < self.height:
                            if self.get_tile(x, y).is_water():
                                water_found = True
                                break
                if water_found:
                    break
            if water_found:
                break
        
        # If no water found within reasonable distance, create a lake
        if not water_found:
            lake_x = center_x + random.randint(-10, 10)
            lake_y = center_y + random.randint(-10, 10)
            lake_size = random.randint(5, 10)
            
            for y in range(lake_y - lake_size, lake_y + lake_size):
                for x in range(lake_x - lake_size, lake_x + lake_size):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        # Create oval-shaped lake
                        distance = math.sqrt(((x - lake_x) / lake_size) ** 2 + ((y - lake_y) / lake_size) ** 2)
                        if distance < 1:
                            if distance < 0.7:
                                self.set_tile(x, y, "deep_water")
                            else:
                                self.set_tile(x, y, "shallow_water")
                        elif distance < 1.2:
                            self.set_tile(x, y, "sand")

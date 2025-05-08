import pygame
from world.tile import Tile
import random

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
    
    def is_wall(self, x, y):
        """Check if the tile at the specified position is a wall"""
        tile = self.get_tile(x, y)
        return tile and tile.type == "wall"
    
    def is_adjacent_to_water(self, grid_x, grid_y):
        """Check if the given position is adjacent to water"""
    # Check the tile itself and all adjacent tiles
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = grid_x + dx, grid_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    tile = self.get_tile(nx, ny)
                    if tile and tile.type == "water":
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
            if self.get_tile(x, y) and self.get_tile(x, y).type == "water":
                return (x, y)
            
        # Add adjacent tiles to the queue
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    (nx, ny) not in visited and
                    not self.is_wall(nx, ny)):
                    queue.append((nx, ny, distance + 1))
                
        return None  # No water found within range
    
    def generate_large_map(self):
        """Generate a large map with various features"""
        # Fill with grass
        for y in range(self.height):
            for x in range(self.width):
                self.set_tile(x, y, "grass")
        
        # Add walls around the edges
        for x in range(self.width):
            self.set_tile(x, 0, "wall")
            self.set_tile(x, self.height - 1, "wall")
        
        for y in range(self.height):
            self.set_tile(0, y, "wall")
            self.set_tile(self.width - 1, y, "wall")
        
        # Add several ponds/lakes
        num_ponds = self.width // 50  # One pond per 50 tiles of width
        for _ in range(num_ponds):
            pond_x = random.randint(10, self.width - 10)
            pond_y = random.randint(10, self.height - 10)
            pond_size = random.randint(5, 15)
            
            # Create the pond
            for y in range(pond_y - pond_size // 2, pond_y + pond_size // 2):
                for x in range(pond_x - pond_size // 2, pond_x + pond_size // 2):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        # Make pond shape more natural with some randomness
                        distance = ((x - pond_x) ** 2 + (y - pond_y) ** 2) ** 0.5
                        if distance < pond_size // 2 + random.uniform(-1, 1):
                            self.set_tile(x, y, "water")
            
            # Add sand around the pond
            for y in range(pond_y - pond_size // 2 - 1, pond_y + pond_size // 2 + 1):
                for x in range(pond_x - pond_size // 2 - 1, pond_x + pond_size // 2 + 1):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if self.get_tile(x, y).type != "water":
                            # Check if adjacent to water
                            is_adjacent = False
                            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                nx, ny = x + dx, y + dy
                                if (0 <= nx < self.width and 0 <= ny < self.height and 
                                    self.get_tile(nx, ny).type == "water"):
                                    is_adjacent = True
                                    break
                            
                            if is_adjacent:
                                self.set_tile(x, y, "sand")
        
        # Add some random walls/obstacles
        num_obstacles = self.width // 20  # One obstacle group per 20 tiles of width
        for _ in range(num_obstacles):
            obstacle_x = random.randint(10, self.width - 10)
            obstacle_y = random.randint(10, self.height - 10)
            obstacle_size = random.randint(3, 8)
            
            # Create the obstacle
            for y in range(obstacle_y, obstacle_y + obstacle_size):
                for x in range(obstacle_x, obstacle_x + obstacle_size):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        # Make obstacle shape more interesting
                        if random.random() < 0.7:  # 70% chance to place a wall
                            self.set_tile(x, y, "wall")

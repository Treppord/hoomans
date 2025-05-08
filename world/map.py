import pygame
from world.tile import Tile

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
    
    def render(self, screen):
        """Render the entire map"""
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].render(screen, x, y)
    
    def is_wall(self, x, y):
        """Check if the tile at the specified position is a wall"""
        tile = self.get_tile(x, y)
        return tile and tile.type == "wall"
    
    def generate_simple_map(self):
        """Generate a simple map with walls around the edges and some features"""
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
        
        # Add a small pond
        for y in range(5, 10):
            for x in range(10, 15):
                self.set_tile(x, y, "water")
        
        # Add some sand around the pond
        for y in range(4, 11):
            for x in range(9, 16):
                if self.get_tile(x, y).type != "water":
                    self.set_tile(x, y, "sand")
        
        # Add some random walls
        for x in range(5, 8):
            self.set_tile(x, 15, "wall")
        
        for y in range(12, 18):
            self.set_tile(20, y, "wall")
            
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

    def is_adjacent_to_water(self, x, y):
        """Check if the given position is adjacent to water"""
        for dx, dy in [(0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.width and 0 <= ny < self.height and 
                self.get_tile(nx, ny) and self.get_tile(nx, ny).is_water()):
                return True
        return False

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
import pygame

class Tile:
    """Base class for all map tiles"""
    
    SIZE = 16  # Each tile is 16x16 pixels
    
    def __init__(self, tile_type="empty"):
        self.type = tile_type
        # Default colors for different tile types
        self.colors = {
            "empty": (0, 0, 0),       # Black
            "wall": (100, 100, 100),  # Gray
            "grass": (0, 150, 0),     # Green
            "water": (0, 0, 200),     # Blue
            "sand": (194, 178, 128)   # Sand color
        }
    
    def render(self, screen, x, y):
        """Render the tile at the specified grid position"""
        color = self.colors.get(self.type, (255, 0, 255))  # Default to magenta for unknown types
        pygame.draw.rect(screen, color, (x * self.SIZE, y * self.SIZE, self.SIZE, self.SIZE))
    
    def is_water(self):
        """Check if this tile is a water tile"""
        return self.type == "water"
    
    def is_walkable(self):
        """Check if entities can walk on this tile"""
        return self.type != "wall"

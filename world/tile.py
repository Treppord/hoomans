import pygame
import random

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
            "sand": (194, 178, 128),  # Sand color
            "forest": (0, 100, 0),    # Dark green
            "mountain": (120, 100, 80), # Brown
            "deep_water": (0, 0, 150), # Dark blue
            "shallow_water": (65, 105, 225), # Royal blue
            "rock": (150, 150, 150),  # Light gray
            "path": (153, 136, 119),  # Dirt path
            "snow": (250, 250, 250)   # Snow
        }
        
        # Add variation to natural tiles
        self.variation = random.randint(0, 15)
        
    def render(self, screen, x, y, width, height):
        """Render the tile at the specified position with the given size"""
        base_color = self.colors.get(self.type, (255, 0, 255))  # Default to magenta for unknown types
        
        # Add slight color variation to natural tiles
        if self.type in ["grass", "sand", "water", "forest", "mountain", "deep_water", "shallow_water"]:
            # Adjust color slightly based on variation
            r, g, b = base_color
            r = max(0, min(255, r + self.variation - 8))
            g = max(0, min(255, g + self.variation - 8))
            b = max(0, min(255, b + self.variation - 8))
            color = (r, g, b)
        else:
            color = base_color
        
        # Draw the base tile
        pygame.draw.rect(screen, color, (x, y, width, height))
        
        # Only add details if the tile is large enough (prevents errors when zoomed out)
        if width >= 4 and height >= 4:
            # Add details based on tile type
            if self.type == "grass" and self.variation > 12:
                # Add small grass tufts
                detail_color = (0, 180, 0)
                pygame.draw.rect(screen, detail_color, (x + width//4, y + height//4, max(1, width//8), max(1, height//8)))
            
            elif self.type == "sand" and self.variation > 10:
                # Add small pebbles
                detail_color = (180, 170, 120)
                pygame.draw.circle(screen, detail_color, (int(x + width//3), int(y + height//3)), max(1, width//10))
            
            elif self.type == "forest":
                # Add tree-like details
                trunk_color = (101, 67, 33)
                leaves_color = (0, 120, 0)
                
                # Draw trunk
                pygame.draw.rect(screen, trunk_color, (x + width//2 - max(1, width//10), y + height//2, max(1, width//5), height//2))
                
                # Draw leaves
                pygame.draw.circle(screen, leaves_color, (int(x + width//2), int(y + height//3)), max(1, width//3))
            
            elif self.type == "mountain":
                # Add mountain peak
                peak_color = (180, 180, 180)
                
                # Draw triangular peak
                points = [
                    (x + width//2, y + height//4),
                    (x + width//4, y + height//2),
                    (x + 3*width//4, y + height//2)
                ]
                pygame.draw.polygon(screen, peak_color, points)
            
            elif self.type == "path":
                # Add path texture
                for i in range(2):
                    detail_color = (133, 116, 99)
                    # Make sure we use integers for the coordinates
                    # Also ensure width and height are at least 1
                    int_width = max(1, int(width))
                    int_height = max(1, int(height))
                    pygame.draw.circle(screen, detail_color, 
                                      (int(x + random.randint(0, int_width)), int(y + random.randint(0, int_height))), 
                                      max(1, int(width//10)))
    
    def is_water(self):
        """Check if this tile is a water tile"""
        return self.type in ["water", "deep_water", "shallow_water"]
    
    def is_walkable(self):
        """Check if entities can walk on this tile"""
        return self.type not in ["wall", "mountain", "deep_water"]

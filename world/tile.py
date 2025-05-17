import pygame
import random
import os

class Tile:
    """Base class for all map tiles"""
    
    SIZE = 16  # Each tile is 16x16 pixels
    # Static dictionary to store loaded tile textures
    TEXTURES = {}
    # Dictionary to store texture variations
    TEXTURE_VARIATIONS = {}
    # Flag to track if we've attempted to load textures
    TEXTURES_LOADED = False
    # Tileset for forest floor
    FOREST_TILESET = None
    FOREST_TILES = []
    
    @classmethod
    def load_tileset(cls, filename, tile_width=16, tile_height=16):
        """Load a tileset image and split it into individual tiles"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tileset_path = os.path.join(project_root, "assets", "tile", filename)
        
        if not os.path.exists(tileset_path):
            return None, []
            
        try:
            # Load the tileset image
            tileset = pygame.image.load(tileset_path).convert_alpha()
            tileset_width, tileset_height = tileset.get_size()
            
            # Calculate how many tiles are in the tileset
            cols = tileset_width // tile_width
            rows = tileset_height // tile_height
            
            # Extract each tile
            tiles = []
            for row in range(rows):
                for col in range(cols):
                    x = col * tile_width
                    y = row * tile_height
                    # Create a new surface for the tile
                    tile = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
                    # Copy the tile from the tileset
                    tile.blit(tileset, (0, 0), (x, y, tile_width, tile_height))
                    tiles.append(tile)
            
            return tileset, tiles
        except Exception:
            return None, []
    
    @classmethod
    def load_textures(cls):
        """Load all tile textures from assets/tile/ folder"""
        # Only load textures once
        if cls.TEXTURES_LOADED:
            return
            
        cls.TEXTURES_LOADED = True
        
        # Get the path to the assets directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tile_assets_path = os.path.join(project_root, "assets", "tile")
        
        # If directory doesn't exist, silently return (will use color scheme)
        if not os.path.exists(tile_assets_path):
            return
        
        # Load forest tileset (64x64 with 16x16 tiles)
        cls.FOREST_TILESET, cls.FOREST_TILES = cls.load_tileset("forest_sheet.png", 16, 16)
        
        # Define tile types to look for
        tile_types = [
            "empty", "wall", "grass", "water", "sand", "forest", 
            "mountain", "deep_water", "shallow_water", "rock", "path", "snow"
        ]
        
        # Load each base texture
        for tile_type in tile_types:
            texture_path = os.path.join(tile_assets_path, f"{tile_type}.png")
            try:
                if os.path.exists(texture_path):
                    cls.TEXTURES[tile_type] = pygame.image.load(texture_path).convert_alpha()
                    
                    # Initialize variations list for this tile type
                    cls.TEXTURE_VARIATIONS[tile_type] = []
                    
                    # Look for variations (tile_type_1.png, tile_type_2.png, etc.)
                    variation_index = 1
                    while True:
                        variation_path = os.path.join(tile_assets_path, f"{tile_type}_{variation_index}.png")
                        if os.path.exists(variation_path):
                            try:
                                variation_texture = pygame.image.load(variation_path).convert_alpha()
                                cls.TEXTURE_VARIATIONS[tile_type].append(variation_texture)
                                variation_index += 1
                            except Exception:
                                break
                        else:
                            # No more variations found
                            break
            except Exception:
                # Silently continue if texture can't be loaded
                pass
    
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
        # Use a smaller variation range to avoid drastic color changes
        self.variation = random.randint(0, 10)
        
        # Ensure textures are loaded
        if not Tile.TEXTURES_LOADED:
            Tile.load_textures()
        
        # Randomly select a texture variation (10% chance for each variation)
        self.selected_texture = None
        
        # For forest tiles, use the tileset if available
        if self.type == "forest" and Tile.FOREST_TILES:
            # Select a random tile from the forest tileset
            # Use a deterministic approach based on the variation value
            tile_index = self.variation % len(Tile.FOREST_TILES)
            self.selected_texture = Tile.FOREST_TILES[tile_index]
        elif self.type in Tile.TEXTURES:
            # Start with the base texture
            self.selected_texture = Tile.TEXTURES[self.type]
            
            # Check if there are variations available
            if self.type in Tile.TEXTURE_VARIATIONS and Tile.TEXTURE_VARIATIONS[self.type]:
                # 10% chance for each variation
                for variation_texture in Tile.TEXTURE_VARIATIONS[self.type]:
                    if random.random() < 0.1:  # 10% chance
                        self.selected_texture = variation_texture
                        break
        
    def render(self, screen, x, y, width, height):
        """Render the tile at the specified position with the given size"""
        # Check if we have a texture for this tile type
        if self.selected_texture:
            # Use the selected texture (either base or variation)
            # Scale the texture to the desired size
            scaled_texture = pygame.transform.scale(self.selected_texture, (width, height))
            # Draw the texture
            screen.blit(scaled_texture, (x, y))
        else:
            # Fall back to color-based rendering
            base_color = self.colors.get(self.type, (255, 0, 255))  # Default to magenta for unknown types
            
            # Add slight color variation to natural tiles - include path in the list
            if self.type in ["grass", "sand", "water", "forest", "mountain", "deep_water", "shallow_water", "path", "snow"]:
                # Adjust color slightly based on variation, but with a smaller range
                r, g, b = base_color
                # Use a more subtle variation formula
                r = max(0, min(255, r + (self.variation - 5)))
                g = max(0, min(255, g + (self.variation - 5)))
                b = max(0, min(255, b + (self.variation - 5)))
                color = (r, g, b)
            else:
                color = base_color
            
            # Draw the base tile
            pygame.draw.rect(screen, color, (x, y, width, height))
            
            # Only add details if the tile is large enough (prevents errors when zoomed out)
            if width >= 4 and height >= 4:
                # Add details based on tile type
                if self.type == "grass" and self.variation > 8:
                    # Add small grass tufts
                    detail_color = (0, 180, 0)
                    pygame.draw.rect(screen, detail_color, (x + width//4, y + height//4, max(1, width//8), max(1, height//8)))
                
                elif self.type == "sand" and self.variation > 7:
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
                    # Add path texture - use fewer details to avoid the "line" effect
                    if self.variation > 5:  # Only add details sometimes
                        
                        # Add small grass tufts
                        detail_color = (0, 180, 0)
                        pygame.draw.rect(screen, detail_color, (x + width//4, y + height//4, max(1, width//8), max(1, height//8)))

    
    def is_water(self):
        """Check if this tile is a water tile"""
        return self.type in ["water", "deep_water", "shallow_water"]

    
    def is_walkable(self):
        """Check if entities can walk on this tile"""
        return self.type not in ["wall", "mountain", "deep_water"]

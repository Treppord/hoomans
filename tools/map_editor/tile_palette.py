"""
Tile palette for selecting different tile types
Integrates with the existing tile system and Aseprite
"""

import pygame
import sys
import os
from typing import Dict, List, Optional

# Import game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from world.tile import Tile

class TilePalette:
    """Manages tile selection and preview"""
    
    def __init__(self, aseprite_integration=None):
        """Initialize the tile palette"""
        self.aseprite = aseprite_integration
        
        # Available tile types
        self.tile_types = [
            "grass", "water", "sand", "forest", "mountain", 
            "deep_water", "shallow_water", "rock", "path", 
            "snow", "wall", "empty"
        ]
        
        # Tile colors for preview (fallback if no textures)
        self.tile_colors = {
            "empty": (0, 0, 0),
            "wall": (100, 100, 100),
            "grass": (0, 150, 0),
            "water": (0, 0, 200),
            "sand": (194, 178, 128),
            "forest": (0, 100, 0),
            "mountain": (120, 100, 80),
            "deep_water": (0, 0, 150),
            "shallow_water": (65, 105, 225),
            "rock": (150, 150, 150),
            "path": (153, 136, 119),
            "snow": (250, 250, 250)
        }
        
        # Load tile textures
        Tile.load_textures()
        
        # UI state
        self.scroll_offset = 0
        self.tile_size = 32
        self.tiles_per_row = 4
        
        print(f"Tile palette initialized with {len(self.tile_types)} tile types")
    
    def handle_event(self, event, palette_rect):
        """Handle events for tile selection"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Calculate which tile was clicked
            relative_pos = (event.pos[0] - palette_rect.left, 
                          event.pos[1] - palette_rect.top - 50)  # Account for header
            
            if relative_pos[1] >= 0:
                tile_x = relative_pos[0] // (self.tile_size + 5)
                tile_y = (relative_pos[1] + self.scroll_offset) // (self.tile_size + 5)
                
                tile_index = tile_y * self.tiles_per_row + tile_x
                
                if 0 <= tile_index < len(self.tile_types):
                    return self.tile_types[tile_index]
        
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll through tiles
            if palette_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset = max(0, self.scroll_offset - event.y * 20)
                return None
        
        return None
    
    def render(self, screen, palette_rect, selected_tile):
        """Render the tile palette"""
        # Draw header
        font = pygame.font.Font(None, 24)
        header_text = font.render("Tiles", True, (255, 255, 255))
        screen.blit(header_text, (palette_rect.left + 10, palette_rect.top + 10))
        
        # Calculate tile grid
        start_y = palette_rect.top + 50
        current_x = palette_rect.left + 10
        current_y = start_y - self.scroll_offset
        
        for i, tile_type in enumerate(self.tile_types):
            # Calculate position
            col = i % self.tiles_per_row
            row = i // self.tiles_per_row
            
            tile_x = palette_rect.left + 10 + col * (self.tile_size + 5)
            tile_y = start_y + row * (self.tile_size + 5) - self.scroll_offset
            
            # Skip if not visible
            if tile_y + self.tile_size < palette_rect.top or tile_y > palette_rect.bottom:
                continue
            
            # Draw tile preview
            tile_rect = pygame.Rect(tile_x, tile_y, self.tile_size, self.tile_size)
            
            # Check if we have a texture for this tile
            if tile_type in Tile.TEXTURES:
                # Scale and draw texture
                texture = Tile.TEXTURES[tile_type]
                scaled_texture = pygame.transform.scale(texture, (self.tile_size, self.tile_size))
                screen.blit(scaled_texture, tile_rect)
            else:
                # Draw colored rectangle
                color = self.tile_colors.get(tile_type, (255, 0, 255))
                pygame.draw.rect(screen, color, tile_rect)
            
            # Draw selection border
            if tile_type == selected_tile:
                pygame.draw.rect(screen, (255, 255, 0), tile_rect, 3)
            else:
                pygame.draw.rect(screen, (100, 100, 100), tile_rect, 1)
            
            # Draw tile name
            small_font = pygame.font.Font(None, 16)
            name_text = small_font.render(tile_type[:4], True, (255, 255, 255))
            screen.blit(name_text, (tile_x, tile_y + self.tile_size + 2))
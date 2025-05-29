"""
Tile palette for the map editor
Provides UI for selecting tiles and tools
"""

import pygame
from typing import List, Tuple, Optional
from enum import Enum

class EditorTool(Enum):
    """Available editor tools"""
    TILE_BRUSH = "tile_brush"
    ENTITY_PLACER = "entity_placer"
    ERASER = "eraser"
    SELECTOR = "selector"
    FILL = "fill"

class TilePalette:
    """Tile and tool selection palette for the map editor"""
    
    def __init__(self, aseprite_integration=None):
        """Initialize the tile palette
        
        Args:
            aseprite_integration: Optional Aseprite integration object
        """
        self.aseprite_integration = aseprite_integration
        
        # Available tiles
        self.available_tiles = [
            "grass", "water", "sand", "forest", "mountain", 
            "deep_water", "shallow_water", "rock", "path", "snow", "wall"
        ]
        
        # Current selection
        self.selected_tile = "grass"
        
        # UI layout
        self.tile_size = 32
        self.tiles_per_row = 3
        self.scroll_offset = 0
        
        # Colors
        self.bg_color = (60, 60, 60)
        self.border_color = (100, 100, 100)
        self.selected_color = (255, 255, 0)
        self.text_color = (255, 255, 255)
        
        # Font
        try:
            self.font = pygame.font.Font(None, 16)
            self.title_font = pygame.font.Font(None, 20)
        except:
            self.font = pygame.font.SysFont(None, 16)
            self.title_font = pygame.font.SysFont(None, 20)
        
        # Tile colors for preview
        self.tile_colors = {
            "grass": (0, 150, 0),
            "water": (0, 0, 200),
            "sand": (194, 178, 128),
            "forest": (0, 100, 0),
            "mountain": (120, 100, 80),
            "deep_water": (0, 0, 150),
            "shallow_water": (65, 105, 225),
            "rock": (150, 150, 150),
            "path": (153, 136, 119),
            "snow": (250, 250, 250),
            "wall": (100, 100, 100)
        }
    
    def handle_event(self, event):
        """Handle palette events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # This will be handled by the parent editor
            return False
        
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll through tiles
            self.scroll_offset = max(0, self.scroll_offset - event.y * 20)
            return True
        
        return False
    
    def render(self, screen, palette_rect):
        """Render the tile palette"""
        # Draw background
        pygame.draw.rect(screen, self.bg_color, palette_rect)
        pygame.draw.rect(screen, self.border_color, palette_rect, 2)
        
        # Draw title
        title_text = self.title_font.render("Tiles", True, self.text_color)
        screen.blit(title_text, (palette_rect.left + 10, palette_rect.top + 10))
        
        # Calculate starting position
        start_y = palette_rect.top + 40 - self.scroll_offset
        
        # Draw tiles
        for i, tile_type in enumerate(self.available_tiles):
            # Calculate position
            row = i // self.tiles_per_row
            col = i % self.tiles_per_row
            
            tile_x = palette_rect.left + 10 + col * (self.tile_size + 5)
            tile_y = start_y + row * (self.tile_size + 25)
            
            # Skip if not visible
            if tile_y + self.tile_size < palette_rect.top or tile_y > palette_rect.bottom:
                continue
            
            # Draw tile preview
            tile_rect = pygame.Rect(tile_x, tile_y, self.tile_size, self.tile_size)
            
            # Tile background
            color = self.tile_colors.get(tile_type, (100, 100, 100))
            pygame.draw.rect(screen, color, tile_rect)
            
            # Add tile-specific details
            self._draw_tile_details(screen, tile_rect, tile_type)
            
            # Selection border
            if tile_type == self.selected_tile:
                pygame.draw.rect(screen, self.selected_color, tile_rect, 3)
            else:
                pygame.draw.rect(screen, self.border_color, tile_rect, 1)
            
            # Tile label
            label_text = self.font.render(tile_type[:4], True, self.text_color)
            screen.blit(label_text, (tile_x, tile_y + self.tile_size + 2))
    
    def _draw_tile_details(self, screen, tile_rect, tile_type):
        """Draw tile-specific visual details"""
        if tile_type == "grass":
            # Add grass tufts
            detail_color = (0, 180, 0)
            pygame.draw.rect(screen, detail_color, 
                           (tile_rect.x + 8, tile_rect.y + 8, 4, 4))
            pygame.draw.rect(screen, detail_color, 
                           (tile_rect.x + 20, tile_rect.y + 16, 3, 3))
        
        elif tile_type == "forest":
            # Add tree-like details
            trunk_color = (101, 67, 33)
            leaves_color = (0, 120, 0)
            
            # Draw trunk
            pygame.draw.rect(screen, trunk_color, 
                           (tile_rect.centerx - 2, tile_rect.centery + 4, 4, 8))
            
            # Draw leaves
            pygame.draw.circle(screen, leaves_color, 
                             (tile_rect.centerx, tile_rect.centery - 2), 8)
        
        elif tile_type == "mountain":
            # Add mountain peak
            peak_color = (180, 180, 180)
            
            # Draw triangular peak
            points = [
                (tile_rect.centerx, tile_rect.y + 6),
                (tile_rect.x + 6, tile_rect.centery),
                (tile_rect.right - 6, tile_rect.centery)
            ]
            pygame.draw.polygon(screen, peak_color, points)
        
        elif tile_type == "path":
            # Add path stones
            stone_color = (120, 100, 80)
            pygame.draw.circle(screen, stone_color, 
                             (tile_rect.x + 10, tile_rect.y + 12), 2)
            pygame.draw.circle(screen, stone_color, 
                             (tile_rect.x + 20, tile_rect.y + 20), 2)
        
        elif tile_type == "sand":
            # Add small pebbles
            pebble_color = (180, 170, 120)
            pygame.draw.circle(screen, pebble_color, 
                             (tile_rect.x + 12, tile_rect.y + 15), 1)
            pygame.draw.circle(screen, pebble_color, 
                             (tile_rect.x + 22, tile_rect.y + 10), 1)
    
    def get_tile_at_pos(self, pos, palette_rect):
        """Get the tile type at the given position within the palette"""
        relative_x = pos[0] - palette_rect.left - 10
        relative_y = pos[1] - palette_rect.top - 40 + self.scroll_offset
        
        if relative_x < 0 or relative_y < 0:
            return None
        
        col = relative_x // (self.tile_size + 5)
        row = relative_y // (self.tile_size + 25)
        
        tile_index = row * self.tiles_per_row + col
        
        if 0 <= tile_index < len(self.available_tiles):
            return self.available_tiles[tile_index]
        
        return None

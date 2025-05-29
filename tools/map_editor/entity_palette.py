"""
Entity palette for the map editor
Provides UI for selecting entity types
"""

import pygame
from typing import List, Optional

class EntityPalette:
    """Entity selection palette for the map editor"""
    
    def __init__(self):
        """Initialize the entity palette"""
        # Available entity types
        self.available_entities = [
            "tree", "house"
        ]
        
        # Current selection
        self.selected_entity = "tree"
        
        # Colors for entity preview
        self.entity_colors = {
            "tree": (0, 120, 0),
            "house": (139, 69, 19)
        }
        
        # Entity descriptions
        self.entity_descriptions = {
            "tree": "Tree (1x2)",
            "house": "House (2x2)"
        }
        
        # UI settings
        self.entity_size = 48
        self.padding = 10
        self.entities_per_row = 2
        
        # Colors
        self.bg_color = (50, 50, 50)
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
        
        # Scroll state
        self.scroll_offset = 0
    
    def handle_event(self, event):
        """Handle palette events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # This will be handled by the parent editor
            return False
        
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll through entities
            self.scroll_offset = max(0, self.scroll_offset - event.y * 20)
            return True
        
        return False
    
    def render(self, screen, palette_rect):
        """Render the entity palette"""
        # Draw background
        pygame.draw.rect(screen, self.bg_color, palette_rect)
        pygame.draw.rect(screen, self.border_color, palette_rect, 2)
        
        # Draw title
        title_text = self.title_font.render("Entities", True, self.text_color)
        screen.blit(title_text, (palette_rect.left + 10, palette_rect.top + 10))
        
        # Calculate starting position
        start_y = palette_rect.top + 40 - self.scroll_offset
        
        # Draw entities
        for i, entity_type in enumerate(self.available_entities):
            # Calculate position
            row = i // self.entities_per_row
            col = i % self.entities_per_row
            
            entity_x = palette_rect.left + 10 + col * (self.entity_size + self.padding)
            entity_y = start_y + row * (self.entity_size + 30)
            
            # Skip if not visible
            if entity_y + self.entity_size < palette_rect.top or entity_y > palette_rect.bottom:
                continue
            
            # Draw entity preview
            entity_rect = pygame.Rect(entity_x, entity_y, self.entity_size, self.entity_size)
            
            # Background color
            color = self.entity_colors.get(entity_type, (100, 100, 100))
            pygame.draw.rect(screen, color, entity_rect)
            
            # Draw entity icon/shape
            if entity_type == "tree":
                # Draw simple tree shape
                trunk_rect = pygame.Rect(entity_x + self.entity_size//2 - 4, 
                                       entity_y + self.entity_size - 16, 8, 16)
                pygame.draw.rect(screen, (101, 67, 33), trunk_rect)
                pygame.draw.circle(screen, (0, 150, 0), 
                                 (entity_x + self.entity_size//2, entity_y + self.entity_size//2), 
                                 self.entity_size//3)
            elif entity_type == "house":
                # Draw simple house shape
                house_rect = pygame.Rect(entity_x + 8, entity_y + 16, 
                                       self.entity_size - 16, self.entity_size - 24)
                pygame.draw.rect(screen, (160, 82, 45), house_rect)
                # Roof
                roof_points = [
                    (entity_x + self.entity_size//2, entity_y + 8),
                    (entity_x + 8, entity_y + 16),
                    (entity_x + self.entity_size - 8, entity_y + 16)
                ]
                pygame.draw.polygon(screen, (139, 69, 19), roof_points)
            
            # Draw selection border
            if entity_type == self.selected_entity:
                pygame.draw.rect(screen, self.selected_color, entity_rect, 3)
            else:
                pygame.draw.rect(screen, self.border_color, entity_rect, 1)
            
            # Draw entity description
            desc_text = self.font.render(self.entity_descriptions.get(entity_type, entity_type), 
                                       True, self.text_color)
            screen.blit(desc_text, (entity_x, entity_y + self.entity_size + 2))
    
    def get_entity_at_pos(self, pos, palette_rect):
        """Get the entity type at the given position within the palette"""
        relative_x = pos[0] - palette_rect.left - 10
        relative_y = pos[1] - palette_rect.top - 40 + self.scroll_offset
        
        if relative_x < 0 or relative_y < 0:
            return None
        
        col = relative_x // (self.entity_size + self.padding)
        row = relative_y // (self.entity_size + 30)
        
        entity_index = row * self.entities_per_row + col
        
        if 0 <= entity_index < len(self.available_entities):
            return self.available_entities[entity_index]
        
        return None

"""
Entity palette for selecting and placing entity tiles
"""

import pygame
import sys
import os
from typing import Dict, List, Optional

class EntityPalette:
    """Manages entity tile selection and preview"""
    
    def __init__(self):
        """Initialize the entity palette"""
        # Available entity types
        self.entity_types = [
            "tree", "house"
            # Add more entity types as they're implemented
        ]
        
        # Entity colors for preview
        self.entity_colors = {
            "tree": (0, 100, 0),
            "house": (139, 69, 19)
        }
        
        # Entity descriptions
        self.entity_descriptions = {
            "tree": "Tree (1x2)",
            "house": "House (2x2)"
        }
        
        # UI state
        self.scroll_offset = 0
        self.entity_size = 48
        self.entities_per_row = 3
        
        print(f"Entity palette initialized with {len(self.entity_types)} entity types")
    
    def handle_event(self, event, palette_rect):
        """Handle events for entity selection"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Calculate which entity was clicked
            relative_pos = (event.pos[0] - palette_rect.left, 
                          event.pos[1] - palette_rect.top - 50)  # Account for header
            
            if relative_pos[1] >= 0:
                entity_x = relative_pos[0] // (self.entity_size + 10)
                entity_y = (relative_pos[1] + self.scroll_offset) // (self.entity_size + 30)
                
                entity_index = entity_y * self.entities_per_row + entity_x
                
                if 0 <= entity_index < len(self.entity_types):
                    return self.entity_types[entity_index]
        
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll through entities
            if palette_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset = max(0, self.scroll_offset - event.y * 20)
                return None
        
        return None
    
    def render(self, screen, palette_rect, selected_entity):
        """Render the entity palette"""
        # Draw header
        font = pygame.font.Font(None, 24)
        header_text = font.render("Entities", True, (255, 255, 255))
        screen.blit(header_text, (palette_rect.left + 10, palette_rect.top + 10))
        
        # Calculate entity grid
        start_y = palette_rect.top + 50
        
        for i, entity_type in enumerate(self.entity_types):
            # Calculate position
            col = i % self.entities_per_row
            row = i // self.entities_per_row
            
            entity_x = palette_rect.left + 10 + col * (self.entity_size + 10)
            entity_y = start_y + row * (self.entity_size + 30) - self.scroll_offset
            
            # Skip if not visible
            if entity_y + self.entity_size < palette_rect.top or entity_y > palette_rect.bottom:
                continue
            
            # Draw entity preview
            entity_rect = pygame.Rect(entity_x, entity_y, self.entity_size, self.entity_size)
            
            # Draw colored rectangle (placeholder for entity preview)
            color = self.entity_colors.get(entity_type, (255, 0, 255))
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
            if entity_type == selected_entity:
                pygame.draw.rect(screen, (255, 255, 0), entity_rect, 3)
            else:
                pygame.draw.rect(screen, (100, 100, 100), entity_rect, 1)
            
            # Draw entity description
            small_font = pygame.font.Font(None, 14)
            desc_text = small_font.render(self.entity_descriptions.get(entity_type, entity_type), 
                                        True, (255, 255, 255))
            screen.blit(desc_text, (entity_x, entity_y + self.entity_size + 2))
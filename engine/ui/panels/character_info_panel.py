"""Character info panel UI element"""
import pygame
from engine.ui.elements.base import UIElement
from engine.ui.constants.colors import DARK_PANEL_BG, BORDER_COLOR, TEXT_COLOR, TITLE_COLOR

class CharacterInfoPanel(UIElement):
    """Panel that displays character information from CNA data"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.entity = None
        self.background_color = DARK_PANEL_BG  # Using color constant
        self.text_color = TEXT_COLOR  # Using color constant
        self.title_color = TITLE_COLOR  # Using color constant
        self.font = pygame.font.Font("assets/font/CandC_LAN.ttf", 24)
        self.title_font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 20)
        self.padding = 15
        self.visible = False
        self.animation_timer = 0
        self.current_frame = 0
        self.animation_speed = 0.5  # Slower animation for the info 
        
    def set_entity(self, entity):
        """Set the entity to display information for"""
        self.entity = entity
        self.visible = (entity is not None and entity.cna_data is not None)
        
    def update_animation(self, delta_time=1/60):
        """Update the animation frame"""
        self.animation_timer += delta_time
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
                self.current_frame = (self.current_frame + 1) % len(self.entity.animation_frames)
        
    def render(self, screen):
        if not self.visible or not self.entity or not self.entity.cna_data:
            return
            
        # Update animation
        self.update_animation()
            
        # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                        (0, 0, self.width, self.height),
                        border_radius=10)
        
        # Draw divider line down the middle
        divider_x = self.width // 2
        pygame.draw.line(panel_surface, (100, 100, 100, 200),
                        (divider_x, 10), (divider_x, self.height - 10), 2)
        
        # Get CNA data
        cna = self.entity.cna_data
        
        # Draw title
        title_text = f"{cna.first_name} {cna.last_name}"
        title_surface = self.title_font.render(title_text, True, self.title_color)
        panel_surface.blit(title_surface, (self.padding, self.padding))
        
        # Left side - Entity visualization
        # Check if entity has animation frames
        if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
            # Calculate position and size for the sprite display
            sprite_rect = pygame.Rect(
                self.padding, 
                self.padding + 40, 
                (self.width // 2) - (self.padding * 2), 
                100
            )
            
            # Get the current animation frame
            if 0 <= self.current_frame < len(self.entity.animation_frames):
                current_frame = self.entity.animation_frames[self.current_frame]
                
                # Apply color tint if the entity has this method
                if hasattr(self.entity, 'apply_color_tint'):
                    current_frame = self.entity.apply_color_tint(current_frame)
                
                # Scale the sprite to fit the display area while maintaining aspect ratio
                frame_width, frame_height = current_frame.get_size()
                scale_factor = min(sprite_rect.width / frame_width, sprite_rect.height / frame_height)
                scaled_width = int(frame_width * scale_factor * 1.5)  # Make it 3x larger
                scaled_height = int(frame_height * scale_factor * 1.5)
                
                # Center the sprite in the display area
                sprite_x = sprite_rect.x + (sprite_rect.width - scaled_width) // 2
                sprite_y = sprite_rect.y + (sprite_rect.height - scaled_height) // 2
                
                # Scale and draw the sprite
                scaled_frame = pygame.transform.scale(current_frame, (scaled_width, scaled_height))
                panel_surface.blit(scaled_frame, (sprite_x, sprite_y))
                
                
            else:
                # Fallback: draw a colored rectangle
                pygame.draw.rect(panel_surface, self.entity.color, sprite_rect)
        else:
            # Fallback: draw a colored rectangle
            entity_rect = pygame.Rect(
                self.padding, 
                self.padding + 40, 
                (self.width // 2) - (self.padding * 2), 
                100
            )
            pygame.draw.rect(panel_surface, self.entity.color, entity_rect)
        
        # Add entity stats below the visualization
        stats_y = self.padding + 40 + 100 + 20  # Below the entity rectangle with some spacing
        
        # Display entity stats if available
        if hasattr(self.entity, 'thirst') or hasattr(self.entity, 'hunger') or hasattr(self.entity, 'health'):
            stats_title = self.font.render("Entity Stats", True, self.title_color)
            panel_surface.blit(stats_title, (self.padding, stats_y))
            stats_y += 30
            
            # Display thirst if available
            if hasattr(self.entity, 'thirst'):
                thirst_text = f"Thirst: {self.entity.thirst}/10"
                thirst_surface = self.small_font.render(thirst_text, True, self.text_color)
                panel_surface.blit(thirst_surface, (self.padding, stats_y))
                stats_y += 25
            
            # Display hunger if available
            if hasattr(self.entity, 'hunger'):
                hunger_text = f"Hunger: {self.entity.hunger}/10"
                hunger_surface = self.small_font.render(hunger_text, True, self.text_color)
                panel_surface.blit(hunger_surface, (self.padding, stats_y))
                stats_y += 25
            
            # Display health if available
            if hasattr(self.entity, 'health'):
                health_text = f"Health: {self.entity.health}/20"
                health_surface = self.small_font.render(health_text, True, self.text_color)
                panel_surface.blit(health_surface, (self.padding, stats_y))
                stats_y += 25
        
        # Right side - CNA attributes
        right_x = (self.width // 2) + self.padding
        y_offset = self.padding
        
        # Basic info section
        y_offset += 10
        info_text = self.font.render("Basic Information", True, self.title_color)
        panel_surface.blit(info_text, (right_x, y_offset))
        y_offset += 30
        
        # Gender, Culture, Nation
        attributes = [
            f"Gender: {cna.gender.name}",
            f"Culture: {cna.culture.name}",
            f"Nation: {cna.nation.name}",
            f"Age: {cna.age_minutes} minutes"
        ]
        
        for attr in attributes:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Health section
        y_offset += 10
        health_text = self.font.render("Health Attributes", True, self.title_color)
        panel_surface.blit(health_text, (right_x, y_offset))
        y_offset += 30
        
        health_attrs = [
            f"Physical: {cna.physical_health}/5",
            f"Generational: {cna.generational_health}/5",
            f"Mental: {cna.mental_health}/5"
        ]
        
        for attr in health_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Extended attributes section
        y_offset += 10
        ext_text = self.font.render("Extended Attributes", True, self.title_color)
        panel_surface.blit(ext_text, (right_x, y_offset))
        y_offset += 30
        
        ext_attrs = [
            f"Intelligence: {cna.intelligence_factor:.2f}",
            f"Adaptability: {cna.adaptability:.2f}",
            f"Immunity: {cna.immunity_strength:.2f}"
        ]
        
        for attr in ext_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))
        
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False
            return True
        return False
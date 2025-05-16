"""Text bubble UI element"""
import pygame
import time
from engine.ui.constants.colors import TEXT_BUBBLE_BG, TEXT_BUBBLE_BORDER, TEXT_COLOR

class TextBubble:
    """Speech bubble that appears above an entity"""
    def __init__(self, text, entity, duration=3.0):
        self.text = text
        self.entity = entity
        self.creation_time = time.time()
        self.duration = duration
        self.font = pygame.font.SysFont(None, 20)
        self.padding = 10
        self.background_color = TEXT_BUBBLE_BG
        self.border_color = TEXT_BUBBLE_BORDER
        self.text_color = TEXT_COLOR
        self.max_width = 200  # Maximum width for text wrapping
        
        # Wrap text if needed
        self.wrapped_text = self._wrap_text(self.text, self.max_width)
        
        # Calculate size based on wrapped text
        max_line_width = max([self.font.render(line, True, self.text_color).get_width() for line in self.wrapped_text])
        self.width = max_line_width + self.padding * 2
        self.height = len(self.wrapped_text) * self.font.get_linesize() + self.padding * 2
        
        # Animation properties
        self.appear_time = 0.2  # Time in seconds for bubble to appear
        self.disappear_time = 0.3  # Time in seconds for bubble to disappear
        
        # For stacking bubbles
        self.vertical_offset = 0  # Will be set by UIManager
        
    def _wrap_text(self, text, max_width):
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = self.font.render(word, True, self.text_color)
            word_width = word_surface.get_width()
            
            # Add space width except for first word in line
            if current_line:
                space_width = self.font.render(' ', True, self.text_color).get_width()
                test_width = current_width + space_width + word_width
            else:
                test_width = current_width + word_width
            
            if test_width <= max_width:
                current_line.append(word)
                current_width = test_width
            else:
                # Start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
        
    def is_expired(self):
        """Check if the bubble should disappear"""
        return time.time() - self.creation_time > self.duration
        
    def render(self, screen):
        if self.is_expired():
            return
            
        # Get camera from game engine
        from engine.core import SimpleGameEngine
        camera = None
        if hasattr(SimpleGameEngine, 'instance'):
            camera = SimpleGameEngine.instance.camera
            
        if not camera:
            return
            
        # Calculate position above entity in world coordinates
        world_x = self.entity.x + self.entity.width // 2
        world_y = self.entity.y - self.height - 5 - self.vertical_offset  # Add vertical offset for stacking
        
        # Apply camera transformation
        screen_x, screen_y, _, _ = camera.apply(world_x, world_y, 0, 0)
        
        # Adjust position to center the bubble
        screen_x -= self.width // 2
        
        # Keep bubble on screen
        screen_x = max(5, min(screen_x, screen.get_width() - self.width - 5))
        screen_y = max(5, min(screen_y, screen.get_height() - self.height - 5))
        
        # Calculate alpha based on time
        elapsed = time.time() - self.creation_time
        alpha = 255
        
        # Fade in
        if elapsed < self.appear_time:
            alpha = int(255 * (elapsed / self.appear_time))
        # Fade out
        elif elapsed > self.duration - self.disappear_time:
            alpha = int(255 * (1 - (elapsed - (self.duration - self.disappear_time)) / self.disappear_time))
        
        # Create a surface with alpha for transparency
        bubble_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw rounded rectangle background
        pygame.draw.rect(bubble_surface, (self.background_color[0], self.background_color[1], 
                                         self.background_color[2], int(self.background_color[3] * alpha / 255)), 
                        (0, 0, self.width, self.height), 
                        border_radius=8)
        
        # Draw border
        pygame.draw.rect(bubble_surface, (self.border_color[0], self.border_color[1], 
                                         self.border_color[2], int(self.border_color[3] * alpha / 255)), 
                        (0, 0, self.width, self.height), 
                        border_radius=8, width=2)
        
        # Draw little triangle pointer at the bottom
        pointer_points = [
            (self.width // 2 - 8, self.height),
            (self.width // 2, self.height + 8),
            (self.width // 2 + 8, self.height)
        ]
        pygame.draw.polygon(bubble_surface, (self.background_color[0], self.background_color[1], 
                                           self.background_color[2], int(self.background_color[3] * alpha / 255)), 
                          pointer_points)
        
        # Draw text
        y_offset = self.padding
        for line in self.wrapped_text:
            text_surface = self.font.render(line, True, (self.text_color[0], self.text_color[1], 
                                                       self.text_color[2], int(alpha)))
            bubble_surface.blit(text_surface, 
                              (self.padding, y_offset))
            y_offset += self.font.get_linesize()
        
        # Draw the bubble on the screen
        screen.blit(bubble_surface, (screen_x, screen_y))



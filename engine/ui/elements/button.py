"""Button UI element"""
import pygame
from engine.ui.elements.base import UIElement
from sound.sound_manager import get_sound_manager


class Button(UIElement):
    """A clickable button UI element"""
    
    def __init__(self, x, y, width, height, text, callback=None, 
                 background_color=(60, 60, 60, 220), hover_color=(80, 80, 80, 220),
                 text_color=(255, 255, 255), disabled_color=(40, 40, 40, 180)):
        """Initialize a button
        
        Args:
            x, y: Position of the button
            width, height: Size of the button
            text: Text to display on the button
            callback: Function to call when button is clicked
            background_color: Normal button color
            hover_color: Color when mouse is hovering over button
            text_color: Color of the button text
            disabled_color: Color when button is disabled
        """
        super().__init__(x, y, width, height, background_color)
        self.text = text
        self.callback = callback
        self.normal_color = background_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.disabled_color = disabled_color
        self.is_hovered = False
        self.hovered = False
        self.is_pressed = False
        self.is_disabled = False
        self.font = None
        self._initialize_font()
        self.sound_manager = get_sound_manager()
        self.hover_sound_played = False  # Track if hover sound was played
    
    # ADD: rect property for compatibility
    @property
    def rect(self):
        """Get the button's rectangle for collision detection and rendering"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def _initialize_font(self):
        """Initialize the font for the button text"""
        try:
            self.font = pygame.font.Font("assets/font/CandC_LAN.ttf", 18)
        except:
            # Fallback to default font if custom font not available
            self.font = pygame.font.SysFont(None, 24)
    
    def set_text(self, text):
        """Set the button text"""
        self.text = text
    
    def set_callback(self, callback):
        """Set the callback function"""
        self.callback = callback
    
    def set_disabled(self, disabled):
        """Enable or disable the button"""
        self.is_disabled = disabled
    
    def handle_event(self, event):
        """Handle mouse events for the button"""
        if not self.visible or self.is_disabled:
            return False
            
        # First, let the base class handle dragging if enabled
        if super().handle_event(event):
            return True
            
        # Handle mouse movement for hover effect
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.hovered
            self.hovered = self.contains_point(event.pos[0], event.pos[1])
            # ALSO update is_hovered for compatibility
            self.is_hovered = self.hovered
            
            # Play hover sound when first hovering
            if self.hovered and not was_hovered and not self.hover_sound_played:
                self.sound_manager.play_ui_hover()
                self.hover_sound_played = True
            elif not self.hovered:
                self.hover_sound_played = False 
            
        # Handle mouse button down
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            mouse_pos = event.pos
            if self.contains_point(mouse_pos[0], mouse_pos[1]):
                self.is_pressed = True
                self.sound_manager.play_ui_click()
                return True
                
        # Handle mouse button up and trigger callback
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left click release
            was_pressed = self.is_pressed
            self.is_pressed = False
            
            mouse_pos = event.pos
            if was_pressed and self.contains_point(mouse_pos[0], mouse_pos[1]):
                # Button was clicked, trigger callback
                if self.callback:
                    self.callback()
                return True
                
        return False
    
    def render(self, screen):
        """Render the button"""
        if not self.visible:
            return
            
        # Determine button color based on state
        if self.is_disabled:
            color = self.disabled_color
        elif self.is_pressed:
            # Darken the hover color when pressed
            r, g, b, a = self.hover_color
            color = (max(0, r-20), max(0, g-20), max(0, b-20), a)
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.normal_color
            
        # Create a surface with alpha for transparency
        button_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw button background with transparency
        pygame.draw.rect(button_surface, color, 
                        (0, 0, self.width, self.height),
                        border_radius=5)
        
        # Draw border
        border_color = (150, 150, 150) if self.is_hovered else self.border_color
        pygame.draw.rect(button_surface, border_color, 
                        (0, 0, self.width, self.height), 
                        width=2, border_radius=5)
        
        # Draw text if present
        if self.text and self.font:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.width//2, self.height//2))
            button_surface.blit(text_surface, text_rect)
        
        # Draw the button on the screen
        screen.blit(button_surface, (self.x, self.y))

"""Base UI element class"""
import pygame

class UIElement:
    """Base class for UI elements"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        
    def render(self, screen):
        """Render the UI element - override in subclasses"""
        pass
    
    def handle_event(self, event):
        """Handle input events - override in subclasses"""
        pass
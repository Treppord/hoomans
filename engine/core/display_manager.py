"""Display and window management"""
import pygame
import os
from engine.config.config_loader import get_config_loader

class DisplayManager:
    """Manages display settings, fullscreen, and window operations"""
    
    def __init__(self, title=None, width=None, height=None):
        config = get_config_loader()
        display_config = config.get_setting('game_settings', 'display', default={})
        
        # Initialize pygame display
        pygame.init()
        
        # Set up display properties
        self.title = title or display_config.get('title', 'Simple Game Engine')
        self.default_width = width or display_config.get('default_width', 800)
        self.default_height = height or display_config.get('default_height', 600)
        
        self.width = self.default_width
        self.height = self.default_height
        self.fullscreen = False
        self.borderless = False
        
        # Create the display
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(self.title)
        
        # Set up window icon
        self._setup_window_icon()
    
    def _setup_window_icon(self):
        """Load and set the window icon"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logo_path = os.path.join(project_root, "assets", "logo.png")
            
            if os.path.exists(logo_path):
                logo = pygame.image.load(logo_path)
                pygame.display.set_icon(logo)
                print(f"Set window icon from: {logo_path}")
            else:
                print(f"Logo file not found at: {logo_path}")
                self._create_default_icon()
        except Exception as e:
            print(f"Error setting window icon: {e}")
            self._create_default_icon()
    
    def _create_default_icon(self):
        """Create a simple default icon if the logo file is not found"""
        try:
            icon = pygame.Surface((32, 32))
            icon.fill((30, 60, 90))
            pygame.draw.rect(icon, (200, 230, 255), (8, 6, 4, 20))
            pygame.draw.rect(icon, (200, 230, 255), (20, 6, 4, 20))
            pygame.draw.rect(icon, (200, 230, 255), (8, 14, 16, 4))
            pygame.display.set_icon(icon)
            print("Created and set default icon")
        except Exception as e:
            print(f"Error creating default icon: {e}")
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            desktop_info = pygame.display.Info()
            new_width, new_height = desktop_info.current_w, desktop_info.current_h
            self.screen = pygame.display.set_mode((new_width, new_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.default_width, self.default_height), pygame.RESIZABLE)
        
        self._update_dimensions()
        return self.width, self.height
    
    def toggle_borderless_fullscreen(self):
        """Toggle borderless fullscreen mode"""
        import sys
        
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            desktop_info = pygame.display.Info()
            new_width, new_height = desktop_info.current_w, desktop_info.current_h
            
            if sys.platform == 'darwin':
                try:
                    self.screen = pygame.display.set_mode(
                        (0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF
                    )
                    self.borderless = False
                except pygame.error as e:
                    print(f"Error creating fullscreen window: {e}")
                    self.screen = pygame.display.set_mode(
                        (self.default_width, self.default_height), pygame.RESIZABLE
                    )
                    self.fullscreen = False
                    self.borderless = False
        else:
            self.screen = pygame.display.set_mode((self.default_width, self.default_height), pygame.RESIZABLE)
            self.borderless = False
        
        self._update_dimensions()
        return self.width, self.height
    
    def handle_resize(self, new_width, new_height):
        """Handle window resize event"""
        if not self.fullscreen:
            self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
            self._update_dimensions()
            return self.width, self.height
        return None
    
    def _update_dimensions(self):
        """Update internal width and height from screen"""
        self.width, self.height = self.screen.get_size()
    
    def get_screen(self):
        """Get the pygame screen surface"""
        return self.screen
    
    def get_size(self):
        """Get current screen dimensions"""
        return self.width, self.height
    
    def clear(self, color=None):
        """Clear the screen with the specified color"""
        if color is None:
            config = get_config_loader()
            color = config.get_setting('game_settings', 'theme', 'background_color', default=[0, 0, 0])
        self.screen.fill(color)
    
    def flip(self):
        """Update the display"""
        pygame.display.flip()
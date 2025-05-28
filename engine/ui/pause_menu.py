"""Pause Menu for the game"""
import pygame
from engine.ui.constants.colors import DARK_PANEL_BG, TEXT_COLOR, TITLE_COLOR
from engine.ui.elements.base import UIElement
from engine.ui.elements.button import Button

class PauseMenu(UIElement):
    """Pause menu that appears when ESC is pressed during gameplay"""
    
    def __init__(self, screen_width, screen_height, resume_callback=None, 
                 return_to_menu_callback=None, quit_callback=None):
        """Initialize the pause menu
        
        Args:
            screen_width: Width of the screen
            screen_height: Height of the screen
            resume_callback: Function to call when Resume is clicked
            return_to_menu_callback: Function to call when Return to Menu is clicked
            quit_callback: Function to call when Quit Game is clicked
        """
        # Create a centered panel
        panel_width = 400
        panel_height = 300
        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2
        
        super().__init__(panel_x, panel_y, panel_width, panel_height, 
                        background_color=(40, 40, 40, 240))
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.resume_callback = resume_callback
        self.return_to_menu_callback = return_to_menu_callback
        self.quit_callback = quit_callback
        self.buttons = []
        self.title_font = None
        self.visible = False  # Start hidden
        
        # Initialize fonts and UI elements
        self._initialize_fonts()
        self._create_buttons()
    
    def _initialize_fonts(self):
        """Initialize fonts for the menu"""
        try:
            self.title_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 36)
        except:
            # Fallback to default font
            self.title_font = pygame.font.SysFont(None, 36)
    
    def _create_buttons(self):
        """Create menu buttons"""
        button_width = 250
        button_height = 50
        button_spacing = 15
        
        # Calculate vertical position for buttons (centered within the panel)
        total_buttons_height = 3 * button_height + 2 * button_spacing
        start_y = self.y + (self.height - total_buttons_height) // 2 + 30  # Offset for title
        
        # Create Resume button
        resume_button = Button(
            x=self.x + (self.width - button_width) // 2,
            y=start_y,
            width=button_width,
            height=button_height,
            text="Resume",
            callback=self._resume_game
        )
        self.buttons.append(resume_button)
        
        # Create Return to Menu button
        menu_button = Button(
            x=self.x + (self.width - button_width) // 2,
            y=start_y + button_height + button_spacing,
            width=button_width,
            height=button_height,
            text="Return to Menu",
            callback=self._return_to_menu
        )
        self.buttons.append(menu_button)
        
        # Create Quit Game button
        quit_button = Button(
            x=self.x + (self.width - button_width) // 2,
            y=start_y + 2 * (button_height + button_spacing),
            width=button_width,
            height=button_height,
            text="Quit Game",
            callback=self._quit_game
        )
        self.buttons.append(quit_button)
    
    def _resume_game(self):
        """Resume the game"""
        self.hide()
        if self.resume_callback:
            self.resume_callback()
    
    def _return_to_menu(self):
        """Return to main menu"""
        self.hide()
        if self.return_to_menu_callback:
            self.return_to_menu_callback()
    
    def _quit_game(self):
        """Quit the game"""
        if self.quit_callback:
            self.quit_callback()
    
    def show(self):
        """Show the pause menu"""
        self.visible = True
    
    def hide(self):
        """Hide the pause menu"""
        self.visible = False
    
    def toggle(self):
        """Toggle the pause menu visibility"""
        self.visible = not self.visible
    
    def update_screen_size(self, screen_width, screen_height):
        """Update menu when screen size changes"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Recalculate panel position
        panel_x = (screen_width - self.width) // 2
        panel_y = (screen_height - self.height) // 2
        self.x = panel_x
        self.y = panel_y
        
        # Recreate buttons with new positions
        self.buttons = []
        self._create_buttons()
    
    def handle_event(self, event):
        """Handle menu events"""
        if not self.visible:
            return False
        
        # Handle ESC key to close menu
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume_game()
            return True
        
        # Pass events to buttons
        for button in self.buttons:
            if button.handle_event(event):
                return True
        
        # Check if clicking outside the panel should close it
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if not self.contains_point(mouse_pos[0], mouse_pos[1]):
                # Clicked outside the panel, but don't close automatically
                # User should use Resume button or ESC key
                pass
        
        return True  # Consume all events when visible
    
    def render(self, screen):
        """Render the pause menu"""
        if not self.visible:
            return
        
        # Draw semi-transparent overlay over the entire screen
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        screen.blit(overlay, (0, 0))
        
        # Draw the panel background
        super().render(screen)
        
        # Draw title
        title_text = "PAUSED"
        title_surface = self.title_font.render(title_text, True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(self.x + self.width // 2, self.y + 40))
        screen.blit(title_surface, title_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.render(screen)
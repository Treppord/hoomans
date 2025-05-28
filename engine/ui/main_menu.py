"""Main Menu for the game"""
import pygame
from engine.ui.constants.colors import DARK_PANEL_BG, TEXT_COLOR, TITLE_COLOR
from engine.ui.world_select_panel import WorldSelectPanel
from engine.ui.elements.base import UIElement
from engine.ui.elements.button import Button

class MainMenu(UIElement):
    # Add to __init__ method
    def __init__(self, screen_width, screen_height, start_game_callback=None, quit_callback=None):
        """Initialize the main menu
        
        Args:
            screen_width: Width of the screen
            screen_height: Height of the screen
            start_game_callback: Function to call when Start Game is clicked
            quit_callback: Function to call when Quit is clicked
        """
        # Create a full-screen panel
        super().__init__(0, 0, screen_width, screen_height, background_color=(20, 20, 30, 255))
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.start_game_callback = start_game_callback
        self.quit_callback = quit_callback
        self.buttons = []
        self.title_font = None
        self.subtitle_font = None
        self.logo = None
        
        # Add current state tracking
        self.current_state = "main"  # "main" or "world_select"
        
        # Add world select panel
        self.world_select_panel = WorldSelectPanel(
            screen_width, 
            screen_height,
            on_select_callback=self._on_world_selected,
            on_back_callback=self._return_to_main
        )
        
        # Initialize fonts and UI elements
        self._initialize_fonts()
        self._load_logo()
        self._create_buttons()
    
    # Add new methods for world selection
    def _show_world_select(self):
        """Show the world selection panel"""
        print("Showing world selection panel")
        self.current_state = "world_select"
        # Refresh the world list
        self.world_select_panel._load_world_list()
    
    def _return_to_main(self):
        """Return to the main menu from world selection"""
        print("Returning to main menu")
        self.current_state = "main"
    
    def _on_world_selected(self, seed):
        """Handle world selection"""
        print(f"Selected world with seed: {seed}")
        if self.start_game_callback:
            self.start_game_callback(seed)
    
    # Modify _create_buttons method
    def _create_buttons(self):
        """Create menu buttons"""
        button_width = 300
        button_height = 60
        button_spacing = 20
        
        # Calculate vertical position for buttons (centered)
        total_buttons_height = 4 * button_height + 3 * button_spacing  # Now 4 buttons
        start_y = (self.screen_height - total_buttons_height) // 2 + 50  # Offset a bit from center
        
        # Create Start New Game button
        start_button = Button(
            x=(self.screen_width - button_width) // 2,
            y=start_y,
            width=button_width,
            height=button_height,
            text="Start New Game",
            callback=self._start_new_game
        )
        self.buttons.append(start_button)
        
        # Create Load World button
        load_button = Button(
            x=(self.screen_width - button_width) // 2,
            y=start_y + button_height + button_spacing,
            width=button_width,
            height=button_height,
            text="Load World",
            callback=self._show_world_select
        )
        self.buttons.append(load_button)
        
        # Create Options button
        options_button = Button(
            x=(self.screen_width - button_width) // 2,
            y=start_y + 2 * (button_height + button_spacing),
            width=button_width,
            height=button_height,
            text="Options",
            callback=self._show_options
        )
        self.buttons.append(options_button)
        
        # Create Quit button
        quit_button = Button(
            x=(self.screen_width - button_width) // 2,
            y=start_y + 3 * (button_height + button_spacing),
            width=button_width,
            height=button_height,
            text="Quit",
            callback=self.quit_callback
        )
        self.buttons.append(quit_button)
    
    # Update update_screen_size method
    def update_screen_size(self, screen_width, screen_height):
        """Update menu when screen size changes"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = screen_width
        self.height = screen_height
        
        # Recreate buttons with new positions
        self.buttons = []
        self._create_buttons()
        
        # Update world select panel
        self.world_select_panel.update_screen_size(screen_width, screen_height)
    
    # Update handle_event method
    def handle_event(self, event):
        """Handle menu events"""
        # If in world select mode, pass events to world select panel
        if self.current_state == "world_select":
            return self.world_select_panel.handle_event(event)
        
        # Otherwise, pass events to buttons
        for button in self.buttons:
            if button.handle_event(event):
                return True
        return False
    
    # Update render method
    def render(self, screen):
        """Render the main menu"""
        # If in world select mode, render world select panel
        if self.current_state == "world_select":
            self.world_select_panel.render(screen)
            return
        
        # Otherwise, render main menu
        # Draw background
        screen.fill((20, 20, 30))  # Dark blue background
        
        # Draw title
        if self.logo:
            # Draw logo
            logo_rect = self.logo.get_rect(center=(self.screen_width // 2, self.screen_height // 4))
            screen.blit(self.logo, logo_rect)
        else:
            # Draw title text
            title_text = "HOOMANS"
            title_surface = self.title_font.render(title_text, True, TITLE_COLOR)
            title_rect = title_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 4))
            screen.blit(title_surface, title_rect)
        
        # Draw subtitle
        subtitle_text = "A Survival Simulation"
        subtitle_surface = self.subtitle_font.render(subtitle_text, True, TEXT_COLOR)
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 4 + 80))
        screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw version
        version_text = "v0.1 Alpha"
        version_surface = pygame.font.SysFont(None, 20).render(version_text, True, (150, 150, 150))
        screen.blit(version_surface, (self.screen_width - 100, self.screen_height - 30))
        
        # Draw buttons
        for button in self.buttons:
            button.render(screen)

    def _initialize_fonts(self):
        """Initialize fonts for the menu"""
        try:
            self.title_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 72)
            self.subtitle_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 32)
        except:
            # Fallback to default fonts
            self.title_font = pygame.font.SysFont(None, 72)
            self.subtitle_font = pygame.font.SysFont(None, 32)
    
    def _load_logo(self):
        """Load the game logo"""
        try:
            self.logo = pygame.image.load("assets/logo.png")
            # Scale logo to reasonable size if needed
            max_logo_width = self.screen_width * 0.5
            if self.logo.get_width() > max_logo_width:
                scale_factor = max_logo_width / self.logo.get_width()
                new_size = (int(self.logo.get_width() * scale_factor), 
                           int(self.logo.get_height() * scale_factor))
                self.logo = pygame.transform.scale(self.logo, new_size)
        except:
            # No logo available, we'll use text instead
            self.logo = None
    
    def _show_options(self):
        """Show options menu (placeholder)"""
        print("Options menu not implemented yet")
        
    def _start_game_callback(self, seed=None):
        """Handle start game button click"""
        try:
            if seed is None:
                # Generate a new random seed for a new game
                import random
                seed = random.randint(1, 100000)
                print(f"Generated new random seed: {seed}")
                
                # Create an empty cache file for this new seed
                from engine.core import SimpleGameEngine
                if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'world_cache'):
                    SimpleGameEngine.instance.world_cache.create_empty_cache(seed)
                    print(f"Created empty cache for new world seed: {seed}")
            
            # Call the callback with the seed and indicate if it's a new world
            if self.start_game_callback:
                self.start_game_callback(seed, is_new_world=(seed is None or not self._cache_exists_for_seed(seed)))
        except Exception as e:
            import traceback
            print(f"Error starting game: {e}")
            traceback.print_exc()
    
    def _cache_exists_for_seed(self, seed):
        """Check if a cache file exists for the given seed"""
        import os
        from engine.core import SimpleGameEngine
        
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'world_cache'):
            cache_dir = SimpleGameEngine.instance.world_cache.cache_dir
            cache_file = os.path.join(cache_dir, f"world_{seed}.json")
            return os.path.exists(cache_file)
        return False

    def _start_new_game(self):
        """Start a completely new game with a fresh seed"""
        try:
            # Generate a new random seed
            import random
            seed = random.randint(1, 100000)
            print(f"Starting new game with fresh seed: {seed}")
            
            # Call the callback indicating this is a new world
            if self.start_game_callback:
                self.start_game_callback(seed, is_new_world=True)
        except Exception as e:
            import traceback
            print(f"Error starting new game: {e}")
            traceback.print_exc()
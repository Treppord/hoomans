"""Main Menu for the game"""
import pygame
import time
from engine.ui.constants.colors import DARK_PANEL_BG, TEXT_COLOR, TITLE_COLOR
from engine.ui.world_select_panel import WorldSelectPanel
from engine.ui.elements.base import UIElement
from engine.ui.elements.button import Button
from sound.sound_manager import get_sound_manager

class MainMenu(UIElement):
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
        self.sound_manager = get_sound_manager()
        self.buttons = []
        self.title_font = None
        self.subtitle_font = None
        self.logo = None
        
        # Add current state tracking
        self.current_state = "main"  # "main" or "load_world"
        
        # NEW: Combined world loading support
        self.available_worlds = []  # Saved worlds from cache
        self.available_maps = []    # Custom maps
        self.worlds_last_scanned = 0
        self.maps_last_scanned = 0
        self.scan_interval = 5.0
        self.world_list_scroll = 0
        self.world_buttons = []
        
        # Initialize fonts and UI elements
        self._initialize_fonts()
        self._load_logo()
        self._create_buttons()
    
    def _create_buttons(self):
        """Create menu buttons"""
        button_width = 300
        button_height = 60
        button_spacing = 20
        
        # Calculate vertical position for buttons (centered) - Now 4 buttons
        total_buttons_height = 4 * button_height + 3 * button_spacing
        start_y = (self.screen_height - total_buttons_height) // 2 + 50
        
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
        
        # Create Load World button (combines saved worlds and custom maps)
        load_button = Button(
            x=(self.screen_width - button_width) // 2,
            y=start_y + button_height + button_spacing,
            width=button_width,
            height=button_height,
            text="Load World",
            callback=self._show_load_world
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
    
    def _show_load_world(self):
        """Show the combined world loading panel"""
        print("Showing load world panel")
        self.current_state = "load_world"
        self._scan_available_worlds()
        self._scan_available_maps()
        self._create_world_buttons()
    
    def _scan_available_worlds(self):
        """Scan for available saved worlds"""
        current_time = time.time()
        if current_time - self.worlds_last_scanned < self.scan_interval:
            return
        
        try:
            from engine.core.simple_game_engine import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and SimpleGameEngine.instance:
                engine = SimpleGameEngine.instance
                if hasattr(engine, 'world_cache'):
                    # Get saved worlds from cache directory
                    import os
                    cache_dir = engine.world_cache.cache_dir
                    self.available_worlds = []
                    
                    if os.path.exists(cache_dir):
                        for filename in os.listdir(cache_dir):
                            if filename.startswith('world_') and filename.endswith('.json'):
                                cache_path = os.path.join(cache_dir, filename)
                                world_info = self._get_world_info(cache_path)
                                if world_info:
                                    self.available_worlds.append(world_info)
                    
                    # Sort by last played (most recent first)
                    self.available_worlds.sort(key=lambda x: x.get('last_played', 0), reverse=True)
                    self.worlds_last_scanned = current_time
                    print(f"Found {len(self.available_worlds)} saved worlds")
        except Exception as e:
            print(f"Error scanning saved worlds: {e}")
            self.available_worlds = []
    
    def _scan_available_maps(self):
        """Scan for available custom maps"""
        current_time = time.time()
        if current_time - self.maps_last_scanned < self.scan_interval:
            return
        
        try:
            from engine.core.simple_game_engine import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and SimpleGameEngine.instance:
                engine = SimpleGameEngine.instance
                if hasattr(engine, 'world_cache'):
                    self.available_maps = engine.world_cache.get_available_maps()
                    self.maps_last_scanned = current_time
                    print(f"Found {len(self.available_maps)} custom maps")
        except Exception as e:
            print(f"Error scanning custom maps: {e}")
            self.available_maps = []
    
    def _get_world_info(self, cache_path):
        """Get information about a saved world"""
        try:
            import json
            import os
            
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            seed = cache_data.get('seed', 'Unknown')
            last_updated = cache_data.get('last_updated', 0)
            entity_count = len(cache_data.get('entity_positions', {}))
            memory_count = sum(len(memories) for memories in cache_data.get('entity_memories', {}).values())
            
            # Check if it's a custom map world
            is_custom = cache_data.get('is_custom_map', False)
            custom_map_path = cache_data.get('custom_map_path', '')
            
            file_size = os.path.getsize(cache_path)
            
            return {
                'type': 'saved_world',
                'seed': seed,
                'filename': os.path.basename(cache_path),
                'full_path': cache_path,
                'last_played': last_updated,
                'last_played_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_updated)),
                'entity_count': entity_count,
                'memory_count': memory_count,
                'file_size_kb': file_size / 1024,
                'is_custom_map': is_custom,
                'custom_map_name': os.path.basename(custom_map_path) if custom_map_path else None
            }
        except Exception as e:
            print(f"Error reading world info from {cache_path}: {e}")
            return None
    
    def _create_world_buttons(self):
        """Create buttons for both saved worlds and custom maps"""
        self.world_buttons = []
        
        button_width = 700
        button_height = 80
        button_spacing = 10
        start_y = 150
        current_y = start_y
        
        # Add section header for saved worlds
        if self.available_worlds:
            current_y += 30  # Space for header
            
            for i, world_info in enumerate(self.available_worlds):
                y_pos = current_y + i * (button_height + button_spacing) - self.world_list_scroll
                
                if y_pos > -button_height and y_pos < self.screen_height:
                    world_button = Button(
                        self.screen_width // 2 - button_width // 2,
                        y_pos,
                        button_width, button_height,
                        "",  # Custom rendering
                        lambda w=world_info: self._load_saved_world(w)
                    )
                    world_button.world_info = world_info
                    world_button.item_type = 'saved_world'
                    self.world_buttons.append(world_button)
            
            current_y += len(self.available_worlds) * (button_height + button_spacing) + 40
        
        # Add section header for custom maps
        if self.available_maps:
            current_y += 30  # Space for header
            
            for i, map_info in enumerate(self.available_maps):
                y_pos = current_y + i * (button_height + button_spacing) - self.world_list_scroll
                
                if y_pos > -button_height and y_pos < self.screen_height:
                    map_button = Button(
                        self.screen_width // 2 - button_width // 2,
                        y_pos,
                        button_width, button_height,
                        "",  # Custom rendering
                        lambda m=map_info: self._load_custom_map(m)
                    )
                    map_button.world_info = map_info
                    map_button.item_type = 'custom_map'
                    self.world_buttons.append(map_button)
    
    def _load_saved_world(self, world_info):
        """Load a saved world"""
        print(f"Loading saved world: {world_info['seed']}")
        
        try:
            if self.start_game_callback:
                # If it's a custom map world, handle it specially
                if world_info.get('is_custom_map', False):
                    # Load the custom map first
                    from engine.core.simple_game_engine import SimpleGameEngine
                    if hasattr(SimpleGameEngine, 'instance') and SimpleGameEngine.instance:
                        engine = SimpleGameEngine.instance
                        if hasattr(engine, 'world_cache'):
                            # Set the world seed to load the cache
                            engine.world_cache.set_world_seed(world_info['seed'])
                            # The custom map path should be restored from cache
                            self.start_game_callback(seed=world_info['seed'], is_new_world=False, use_custom_map=True)
                else:
                    # Regular procedural world
                    self.start_game_callback(seed=world_info['seed'], is_new_world=False, use_custom_map=False)
        except Exception as e:
            print(f"Error loading saved world: {e}")
    
    def _load_custom_map(self, map_info):
        """Load a custom map"""
        print(f"Loading custom map: {map_info['filename']}")
        
        try:
            from engine.core.simple_game_engine import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and SimpleGameEngine.instance:
                engine = SimpleGameEngine.instance
                if hasattr(engine, 'world_cache'):
                    # Set the custom map in world cache
                    success = engine.world_cache.set_custom_map(map_info['full_path'])
                    if success and self.start_game_callback:
                        # Start the game with custom map
                        self.start_game_callback(seed=None, is_new_world=True, use_custom_map=True)
                    else:
                        print(f"Failed to set custom map: {map_info['filename']}")
        except Exception as e:
            print(f"Error loading custom map: {e}")
    
    def _refresh_worlds(self):
        """Force refresh of available worlds and maps"""
        self.worlds_last_scanned = 0
        self.maps_last_scanned = 0
        self._scan_available_worlds()
        self._scan_available_maps()
        self._create_world_buttons()
    
    def _return_to_main(self):
        """Return to the main menu"""
        print("Returning to main menu")
        self.current_state = "main"
    
    def update_screen_size(self, screen_width, screen_height):
        """Update menu when screen size changes"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = screen_width
        self.height = screen_height
        
        # Recreate buttons with new positions
        self.buttons = []
        self._create_buttons()
        
        # Recreate world buttons if in that state
        if self.current_state == "load_world":
            self._create_world_buttons()
    
    def handle_event(self, event):
        """Handle menu events"""
        # Handle scrolling in load world menu
        if self.current_state == "load_world" and event.type == pygame.MOUSEWHEEL:
            self.world_list_scroll = max(0, self.world_list_scroll - event.y * 30)
            self._create_world_buttons()  # Recreate buttons for new scroll position
            return True
        
        # If in load world mode, handle world loading events
        if self.current_state == "load_world":
            # Handle world buttons
            for button in self.world_buttons:
                if button.handle_event(event):
                    return True
            
            # Handle back button (ESC key)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._return_to_main()
                return True
            
            # Handle temp buttons (back and refresh) - UPDATE: Check if they exist first
            if hasattr(self, '_temp_back_button'):
                if self._temp_back_button.handle_event(event):
                    return True
            if hasattr(self, '_temp_refresh_button'):
                if self._temp_refresh_button.handle_event(event):
                    return True
            
            return False
        
        # Otherwise, pass events to main menu buttons
        for button in self.buttons:
            if button.handle_event(event):
                return True
        return False


    def render(self, screen):
        """Render the main menu"""
        # If in load world mode, render load world panel
        if self.current_state == "load_world":
            self._render_load_world(screen)
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
    
    def _render_load_world(self, screen):
        """Render the load world screen with both saved worlds and custom maps"""
        # Clear background
        screen.fill((20, 20, 30))
        
        # Draw title
        title_text = "Load World"
        title_surface = self.title_font.render(title_text, True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 80))
        screen.blit(title_surface, title_rect)
        
        # Draw back button
        back_button = Button(50, 50, 100, 40, "Back", self._return_to_main)
        back_button.render(screen)
        self._temp_back_button = back_button
        
        # Draw refresh button
        refresh_button = Button(self.screen_width - 150, 50, 100, 40, "Refresh", self._refresh_worlds)
        refresh_button.render(screen)
        self._temp_refresh_button = refresh_button
        
        # Draw section headers and content
        current_y = 150
        
        # Saved Worlds Section
        if self.available_worlds:
            header_font = pygame.font.Font(None, 28)
            header_text = header_font.render("Saved Worlds", True, (200, 200, 200))
            header_y = current_y - self.world_list_scroll
            if header_y > 120 and header_y < self.screen_height:
                screen.blit(header_text, (self.screen_width // 2 - 350, header_y))
        
        # Custom Maps Section
        if self.available_maps:
            saved_worlds_height = len(self.available_worlds) * 90 + 70  # Height of saved worlds section
            header_y = current_y + saved_worlds_height - self.world_list_scroll
            if header_y > 120 and header_y < self.screen_height:
                header_font = pygame.font.Font(None, 28)
                header_text = header_font.render("Custom Maps", True, (200, 200, 200))
                screen.blit(header_text, (self.screen_width // 2 - 350, header_y))
        
        # Render world/map buttons
        for button in self.world_buttons:
            if hasattr(button, 'world_info') and hasattr(button, 'item_type'):
                if button.item_type == 'saved_world':
                    self._render_saved_world_button(screen, button)
                elif button.item_type == 'custom_map':
                    self._render_custom_map_button(screen, button)
            else:
                button.render(screen)
        
        # Show "no worlds" message if needed
        if not self.available_worlds and not self.available_maps:
            no_worlds_text = pygame.font.Font(None, 24).render(
                "No saved worlds or custom maps found.",
                True, (150, 150, 150)
            )
            no_worlds_rect = no_worlds_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            screen.blit(no_worlds_text, no_worlds_rect)
            
            instruction_text = pygame.font.Font(None, 20).render(
                "Start a new game or create custom maps using the Map Creator tool.",
                True, (100, 100, 100)
            )
            instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 30))
            screen.blit(instruction_text, instruction_rect)
        
        # Show scroll hint if there are many items
        if len(self.available_worlds) + len(self.available_maps) > 6:
            scroll_hint = pygame.font.Font(None, 18).render(
                "Use mouse wheel to scroll",
                True, (100, 100, 100)
            )
            screen.blit(scroll_hint, (self.screen_width - 200, self.screen_height - 30))
    
    def _render_saved_world_button(self, screen, button):
        """Render a saved world button"""
        world_info = button.world_info
        
        # Draw button background with different color for saved worlds
        color = (70, 90, 70) if button.is_hovered else (50, 70, 50)  # Green tint
        pygame.draw.rect(screen, color, button.rect, border_radius=5)
        pygame.draw.rect(screen, (100, 150, 100), button.rect, 2, border_radius=5)
        
        # Draw world information
        y_offset = button.rect.top + 10
        
        # World name/seed
        name_font = pygame.font.Font(None, 32)
        if world_info.get('is_custom_map', False):
            world_name = f"Custom Map: {world_info.get('custom_map_name', 'Unknown')}"
        else:
            world_name = f"World (Seed: {world_info['seed']})"
        
        name_text = name_font.render(world_name, True, (255, 255, 255))
        screen.blit(name_text, (button.rect.left + 15, y_offset))
        
        # World details
        details = f"Entities: {world_info['entity_count']} • Memories: {world_info['memory_count']} • {world_info['file_size_kb']:.1f} KB"
        
        details_font = pygame.font.Font(None, 20)
        details_text = details_font.render(details, True, (200, 200, 200))
        screen.blit(details_text, (button.rect.left + 15, y_offset + 30))
        
        # Last played date
        date_text = details_font.render(f"Last played: {world_info['last_played_str']}", True, (150, 150, 150))
        screen.blit(date_text, (button.rect.left + 15, y_offset + 50))
        
        # Type indicator
        type_text = details_font.render("SAVED WORLD", True, (100, 200, 100))
        screen.blit(type_text, (button.rect.right - type_text.get_width() - 15, y_offset + 10))
    
    def _render_custom_map_button(self, screen, button):
        """Render a custom map button"""
        map_info = button.world_info
        
        # Draw button background with different color for custom maps
        color = (70, 70, 90) if button.is_hovered else (50, 50, 70)  # Blue tint
        pygame.draw.rect(screen, color, button.rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 150), button.rect, 2, border_radius=5)
        
        # Draw map information
        y_offset = button.rect.top + 10
        
        # Map name
        name_font = pygame.font.Font(None, 32)
        name_text = name_font.render(map_info['filename'], True, (255, 255, 255))
        screen.blit(name_text, (button.rect.left + 15, y_offset))
        
        # Map details
        details = f"{map_info['width']}x{map_info['height']} • {map_info['file_size_kb']:.1f} KB"
        if map_info['compressed']:
            details += " • Compressed"
        
        details_font = pygame.font.Font(None, 20)
        details_text = details_font.render(details, True, (200, 200, 200))
        screen.blit(details_text, (button.rect.left + 15, y_offset + 30))
        
        # Modification date
        date_text = details_font.render(f"Modified: {map_info['modified_str']}", True, (150, 150, 150))
        screen.blit(date_text, (button.rect.left + 15, y_offset + 50))
        
        # Entity and item counts
        counts_text = f"Entities: {map_info['entity_count']} • Items: {map_info['item_count']}"
        counts_surface = details_font.render(counts_text, True, (150, 150, 150))
        screen.blit(counts_surface, (button.rect.right - counts_surface.get_width() - 15, y_offset + 30))
        
        # Type indicator
        type_text = details_font.render("CUSTOM MAP", True, (100, 100, 200))
        screen.blit(type_text, (button.rect.right - type_text.get_width() - 15, y_offset + 10))

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
                from engine.core.simple_game_engine import SimpleGameEngine
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
        from engine.core.simple_game_engine import SimpleGameEngine
        
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

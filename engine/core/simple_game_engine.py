"""
Refactored Simple Game Engine Core
Main engine class that coordinates all subsystems
"""
import pygame
import sys
import os
import random

# Core engine components
from engine.core.display_manager import DisplayManager
from engine.core.game_state_manager import GameStateManager
from engine.core.input_manager import InputManager
from engine.core.event_handler import EventHandler
from engine.core.game_loop import GameLoop
from engine.core.game_data_manager import GameDataManager
from engine.core.chat_manager import ChatManager
from engine.core.ui_setup import UISetup
from engine.core.world_cache_manager import WorldCacheManager

# Engine subsystems
from engine.camera import Camera
from engine.physics import PhysicsEngine
from engine.ai import AIManager
from engine.data_manager import DataManager
from engine.ui.ui_manager import UIManager
from engine.ui.theme_manager import ThemeManager
from engine.ui.pause_menu import PauseMenu
from engine.ui.main_menu import MainMenu

# Configuration
from engine.config.config_loader import get_config_loader

# Sound system
from sound.sound_manager import get_sound_manager


class SimpleGameEngine:
    """
    Main game engine class that coordinates all subsystems.
    Refactored to be modular and configurable.
    """
    
    # Class variable to store instance reference
    instance = None
    
    def __init__(self, title=None, width=None, height=None, fps=None, map_seed=None):
        """Initialize the game engine with optional parameters"""
        # Store instance reference
        SimpleGameEngine.instance = self
        
        # Load configuration
        self.config = get_config_loader()
        
        # Initialize display manager
        self.display_manager = DisplayManager(title, width, height)
        
        # Initialize game state manager
        self.state_manager = GameStateManager()
        
        # Set up clock for controlling frame rate
        display_config = self.config.get_setting('game_settings', 'display', default={})
        self.fps = fps or display_config.get('default_fps', 60)
        self.clock = pygame.time.Clock()
        
        # Initialize sound manager
        self.sound_manager = get_sound_manager()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Initialize camera
        camera_config = self.config.get_setting('game_settings', 'camera', default={})
        self.camera = Camera(self.display_manager.width, self.display_manager.height)
        self.show_grid = camera_config.get('show_grid_default', False)
        
        # Initialize core managers
        self.input_manager = InputManager()
        self.event_handler = EventHandler(self)
        self.game_loop = GameLoop(self)
        
        # Initialize subsystems
        self.physics = PhysicsEngine()
        self.ai_manager = AIManager()
        self.data = DataManager()
        
        # Initialize UI system
        self.ui = UIManager(self.display_manager.width, self.display_manager.height)
        
        # Initialize specialized managers
        self.game_data_manager = GameDataManager(self.data)
        self.chat_manager = ChatManager(self)
        self.ui_setup = UISetup(self)
        self.world_cache_manager = WorldCacheManager(self)
        
        # Entity management (will be set by game_engine.py)
        self.entity_manager = None
        
        # Game state
        self.running = False
        self.map_seed = map_seed
        
        # Game objects storage (maintained for backward compatibility)
        self.objects = []
        self.world_map = None
        self.player = None
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all game components"""
        # Load item icons after pygame is initialized
        self.load_item_icons()
        
        # Set up initial game data
        self.game_data_manager.setup_initial_game_data()
        
        # Set up UI elements
        self.ui_setup.setup_ui_elements()
        
        # Create pause menu
        self._create_pause_menu()
        
        # Create main menu
        self._create_main_menu()
        
        # Initialize world cache if seed is provided
        if self.map_seed is not None:
            self.world_cache_manager.setup_world_cache()
        
        # Set up last update time for game loop
        self.game_loop.last_update_time = 0
    
    def _create_pause_menu(self):
        """Create the pause menu"""
        self.pause_menu = PauseMenu(
            self.display_manager.width,
            self.display_manager.height,
            resume_callback=self._resume_game,
            return_to_menu_callback=self._return_to_main_menu,
            quit_callback=self._quit_game
        )
        self.ui.set_pause_menu(self.pause_menu)
    
    def _create_main_menu(self):
        """Create the main menu"""
        self.main_menu = MainMenu(
            self.display_manager.width,
            self.display_manager.height,
            start_game_callback=self._start_game_from_menu,
            quit_callback=self._quit_game
        )
        print(f"DEBUG: Main menu initialized with dimensions {self.display_manager.width}x{self.display_manager.height}")
    
    def load_item_icons(self):
        """Load all item icons after pygame is initialized"""
        try:
            from entities.items.item_factory import ItemFactory
            
            # Ensure item assets exist
            ItemFactory.ensure_item_assets_exist()
            
            # Make sure templates are registered
            if not hasattr(ItemFactory, '_templates') or not ItemFactory._templates:
                ItemFactory.register_item_templates()
            
            # Load icons for all registered item templates
            for item_id, template in ItemFactory._templates.items():
                template.ensure_icon_loaded()
                print(f"Loaded icon for item: {item_id}")
                
            # If item manager exists, ensure all its items have icons loaded
            if hasattr(self, 'item_manager') and self.item_manager:
                for item_def in self.item_manager.get_all_items():
                    if item_def.item_id in ItemFactory._templates:
                        ItemFactory._templates[item_def.item_id].ensure_icon_loaded()
        except ImportError:
            print("Warning: ItemFactory not available, skipping item icon loading")
    
    def set_world_map(self, world_map):
        """Set the world map for the game"""
        self.world_map = world_map
        self.physics.set_world_map(world_map)
        
        # Connect world cache to world map
        if hasattr(self, 'world_cache'):
            world_map.set_world_cache(self.world_cache)
    
    def add_object(self, obj):
        """
        Add a game object to the world (backward compatibility method)
        
        This method is maintained for backward compatibility.
        New code should use entity_manager.add_entity() instead.
        """
        self.objects.append(obj)
        
        # If this is a player-controlled object, store a reference
        if hasattr(obj, 'controllable') and obj.controllable:
            print(f"DEBUG: Player object added with ID {obj.get_entity_id()}")
            self.player = obj
            self.camera.set_follow_target(obj)
            
            # Debug inventory
            if hasattr(obj, 'inventory'):
                print(f"DEBUG: Player has inventory with {len(obj.inventory.slots)} slots")
            else:
                print("DEBUG: Player does not have inventory attribute")
        
        return obj
    
    def spawn_food_npc(self, x=None, y=None, food_type=None):
        """
        Spawn a food NPC (backward compatibility method)
        
        This method is maintained for backward compatibility.
        New code should use entity_manager.spawn_food_npc() instead.
        """
        if self.entity_manager:
            return self.entity_manager.spawn_food_npc(x, y, food_type)
        else:
            # Fallback to original implementation
            try:
                from entities.food_npc import FoodNPC
                from engine.ai import FoodWanderAI
                
                # If no position specified, find a random valid position
                if x is None or y is None:
                    valid_positions = []
                    
                    # Find valid spawn positions (grass or dirt, not water or walls)
                    for y_pos in range(self.world_map.height):
                        for x_pos in range(self.world_map.width):
                            tile = self.world_map.get_tile(x_pos, y_pos)
                            if tile and hasattr(tile, 'is_walkable') and tile.is_walkable():
                                # Don't spawn on water
                                if not (hasattr(tile, 'is_water') and tile.is_water()):
                                    valid_positions.append((x_pos, y_pos))
                    
                    # Choose a random valid position
                    if valid_positions:
                        x, y = random.choice(valid_positions)
                    else:
                        # Fallback to a default position if no valid positions found
                        x, y = 10, 10
                
                # Create the food NPC
                food_ai = FoodWanderAI()
                food_npc = FoodNPC(grid_x=x, grid_y=y, ai_controller=food_ai)
                
                # Set specific food type if provided
                if food_type:
                    food_npc.food_type = food_type
                    food_npc.set_color_by_food_type()
                
                # Add the food NPC to the game objects
                self.add_object(food_npc)
                
                return food_npc
            except ImportError:
                print("Warning: FoodNPC not available")
                return None
    
    def add_ai_controller(self, controller):
        """Add an AI controller to the game"""
        return self.ai_manager.add_controller(controller)
    
    def _resume_game(self):
        """Resume the game from pause menu"""
        self.state_manager.set_state(self.state_manager.game_state_constants.RUNNING)
        print("Game resumed")
    
    def _pause_game(self):
        """Pause the game"""
        self.state_manager.set_state(self.state_manager.game_state_constants.PAUSED)
        if hasattr(self, 'pause_menu'):
            self.pause_menu.show()
        print("Game paused")
    
    def _return_to_main_menu(self):
        """Return to main menu from pause menu"""
        # Save all entity states before returning to menu
        self.world_cache_manager.save_all_entity_states()
        
        self.state_manager.set_state(self.state_manager.game_state_constants.MAIN_MENU)
        self.sound_manager.play_music("track_main", loops=-1, fade_in=1000)
        print("Returned to main menu")
    
    def _quit_game(self):
        """Quit the game"""
        # Save all entity states before quitting
        self.world_cache_manager.save_all_entity_states()
        
        self.sound_manager.cleanup()
        print("Quitting game")
        self.running = False
    
    def _start_game_from_menu(self, seed=None, is_new_world=False, use_custom_map=False):
        """Start the game from the main menu with custom map support"""
        try:
            print(f"Starting game from menu - seed: {seed}, new world: {is_new_world}, custom map: {use_custom_map}")
            self.state_manager.set_state(self.state_manager.game_state_constants.RUNNING)
            
            # Switch to game music
            self.sound_manager.play_music("track_game", loops=-1, fade_in=1000)
            
            # Handle custom map loading
            if use_custom_map and hasattr(self, 'world_cache'):
                custom_map_path = self.world_cache.get_custom_map_path()
                if custom_map_path:
                    print(f"Loading custom map: {custom_map_path}")
                    
                    # Load the custom map
                    custom_world_map = self.world_cache.load_custom_map_world()
                    if custom_world_map:
                        # Set the custom map as the world map
                        self.set_world_map(custom_world_map)
                        
                        # Load cached entities for this custom map
                        self.world_cache_manager.load_cached_entities()
                        
                        print("Custom map loaded successfully")
                        return
                    else:
                        print("Failed to load custom map, falling back to procedural generation")
                        use_custom_map = False
            
            # Handle procedural world generation
            if not use_custom_map:
                # Set map seed if provided
                if seed is not None:
                    self.map_seed = seed
                    print(f"Using provided seed: {seed}")
            
            # Load item icons after pygame is initialized
            self.load_item_icons()
            
            # Handle world cache setup
            if hasattr(self, 'world_cache'):
                if is_new_world:
                    print(f"Creating fresh world cache for new seed: {self.map_seed}")
                    self.world_cache.create_fresh_world(self.map_seed)
                else:
                    print(f"Loading existing world cache for seed: {self.map_seed}")
                    self.world_cache.set_world_seed(self.map_seed)
            
            # If we have a world map already, regenerate it with the new seed
            if hasattr(self, 'world_map') and self.world_map:
                print(f"Regenerating world map with seed: {self.map_seed}")
                self.world_map.generate_realistic_map(seed=self.map_seed)
                
                # Only load cached entities if this is NOT a new world
                if not is_new_world:
                    self.world_cache_manager.load_cached_entities()
                else:
                    print("Skipping cached entity loading for new world")
                
        except Exception as e:
            import traceback
            print(f"Error starting game from menu: {e}")
            traceback.print_exc()
            
            # Try to recover
            self.state_manager.set_state(self.state_manager.game_state_constants.RUNNING)
            if hasattr(self, 'world_map') and self.world_map:
                # Generate a fallback map
                self.world_map._generate_fallback_map()
    
    def handle_events(self):
        """Process all input events - delegated to event handler"""
        self.event_handler.handle_events()
    
    def update(self):
        """Update game logic - delegated to game loop"""
        self.game_loop.update()
            
    def render(self):
        """Render all game objects - SINGLE SOURCE OF TRUTH FOR RENDER ORDER"""
        # Clear the screen
        self.display_manager.clear()
        
        # If in main menu, render it and return
        if self.state_manager.is_state(self.state_manager.game_state_constants.MAIN_MENU):
            if hasattr(self, 'main_menu'):
                self.main_menu.render(self.display_manager.get_screen())
            else:
                print("ERROR: Main menu not initialized")
            self.display_manager.flip()
            return
        
        # ===== RENDER ORDER - DO NOT CHANGE THIS ORDER! =====
        
        # 1. Background
        self.theme_manager.render_background(self.display_manager.get_screen(), self.camera)
        
        # 2. World map (terrain tiles + world items only, NO entity tiles)
        if self.world_map:
            self.world_map.render(self.display_manager.get_screen(), self.camera)
        
        # 3. Entity tiles (buildings, trees, etc.) - RENDERED ONCE HERE ONLY
        if self.world_map and hasattr(self.world_map, 'entity_tile_manager'):
            self.world_map.entity_tile_manager.render(self.display_manager.get_screen(), self.camera)
        
        # 4. Entities (players, NPCs, etc.)
        if self.entity_manager:
            entities = self.entity_manager.get_all_entities()
        else:
            entities = self.objects
            
        for obj in entities:
            if hasattr(obj, 'render'):
                obj.render(self.display_manager.get_screen(), self.camera)
        
        # 5. Foreground effects
        self.theme_manager.render_foreground(self.display_manager.get_screen(), self.camera)
        
        # 6. UI elements (stats panel, etc.)
        self.ui.render(self.display_manager.get_screen())
        
        # 7. Interaction menu (ON TOP OF EVERYTHING EXCEPT PAUSE MENU)
        if (hasattr(self, 'player') and self.player and 
            hasattr(self.player, 'interaction_menu') and 
            self.player.interaction_menu and
            hasattr(self.player.interaction_menu, 'visible') and
            self.player.interaction_menu.visible):
            self.player.interaction_menu.render(self.display_manager.get_screen())
        
        # 8. Pause menu (ABSOLUTE TOP)
        if (self.state_manager.is_state(self.state_manager.game_state_constants.PAUSED) and 
            hasattr(self, 'pause_menu')):
            self.pause_menu.render(self.display_manager.get_screen())
        
        # Update the display
        self.display_manager.flip()


    def _get_player_interaction_menu(self):
        """Safely get the player's interaction menu if it exists"""
        try:
            if (hasattr(self, 'player') and self.player and 
                hasattr(self.player, 'interaction_menu') and 
                self.player.interaction_menu):
                return self.player.interaction_menu
        except AttributeError:
            pass
        return None

    def _is_interaction_menu_visible(self):
        """Check if the player's interaction menu is visible"""
        menu = self._get_player_interaction_menu()
        return menu and hasattr(menu, 'visible') and menu.visible
    
    def run(self):
        """Main game loop"""
        self.running = True
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.fps)
        
        # Clean up
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources before exit"""
        if hasattr(self, 'ai_universe'):
            self.ai_universe.stop()
        
        if hasattr(self, 'sound_manager'):
            self.sound_manager.cleanup()
        
        pygame.quit()
        sys.exit()
    
    # Legacy compatibility methods - these maintain the original API
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        new_size = self.display_manager.toggle_fullscreen()
        self._update_components_for_resize(*new_size)
        return new_size
    
    def toggle_borderless_fullscreen(self):
        """Toggle borderless fullscreen mode"""
        new_size = self.display_manager.toggle_borderless_fullscreen()
        self._update_components_for_resize(*new_size)
        return new_size
    
    def handle_resize(self, new_width, new_height):
        """Handle window resize event"""
        new_size = self.display_manager.handle_resize(new_width, new_height)
        if new_size:
            self._update_components_for_resize(*new_size)
        return new_size
    
    def _update_components_for_resize(self, width, height):
        """Update all components when screen size changes"""
        self.camera.update_screen_size(width, height)
        self.ui.update_screen_size(width, height)
        self.ui_setup.update_ui_positions(width, height)
        
        if hasattr(self, 'pause_menu'):
            self.pause_menu.update_screen_size(width, height)
        
        if hasattr(self, 'main_menu'):
            self.main_menu.update_screen_size(width, height)
        
        print(f"Screen mode changed: ({width}x{height})")
    
    # Properties for backward compatibility
    @property
    def width(self):
        """Get screen width"""
        return self.display_manager.width
    
    @property
    def height(self):
        """Get screen height"""
        return self.display_manager.height
    
    @property
    def screen(self):
        """Get pygame screen surface"""
        return self.display_manager.get_screen()
    
    @property
    def paused(self):
        """Check if game is paused"""
        return self.state_manager.is_state(self.state_manager.game_state_constants.PAUSED)
    
    @paused.setter
    def paused(self, value):
        """Set paused state"""
        if value:
            self._pause_game()
        else:
            self._resume_game()
    
    @property
    def game_state(self):
        """Get current game state"""
        return self.state_manager.get_state()
    
    @game_state.setter
    def game_state(self, value):
        """Set game state"""
        self.state_manager.set_state(value)
    
    # Backward compatibility for chat input
    @property
    def chat_input(self):
        """Get chat input reference"""
        return getattr(self, '_chat_input', None)
    
    @chat_input.setter
    def chat_input(self, value):
        """Set chat input reference"""
        self._chat_input = value
    
    # Backward compatibility for input handler
    @property
    def input_handler(self):
        """Get input manager (backward compatibility)"""
        return self.input_manager

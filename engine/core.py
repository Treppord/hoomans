from engine.camera import Camera
from entities.npc import NPC
from ai.controllers.ai_universe_controller import WorldStateCollector
from sound.sound_manager import get_sound_manager

import pygame
import sys
from engine.physics import PhysicsEngine
from engine.input_handler import InputHandler
from engine.ai import AIManager
from engine.data_manager import DataManager
from engine.ui.ui_manager import UIManager
from engine.ui.panels.stats_panel import StatsPanel
from engine.ui.elements.chat_input import ChatInputBox
from engine.ui.theme_manager import ThemeManager
from engine.ui.pause_menu import PauseMenu
from engine.camera import Camera
import random
import os
from engine.ui.main_menu import MainMenu

# Add these constants near the top of the file
class GameState:
    """Game state constants"""
    MAIN_MENU = 0
    RUNNING = 1
    PAUSED = 2
    GAME_OVER = 3


class SimpleGameEngine:

# Add this method to the SimpleGameEngine class
    def load_item_icons(self):
        """Load all item icons after pygame is initialized"""
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
                # Find the template in ItemFactory
                if item_def.item_id in ItemFactory._templates:
                    ItemFactory._templates[item_def.item_id].ensure_icon_loaded()

    def setup_world_cache(self):
        """Set up the world cache for persistent memory"""
        from world.world_cache import WorldCache
        self.world_cache = WorldCache()  # Use default cache_dir
        self.world_cache.set_world_seed(self.map_seed)  # Set the seed separately
        print(f"DEBUG: World cache initialized with seed {self.map_seed}")

    # Modify the __init__ method to include world_cache initialization
    def __init__(self, title="Simple Game Engine", width=800, height=600, fps=60, map_seed=None):
        # Initialize pygame
        pygame.init()
        self.sound_manager = get_sound_manager()

        # Store default dimensions
        self.default_width = width
        self.default_height = height
        
        self.last_update_time = 0
        
        self.game_state = GameState.MAIN_MENU
        
        # Set up the display
        self.width = width
        self.height = height
        self.fullscreen = False
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)
        self.theme_manager = ThemeManager()
        
        # Load and set the window icon
        try:
            # Get the path to the logo
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(project_root, "assets", "logo.png")
        
            if os.path.exists(logo_path):
                logo = pygame.image.load(logo_path)
                pygame.display.set_icon(logo)
                print(f"Set window icon from: {logo_path}")
            else:
                print(f"Logo file not found at: {logo_path}")
                # Create a simple icon if the logo doesn't exist
                self._create_default_icon()
        except Exception as e:
            print(f"Error setting window icon: {e}")
            # Create a simple icon if there was an error
            self._create_default_icon()
        
        # Store instance reference
        SimpleGameEngine.instance = self
        
        # Set up the clock for controlling frame rate
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.map_seed = map_seed
        
        # Initialize camera
        self.camera = Camera(width, height)
        self.show_grid = False  # Default to not showing grid

        
        # Game objects storage
        self.objects = []
        
        # World map
        self.world_map = None
        
        # Initialize physics engine
        self.physics = PhysicsEngine()
        
        # Initialize input handler
        self.input_handler = InputHandler()
        
        # Initialize AI manager
        self.ai_manager = AIManager()
        
        # Initialize data manager
        self.data = DataManager()
        
        # Initialize UI
        self.ui = UIManager(width, height)
        self.load_item_icons()

        # Create pause menu
        self.pause_menu = PauseMenu(
            width, 
            height,
            resume_callback=self._resume_game,
            return_to_menu_callback=self._return_to_main_menu,
            quit_callback=self._quit_game
        )
        self.ui.set_pause_menu(self.pause_menu)
        
        # Create chat input box BEFORE adding it to UI
        chat_input_width = 400
        chat_input_height = 40
        chat_input_x = self.width - chat_input_width - 10  # 10px from right edge
        chat_input_y = self.height - chat_input_height - 10  # 10px from bottom edge
        
        print("DEBUG: Creating chat input box")
        self.chat_input = ChatInputBox(
            chat_input_x, 
            chat_input_y, 
            chat_input_width, 
            chat_input_height,
            callback=self.handle_chat_message
        )
        
        print(f"DEBUG: Adding chat input to UI manager: {self.chat_input}")
        # Now add the chat input to the UI manager
        self.ui.add_element(self.chat_input)
        
        # Initialize world cache if seed is provided
        if self.map_seed is not None:
            self.setup_world_cache()
        
        # Player reference (will be set when player is added)
        self.player = None
        
        # Paused state
        self.paused = False
        
        # Set up initial game values
        self.setup_game_data()
        
        # Set up UI elements
        self.setup_ui()
        
        self.item_manager = None  # Will be set after initialization

        # Create main menu - make sure this happens AFTER pygame is initialized
        self.main_menu = MainMenu(
            width, 
            height, 
            start_game_callback=self._start_game_from_menu,
            quit_callback=self._quit_game
        )
        print(f"DEBUG: Main menu initialized with dimensions {width}x{height}")

        
        # Game state
        self.running = False

    def _resume_game(self):
        """Resume the game from pause menu"""
        self.paused = False
        self.game_state = GameState.RUNNING
        print("Game resumed")

    def _return_to_main_menu(self):
        """Return to main menu from pause menu"""
        # Save all entity states before returning to menu
        self._save_all_entity_states()
        

        
        self.paused = False
        self.game_state = GameState.MAIN_MENU
        self.sound_manager.play_music("track_main", loops=-1, fade_in=1000)
        print("Returned to main menu")

    def _quit_game(self):
        """Quit the game"""
        # Save all entity states before quitting
        self._save_all_entity_states()
        
        self.sound_manager.cleanup()

        
        print("Quitting game")
        self.running = False
    
    def _save_all_entity_states(self):
        """Save all entity positions and states to cache"""
        if hasattr(self, 'world_cache') and self.world_cache:
            print("DEBUG: Saving all entity states...")
            
            # Save all entities that support caching
            entities_saved = 0
            for obj in self.objects:
                if hasattr(obj, 'save_position_to_cache'):
                    try:
                        obj.save_position_to_cache()
                        entities_saved += 1
                    except Exception as e:
                        print(f"Warning: Could not save entity {obj.get_entity_id()}: {e}")
            
            # Save all entity tiles
            if (hasattr(self, 'world_map') and 
                hasattr(self.world_map, 'entity_tile_manager')):
                
                entity_tiles_saved = 0
                for entity_tile in self.world_map.entity_tile_manager.entity_tiles:
                    try:
                        save_data = entity_tile.get_save_data()
                        self.world_cache.save_entity_tile(
                            entity_tile.base_x, entity_tile.base_y,
                            entity_tile.tile_type, save_data
                        )
                        entity_tiles_saved += 1
                    except Exception as e:
                        print(f"Warning: Could not save entity tile at ({entity_tile.base_x}, {entity_tile.base_y}): {e}")
                
                print(f"DEBUG: Saved {entity_tiles_saved} entity tiles")
            
            # Force save the cache to disk
            try:
                self.world_cache._save_cache()
                print(f"DEBUG: Successfully saved {entities_saved} entities to cache")
            except Exception as e:
                print(f"Error saving cache: {e}")
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            # Get desktop size for fullscreen
            desktop_info = pygame.display.Info()
            new_width, new_height = desktop_info.current_w, desktop_info.current_h
            self.screen = pygame.display.set_mode((new_width, new_height), pygame.FULLSCREEN)
        else:
            # Return to windowed mode with default size
            self.screen = pygame.display.set_mode((self.default_width, self.default_height), pygame.RESIZABLE)
        
        # Update width and height
        self.width, self.height = self.screen.get_size()
        
        # Update camera and UI
        self.camera.update_screen_size(self.width, self.height)
        self.ui.update_screen_size(self.width, self.height)
        
        # Update pause menu size
        if hasattr(self, 'pause_menu'):
            self.pause_menu.update_screen_size(self.width, self.height)
        
        print(f"Screen mode changed: {'Fullscreen' if self.fullscreen else 'Windowed'} ({self.width}x{self.height})")

    
    def handle_resize(self, new_width, new_height):
        """Handle window resize event"""
        if not self.fullscreen:
            self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
            self.width, self.height = new_width, new_height
            
            # Update camera and UI
            self.camera.update_screen_size(self.width, self.height)
            self.ui.update_screen_size(self.width, self.height)
            
            # Update pause menu size
            if hasattr(self, 'pause_menu'):
                self.pause_menu.update_screen_size(self.width, self.height)
            
            print(f"Window resized to {self.width}x{self.height}")


        
    def setup_game_data(self):
        """Set up initial game values"""
        # Create player stats
        self.data.create_player_stat("health", 20, 0, 20)
        self.data.create_player_stat("hunger", 10, 0, 10)
        self.data.create_player_stat("thirst", 10, 0, 10)
        self.data.create_player_stat("score", 0, 0, None)
        
        # Create game values
        self.data.create_value("game_time", 0)
        self.data.create_value("enemies_defeated", 0)
        
        # Add some starting inventory
        self.data.add_inventory_item("health_potion", 3)
    
    def setup_ui(self):
        """Set up UI elements"""
        # Add stats panel in top right corner
        stats_panel_width = 200
        stats_panel_height = 120
        stats_panel_x = self.width - stats_panel_width - 10  # 10px from right edge
        stats_panel_y = 10  # 10px from top edge
        
        self.ui.add_element(
            StatsPanel(stats_panel_x, stats_panel_y, stats_panel_width, stats_panel_height, self.data)
        )
        
        if hasattr(self, 'chat_input') and self.chat_input:
            chat_input_width = 400
            chat_input_height = 40
            chat_input_x = self.width - chat_input_width - 10  # 10px 
            chat_input_y = self.height - chat_input_height - 10  # 10px 
            self.chat_input.x = chat_input_x
            self.chat_input.y = chat_input_y
        
    def handle_chat_message(self, message):
        """Handle a chat message from the player"""
        if self.player:
            print(f"Chat message: {message}")  # Debug output
            
            # Check for commands first
            if message.startswith("/"):
                self.process_command(message[1:])  # Remove the "/" and process command
                # When chat is closed, reset chat mode in input handler
                self.input_handler.set_chat_mode(False)
                return
            
            bubble = self.ui.add_text_bubble(message, self.player, duration=5.0)
            # Find NPCs in vicinity and have them respond
            self.process_npc_responses_to_chat(message)
            
            # When chat is closed, reset chat mode in input handler
            self.input_handler.set_chat_mode(False)
    
    def process_npc_responses_to_chat(self, message):
        """Process NPC responses to player chat messages"""
        if not self.player:
            return
            
        # Define vicinity range (in grid cells)
        vicinity_range = 8
        
        # Find NPCs within range
        nearby_npcs = []
        for obj in self.objects:
            if isinstance(obj, NPC) and hasattr(obj, 'grid_x') and hasattr(obj, 'grid_y'):
                # Calculate Manhattan distance
                distance = abs(obj.grid_x - self.player.grid_x) + abs(obj.grid_y - self.player.grid_y)
                if distance <= vicinity_range:
                    nearby_npcs.append(obj)
        
        # Debug output
        print(f"DEBUG: Found {len(nearby_npcs)} NPCs in chat vicinity of player")
        
        # If no NPCs in range, return
        if not nearby_npcs:
            return
            
        # For each nearby NPC, generate a response via AI Universe
        if hasattr(self, 'ai_universe'):
            for npc in nearby_npcs:
                # Debug output
                print(f"DEBUG: Requesting chat response from NPC {npc.get_entity_id()} at position ({npc.grid_x}, {npc.grid_y})")
                
                # Create a special state update to trigger a response
                self.ai_universe.update_agent_state(
                    agent_id=npc.get_entity_id(),  # Use persistent entity ID
                    grid_x=npc.grid_x,
                    grid_y=npc.grid_y,
                    player_message=message,
                    should_respond=True
                )
                
                # Check if the message contains advice about water or other resources
                if ("water" in message.lower() or "thirsty" in message.lower()) and hasattr(npc, 'thirst') and npc.thirst <= 2:
                    # If the NPC is thirsty and the player is giving water advice, make them more likely to follow it
                    self.ai_universe.update_agent_state(
                        agent_id=npc.get_entity_id(),  # Use persistent entity ID
                        needs_advice=True,
                        advice_topic="water",
                        advice_urgency=5 - npc.thirst  # Higher urgency for lower thirst
                    )
                    print(f"DEBUG: NPC {npc.get_entity_id()} is thirsty and received potential water advice")

                

    def set_world_map(self, world_map):
        """Set the world map for the game"""
        self.world_map = world_map
        self.physics.set_world_map(world_map)
        
        # Connect world cache to world map
        if hasattr(self, 'world_cache'):
            world_map.set_world_cache(self.world_cache)
        
    def add_object(self, obj):
        """Add a game object to the world"""
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
        """Spawn a food NPC at the specified position or a random valid position"""
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
        
    def add_ai_controller(self, controller):
        """Add an AI controller to the game"""
        return self.ai_manager.add_controller(controller)

        
    def handle_events(self):
        """Process all input events"""
        # Process pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # Handle delayed music start
            if event.type == pygame.USEREVENT + 1:
                if self.game_state == GameState.MAIN_MENU:
                    self.sound_manager.play_music("track_main", loops=-1)
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Cancel the timer
                continue
            
            menu_handled = False
            for obj in self.objects:
                if hasattr(obj, 'interaction_menu') and obj.interaction_menu and obj.interaction_menu.visible:
                    if obj.interaction_menu.handle_event(event):
                        menu_handled = True
                        break
            
            if menu_handled:
                continue

            # Check for F key to toggle interaction menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                print("DEBUG: F key pressed directly in SimpleGameEngine")
                for obj in self.objects:
                    if hasattr(obj, 'controllable') and obj.controllable and hasattr(obj, 'toggle_interaction_menu'):
                        print("DEBUG: Toggling interaction menu for player")
                        obj.toggle_interaction_menu()
                        break

            # Handle window resize events
            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.handle_resize(event.w, event.h)
                    
                    # Update main menu if it exists
                    if hasattr(self, 'main_menu'):
                        self.main_menu.update_screen_size(self.width, self.height)
                        
                    # Update pause menu if it exists and we're in paused state
                    if hasattr(self, 'pause_menu') and self.game_state == GameState.PAUSED:
                        self.pause_menu.update_screen_size(self.width, self.height)
            
            
            # If in main menu, let it handle events
            if self.game_state == GameState.MAIN_MENU:
                pygame.time.set_timer(pygame.USEREVENT + 1, 500)  # Start music after 500ms

                if hasattr(self, 'main_menu') and self.main_menu.handle_event(event):
                    continue
                
                # Check for Escape key to quit from menu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                    
                # Skip other event handling in menu mode
                continue
            
            # Handle pause menu events when in paused state
            if self.game_state == GameState.PAUSED:
                if hasattr(self, 'pause_menu') and self.pause_menu.handle_event(event):
                    continue
            
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and 
                self.game_state == GameState.RUNNING):
                if hasattr(self, 'pause_menu') and self.pause_menu.visible:
                    # If pause menu is already visible, resume the game
                    self._resume_game()
                else:
                    # Show pause menu and pause the game
                    self.paused = True
                    self.game_state = GameState.PAUSED
                    if hasattr(self, 'pause_menu'):
                        self.pause_menu.show()
                    print("Game paused - ESC menu shown")
                continue
            
            # Let UI handle events first (for active chat input)
            if self.ui.handle_event(event):
                continue
                
            # Check for F11 to toggle fullscreen
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
                continue
                
            # Check for F10 to toggle borderless fullscreen
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F10:
                self.toggle_borderless_fullscreen()
                continue
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    # Toggle ambient effects
                    self.theme_manager.toggle_ambient_effects()
                    print(f"Ambient effects: {'ON' if self.theme_manager.use_ambient_effects else 'OFF'}")
                elif event.key == pygame.K_F2:
                    # Toggle particles
                    self.theme_manager.toggle_particles()
                    print(f"Particles: {'ON' if self.theme_manager.use_particles else 'OFF'}")
                elif event.key == pygame.K_F3:
                    # Toggle decorative elements
                    self.theme_manager.toggle_decorative_elements()
                    print(f"Decorative elements: {'ON' if self.theme_manager.use_decorative_elements else 'OFF'}")
                elif event.key == pygame.K_F4:
                    # Toggle lighting effects
                    self.theme_manager.toggle_lighting()
                    print(f"Lighting effects: {'ON' if self.theme_manager.use_lighting else 'OFF'}")
                
            # Add grid toggle with G key
            if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                self.show_grid = not self.show_grid
                self.camera.show_grid = self.show_grid  # Pass to camera
                print(f"Grid {'shown' if self.show_grid else 'hidden'}")
                continue
                
            # Check for spacebar to toggle pause
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not self.input_handler.chat_mode:
                self.paused = not self.paused
                print(f"Game {'paused' if self.paused else 'resumed'}")
                continue
                
            # Direct check for T key to toggle chat
            if event.type == pygame.KEYDOWN and event.key == pygame.K_t and not self.input_handler.chat_mode:
                print("Chat mode activated")  # Debug output
                if hasattr(self, 'chat_input') and self.chat_input is not None:
                    self.input_handler.chat_mode = True
                    self.chat_input.toggle()
                else:
                    print("ERROR: Chat input not initialized")
                continue
            
                
            # Handle mouse wheel for zooming or chat scrolling
            if event.type == pygame.MOUSEWHEEL:
                # If in chat mode, scroll the chat history instead of zooming
                if self.input_handler.chat_mode and hasattr(self, 'chat_input'):
                    # Pass the scroll event to the chat input
                    # In pygame, positive y means scroll up (wheel away from user)
                    self.chat_input.handle_scroll(event.y)
                    continue
                else:
                    # Normal zoom behavior when not in chat mode
                    if event.y > 0:
                        self.camera.zoom_in(0.1)
                    elif event.y < 0:
                        self.camera.zoom_out(0.1)
                continue
            
            # Check for Tab key to close character info panel
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                if hasattr(self, 'ui') and self.ui:
                    if hasattr(self.ui, 'char_info_panel') and self.ui.char_info_panel.visible:
                        self.ui.char_info_panel.visible = False
                        print("Character info panel closed with Tab key")
                        continue
                            
            # Handle mouse buttons for panning
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if we're clicking on the map (not UI)
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if any entity was clicked
                    entity_clicked = False
                    for obj in self.objects:
                        if hasattr(obj, 'contains_point') and obj.contains_point(mouse_pos[0], mouse_pos[1], self.camera):
                            print(f"Entity clicked: {obj.__class__.__name__}")
                            self.ui.show_entity_info(obj)
                            entity_clicked = True
                            break
                    
                    # If no entity was clicked, start panning
                    if not entity_clicked:
                        self.camera.start_drag(mouse_pos[0], mouse_pos[1])
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.camera.stop_drag()
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.camera.dragging:
                    self.camera.update_drag(event.pos[0], event.pos[1])
                    
        
        # Update input handler for continuous key state
        self.input_handler.update()
        
        # Only handle movement if not in chat mode and not paused
        if not self.input_handler.chat_mode and not self.paused:
            for obj in self.objects:
                self.input_handler.handle_entity_movement(obj)
                self.input_handler.handle_entity_action(obj)
                self.input_handler.handle_entity_interaction(obj)
                
                


                
    def toggle_borderless_fullscreen(self):
        """Toggle borderless fullscreen mode (windowed fullscreen)"""
        import sys
        
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            # Get desktop size for fullscreen
            desktop_info = pygame.display.Info()
            new_width, new_height = desktop_info.current_w, desktop_info.current_h
            
            print(f"Attempting borderless fullscreen at resolution: {new_width}x{new_height}")
            
            # For macOS, we need a special approach
            if sys.platform == 'darwin':
                try:
                    # On macOS, we'll use a combination that works better
                    self.screen = pygame.display.set_mode(
                        (0, 0),  # Use (0,0) to get full desktop size
                        pygame.FULLSCREEN | pygame.DOUBLEBUF
                    )
                    self.borderless = False  # Not truly borderless, but fullscreen
                except pygame.error as e:
                    print(f"Error creating fullscreen window: {e}")
                    # Fallback to windowed mode
                    self.screen = pygame.display.set_mode(
                        (self.default_width, self.default_height),
                        pygame.RESIZABLE
                    )
                    self.fullscreen = False
                    self.borderless = False
        else:
            # Return to windowed mode with default size
            self.screen = pygame.display.set_mode((self.default_width, self.default_height), pygame.RESIZABLE)
            self.borderless = False
        
        # Update width and height
        self.width, self.height = self.screen.get_size()
        
        # Update camera and UI
        self.camera.update_screen_size(self.width, self.height)
        self.ui.update_screen_size(self.width, self.height)
        
        # Update pause menu size
        if hasattr(self, 'pause_menu'):
            self.pause_menu.update_screen_size(self.width, self.height)
        
        mode_str = "Fullscreen"
        if self.fullscreen and self.borderless:
            mode_str = "Borderless Fullscreen"
        elif not self.fullscreen:
            mode_str = "Windowed"
            
        print(f"Screen mode changed: {mode_str} ({self.width}x{self.height})")

    def process_chat(self, message):
        """Process a chat message from the player"""
        if not message.strip():
            return
            
        # Set input handler to chat mode
        self.input_handler.chat_mode = False
        
        # Get the player entity
        player = None
        for obj in self.objects:
            if hasattr(obj, 'controllable') and obj.controllable:
                player = obj
                break
        
        if not player:
            return
        
        # Check for commands
        if message.startswith("/"):
            self.process_command(message[1:])  # This line exists but process_command wasn't working
            return

        
        # Find the nearest NPC within chat range
        nearest_npc = None
        min_distance = float('inf')
        chat_range = 5  # Maximum distance for chat in grid cells
        
        for obj in self.objects:
            if hasattr(obj, 'is_npc') and obj.is_npc:
                # Calculate distance
                dx = obj.grid_x - player.grid_x
                dy = obj.grid_y - player.grid_y
                distance = (dx ** 2 + dy ** 2) ** 0.5
                
                if distance <= chat_range and distance < min_distance:
                    nearest_npc = obj
                    min_distance = distance
        
        # If an NPC is in range, send the message to it
        if nearest_npc:
            # Add the message to chat history
            self.chat_input.add_chat_message(message, "player")
            
            # Set a flag to prevent duplicate message
            self.chat_input.skip_next_add = True
            
            # Get the NPC's entity ID
            npc_id = nearest_npc.get_entity_id() if hasattr(nearest_npc, 'get_entity_id') else None
            
            if npc_id:
                # Add a text bubble above the player
                self.ui.add_text_bubble(message, player)
                
                # Request a response from the AI controller
                if hasattr(self, 'ai_controller'):
                    self.ai_controller.update_agent_state(
                        npc_id,
                        player_message=message,
                        should_respond=True
                    )
        else:
            # No NPC in range, just add to chat history
            self.chat_input.add_chat_message(message, "player")
            
            # Add a text bubble above the player
            self.ui.add_text_bubble(message, player)

    
    def update(self):
        """Update game logic"""
        
        if self.game_state == GameState.MAIN_MENU:
            return
            
        if self.paused:
            return
        
        # Calculate delta time
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_update_time) / 1000.0  # Convert to seconds
        self.last_update_time = current_time
        
        # Update theme manager
        self.theme_manager.update(delta_time)
        
        # Add ambient particles
        self.theme_manager.add_ambient_particles(self.camera, count=1)
        
            
        self.camera.update()

        # Update game time
        self.data.add_to_value("game_time", 1)
        
        # Process AI decisions first to prioritize chat responses
        if hasattr(self, 'ai_universe'):
            decisions = self.ai_universe.get_pending_decisions()
            for decision in decisions:
                print(f"DEBUG: Processing decision for agent {decision.agent_id}, action={decision.action}, speech='{decision.speech}'")
                # Find the corresponding object
                found_object = False
                for obj in self.objects:
                    # Try both direct ID comparison and entity_id comparison
                    if (obj.get_entity_id() == decision.agent_id or 
                        str(id(obj)) == decision.agent_id):
                        found_object = True
                        # Apply the decision to the NPC
                        if isinstance(obj, NPC):
                            obj.apply_ai_decision(decision)
                        
                        # Handle speech with text bubbles
                        if decision.speech and hasattr(self, 'ui'):
                            print(f"DEBUG: Adding text bubble for speech: '{decision.speech}'")
                            self.ui.add_text_bubble(decision.speech, obj, duration=3.0)
                        elif not decision.speech:
                            print(f"DEBUG: No speech to display for agent {decision.agent_id}")
                        
                        # Add debug output to help diagnose ID issues
                        print(f"DEBUG: Matched agent ID {decision.agent_id} to object with entity_id {obj.get_entity_id()}")
                        break
                
                if not found_object:
                    print(f"DEBUG: Could not find object for agent {decision.agent_id}")
                    # Add more debug info to help diagnose the issue
                    print(f"DEBUG: Available entity IDs: {[obj.get_entity_id() for obj in self.objects if hasattr(obj, 'get_entity_id')]}")
        
        # Update all game objects
        for obj in self.objects:
            if hasattr(obj, 'update'):
                obj.update()
                
                # Special check for player to ensure animation state is correct
                if hasattr(obj, 'controllable') and obj.controllable:
                    # Check if any movement keys are pressed
                    keys = pygame.key.get_pressed()
                    movement_keys = [
                        pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                        pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s
                    ]
                    
                    # If any movement key is pressed, force the walk animation
                    if any(keys[key] for key in movement_keys):
                        obj.force_walk_animation = True
                        obj.walk_animation_start_time = pygame.time.get_ticks()
                        obj.is_moving = True
        
        # Update player thirst in data manager if player exists
        if self.player and hasattr(self.player, 'thirst'):
            self.data.get_player_stat("thirst").set(self.player.thirst)
            
        if hasattr(self.player, 'hunger'):
            self.data.get_player_stat("hunger").set(self.player.hunger)
        
        # Update AI Universe for NPCs
        if hasattr(self, 'ai_universe'):
            for obj in self.objects:
                if isinstance(obj, NPC) and hasattr(obj, 'grid_x') and hasattr(obj, 'grid_y'):
                    # Collect world state for this NPC
                    nearby_tiles = WorldStateCollector.collect_nearby_tiles(
                        self.world_map, obj.grid_x, obj.grid_y, radius=5)
                    nearby_entities = WorldStateCollector.collect_nearby_entities(
                        self.objects, obj.grid_x, obj.grid_y, radius=5)
                    
                    # Update agent state in AI universe
                    self.ai_universe.update_agent_state(
                        agent_id=obj.get_entity_id(),  # Use persistent entity ID
                        grid_x=obj.grid_x,
                        grid_y=obj.grid_y,
                        thirst=obj.thirst if hasattr(obj, 'thirst') else 5,
                        hunger=getattr(obj, 'hunger', 5),
                        health=getattr(obj, 'health', 5),
                        nearby_tiles=nearby_tiles,
                        nearby_entities=nearby_entities,
                        cna_file=obj.cna_file if hasattr(obj, 'cna_file') else None
                    )
            
            # Check for NPC-to-NPC interactions
            for obj1 in self.objects:
                if isinstance(obj1, NPC) and hasattr(obj1, 'grid_x') and hasattr(obj1, 'grid_y'):
                    # Only check for interaction occasionally (10% chance per frame)
                    if random.random() < 0.1:
                        for obj2 in self.objects:
                            if (obj1 != obj2 and isinstance(obj2, NPC) and 
                                hasattr(obj2, 'grid_x') and hasattr(obj2, 'grid_y')):
                                # Calculate distance between NPCs
                                distance = abs(obj1.grid_x - obj2.grid_x) + abs(obj1.grid_y - obj2.grid_y)
                                
                                # If NPCs are close to each other, initiate conversation
                                if distance <= 8:
                                    # Only 20% chance to actually start conversation when in range
                                    if random.random() < 0.2 and hasattr(self, 'ai_universe'):
                                        # Create a special state update for NPC-to-NPC chat
                                        self.ai_universe.update_agent_state(
                                            agent_id=obj1.get_entity_id(),  # Use persistent entity ID
                                            grid_x=obj1.grid_x,
                                            grid_y=obj1.grid_y,
                                            npc_interaction=True,
                                            other_npc_id=obj2.get_entity_id()  # Use persistent entity ID
                                        )
                                        # Only one NPC needs to initiate
                                        break
        
        # Update AI for all NPCs (keep the existing AI system as fallback)
        self.ai_manager.update(self.world_map, self.objects)
        
        # Update physics for all objects
        self.physics.update(self.objects)
        
        # Update player thirst in data manager if player exists
        if self.player and hasattr(self.player, 'thirst'):
            self.data.get_player_stat("thirst").set(self.player.thirst)
        
        # Example: slowly decrease hunger and thirst over time
        if self.data.get_value("game_time").value % 1200 == 0:  # Every 20 seconds (at 60 FPS)
            if self.data.get_player_stat("hunger").value > 0:
                self.data.get_player_stat("hunger").subtract(1)
            if self.data.get_player_stat("thirst").value > 0:
                self.data.get_player_stat("thirst").subtract(1)
                
                # Also update player entity's thirst if it exists
                if self.player and hasattr(self.player, 'thirst') and self.player.thirst > 0:
                    self.player.thirst -= 1





    def render(self):
        """Render all game objects"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        
        # If in main menu, render it and return
        if self.game_state == GameState.MAIN_MENU:
            if hasattr(self, 'main_menu'):
                self.main_menu.render(self.screen)
            else:
                print("ERROR: Main menu not initialized")
            pygame.display.flip()
            return
        
        self.theme_manager.render_background(self.screen, self.camera)
        
        
        # Draw the world map first
        if self.world_map:
            self.world_map.render(self.screen, self.camera)
        
        # Draw all objects
        for obj in self.objects:
            if hasattr(obj, 'render'):
                obj.render(self.screen, self.camera)
        
        # Draw entity tiles last (on top of everything)
        if self.world_map and hasattr(self.world_map, 'entity_tile_manager'):
            self.world_map.entity_tile_manager.render(self.screen, self.camera)
    
        
        self.theme_manager.render_foreground(self.screen, self.camera)

        
        # Draw UI elements last (on top)
        self.ui.render(self.screen)
        
        if self.game_state == GameState.PAUSED and hasattr(self, 'pause_menu'):
            self.pause_menu.render(self.screen)
        
        # Update the display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        self.running = True
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.fps)
        
        # Clean up
        if hasattr(self, 'ai_universe'):
            self.ai_universe.stop()
            
        # Clean up sound manager
        if hasattr(self, 'sound_manager'):
            self.sound_manager.cleanup()
            
        self.theme_manager.render_background(self.screen, self.camera)
        self.theme_manager.render_foreground(self.screen, self.camera)
        
            
        pygame.quit()
        sys.exit()
        
        
    def _create_default_icon(self):
        """Create a simple default icon if the logo file is not found"""
        try:
            # Create a simple 32x32 icon
            icon = pygame.Surface((32, 32))
            icon.fill((30, 60, 90))  # Dark blue background
        
        # Draw a simple H
            pygame.draw.rect(icon, (200, 230, 255), (8, 6, 4, 20))  # Left vertical line
            pygame.draw.rect(icon, (200, 230, 255), (20, 6, 4, 20))  # Right vertical line
            pygame.draw.rect(icon, (200, 230, 255), (8, 14, 16, 4))  # Horizontal line
        
            # Set as icon
            pygame.display.set_icon(icon)
            print("Created and set default icon")
        except Exception as e:
            print(f"Error creating default icon: {e}")
            
            
    def _start_game_from_menu(self, seed=None, is_new_world=False):
        """Start the game from the main menu
        
        Args:
            seed: Optional seed to use for world generation
            is_new_world: Whether this is a completely new world (not loaded from cache)
        """
        try:
            print(f"Starting game from menu with seed: {seed}, new world: {is_new_world}")
            self.game_state = GameState.RUNNING

            # Switch to game music
            self.sound_manager.play_music("track_game", loops=-1, fade_in=1000)
            
            # Set map seed if provided
            if seed is not None:
                self.map_seed = seed
                print(f"Using provided seed: {seed}")
            
            # Load item icons after pygame is initialized
            self.load_item_icons()
            
            # Handle world cache setup
            if hasattr(self, 'world_cache'):
                if is_new_world:
                    # For new worlds, clear the cache and start fresh
                    print(f"Creating fresh world cache for new seed: {self.map_seed}")
                    self.world_cache.create_fresh_world(self.map_seed)
                else:
                    # For existing worlds, load the cache
                    print(f"Loading existing world cache for seed: {self.map_seed}")
                    self.world_cache.set_world_seed(self.map_seed)
            
            # If we have a world map already, regenerate it with the new seed
            if hasattr(self, 'world_map') and self.world_map:
                print(f"Regenerating world map with seed: {self.map_seed}")
                self.world_map.generate_realistic_map(seed=self.map_seed)
                
                # Only load cached entities if this is NOT a new world
                if not is_new_world:
                    self._load_cached_entities()
                else:
                    print("Skipping cached entity loading for new world")
                
        except Exception as e:
            import traceback
            print(f"Error starting game from menu: {e}")
            traceback.print_exc()
            
            # Try to recover
            self.game_state = GameState.RUNNING
            if hasattr(self, 'world_map') and self.world_map:
                # Generate a fallback map
                self.world_map._generate_fallback_map()


    def _load_cached_entities(self):
        """Load cached entity positions and states"""
        if not hasattr(self, 'world_cache'):
            return
            
        try:
            cached_entities = self.world_cache.get_all_entity_positions()
            
            # Handle case where cached_entities might be a dict instead of a list
            if isinstance(cached_entities, dict):
                # Convert dict to list of entity data
                entity_list = []
                for entity_id, entity_data in cached_entities.items():
                    if isinstance(entity_data, dict):
                        entity_data["entity_id"] = entity_id
                        entity_list.append(entity_data)
                cached_entities = entity_list
            
            for entity_data in cached_entities:
                if not isinstance(entity_data, dict):
                    print(f"Warning: Invalid entity data format: {entity_data}")
                    continue
                    
                entity_id = entity_data.get("entity_id")
                entity_type = entity_data.get("type")
                
                if not entity_id:
                    print(f"Warning: Entity data missing entity_id: {entity_data}")
                    continue
                
                # Find existing entity with this ID
                existing_entity = None
                for obj in self.objects:
                    if hasattr(obj, 'get_entity_id') and obj.get_entity_id() == entity_id:
                        existing_entity = obj
                        break
                
                if existing_entity and hasattr(existing_entity, 'load_position_from_cache'):
                    existing_entity.load_position_from_cache()
                    print(f"DEBUG: Loaded cached position for entity {entity_id}")
                    
        except Exception as e:
            print(f"Error loading cached entities: {e}")
            import traceback
            traceback.print_exc()

                
    def process_command(self, command):
        """Process debug commands"""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == "debug_map":
            if hasattr(self, 'world_map'):
                self.world_map.enable_debug_mode()
                print("Map debug mode enabled. Next map generation will create debug files.")
            else:
                print("No world map available")
        
        elif cmd == "regen_map":
            if hasattr(self, 'world_map'):
                seed = int(parts[1]) if len(parts) > 1 else None
                self.world_map.generate_realistic_map(seed=seed)
                print(f"Map regenerated with seed: {seed}")
            else:
                print("No world map available")
        
        elif cmd == "help":
            print("Available commands:")
            print("  debug_map - Enable debug visualization")
            print("  regen_map [seed] - Regenerate map with optional seed")
            print("  help - Show this help")



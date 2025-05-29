"""Event handling and processing"""
import pygame
from engine.config.config_loader import get_config_loader

class EventHandler:
    """Handles pygame events and delegates to appropriate managers"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.config = get_config_loader()
        
        # Load mouse settings
        mouse_config = self.config.get_setting('input_mappings', 'mouse', default={})
        self.zoom_sensitivity = mouse_config.get('zoom_sensitivity', 0.1)
        self.pan_button = mouse_config.get('pan_button', 1)
    
    def handle_events(self):
        """Process all input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_engine.running = False
                return
            
            # SECOND PRIORITY: Interaction menu (if player has one and it's visible)
            # FIXED: Add comprehensive safety checks
            if (hasattr(self, 'player') and self.player and 
                hasattr(self.player, 'interaction_menu') and 
                self.player.interaction_menu and
                hasattr(self.player.interaction_menu, 'visible') and
                self.player.interaction_menu.visible and
                hasattr(self.player.interaction_menu, 'handle_event') and
                self.player.interaction_menu.handle_event(event)):
                continue
            
            
            # Handle delayed music start
            if event.type == pygame.USEREVENT + 1:
                if self.game_engine.state_manager.is_state(self.game_engine.state_manager.game_state_constants.MAIN_MENU):
                    self.game_engine.sound_manager.play_music("track_main", loops=-1)
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                continue
            
            # Handle interaction menu events
            if self._handle_interaction_menu_events(event):
                continue
            
            # Handle window resize
            if self._handle_resize_event(event):
                continue
            
            # Handle state-specific events
            if self._handle_state_specific_events(event):
                continue
            
            # Handle UI events
            if self._handle_ui_events(event):
                continue
            
            # Handle system keys
            if self._handle_system_keys(event):
                continue
            
            # Handle debug keys
            if self._handle_debug_keys(event):
                continue
            
            # Handle game-specific keys
            if self._handle_game_keys(event):
                continue
            
            # Handle mouse events
            if self._handle_mouse_events(event):
                continue
        
        # Update input manager for continuous key state
        self.game_engine.input_manager.update()
        
        
        # Handle entity input if not in chat mode and not paused
        if (not self.game_engine.input_manager.chat_mode and 
            not self.game_engine.state_manager.is_state(self.game_engine.state_manager.game_state_constants.PAUSED)):
            self._handle_entity_input()
    
    def _handle_interaction_menu_events(self, event):
        """Handle interaction menu events"""
        menu_handled = False
        for obj in self.game_engine.objects:
            if hasattr(obj, 'interaction_menu') and obj.interaction_menu and obj.interaction_menu.visible:
                if obj.interaction_menu.handle_event(event):
                    menu_handled = True
                    break
        
        if menu_handled:
            return True
        
        # Check for F key to toggle interaction menu
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            print("DEBUG: F key pressed directly in EventHandler")
            for obj in self.game_engine.objects:
                if hasattr(obj, 'controllable') and obj.controllable and hasattr(obj, 'toggle_interaction_menu'):
                    print("DEBUG: Toggling interaction menu for player")
                    obj.toggle_interaction_menu()
                    break
            return True
        
        return False
    
    def _handle_resize_event(self, event):
        """Handle window resize events"""
        if event.type == pygame.VIDEORESIZE:
            if not self.game_engine.display_manager.fullscreen:
                new_size = self.game_engine.display_manager.handle_resize(event.w, event.h)
                if new_size:
                    self._update_components_for_resize(*new_size)
            return True
        return False
    
    def _handle_state_specific_events(self, event):
        """Handle events specific to current game state"""
        current_state = self.game_engine.state_manager.get_state()
        
        # Main menu events
        if current_state == self.game_engine.state_manager.game_state_constants.MAIN_MENU:
            pygame.time.set_timer(pygame.USEREVENT + 1, 500)
            
            if hasattr(self.game_engine, 'main_menu') and self.game_engine.main_menu.handle_event(event):
                return True
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game_engine.running = False
                return True
            
            return True  # Skip other event handling in menu mode
        
        # Pause menu events
        if current_state == self.game_engine.state_manager.game_state_constants.PAUSED:
            if hasattr(self.game_engine, 'pause_menu') and self.game_engine.pause_menu.handle_event(event):
                return True
        
        # Handle escape key for pausing/resuming
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and 
            current_state == self.game_engine.state_manager.game_state_constants.RUNNING):
            if hasattr(self.game_engine, 'pause_menu') and self.game_engine.pause_menu.visible:
                self.game_engine._resume_game()
            else:
                self.game_engine._pause_game()
            return True
        
        return False
    
    def _handle_ui_events(self, event):
        """Handle UI events"""
        return self.game_engine.ui.handle_event(event)
    
    def _handle_system_keys(self, event):
        """Handle system key events"""
        if event.type != pygame.KEYDOWN:
            return False
        
        # Fullscreen toggle
        if event.key == pygame.K_F11:
            new_size = self.game_engine.display_manager.toggle_fullscreen()
            self._update_components_for_resize(*new_size)
            return True
        
        # Borderless fullscreen toggle
        if event.key == pygame.K_F10:
            new_size = self.game_engine.display_manager.toggle_borderless_fullscreen()
            self._update_components_for_resize(*new_size)
            return True
        
        return False
    
    def _handle_debug_keys(self, event):
        """Handle debug key events"""
        if event.type != pygame.KEYDOWN:
            return False
        
        debug_actions = {
            pygame.K_F1: ('toggle_ambient_effects', 'Ambient effects'),
            pygame.K_F2: ('toggle_particles', 'Particles'),
            pygame.K_F3: ('toggle_decorative_elements', 'Decorative elements'),
            pygame.K_F4: ('toggle_lighting', 'Lighting effects')
        }
        
        if event.key in debug_actions:
            method_name, feature_name = debug_actions[event.key]
            if hasattr(self.game_engine.theme_manager, method_name):
                getattr(self.game_engine.theme_manager, method_name)()
                enabled = getattr(self.game_engine.theme_manager, f"use_{method_name.replace('toggle_', '')}", True)
                print(f"{feature_name}: {'ON' if enabled else 'OFF'}")
            return True
        
        return False
    
    def _handle_game_keys(self, event):
        """Handle game-specific key events"""
        if event.type != pygame.KEYDOWN:
            return False
        
        # Grid toggle
        if event.key == pygame.K_g:
            self.game_engine.show_grid = not self.game_engine.show_grid
            self.game_engine.camera.show_grid = self.game_engine.show_grid
            print(f"Grid {'shown' if self.game_engine.show_grid else 'hidden'}")
            return True
        
        # Pause toggle
        if event.key == pygame.K_SPACE and not self.game_engine.input_manager.chat_mode:
            current_state = self.game_engine.state_manager.get_state()
            if current_state == self.game_engine.state_manager.game_state_constants.RUNNING:
                self.game_engine._pause_game()
            elif current_state == self.game_engine.state_manager.game_state_constants.PAUSED:
                self.game_engine._resume_game()
            return True
        
        # Chat toggle
        if event.key == pygame.K_t and not self.game_engine.input_manager.chat_mode:
            print("Chat mode activated")
            if hasattr(self.game_engine, 'chat_input') and self.game_engine.chat_input is not None:
                self.game_engine.input_manager.chat_mode = True
                self.game_engine.chat_input.toggle()
            else:
                print("ERROR: Chat input not initialized")
            return True
        
        # Tab key for character info panel
        if event.key == pygame.K_TAB:
            if hasattr(self.game_engine, 'ui') and self.game_engine.ui:
                if hasattr(self.game_engine.ui, 'char_info_panel') and self.game_engine.ui.char_info_panel.visible:
                    self.game_engine.ui.char_info_panel.visible = False
                    print("Character info panel closed with Tab key")
                    return True
        
        return False
    
    def _handle_mouse_events(self, event):
        """Handle mouse events"""
        # Mouse wheel for zooming or chat scrolling
        if event.type == pygame.MOUSEWHEEL:
            if self.game_engine.input_manager.chat_mode and hasattr(self.game_engine, 'chat_input'):
                self.game_engine.chat_input.handle_scroll(event.y)
                return True
            else:
                if event.y > 0:
                    self.game_engine.camera.zoom_in(self.zoom_sensitivity)
                elif event.y < 0:
                    self.game_engine.camera.zoom_out(self.zoom_sensitivity)
                return True
        
        # Mouse button events
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == self.pan_button:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check if any entity was clicked
                entity_clicked = False
                for obj in self.game_engine.objects:
                    if hasattr(obj, 'contains_point') and obj.contains_point(mouse_pos[0], mouse_pos[1], self.game_engine.camera):
                        print(f"Entity clicked: {obj.__class__.__name__}")
                        self.game_engine.ui.show_entity_info(obj)
                        entity_clicked = True
                        break
                
                # If no entity was clicked, start panning
                if not entity_clicked:
                    self.game_engine.camera.start_drag(mouse_pos[0], mouse_pos[1])
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == self.pan_button:
                self.game_engine.camera.stop_drag()
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.game_engine.camera.dragging:
                self.game_engine.camera.update_drag(event.pos[0], event.pos[1])
                return True
        
        return False
    
    def _handle_entity_input(self):
        """Handle entity input for movement and actions"""
        for obj in self.game_engine.objects:
            self.game_engine.input_manager.handle_entity_movement(obj)
            self.game_engine.input_manager.handle_entity_action(obj)
            self.game_engine.input_manager.handle_entity_interaction(obj)
    
    def _update_components_for_resize(self, width, height):
        """Update all components when screen size changes"""
        self.game_engine.camera.update_screen_size(width, height)
        self.game_engine.ui.update_screen_size(width, height)
        
        if hasattr(self.game_engine, 'pause_menu'):
            self.game_engine.pause_menu.update_screen_size(width, height)
        
        if hasattr(self.game_engine, 'main_menu'):
            self.game_engine.main_menu.update_screen_size(width, height)
        
        print(f"Screen mode changed: ({width}x{height})")
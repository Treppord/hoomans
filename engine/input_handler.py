import pygame

class InputHandler:
    """Handles user input and maps it to game actions"""
    
    def __init__(self):
        # Key bindings - can be customized
        self.key_bindings = {
            "move_left": pygame.K_LEFT,
            "move_right": pygame.K_RIGHT,
            "move_up": pygame.K_UP,
            "move_down": pygame.K_DOWN,
            "action": pygame.K_SPACE,
            "interact": pygame.K_e,
            "chat": pygame.K_t,
            "pause": pygame.K_ESCAPE
        }
        
        # Track pressed keys
        self.pressed_keys = {}
        
        # Track key states for single press detection
        self.previous_key_states = {}
        
        # Chat input mode
        self.chat_mode = False
    
    def update(self):
        """Update key states for this frame"""
        keys = pygame.key.get_pressed()
        
        # Store previous states for keys we care about
        for action, key in self.key_bindings.items():
            self.previous_key_states[key] = self.pressed_keys.get(key, False)
            self.pressed_keys[key] = keys[key]
    
    def is_action_pressed(self, action):
        """Check if an action's key is currently pressed"""
        if action in self.key_bindings:
            key = self.key_bindings[action]
            return self.pressed_keys.get(key, False)
        return False
    
    def is_action_just_pressed(self, action):
        """Check if an action's key was just pressed this frame"""
        if action in self.key_bindings:
            key = self.key_bindings[action]
            return self.pressed_keys.get(key, False) and not self.previous_key_states.get(key, False)
        return False
    
    def rebind_key(self, action, new_key):
        """Change the key binding for an action"""
        if action in self.key_bindings:
            self.key_bindings[action] = new_key
    
    def handle_entity_movement(self, entity):
        """Apply movement input to an entity"""
        if not hasattr(entity, 'controllable') or not entity.controllable:
            return
        
        if self.chat_mode:
            return
    
        if not hasattr(entity, 'is_moving') or entity.is_moving:
            return
        
        current_ticks = pygame.time.get_ticks()
        
        if not hasattr(entity, 'last_move_time'):
            entity.last_move_time = current_ticks
            
        move_delay = int(1000 / (entity.speed * 10)) if hasattr(entity, 'speed') else 100
        
        if current_ticks - entity.last_move_time < move_delay:
            return
            
        entity.last_move_time = current_ticks
            
            
        if self.is_action_pressed("move_left"):
            entity.target_grid_x = max(0, entity.grid_x - 1)
            entity.is_moving = True
        elif self.is_action_pressed("move_right"):
            entity.target_grid_x = entity.grid_x + 1
            entity.is_moving = True
        elif self.is_action_pressed("move_up"):
            entity.target_grid_y = max(0, entity.grid_y - 1)
            entity.is_moving = True
        elif self.is_action_pressed("move_down"):
            entity.target_grid_y = entity.grid_y + 1
            entity.is_moving = True
    
    def handle_entity_action(self, entity):
        """Apply action input to an entity"""
        if not hasattr(entity, 'controllable') or not entity.controllable:
            return
            
        if self.chat_mode:
            return
            
        if hasattr(entity, 'perform_action') and self.is_action_just_pressed("action"):
            entity.perform_action()
            
    def handle_entity_interaction(self, entity):
        """Apply interaction input to an entity"""
        if not hasattr(entity, 'controllable') or not entity.controllable:
            return
            
        if self.chat_mode:
            return
            
        if hasattr(entity, 'interact') and self.is_action_just_pressed("interact"):
            entity.interact()
    
    def handle_chat_toggle(self, chat_input_box):
        """Handle toggling chat input"""
        if self.is_action_just_pressed("chat") and not self.chat_mode:
            self.chat_mode = True
            chat_input_box.toggle()
            return True
        return False
    
    def set_chat_mode(self, active):
        """Set chat input mode"""
        self.chat_mode = active
    
    def process_events(self):
        """Process all pygame events and return if the game should quit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
            # Handle mouse clicks for entity selection
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                self.mouse_pos = event.pos
                self.mouse_clicked = True
                
        self.update()
        return True
    
    def check_entity_clicks(self, entities, ui_manager):
        """Check if any entity was clicked"""
        if not hasattr(self, 'mouse_clicked') or not self.mouse_clicked:
            return
    
    # Get mouse position
        mouse_x, mouse_y = self.mouse_pos
        print(f"Mouse clicked at ({mouse_x}, {mouse_y})")
    
    # Reset click state
        self.mouse_clicked = False
    
    # Check each entity
        for entity in entities:
            if hasattr(entity, 'contains_point'):
                if entity.contains_point(mouse_x, mouse_y):
                    # Entity was clicked
                    print(f"Entity clicked: {entity.__class__.__name__} at ({entity.x}, {entity.y})")
                    ui_manager.show_entity_info(entity)
                    return
    
        print("No entity was clicked")

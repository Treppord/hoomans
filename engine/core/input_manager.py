"""Enhanced input management with configurable key mappings"""
import pygame
from engine.config.config_loader import get_config_loader

class InputManager:
    """Manages input handling with configurable key mappings"""
    
    def __init__(self):
        self.config = get_config_loader()
        self.chat_mode = False
        self.keys_pressed = None  # Will store the pygame key state
        
        # Track key states for single press detection
        self.previous_key_states = {}
        
        # Load key mappings from config
        self._load_key_mappings()
        
        # Debug: Print loaded key mappings
        print("DEBUG: Loaded key mappings:")
        print(f"  Movement keys: {self.movement_keys}")
        print(f"  Action keys: {self.action_keys}")
    
    def _load_key_mappings(self):
        """Load key mappings from configuration"""
        input_config = self.config.get_config('input_mappings')
        print(f"DEBUG: Input config loaded: {input_config}")
        
        self.movement_keys = {}
        self.action_keys = {}
        self.system_keys = {}
        self.debug_keys = {}
        
        # Load movement keys
        movement = input_config.get('movement', {})
        for action, key_names in movement.items():
            pygame_keys = self.config.get_pygame_keys(f'input_mappings.movement.{action}')
            self.movement_keys[action] = pygame_keys
            print(f"DEBUG: Movement '{action}' mapped to keys: {pygame_keys}")
        
        # Load action keys
        actions = input_config.get('actions', {})
        for action, key_names in actions.items():
            self.action_keys[action] = self.config.get_pygame_keys(f'input_mappings.actions.{action}')
        
        # Load system keys
        system = input_config.get('system', {})
        for action, key_names in system.items():
            self.system_keys[action] = self.config.get_pygame_keys(f'input_mappings.system.{action}')
        
        # Load debug keys
        debug = input_config.get('debug', {})
        for action, key_names in debug.items():
            self.debug_keys[action] = self.config.get_pygame_keys(f'input_mappings.debug.{action}')
    
    def update(self):
        """Update input state"""
        # Store previous key states
        if self.keys_pressed is not None:
            # Store previous states for keys we care about
            all_keys = []
            for key_list in [self.movement_keys, self.action_keys, self.system_keys, self.debug_keys]:
                for keys in key_list.values():
                    all_keys.extend(keys)
            
            for key in all_keys:
                if key < len(self.keys_pressed):
                    self.previous_key_states[key] = self.keys_pressed[key]
        
        # Store the pygame key state directly
        self.keys_pressed = pygame.key.get_pressed()
    
    def is_action_pressed(self, action_type, action):
        """Check if an action is currently pressed"""
        if self.keys_pressed is None:
            return False
            
        key_map = getattr(self, f"{action_type}_keys", {})
        keys = key_map.get(action, [])
        
        # Check if any of the mapped keys are pressed
        result = any(self.keys_pressed[key] for key in keys if key < len(self.keys_pressed))
        
        # Debug output for movement keys
        if action_type == 'movement' and result:
            print(f"DEBUG: Movement key '{action}' pressed (keys: {keys})")
        
        return result
    
    def is_action_just_pressed(self, action_type, action):
        """Check if an action was just pressed this frame"""
        if self.keys_pressed is None:
            return False
            
        key_map = getattr(self, f"{action_type}_keys", {})
        keys = key_map.get(action, [])
        
        # Check if any key was just pressed (pressed now but not before)
        for key in keys:
            if key < len(self.keys_pressed):
                current_state = self.keys_pressed[key]
                previous_state = self.previous_key_states.get(key, False)
                if current_state and not previous_state:
                    return True
        
        return False
    
    def is_movement_pressed(self, direction):
        """Check if a movement key is pressed"""
        return self.is_action_pressed('movement', direction)
    
    def is_action_key_pressed(self, action):
        """Check if an action key is pressed"""
        return self.is_action_pressed('action', action)
    
    def is_system_key_pressed(self, action):
        """Check if a system key is pressed"""
        return self.is_action_pressed('system', action)
    
    def is_debug_key_pressed(self, action):
        """Check if a debug key is pressed"""
        return self.is_action_pressed('debug', action)
    
    def set_chat_mode(self, enabled):
        """Set chat mode state"""
        self.chat_mode = enabled
    
    def handle_entity_movement(self, entity):
        """Handle movement input for an entity - compatible with Rectangle class"""
        if not hasattr(entity, 'controllable') or not entity.controllable or self.chat_mode:
            return
        
        # Use the same movement logic as the original InputHandler
        current_ticks = pygame.time.get_ticks()
        
        if not hasattr(entity, 'last_move_time'):
            entity.last_move_time = current_ticks
            
        move_delay = int(1000 / (entity.speed * 10)) if hasattr(entity, 'speed') else 100
        
        if current_ticks - entity.last_move_time < move_delay:
            return
            
        entity.last_move_time = current_ticks
        
        # Check for movement input and set target position
        moved = False
        
        if self.is_movement_pressed('left'):
            print(f"DEBUG: Moving left - current pos: ({entity.grid_x}, {entity.grid_y})")
            entity.target_grid_x = max(0, entity.grid_x - 1)
            entity.target_grid_y = entity.grid_y  # Keep Y the same
            entity.facing = 'left'
            moved = True
        elif self.is_movement_pressed('right'):
            print(f"DEBUG: Moving right - current pos: ({entity.grid_x}, {entity.grid_y})")
            entity.target_grid_x = entity.grid_x + 1
            entity.target_grid_y = entity.grid_y  # Keep Y the same
            entity.facing = 'right'
            moved = True
        elif self.is_movement_pressed('up'):
            print(f"DEBUG: Moving up - current pos: ({entity.grid_x}, {entity.grid_y})")
            entity.target_grid_x = entity.grid_x  # Keep X the same
            entity.target_grid_y = max(0, entity.grid_y - 1)
            entity.facing = 'up'
            moved = True
        elif self.is_movement_pressed('down'):
            print(f"DEBUG: Moving down - current pos: ({entity.grid_x}, {entity.grid_y})")
            entity.target_grid_x = entity.grid_x  # Keep X the same
            entity.target_grid_y = entity.grid_y + 1
            entity.facing = 'down'
            moved = True
            
        # Only set is_moving if we actually moved
        if moved:
            entity.is_moving = True
            # Force the animation to use walking frames for a short time
            if hasattr(entity, 'force_walk_animation'):
                entity.force_walk_animation = True
                entity.walk_animation_start_time = current_ticks
            print(f"DEBUG: Set target position to ({entity.target_grid_x}, {entity.target_grid_y})")
    
    def handle_entity_action(self, entity):
        """Handle action input for an entity"""
        if not hasattr(entity, 'controllable') or not entity.controllable or self.chat_mode:
            return
        
        # Handle use item action
        if self.is_action_key_pressed('use_item'):
            if hasattr(entity, 'use_selected_item'):
                entity.use_selected_item()
        
        # Handle other actions that require the entity to have specific methods
        if hasattr(entity, 'perform_action') and self.is_action_just_pressed('action', 'primary'):
            entity.perform_action()
    
    def handle_entity_interaction(self, entity):
        """Handle interaction input for an entity"""
        if not hasattr(entity, 'controllable') or not entity.controllable or self.chat_mode:
            return
        
        # Handle interactions
        if hasattr(entity, 'interact') and self.is_action_just_pressed('action', 'interact'):
            entity.interact()

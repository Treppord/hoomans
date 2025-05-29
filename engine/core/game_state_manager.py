"""Game state management"""
from engine.config.config_loader import get_config_loader

class GameState:
    """Game state constants loaded from configuration"""
    
    def __init__(self):
        config = get_config_loader()
        states = config.get_setting('game_states', 'states', default={})
        
        self.MAIN_MENU = states.get('MAIN_MENU', 0)
        self.RUNNING = states.get('RUNNING', 1)
        self.PAUSED = states.get('PAUSED', 2)
        self.GAME_OVER = states.get('GAME_OVER', 3)

class GameStateManager:
    """Manages game state transitions and callbacks"""
    
    def __init__(self, initial_state=None):
        self.game_state_constants = GameState()
        self.current_state = initial_state or self.game_state_constants.MAIN_MENU
        self.previous_state = None
        self.state_callbacks = {}
    
    def set_state(self, new_state):
        """Change the current game state"""
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            
            # Call state change callback if registered
            if new_state in self.state_callbacks:
                self.state_callbacks[new_state]()
    
    def register_state_callback(self, state, callback):
        """Register a callback for when entering a specific state"""
        self.state_callbacks[state] = callback
    
    def is_state(self, state):
        """Check if current state matches the given state"""
        return self.current_state == state
    
    def get_state(self):
        """Get the current state"""
        return self.current_state
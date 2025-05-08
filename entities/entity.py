class Entity:
    """Base class for all game entities"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def handle_input(self, keys):
        """Handle keyboard input - override in subclasses"""
        pass
    
    def update(self):
        """Update entity state - override in subclasses"""
        pass
    
    def render(self, screen):
        """Render the entity - override in subclasses"""
        pass
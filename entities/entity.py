class Entity:
    """Base class for all game entities"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cna_data = None  # Will hold CNAAttributes when loaded
        self.cna_file = None  # Path to CNA file if loaded from one
    
    def load_cna_file(self, filepath):
        """Load CNA data from a file"""
        try:
                # Use our local CNA utility instead of trying to import from the cna package
            import sys
            import os
            
            # Add the parent directory to sys.path if needed
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            from cna_utils import CNACodec
            self.cna_data = CNACodec.load_from_file(filepath)
            self.cna_file = filepath
            print(f"Successfully loaded CNA file: {filepath}")
            return True
        except Exception as e:
            print(f"Error loading CNA file: {e}")
            import traceback
            traceback.print_exc()
            return False


    
    def handle_input(self, keys):
        """Handle keyboard input - override in subclasses"""
        pass
    
    def update(self):
        """Update entity state - override in subclasses"""
        pass
    
    def render(self, screen):
        """Render the entity - override in subclasses"""
        pass
    
    def contains_point(self, x, y):
        """Check if this entity contains the given point (for click detection)"""
        return False  # Base implementation, override in subclasses

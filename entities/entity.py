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
            
            # Try to import from cna package first (preferred)
            try:
                from cna.cna_codec import CNACodec
            except ImportError:
                # Fall back to cna_utils if cna package is not available
                from cna_utils import CNACodec
                
            self.cna_data = CNACodec.load_from_file(filepath)
            self.cna_file = filepath
            
            # Update entity color based on CNA attributes
            if hasattr(self, 'color') and self.cna_data:
                # Get culture-based color
                culture_colors = {
                    0: (255, 0, 0),     # RED
                    1: (0, 0, 255),     # BLUE
                    2: (0, 255, 0),     # GREEN
                    3: (255, 255, 0),   # YELLOW
                    4: (128, 0, 128),   # PURPLE
                    5: (255, 165, 0),   # ORANGE
                    6: (255, 192, 203), # PINK
                    7: (165, 42, 42),   # BROWN
                    8: (128, 128, 128), # GRAY
                    9: (0, 0, 0),       # BLACK
                    10: (255, 255, 255) # WHITE
                }
                
                # Get base color for culture
                culture_value = self.cna_data.culture.value
                base_color = culture_colors.get(culture_value, (0, 255, 0))
                
                # Debug output to see what's happening
                print(f"DEBUG: Culture value from CNA: {culture_value}, enum: {self.cna_data.culture}")
                
                # Calculate brightness factor based on age
                brightness = 1.0 - (self.cna_data.age_minutes / 60.0 * 0.6)
                
                # Apply brightness to color
                self.color = tuple(int(c * brightness) for c in base_color)
                print(f"Updated entity color to {self.color} based on CNA attributes (culture: {self.cna_data.culture})")
            
            print(f"Successfully loaded CNA file: {filepath}")
            return True
        except Exception as e:
            print(f"Error loading CNA file: {e}")
            import traceback
            traceback.print_exc()
            return False

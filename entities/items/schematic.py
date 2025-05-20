"""Schematic items for constructing buildings and structures"""
from entities.items.item_base import Item
import pygame
import os

class SchematicItem(Item):
    """Base class for building schematic items"""
    
    def __init__(self, item_id, name, description, icon_path=None, 
                 max_stack=5, structure_type=None, width=1, height=1):
        """Initialize a schematic item
        
        Args:
            structure_type: The type of structure this schematic builds
            width: Width of the structure in tiles
            height: Height of the structure in tiles
        """
        super().__init__(item_id, name, description, icon_path, max_stack)
        self.structure_type = structure_type
        self.width = width
        self.height = height
        self.is_schematic = True
        self.preview_texture = None
        self._load_preview_texture()
    
    def _load_preview_texture(self):
        """Load the preview texture for this schematic"""
        # Get project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Try to load the preview texture
        preview_path = os.path.join(project_root, "assets", "structures", f"{self.structure_type}_preview.png")
        
        try:
            if os.path.exists(preview_path):
                self.preview_texture = pygame.image.load(preview_path).convert_alpha()
            else:
                # Create a placeholder preview texture
                self.preview_texture = self._create_placeholder_preview()
                
                # Save it for future use
                try:
                    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
                    pygame.image.save(self.preview_texture, preview_path)
                    print(f"Created placeholder preview texture at {preview_path}")
                except Exception as e:
                    print(f"Error saving preview texture: {e}")
        except Exception as e:
            print(f"Error loading preview texture: {e}")
            self.preview_texture = self._create_placeholder_preview()
    
    def _create_placeholder_preview(self):
        """Create a placeholder preview texture"""
        # Create a surface for the preview
        surface = pygame.Surface((16 * self.width, 16 * self.height), pygame.SRCALPHA)
        
        # Fill with a base color based on structure type
        if self.structure_type == "house":
            # House preview (tan/brown)
            base_color = (180, 140, 100, 200)
        elif self.structure_type == "campfire":
            # Campfire preview (orange/red)
            base_color = (220, 120, 50, 200)
        else:
            # Generic preview (gray)
            base_color = (150, 150, 150, 200)
        
        # Draw the base shape
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(surface, base_color, (x * 16, y * 16, 16, 16))
                pygame.draw.rect(surface, (0, 0, 0, 100), (x * 16, y * 16, 16, 16), 1)
        
        # Add some details based on structure type
        if self.structure_type == "house":
            # Draw a simple house shape
            if self.width >= 2 and self.height >= 2:
                # Roof
                pygame.draw.polygon(surface, (120, 60, 30, 230), [
                    (0, self.height * 8), 
                    (self.width * 16 // 2, 0), 
                    (self.width * 16, self.height * 8)
                ])
                
                # Door
                door_x = (self.width * 16 - 6) // 2
                door_y = self.height * 16 - 12
                pygame.draw.rect(surface, (80, 50, 20, 230), (door_x, door_y, 6, 12))
                
                # Windows
                if self.width >= 3:
                    # Left window
                    pygame.draw.rect(surface, (180, 220, 255, 200), (4, self.height * 8 + 4, 6, 6))
                    # Right window
                    pygame.draw.rect(surface, (180, 220, 255, 200), (self.width * 16 - 10, self.height * 8 + 4, 6, 6))
        
        elif self.structure_type == "campfire":
            # Draw a simple campfire shape
            center_x = self.width * 8
            center_y = self.height * 8
            
            # Fire base (logs)
            pygame.draw.rect(surface, (101, 67, 33, 230), (center_x - 6, center_y, 12, 4))
            pygame.draw.rect(surface, (101, 67, 33, 230), (center_x, center_y - 6, 4, 12))
            
            # Fire (orange/red circle)
            pygame.draw.circle(surface, (255, 100, 0, 200), (center_x, center_y), 6)
            pygame.draw.circle(surface, (255, 200, 0, 150), (center_x, center_y), 4)
        
        return surface
    
    def use(self, user, world=None):
        """Use the schematic to start building"""
        # This will be handled by the interaction menu
        # For now, just print a message
        print(f"Using schematic: {self.name} ({self.structure_type})")
        return False
    
    def create_instance(self):
        """Create a new instance of this schematic item"""
        return SchematicItem(
            self.item_id,
            self.name,
            self.description,
            self.icon_path,
            self.max_stack,
            self.structure_type,
            self.width,
            self.height
        )
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this item class"""
        return cls(
            item_id="generic_schematic",
            name="Generic Schematic",
            description="A blueprint for construction",
            icon_path="items/generic_schematic.png",
            max_stack=5,
            structure_type="generic",
            width=1,
            height=1
        )


class HouseSchematicItem(SchematicItem):
    """Schematic for building a house"""
    
    def __init__(self, item_id="house_schematic", name="House Schematic", 
                 description="Blueprint for constructing a house", icon_path=None,
                 max_stack=5):
        """Initialize a house schematic item"""
        super().__init__(
            item_id, name, description, icon_path or "items/house_schematic.png", 
            max_stack, structure_type="house", width=3, height=3
        )
    
    def create_instance(self):
        """Create a new instance of this house schematic item"""
        return HouseSchematicItem(
            self.item_id,
            self.name,
            self.description,
            self.icon_path,
            self.max_stack
        )
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this house schematic item"""
        return cls()


class CampfireSchematicItem(SchematicItem):
    """Schematic for building a campfire"""
    
    def __init__(self, item_id="campfire_schematic", name="Campfire Schematic", 
                 description="Blueprint for building a campfire", icon_path=None,
                 max_stack=5):
        """Initialize a campfire schematic item"""
        super().__init__(
            item_id, name, description, icon_path or "items/campfire_schematic.png", 
            max_stack, structure_type="campfire", width=1, height=1
        )
    
    def create_instance(self):
        """Create a new instance of this campfire schematic item"""
        return CampfireSchematicItem(
            self.item_id,
            self.name,
            self.description,
            self.icon_path,
            self.max_stack
        )
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this campfire schematic item"""
        return cls()
    
    

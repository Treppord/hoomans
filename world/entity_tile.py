import pygame
import os
from world.tile import Tile

# Load static images for entity tiles
IMAGES = {}

def load_entity_images():
    """Load all entity tile images"""
    global IMAGES
    
    # Get the path to the assets directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(project_root, "assets")
    
    # Define image paths
    image_paths = {
        "tree": "struct_tree.png",
        "house": "struct_house.png",
        "house_door_closed": "struct_house_door_closed.png",
        "house_door_open": "struct_house_door_open.png"
    }
    
    # Load each image
    for key, path in image_paths.items():
        full_path = os.path.join(assets_path, path)
        try:
            if os.path.exists(full_path):
                IMAGES[key] = pygame.image.load(full_path).convert_alpha()
                print(f"Loaded entity image: {key} from {full_path}")
            else:
                print(f"Warning: Entity image file not found: {full_path}")
                # Create a placeholder image
                placeholder = pygame.Surface((Tile.SIZE, Tile.SIZE), pygame.SRCALPHA)
                placeholder.fill((255, 0, 255, 128))  # Magenta semi-transparent
                IMAGES[key] = placeholder
        except Exception as e:
            print(f"Error loading entity image {key}: {e}")
            # Create a placeholder image
            placeholder = pygame.Surface((Tile.SIZE, Tile.SIZE), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255, 128))  # Magenta semi-transparent
            IMAGES[key] = placeholder

# Load images when module is imported
load_entity_images()

def render_entity_texture(screen, texture, x, y, width, height, entity_width, entity_height, rel_x, rel_y, opacity=1.0):
    """
    Helper function to render entity textures correctly based on their dimensions
    
    Args:
        screen: The pygame screen to render to
        texture: The full texture image
        x, y: Screen coordinates to render at
        width, height: Size of the tile on screen
        entity_width, entity_height: Size of the entity in tiles
        rel_x, rel_y: Relative position of this component within the entity
        opacity: Opacity value (0.0-1.0)
    """
    # Calculate the source rectangle from the texture
    # Each tile is 16x16 pixels in the source texture
    src_x = rel_x * Tile.SIZE
    src_y = rel_y * Tile.SIZE
    src_width = Tile.SIZE
    src_height = Tile.SIZE
    
    # Check if the texture is large enough
    texture_width, texture_height = texture.get_size()
    if texture_width >= (entity_width * Tile.SIZE) and texture_height >= (entity_height * Tile.SIZE):
        # The texture covers the whole entity, extract just this component's part
        src_rect = pygame.Rect(src_x, src_y, src_width, src_height)
        component_texture = texture.subsurface(src_rect)
    else:
        # The texture is not properly sized, use the whole texture
        # This is a fallback for improperly sized textures
        component_texture = texture
        print(f"Warning: Texture size mismatch. Expected at least {entity_width*Tile.SIZE}x{entity_height*Tile.SIZE}, got {texture_width}x{texture_height}")
    
    # Scale the component texture to the desired size
    scaled_texture = pygame.transform.scale(component_texture, (width, height))
    
    # Apply opacity if needed
    if opacity < 1.0:
        # Create a copy with the new alpha value
        scaled_texture = scaled_texture.copy()
        scaled_texture.set_alpha(int(255 * opacity))
    
    # Draw the texture
    screen.blit(scaled_texture, (x, y))


class EntityTile:
    """Base class for interactive entity tiles that can span multiple grid cells"""
    
    def __init__(self, base_x, base_y, width=1, height=1, tile_type="entity"):
        """Initialize an entity tile with position and dimensions"""
        self.base_x = base_x  # Base x position in grid coordinates
        self.base_y = base_y  # Base y position in grid coordinates
        self.width = width    # Width in tiles
        self.height = height  # Height in tiles
        self.tile_type = tile_type
        self.opacity = 1.0    # Default opacity
        self.tiles = {}       # Dictionary to store component tiles {(x_offset, y_offset): TileComponent}
        self.is_active = True
        self.entities_inside = []  # List of entities currently inside this entity tile
        self.texture = None   # Full entity texture
        
        # Create the component tiles
        self._create_component_tiles()
    
    def _create_component_tiles(self):
        """Create the component tiles - override in subclasses"""
        # Default implementation creates a single tile
        self.tiles[(0, 0)] = TileComponent(self, 0, 0, self.tile_type)
    
    def get_component_at(self, x, y):
        """Get the component tile at the specified grid position"""
        # Convert to relative coordinates
        rel_x = x - self.base_x
        rel_y = y - self.base_y
        
        # Check if there's a component at this position
        if (rel_x, rel_y) in self.tiles:
            return self.tiles[(rel_x, rel_y)]
        return None
    
    def contains_point(self, x, y):
        """Check if the given grid coordinates are within this entity tile"""
        rel_x = x - self.base_x
        rel_y = y - self.base_y
        return 0 <= rel_x < self.width and 0 <= rel_y < self.height
    
    def get_all_positions(self):
        """Get all grid positions occupied by this entity tile"""
        positions = []
        for rel_x, rel_y in self.tiles.keys():
            positions.append((self.base_x + rel_x, self.base_y + rel_y))
        return positions
    
    def on_entity_enter(self, entity, component_x, component_y):
        """Called when an entity enters this entity tile"""
        # Add entity to the list if not already there
        if entity not in self.entities_inside:
            self.entities_inside.append(entity)
        
        # Default behavior: reduce opacity when entity is behind
        if component_y == 0 and self.height > 1:  # If entering the bottom part of a tall object
            self.opacity = 0.5
    
    def on_entity_exit(self, entity):
        """Called when an entity exits this entity tile"""
        if entity in self.entities_inside:
            self.entities_inside.remove(entity)
        
        # Restore opacity if no entities are inside
        if not self.entities_inside:
            self.opacity = 1.0
    
    def on_interact(self, entity):
        """Called when an entity interacts with this entity tile"""
        pass
    
    def update(self):
        """Update the entity tile state"""
        pass
    
    def render(self, screen, camera):
        """Render all component tiles"""
        # Get screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Sort components by y-coordinate for proper layering
        sorted_components = sorted(self.tiles.items(), key=lambda item: item[0][1])
        
        for (rel_x, rel_y), component in sorted_components:
            # Calculate world position
            world_x = (self.base_x + rel_x) * Tile.SIZE
            world_y = (self.base_y + rel_y) * Tile.SIZE
            
            # Apply camera transformation
            screen_x, screen_y, width, height = camera.apply(
                world_x, world_y, Tile.SIZE, Tile.SIZE
            )
            
            # Only render if on screen
            if (screen_x + width > 0 and screen_x < screen_width and
                screen_y + height > 0 and screen_y < screen_height):
                component.render(screen, screen_x, screen_y, width, height, self.opacity, self.width, self.height)


class TileComponent:
    """A component of an entity tile"""
    
    def __init__(self, parent, x_offset, y_offset, tile_type):
        """Initialize a tile component"""
        self.parent = parent
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.tile_type = tile_type
        self.walkable = True
        self.interactable = True
        
        # Create a base tile for rendering
        self.base_tile = Tile(tile_type)
        
        # Custom rendering properties
        self.custom_color = None
        self.custom_texture = None
    
    def render(self, screen, x, y, width, height, opacity=1.0, entity_width=1, entity_height=1):
        """Render the tile component"""
        if self.custom_texture:
            # Use the helper function to render the texture correctly
            render_entity_texture(
                screen, self.custom_texture, x, y, width, height,
                entity_width, entity_height, self.x_offset, self.y_offset, opacity
            )
        else:
            # Use the base tile rendering with opacity
            if opacity < 1.0:
                # Create a surface with alpha
                surface = pygame.Surface((width, height), pygame.SRCALPHA)
                
                # Get the color
                color = self.custom_color or self.base_tile.colors.get(self.tile_type, (255, 0, 255))
                
                # Apply opacity
                r, g, b = color
                color_with_alpha = (r, g, b, int(255 * opacity))
                
                # Draw on the surface
                pygame.draw.rect(surface, color_with_alpha, (0, 0, width, height))
                
                # Blit to screen
                screen.blit(surface, (x, y))
            else:
                # Normal rendering at full opacity
                if self.custom_color:
                    pygame.draw.rect(screen, self.custom_color, (x, y, width, height))
                else:
                    self.base_tile.render(screen, x, y, width, height)
    
    def is_walkable(self):
        """Check if entities can walk on this component"""
        return self.walkable
    
    def is_interactable(self):
        """Check if entities can interact with this component"""
        return self.interactable


class TreeEntityTile(EntityTile):
    """A tree entity tile that spans 1x2 tiles"""
    
    def __init__(self, base_x, base_y):
        """Initialize a tree entity tile"""
        super().__init__(base_x, base_y, width=1, height=2, tile_type="tree")
    
    def _create_component_tiles(self):
        """Create the tree components: trunk and leaves"""
        # Create a single component for the whole tree
        tree_component = TileComponent(self, 0, 0, "tree")
        tree_component.walkable = False  # Can't walk on the tree
        
        # Use the tree image if available
        if "tree" in IMAGES:
            tree_component.custom_texture = IMAGES["tree"]
        else:
            # Fallback to colors if image not available
            tree_component.custom_color = (0, 100, 0)  # Dark green
        
        # Add component to the tile dictionary
        self.tiles[(0, 0)] = tree_component
        
        # Add a walkable component for the trunk (bottom part)
        trunk = TileComponent(self, 0, 1, "tree_trunk")
        trunk.walkable = True
        # Use the same tree image for the trunk
        if "tree" in IMAGES:
            trunk.custom_texture = IMAGES["tree"]
        else:
            trunk.custom_color = (0, 100, 0)  # Dark green
        
        # Add trunk to the tile dictionary
        self.tiles[(0, 1)] = trunk
    
    def on_entity_enter(self, entity, component_x, component_y):
        """Called when an entity enters this tree"""
        super().on_entity_enter(entity, component_x, component_y)
        
        # If entity is behind the tree (at the trunk), make the tree semi-transparent
        if component_y == 1:  # Trunk component
            self.opacity = 0.5
    
    def on_interact(self, entity):
        """Called when an entity interacts with this tree"""
        # Example: Tree could drop fruit or wood
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
            SimpleGameEngine.instance.ui.add_text_bubble("This is a tree!", entity, duration=2.0)


class HouseEntityTile(EntityTile):
    """A house entity tile that spans 2x2 tiles"""
    
    def __init__(self, base_x, base_y):
        """Initialize a house entity tile"""
        super().__init__(base_x, base_y, width=2, height=2, tile_type="house")
        self.door_position = (base_x, base_y + 1)  # Bottom-left is the door
        self.is_door_open = False
        self.max_occupants = 4
    
    def _create_component_tiles(self):
        """Create the house components: walls, roof, door"""
        # Main house structure
        house_component = TileComponent(self, 0, 0, "house")
        house_component.walkable = False
        
        # Use the house image if available
        if "house" in IMAGES:
            house_component.custom_texture = IMAGES["house"]
        else:
            # Fallback to colors if image not available
            house_component.custom_color = (139, 69, 19)  # Brown
        
        # Door component (bottom right)
        door = TileComponent(self, 1, 1, "house_door")
        door.walkable = True  # Can walk through the door
        
        # Use door images if available
        if "house_door_closed" in IMAGES:
            door.custom_texture = IMAGES["house_door_closed"]
        else:
            # Fallback to colors if image not available
            door.custom_color = (120, 81, 45)  # Dark brown
        
        # Add components to the tile dictionary
        self.tiles[(0, 0)] = house_component
        
        # Add invisible components for collision
        wall1 = TileComponent(self, 1, 0, "house_wall")
        wall1.walkable = False
        wall1.custom_color = None  # No visible color, just for collision
        
        wall2 = TileComponent(self, 0, 1, "house_wall")
        wall2.walkable = False
        wall2.custom_color = None  # No visible color, just for collision
        
        self.tiles[(1, 0)] = wall1
        self.tiles[(0, 1)] = wall2
        self.tiles[(1, 1)] = door
    
    def on_entity_enter(self, entity, component_x, component_y):
        """Called when an entity enters this house"""
        super().on_entity_enter(entity, component_x, component_y)
        
        # Check if entering through the door
        if component_x == 1 and component_y == 1:
            self.is_door_open = True
            
            # If we have too many occupants, some might leave
            if len(self.entities_inside) > self.max_occupants:
                # Find the entity that's been inside the longest
                if self.entities_inside:
                    oldest_entity = self.entities_inside[0]
                    self.entities_inside.remove(oldest_entity)
                    
                    # Make the entity leave
                    if hasattr(oldest_entity, 'ai_controller'):
                        oldest_entity.target_grid_x = self.base_x + 2  # Move outside
                        oldest_entity.target_grid_y = self.base_y + 1
                        oldest_entity.is_moving = True
    
    def on_entity_exit(self, entity):
        """Called when an entity exits this house"""
        super().on_entity_exit(entity)
        
        # Close the door if no one is inside
        if not self.entities_inside:
            self.is_door_open = False
    
    def on_interact(self, entity):
        """Called when an entity interacts with this house"""
        # Show information about who's inside
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
            if self.entities_inside:
                message = f"This house has {len(self.entities_inside)} occupants."
            else:
                message = "This house is empty."
            SimpleGameEngine.instance.ui.add_text_bubble(message, entity, duration=2.0)
    
    def update(self):
        """Update the house state"""
        # Update door appearance based on open/closed state
        door = self.tiles.get((1, 1))
        if door:
            if self.is_door_open and "house_door_open" in IMAGES:
                door.custom_texture = IMAGES["house_door_open"]
            elif not self.is_door_open and "house_door_closed" in IMAGES:
                door.custom_texture = IMAGES["house_door_closed"]
            else:
                # Fallback to colors if images not available
                if self.is_door_open:
                    door.custom_color = (160, 120, 80)  # Lighter brown for open door
                else:
                    door.custom_color = (120, 81, 45)  # Dark brown for closed door


class EntityTileManager:
    """Manages all entity tiles in the world"""
    
    def __init__(self, world_map):
        """Initialize the entity tile manager"""
        self.world_map = world_map
        self.entity_tiles = []  # List of all entity tiles
        self.entity_tile_map = {}  # Maps grid positions to entity tiles
    
    def add_entity_tile(self, entity_tile):
        """Add an entity tile to the world"""
        self.entity_tiles.append(entity_tile)
        
        # Register all positions occupied by this entity tile
        for pos in entity_tile.get_all_positions():
            self.entity_tile_map[pos] = entity_tile
        
        return entity_tile
    
    def remove_entity_tile(self, entity_tile):
        """Remove an entity tile from the world"""
        if entity_tile in self.entity_tiles:
            self.entity_tiles.remove(entity_tile)
            
            # Unregister all positions
            for pos in entity_tile.get_all_positions():
                if pos in self.entity_tile_map:
                    del self.entity_tile_map[pos]
    
    def get_entity_tile_at(self, x, y):
        """Get the entity tile at the specified grid position"""
        return self.entity_tile_map.get((x, y))
    
    def get_component_at(self, x, y):
        """Get the tile component at the specified grid position"""
        entity_tile = self.get_entity_tile_at(x, y)
        if entity_tile:
            return entity_tile.get_component_at(x, y)
        return None
    
    def handle_entity_movement(self, entity):
        """Handle entity movement in relation to entity tiles"""
        if hasattr(entity, 'grid_x') and hasattr(entity, 'grid_y'):
            # Check if entity is entering an entity tile
            entity_tile = self.get_entity_tile_at(entity.grid_x, entity.grid_y)
            if entity_tile:
                # Get the specific component being entered
                component_x = entity.grid_x - entity_tile.base_x
                component_y = entity.grid_y - entity_tile.base_y
                entity_tile.on_entity_enter(entity, component_x, component_y)
            
            # Check if entity is exiting an entity tile
            # We need to track the previous position for this
            if hasattr(entity, 'previous_grid_x') and hasattr(entity, 'previous_grid_y'):
                prev_entity_tile = self.get_entity_tile_at(entity.previous_grid_x, entity.previous_grid_y)
                if prev_entity_tile and prev_entity_tile != entity_tile:
                    prev_entity_tile.on_entity_exit(entity)
    
    def handle_entity_interaction(self, entity, target_x, target_y):
        """Handle entity interaction with entity tiles"""
        entity_tile = self.get_entity_tile_at(target_x, target_y)
        if entity_tile:
            entity_tile.on_interact(entity)
            return True
        return False
    
    def update(self):
        """Update all entity tiles"""
        for entity_tile in self.entity_tiles:
            entity_tile.update()
    
    def render(self, screen, camera):
        """Render all entity tiles"""
        # Debug output to confirm entity tiles exist
        if not self.entity_tiles:
            return
            
        # First render opaque entity tiles
        for entity_tile in self.entity_tiles:
            if entity_tile.opacity >= 1.0:
                entity_tile.render(screen, camera)
        
        # Then render transparent entity tiles (on top)
        for entity_tile in self.entity_tiles:
            if entity_tile.opacity < 1.0:
                entity_tile.render(screen, camera)

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
                # Load the image
                img = pygame.image.load(full_path).convert_alpha()
                
                # For house, ensure it's at least 32x32 (2x2 tiles)
                if key == "house":
                    img_width, img_height = img.get_size()
                    if img_width < 32 or img_height < 32:
                        print(f"Warning: House image is too small ({img_width}x{img_height}), resizing to 32x32")
                        # Create a larger surface and blit the original image onto it
                        new_img = pygame.Surface((32, 32), pygame.SRCALPHA)
                        new_img.fill((0, 0, 0, 0))  # Transparent
                        
                        # Blit the original image in the center
                        x_offset = (32 - img_width) // 2
                        y_offset = (32 - img_height) // 2
                        new_img.blit(img, (x_offset, y_offset))
                        img = new_img
                
                IMAGES[key] = img
                print(f"Loaded entity image: {key} from {full_path}")
            else:
                print(f"Warning: Entity image file not found: {full_path}")
                # Create a placeholder image
                if key == "house":
                    # For house, create a 32x32 placeholder (2x2 tiles)
                    placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
                else:
                    placeholder = pygame.Surface((Tile.SIZE, Tile.SIZE), pygame.SRCALPHA)
                placeholder.fill((255, 0, 255, 128))  # Magenta semi-transparent
                IMAGES[key] = placeholder
        except Exception as e:
            print(f"Error loading entity image {key}: {e}")
            # Create a placeholder image
            if key == "house":
                # For house, create a 32x32 placeholder (2x2 tiles)
                placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
            else:
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
    
    # Get texture dimensions
    texture_width, texture_height = texture.get_size()
    
    # Check if the texture is large enough for the entire entity
    if texture_width >= (entity_width * Tile.SIZE) and texture_height >= (entity_height * Tile.SIZE):
        # The texture covers the whole entity, extract just this component's part
        src_rect = pygame.Rect(src_x, src_y, src_width, src_height)
        component_texture = texture.subsurface(src_rect)
    else:
        # The texture is not properly sized for the entire entity
        # Try to handle it gracefully by using the whole texture for each component
        
        # If the texture is at least as large as a single tile, use it directly
        if texture_width >= Tile.SIZE and texture_height >= Tile.SIZE:
            component_texture = texture
        else:
            # Create a placeholder texture
            component_texture = pygame.Surface((Tile.SIZE, Tile.SIZE), pygame.SRCALPHA)
            component_texture.fill((255, 0, 255, 128))  # Magenta semi-transparent
            
        print(f"Warning: Texture size mismatch. Expected at least {entity_width*Tile.SIZE}x{entity_height*Tile.SIZE}, got {texture_width}x{texture_height}. Using simplified rendering.")
    
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
        
        # NEW: Track if this tile was constructed by a player
        self.is_constructed = False
        self.construction_time = None
        self.constructed_by = None  # Entity ID of who constructed it
        
        # Create the component tiles
        self._create_component_tiles()
    
    def mark_as_constructed(self, constructed_by_entity_id=None):
        """Mark this entity tile as constructed by a player"""
        import time
        self.is_constructed = True
        self.construction_time = time.time()
        self.constructed_by = constructed_by_entity_id
        print(f"DEBUG: Marked {self.tile_type} at ({self.base_x}, {self.base_y}) as constructed")
    

        
    
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
    
    def get_save_data(self):
        """Get data to save to cache"""
        base_data = {
            "opacity": self.opacity,
            "is_active": self.is_active,
            "entities_inside_count": len(self.entities_inside) if isinstance(self.entities_inside, list) else 0
        }
        
        # Add construction data
        if self.is_constructed:
            base_data.update({
                "is_constructed": self.is_constructed,
                "construction_time": self.construction_time,
                "constructed_by": self.constructed_by
            })
        
        return base_data
    
    def load_save_data(self, data):
        """Load data from cache"""
        self.opacity = data.get("opacity", 1.0)
        self.is_active = data.get("is_active", True)
        # Ensure entities_inside is always a list
        self.entities_inside = []
        
        # Load construction data
        self.is_constructed = data.get("is_constructed", False)
        self.construction_time = data.get("construction_time")
        self.constructed_by = data.get("constructed_by")
        
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
        self.entities_in_trunk = []  # Track entities specifically in the trunk area
    
    def get_save_data(self):
        """Get data to save to cache"""
        data = super().get_save_data()
        data.update({
            "entities_in_trunk_count": len(self.entities_in_trunk) if isinstance(self.entities_in_trunk, list) else 0
        })
        return data
    
    def load_save_data(self, data):
        """Load data from cache"""
        super().load_save_data(data)
        # Ensure entities_in_trunk is always a list
        self.entities_in_trunk = []
    
    def _create_component_tiles(self):
        """Create the tree components: trunk and leaves"""
        # Create a single component for the whole tree
        tree_component = TileComponent(self, 0, 0, "tree")
        tree_component.walkable = True  # Can walk behind top of tree
        
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
        trunk.walkable = False
        # Use the same tree image for the trunk
        if "tree" in IMAGES:
            trunk.custom_texture = IMAGES["tree"]
        else:
            trunk.custom_color = (0, 100, 0)  # Dark green
        
        # Add trunk to the tile dictionary
        self.tiles[(0, 1)] = trunk
    
    def on_entity_enter(self, entity, component_x, component_y):
        """Called when an entity enters this tree"""
        # Add entity to the list if not already there
        if entity not in self.entities_inside:
            self.entities_inside.append(entity)
        
        # If entity is behind the tree (at the trunk), make the tree semi-transparent
        if component_y == 1:  # Trunk component
            # Add entity to trunk tracking list
            if entity not in self.entities_in_trunk:
                self.entities_in_trunk.append(entity)
                self.opacity = 0.5
                print(f"Entity entered tree trunk, opacity set to 0.5, {len(self.entities_in_trunk)} entities in trunk")
    
    def on_entity_exit(self, entity):
        """Called when an entity exits this tree"""
        # Remove entity from the lists
        if entity in self.entities_inside:
            self.entities_inside.remove(entity)
        
        if entity in self.entities_in_trunk:
            self.entities_in_trunk.remove(entity)
            print(f"Entity exited tree trunk, {len(self.entities_in_trunk)} entities remain in trunk")
            
            # Restore opacity if no entities are in the trunk
            if not self.entities_in_trunk:
                self.opacity = 1.0
                print(f"No entities in tree trunk, opacity restored to 1.0")


class HouseEntityTile(EntityTile):
    """A house entity tile that spans 2x2 tiles"""
    
    def __init__(self, base_x, base_y):
        """Initialize a house entity tile"""
        super().__init__(base_x, base_y, width=2, height=2, tile_type="house")
        self.door_position = (base_x, base_y + 1)  # Bottom-left is the door
        self.is_door_open = False
        self.max_occupants = 4
        
        # Use the house texture for the entire entity
        self.texture = IMAGES.get("house")
    
    def get_save_data(self):
        """Get data to save to cache"""
        data = super().get_save_data()
        data.update({
            "is_door_open": self.is_door_open,
            "max_occupants": self.max_occupants,
            "door_position": self.door_position
        })
        return data
    
    def load_save_data(self, data):
        """Load data from cache"""
        super().load_save_data(data)
        self.is_door_open = data.get("is_door_open", False)
        self.max_occupants = data.get("max_occupants", 4)
        self.door_position = tuple(data.get("door_position", (self.base_x, self.base_y + 1)))
    
    def _create_component_tiles(self):
        """Create the house components: walls, roof, door"""
        # Use the house image if available
        house_texture = IMAGES.get("house")
        
        # Top-left component (main house structure)
        top_left = TileComponent(self, 0, 0, "house_top_left")
        top_left.walkable = True
        top_left.custom_texture = house_texture
        
        # Top-right component
        top_right = TileComponent(self, 1, 0, "house_top_right")
        top_right.walkable = True
        top_right.custom_texture = house_texture
        
        # Bottom-left component (wall)
        bottom_left = TileComponent(self, 0, 1, "house_bottom_left")
        bottom_left.walkable = False
        bottom_left.custom_texture = house_texture
        
        # Bottom-right component (door)
        door = TileComponent(self, 1, 1, "house_door")
        door.walkable = False 
        door.custom_texture = house_texture
        
        # Add all components to the tile dictionary
        self.tiles[(0, 0)] = top_left
        self.tiles[(1, 0)] = top_right
        self.tiles[(0, 1)] = bottom_left
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
        from engine.core.simple_game_engine import SimpleGameEngine
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
            # First, ensure the door component uses the house texture for the structure
            if "house" in IMAGES:
                door.custom_texture = IMAGES["house"]
            
            # Then, handle the door state (open/closed) with a separate overlay or color change
            if self.is_door_open:
                if "house_door_open" in IMAGES:
                    # We could overlay the door texture here if needed
                    pass
                else:
                    # Use a lighter color to indicate open door
                    door.custom_color = (160, 120, 80)  # Lighter brown for open door
            else:
                if "house_door_closed" in IMAGES:
                    # We could overlay the door texture here if needed
                    pass
                else:
                    # Use a darker color to indicate closed door
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
        
        # Only save to world cache if we're not loading from cache
        if (hasattr(self.world_map, 'world_cache') and 
            self.world_map.world_cache and 
            not getattr(self.world_map, '_loading_from_cache', False)):
            save_data = entity_tile.get_save_data()
            self.world_map.world_cache.save_entity_tile(
                entity_tile.base_x, entity_tile.base_y, 
                entity_tile.tile_type, save_data
            )
        
        return entity_tile


    
    def remove_entity_tile(self, entity_tile):
        """Remove an entity tile from the world"""
        if entity_tile in self.entity_tiles:
            self.entity_tiles.remove(entity_tile)
            
            # Unregister all positions
            for pos in entity_tile.get_all_positions():
                if pos in self.entity_tile_map:
                    del self.entity_tile_map[pos]
            
            # Mark as removed in world cache if available
            if hasattr(self.world_map, 'world_cache') and self.world_map.world_cache:
                self.world_map.world_cache.remove_entity_tile(
                    entity_tile.base_x, entity_tile.base_y
                )
    
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
        if not hasattr(entity, 'grid_x') or not hasattr(entity, 'grid_y'):
            return
            
        # Get current position
        current_x, current_y = entity.grid_x, entity.grid_y
        
        # Get previous position (default to current if not available)
        prev_x = getattr(entity, 'previous_grid_x', current_x)
        prev_y = getattr(entity, 'previous_grid_y', current_y)
        
        # Get current and previous entity tiles
        current_entity_tile = self.get_entity_tile_at(current_x, current_y)
        prev_entity_tile = self.get_entity_tile_at(prev_x, prev_y)
        
        # If entity hasn't moved, nothing to do
        if current_x == prev_x and current_y == prev_y:
            return
            
        # Case 1: Entity has entered a new entity tile
        if current_entity_tile and current_entity_tile != prev_entity_tile:
            component_x = current_x - current_entity_tile.base_x
            component_y = current_y - current_entity_tile.base_y
            current_entity_tile.on_entity_enter(entity, component_x, component_y)
            print(f"Entity entered new entity tile at ({current_entity_tile.base_x}, {current_entity_tile.base_y})")
        
        # Case 2: Entity has exited an entity tile
        if prev_entity_tile and prev_entity_tile != current_entity_tile:
            prev_entity_tile.on_entity_exit(entity)
            print(f"Entity exited entity tile at ({prev_entity_tile.base_x}, {prev_entity_tile.base_y})")
        
        # Case 3: Entity has moved within the same entity tile
        if current_entity_tile and prev_entity_tile and current_entity_tile == prev_entity_tile:
            # Check if the component has changed
            prev_component_x = prev_x - prev_entity_tile.base_x
            prev_component_y = prev_y - prev_entity_tile.base_y
            current_component_x = current_x - current_entity_tile.base_x
            current_component_y = current_y - current_entity_tile.base_y
            
            if prev_component_x != current_component_x or prev_component_y != current_component_y:
                # Special handling for TreeEntityTile
                if isinstance(current_entity_tile, TreeEntityTile):
                    # If moving from trunk to leaves or out of the tree
                    if prev_component_y == 1 and current_component_y != 1:
                        if entity in current_entity_tile.entities_in_trunk:
                            current_entity_tile.entities_in_trunk.remove(entity)
                            print(f"Entity moved from trunk to leaves, {len(current_entity_tile.entities_in_trunk)} entities remain in trunk")
                            
                            # Update opacity if needed
                            if not current_entity_tile.entities_in_trunk:
                                current_entity_tile.opacity = 1.0
                                print(f"No entities in tree trunk, opacity restored to 1.0")
                    
                    # If moving from leaves to trunk
                    elif current_component_y == 1:
                        if entity not in current_entity_tile.entities_in_trunk:
                            current_entity_tile.entities_in_trunk.append(entity)
                            current_entity_tile.opacity = 0.5
                            print(f"Entity moved from leaves to trunk, opacity set to 0.5")
                else:
                    # For other entity tiles, just call on_entity_enter with new component
                    current_entity_tile.on_entity_enter(entity, current_component_x, current_component_y)

                    
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
            
            # Save updated state to cache periodically
            if hasattr(self.world_map, 'world_cache') and self.world_map.world_cache:
                # Save every 30 seconds or when significant changes occur
                import time
                current_time = time.time()
                if not hasattr(entity_tile, '_last_cache_save'):
                    entity_tile._last_cache_save = current_time
                
                if current_time - entity_tile._last_cache_save > 30:  # 30 seconds
                    save_data = entity_tile.get_save_data()
                    self.world_map.world_cache.save_entity_tile(
                        entity_tile.base_x, entity_tile.base_y, 
                        entity_tile.tile_type, save_data
                    )
                    entity_tile._last_cache_save = current_time
    
    
    def render(self, screen, camera):
        """Render all entity tiles - DEPRECATED: Now handled by main game engine"""
        # This method is now deprecated and should not be called directly
        # Entity tiles are rendered through the main game engine's depth sorting system
        print("WARNING: EntityTileManager.render() called directly - this is deprecated")
        print("Entity tiles should be rendered through the main game engine's depth sorting")
        
        # For backward compatibility, still provide the rendering
        self._render_entity_tiles(screen, camera)
    
    def _render_entity_tiles(self, screen, camera):
        """Internal method to render entity tiles"""
        # Get screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Sort entity tiles by their bottom Y coordinate for proper depth
        sorted_tiles = sorted(self.entity_tiles, key=lambda tile: tile.base_y + tile.height - 1)
        
        for entity_tile in sorted_tiles:
            # Check if entity tile is visible on screen
            world_x = entity_tile.base_x * Tile.SIZE
            world_y = entity_tile.base_y * Tile.SIZE
            world_width = entity_tile.width * Tile.SIZE
            world_height = entity_tile.height * Tile.SIZE
            
            # Apply camera transformation to check visibility
            screen_x, screen_y, screen_width_tile, screen_height_tile = camera.apply(
                world_x, world_y, world_width, world_height
            )
            
            # Only render if on screen
            if (screen_x + screen_width_tile > 0 and screen_x < screen_width and
                screen_y + screen_height_tile > 0 and screen_y < screen_height):
                entity_tile.render(screen, camera)
    
    def get_entity_tiles_for_depth_sorting(self):
        """Get entity tiles prepared for depth sorting"""
        return self.entity_tiles

    def has_entity_at(self, x, y):
        """Check if there's an entity tile at the specified position"""
        return (x, y) in self.entity_tile_map

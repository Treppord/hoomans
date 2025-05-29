"""
Custom entity tile renderer for the map editor
Handles proper rendering of entity tiles with correct texture sizing
"""

import pygame
import os
from world.tile import Tile

class MapEditorEntityRenderer:
    """Custom renderer for entity tiles in the map editor"""
    
    def __init__(self):
        """Initialize the entity renderer"""
        self.entity_textures = {}
        self.load_entity_textures()
    
    def load_entity_textures(self):
        """Load entity textures with proper sizing for map editor"""
        # Get the path to the assets directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assets_path = os.path.join(project_root, "assets")
        
        # Define texture paths and expected sizes
        texture_configs = {
            "tree": {
                "file": "struct_tree.png",
                "expected_size": (16, 32),  # 1x2 tiles
                "tile_width": 1,
                "tile_height": 2
            },
            "house": {
                "file": "struct_house.png", 
                "expected_size": (32, 32),  # 2x2 tiles
                "tile_width": 2,
                "tile_height": 2
            }
        }
        
        for entity_type, config in texture_configs.items():
            texture_path = os.path.join(assets_path, config["file"])
            
            try:
                if os.path.exists(texture_path):
                    # Load the texture
                    texture = pygame.image.load(texture_path).convert_alpha()
                    texture_width, texture_height = texture.get_size()
                    expected_width, expected_height = config["expected_size"]
                    
                    # Check if texture needs resizing
                    if texture_width != expected_width or texture_height != expected_height:
                        print(f"Map Editor: Resizing {entity_type} texture from {texture_width}x{texture_height} to {expected_width}x{expected_height}")
                        texture = pygame.transform.scale(texture, config["expected_size"])
                    
                    self.entity_textures[entity_type] = {
                        "texture": texture,
                        "tile_width": config["tile_width"],
                        "tile_height": config["tile_height"]
                    }
                    print(f"Map Editor: Loaded {entity_type} texture ({expected_width}x{expected_height})")
                else:
                    print(f"Map Editor: Creating placeholder for {entity_type}")
                    self._create_placeholder_texture(entity_type, config)
                    
            except Exception as e:
                print(f"Map Editor: Error loading {entity_type} texture: {e}")
                self._create_placeholder_texture(entity_type, config)
    
    def _create_placeholder_texture(self, entity_type, config):
        """Create a placeholder texture for an entity type"""
        width, height = config["expected_size"]
        texture = pygame.Surface((width, height), pygame.SRCALPHA)
        
        if entity_type == "tree":
            # Draw a simple tree
            # Trunk (bottom half)
            trunk_rect = pygame.Rect(6, height - 8, 4, 8)
            pygame.draw.rect(texture, (101, 67, 33), trunk_rect)
            
            # Leaves (top part)
            pygame.draw.circle(texture, (0, 120, 0), (8, 8), 6)
            
        elif entity_type == "house":
            # Draw a simple house
            # Main structure
            house_rect = pygame.Rect(2, 8, width - 4, height - 10)
            pygame.draw.rect(texture, (139, 69, 19), house_rect)
            
            # Roof
            roof_points = [
                (width // 2, 2),
                (2, 8),
                (width - 2, 8)
            ]
            pygame.draw.polygon(texture, (101, 67, 33), roof_points)
            
            # Door
            door_rect = pygame.Rect(width - 8, height - 8, 6, 8)
            pygame.draw.rect(texture, (80, 50, 20), door_rect)
        
        else:
            # Generic placeholder
            pygame.draw.rect(texture, (255, 0, 255), (0, 0, width, height))
        
        self.entity_textures[entity_type] = {
            "texture": texture,
            "tile_width": config["tile_width"],
            "tile_height": config["tile_height"]
        }
    
    def render_entity_tile(self, screen, entity_tile, camera):
        """Render an entity tile using the map editor camera"""
        entity_type = entity_tile.tile_type
        
        if entity_type not in self.entity_textures:
            print(f"Map Editor: No texture for entity type: {entity_type}")
            return
        
        texture_data = self.entity_textures[entity_type]
        texture = texture_data["texture"]
        tile_width = texture_data["tile_width"]
        tile_height = texture_data["tile_height"]
        
        # Calculate world position and size
        world_x = entity_tile.base_x * Tile.SIZE
        world_y = entity_tile.base_y * Tile.SIZE
        world_width = tile_width * Tile.SIZE
        world_height = tile_height * Tile.SIZE
        
        # Apply camera transformation
        screen_x, screen_y, screen_width, screen_height = camera.apply(
            world_x, world_y, world_width, world_height
        )
        
        # Scale texture to screen size
        if screen_width != texture.get_width() or screen_height != texture.get_height():
            scaled_texture = pygame.transform.scale(texture, (int(screen_width), int(screen_height)))
        else:
            scaled_texture = texture
        
        # Apply opacity if needed
        if hasattr(entity_tile, 'opacity') and entity_tile.opacity < 1.0:
            scaled_texture = scaled_texture.copy()
            scaled_texture.set_alpha(int(255 * entity_tile.opacity))
        
        # Draw the texture
        screen.blit(scaled_texture, (int(screen_x), int(screen_y)))
    
    def get_entity_texture(self, entity_type):
        """Get the texture for a specific entity type"""
        return self.entity_textures.get(entity_type, {}).get("texture")
    
    def get_entity_size(self, entity_type):
        """Get the tile size for a specific entity type"""
        if entity_type in self.entity_textures:
            data = self.entity_textures[entity_type]
            return data["tile_width"], data["tile_height"]
        return 1, 1
"""
World Item System - Items that exist in the world and can be picked up
"""
import pygame
import math
import random
from typing import Dict, List, Optional, Tuple
from entities.items.item_factory import ItemFactory
from entities.items.item_base import Item

class WorldItem:
    """Represents an item that exists in the world at a specific location"""
    
    def __init__(self, item: Item, x: int, y: int, world_x: float = None, world_y: float = None):
        """
        Initialize a world item
        
        Args:
            item: The item instance
            x: Grid X coordinate
            y: Grid Y coordinate
            world_x: Precise world X coordinate (for sub-tile positioning)
            world_y: Precise world Y coordinate (for sub-tile positioning)
        """
        self.item = item
        self.grid_x = x
        self.grid_y = y
        self.world_x = world_x if world_x is not None else x * 16 + 8
        self.world_y = world_y if world_y is not None else y * 16 + 8
        
        # Visual properties
        self.bob_offset = 0.0
        self.bob_speed = 2.0
        self.rotation = 0.0
        self.scale = 1.0
        
        # Pickup properties
        self.pickup_radius = 12  # Pixels
        self.can_be_picked_up = True
        self.spawn_time = pygame.time.get_ticks()
        self.pickup_delay = 500  # Milliseconds before item can be picked up
        
        # Animation properties
        self.highlight = False
        self.highlight_timer = 0
        
    def update(self, delta_time: float = 1/60):
        """Update the world item (animations, etc.)"""
        current_time = pygame.time.get_ticks()
        
        # Update bobbing animation
        self.bob_offset = 2 * math.sin(current_time * 0.003 * self.bob_speed)
        
        # Update rotation
        self.rotation += 30 * delta_time  # 30 degrees per second
        if self.rotation >= 360:
            self.rotation -= 360
            
        # Update highlight
        if self.highlight:
            self.highlight_timer += delta_time
            if self.highlight_timer > 2.0:  # Highlight for 2 seconds
                self.highlight = False
                self.highlight_timer = 0
    
    def can_pickup(self) -> bool:
        """Check if this item can be picked up"""
        if not self.can_be_picked_up:
            return False
            
        # Check pickup delay
        current_time = pygame.time.get_ticks()
        return current_time - self.spawn_time >= self.pickup_delay
    
    def is_in_pickup_range(self, entity_x: float, entity_y: float) -> bool:
        """Check if an entity is within pickup range"""
        if not self.can_pickup():
            return False
            
        # Calculate distance
        dx = entity_x - self.world_x
        dy = entity_y - self.world_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        return distance <= self.pickup_radius
    
    def render(self, screen, camera):
        """Render the world item with proper scaling based on camera zoom"""
        # Calculate screen position using the tile size
        screen_x, screen_y, width, height = camera.apply(
            self.world_x - 8, self.world_y - 8 + self.bob_offset, 16, 16
        )
        
        # Skip rendering if off-screen
        if (screen_x + width < 0 or screen_x > screen.get_width() or
            screen_y + height < 0 or screen_y > screen.get_height()):
            return
        
        # The width and height from camera.apply already include zoom scaling
        # So we use them directly for consistent tile-relative sizing
        item_width = int(width * 0.8)  # Make item slightly smaller than tile (80% of tile size)
        item_height = int(height * 0.8)
        
        # Center the item within the tile
        item_x = screen_x + (width - item_width) // 2
        item_y = screen_y + (height - item_height) // 2
        
        # Ensure item icon is loaded
        if self.item.icon is None:
            self.item.ensure_icon_loaded()
        
        if self.item.icon:
            # Create a copy of the icon for transformations
            icon = self.item.icon.copy()
            
            # Apply rotation if enabled
            if self.rotation != 0:
                icon = pygame.transform.rotate(icon, self.rotation)
            
            # Scale the icon to the calculated size (this handles zoom automatically)
            if icon.get_width() != item_width or icon.get_height() != item_height:
                icon = pygame.transform.scale(icon, (item_width, item_height))
            
            # Apply additional scaling if set
            if self.scale != 1.0:
                scaled_width = int(item_width * self.scale)
                scaled_height = int(item_height * self.scale)
                icon = pygame.transform.scale(icon, (scaled_width, scaled_height))
                # Adjust position for additional scaling
                item_x -= (scaled_width - item_width) // 2
                item_y -= (scaled_height - item_height) // 2
                item_width, item_height = scaled_width, scaled_height
            
            # Draw shadow (only if item is large enough to see shadow)
            if item_width > 8 and item_height > 8:
                shadow_offset = max(1, int(2 * camera.zoom))
                shadow_surface = pygame.Surface((item_width, item_height), pygame.SRCALPHA)
                shadow_surface.fill((0, 0, 0, 60))
                screen.blit(shadow_surface, (item_x + shadow_offset, item_y + shadow_offset))
            
            # Draw the item icon
            screen.blit(icon, (item_x, item_y))
            
            # Draw highlight effect if highlighted
            if self.highlight:
                highlight_alpha = int(128 + 127 * math.sin(self.highlight_timer * 8))
                highlight_padding = max(2, int(4 * camera.zoom))
                highlight_surface = pygame.Surface(
                    (item_width + highlight_padding * 2, item_height + highlight_padding * 2), 
                    pygame.SRCALPHA
                )
                highlight_surface.fill((255, 255, 0, highlight_alpha))
                screen.blit(highlight_surface, (item_x - highlight_padding, item_y - highlight_padding))
            
            # Draw quantity if more than 1 (only if item is large enough)
            if self.item.quantity > 1 and item_width > 12:
                # Scale font size based on zoom
                font_size = max(12, int(16 * camera.zoom))
                font = pygame.font.Font(None, font_size)
                text = font.render(str(self.item.quantity), True, (255, 255, 255))
                
                # Position text in bottom-right corner of item
                text_rect = text.get_rect(
                    bottomright=(item_x + item_width - 1, item_y + item_height - 1)
                )
                
                # Draw text shadow (only if large enough)
                if font_size > 14:
                    shadow = font.render(str(self.item.quantity), True, (0, 0, 0))
                    shadow_rect = shadow.get_rect(
                        bottomright=(item_x + item_width, item_y + item_height)
                    )
                    screen.blit(shadow, shadow_rect)
                
                # Draw text
                screen.blit(text, text_rect)
        else:
            # If no icon, draw a colored rectangle and item name
            # Use a color based on item type
            item_color = self._get_item_type_color()
            pygame.draw.rect(screen, item_color, (item_x, item_y, item_width, item_height))
            pygame.draw.rect(screen, (0, 0, 0), (item_x, item_y, item_width, item_height), 1)
            
            # Draw item name if large enough
            if item_width > 20 and item_height > 12:
                font_size = max(10, int(12 * camera.zoom))
                font = pygame.font.Font(None, font_size)
                text = font.render(self.item.name[:4], True, (255, 255, 255))
                text_rect = text.get_rect(center=(item_x + item_width // 2, item_y + item_height // 2))
                screen.blit(text, text_rect)

    def _get_item_type_color(self):
        """Get a color based on the item type for fallback rendering"""
        # Determine color based on item class or name
        if hasattr(self.item, '__class__'):
            class_name = self.item.__class__.__name__
            if 'Food' in class_name or 'apple' in self.item.name.lower():
                return (255, 100, 100)  # Red for food
            elif 'Water' in class_name or 'water' in self.item.name.lower():
                return (100, 100, 255)  # Blue for water
            elif 'Tool' in class_name or 'axe' in self.item.name.lower():
                return (150, 150, 150)  # Gray for tools
            elif 'Schematic' in class_name:
                return (255, 255, 100)  # Yellow for schematics
        
        # Default color
        return (200, 200, 200)  # Light gray

    def debug_render_bounds(self, screen, camera):
        """Debug method to render item bounds and pickup radius"""
        # Calculate screen position
        screen_x, screen_y, width, height = camera.apply(
            self.world_x - 8, self.world_y - 8 + self.bob_offset, 16, 16
        )
        
        # Draw item bounds
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y, width, height), 1)
        
        # Draw pickup radius
        pickup_radius_screen = self.pickup_radius * camera.zoom
        pygame.draw.circle(screen, (0, 255, 0), 
                          (int(screen_x + width/2), int(screen_y + height/2)), 
                          int(pickup_radius_screen), 1)
        
        # Draw center point
        pygame.draw.circle(screen, (255, 255, 0), 
                          (int(screen_x + width/2), int(screen_y + height/2)), 2)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "item": self.item.to_dict(),
            "grid_x": self.grid_x,
            "grid_y": self.grid_y,
            "world_x": self.world_x,
            "world_y": self.world_y,
            "spawn_time": self.spawn_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> Optional['WorldItem']:
        """Create from dictionary"""
        item_data = data.get("item")
        if not item_data:
            return None
            
        item = Item.from_dict(item_data)
        if not item:
            return None
            
        world_item = cls(
            item=item,
            x=data.get("grid_x", 0),
            y=data.get("grid_y", 0),
            world_x=data.get("world_x"),
            world_y=data.get("world_y")
        )
        
        world_item.spawn_time = data.get("spawn_time", pygame.time.get_ticks())
        return world_item


class WorldItemManager:
    """Manages all items in the world"""
    
    def __init__(self, world_map):
        """Initialize the world item manager"""
        self.world_map = world_map
        self.items: List[WorldItem] = []
        self.items_by_tile: Dict[Tuple[int, int], List[WorldItem]] = {}
        
    def spawn_item(self, item_id: str, x: int, y: int, quantity: int = 1, 
                   offset_x: float = 0, offset_y: float = 0) -> Optional[WorldItem]:
        """
        Spawn an item in the world
        
        Args:
            item_id: ID of the item to spawn
            x: Grid X coordinate
            y: Grid Y coordinate
            quantity: Number of items to spawn
            offset_x: X offset from tile center (in pixels)
            offset_y: Y offset from tile center (in pixels)
        """
        print(f"DEBUG: Attempting to spawn {quantity}x {item_id} at tile ({x}, {y})")
        
        # Create the item
        item = ItemFactory.create_item(item_id, quantity)
        if not item:
            print(f"ERROR: Failed to create item {item_id}")
            return None
        
        print(f"DEBUG: Successfully created item: {item.name}")
        
        # Check if the tile is valid
        if not (0 <= x < self.world_map.width and 0 <= y < self.world_map.height):
            print(f"ERROR: Invalid spawn coordinates: ({x}, {y}) - Map size: {self.world_map.width}x{self.world_map.height}")
            return None
        
        # Calculate world position
        world_x = x * 16 + 8 + offset_x
        world_y = y * 16 + 8 + offset_y
        
        print(f"DEBUG: World position: ({world_x}, {world_y})")
        
        # Create world item
        world_item = WorldItem(item, x, y, world_x, world_y)
        
        # Add to lists
        self.items.append(world_item)
        
        # Add to tile index
        tile_key = (x, y)
        if tile_key not in self.items_by_tile:
            self.items_by_tile[tile_key] = []
        self.items_by_tile[tile_key].append(world_item)
        
        print(f"SUCCESS: Spawned {quantity}x {item_id} at ({x}, {y}). Total items in world: {len(self.items)}")
        return world_item
    
    def spawn_item_at_position(self, item_id: str, world_x: float, world_y: float, 
                              quantity: int = 1) -> Optional[WorldItem]:
        """
        Spawn an item at a specific world position
        
        Args:
            item_id: ID of the item to spawn
            world_x: World X coordinate in pixels
            world_y: World Y coordinate in pixels
            quantity: Number of items to spawn
        """
        # Convert to grid coordinates
        grid_x = int(world_x // 16)
        grid_y = int(world_y // 16)
        
        # Calculate offset from tile center
        offset_x = world_x - (grid_x * 16 + 8)
        offset_y = world_y - (grid_y * 16 + 8)
        
        return self.spawn_item(item_id, grid_x, grid_y, quantity, offset_x, offset_y)
    
    def remove_item(self, world_item: WorldItem):
        """Remove an item from the world"""
        if world_item in self.items:
            self.items.remove(world_item)
            
            # Remove from tile index
            tile_key = (world_item.grid_x, world_item.grid_y)
            if tile_key in self.items_by_tile and world_item in self.items_by_tile[tile_key]:
                self.items_by_tile[tile_key].remove(world_item)
                
                # Clean up empty tile lists
                if not self.items_by_tile[tile_key]:
                    del self.items_by_tile[tile_key]
    
    def get_items_at_tile(self, x: int, y: int) -> List[WorldItem]:
        """Get all items at a specific tile"""
        return self.items_by_tile.get((x, y), [])
    
    def get_items_in_range(self, center_x: float, center_y: float, radius: float) -> List[WorldItem]:
        """Get all items within a certain range of a position"""
        items_in_range = []
        
        for item in self.items:
            dx = item.world_x - center_x
            dy = item.world_y - center_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance <= radius:
                items_in_range.append(item)
        
        return items_in_range
    
    def try_pickup_items(self, entity) -> List[Item]:
        """
        Try to pick up items near an entity
        
        Args:
            entity: The entity trying to pick up items
            
        Returns:
            List of items that were picked up
        """
        if not hasattr(entity, 'inventory'):
            return []
        
        # Calculate entity position
        entity_x = entity.grid_x * 16 + 8
        entity_y = entity.grid_y * 16 + 8
        
        # Find items in pickup range
        items_to_pickup = []
        for item in self.items:
            if item.is_in_pickup_range(entity_x, entity_y):
                items_to_pickup.append(item)
        
        # Try to pick up each item
        picked_up_items = []
        for world_item in items_to_pickup:
            # Try to add to inventory
            if entity.inventory.add_item(world_item.item):
                picked_up_items.append(world_item.item)
                self.remove_item(world_item)
                
                # Show pickup message
                entity_type = "Player" if getattr(entity, 'controllable', False) else "NPC"
                print(f"{entity_type} picked up {world_item.item.quantity}x {world_item.item.name}")
                
                # Add visual effect
                world_item.highlight = True
        
        return picked_up_items
    
    def update(self, delta_time: float = 1/60):
        """Update all world items"""
        for item in self.items:
            item.update(delta_time)
            
            # Update pickup radius based on current zoom if needed
            # This ensures pickup works consistently at different zoom levels
            base_pickup_radius = 12
            # Keep pickup radius constant in world coordinates, not screen coordinates
            item.pickup_radius = base_pickup_radius
    
    def render(self, screen, camera):
        """Render all world items with proper culling"""
        if not self.items:
            return
        
        # Only render items that are potentially visible
        visible_items = []
        for item in self.items:
            if camera.is_point_visible(item.world_x, item.world_y, margin=32):
                visible_items.append(item)
        
        if not visible_items:
            return
        
        # Sort visible items by Y position for proper depth sorting
        sorted_items = sorted(visible_items, key=lambda item: item.world_y)
        
        # Render each visible item
        for item in sorted_items:
            item.render(screen, camera)
    
    def debug_render_all_bounds(self, screen, camera):
        """Debug method to render bounds for all items"""
        for item in self.items:
            item.debug_render_bounds(screen, camera)
    
    def clear_all_items(self):
        """Remove all items from the world"""
        self.items.clear()
        self.items_by_tile.clear()
    
    def save_to_cache(self, world_cache):
        """Save all world items to cache"""
        if not world_cache:
            return
            
        items_data = []
        for item in self.items:
            items_data.append(item.to_dict())
        
        world_cache.save_world_items(items_data)
    
    def load_from_cache(self, world_cache):
        """Load world items from cache"""
        if not world_cache:
            return
            
        items_data = world_cache.get_world_items()
        if not items_data:
            return
        
        # Clear existing items
        self.clear_all_items()
        
        # Load items from cache
        for item_data in items_data:
            world_item = WorldItem.from_dict(item_data)
            if world_item:
                self.items.append(world_item)
                
                # Add to tile index
                tile_key = (world_item.grid_x, world_item.grid_y)
                if tile_key not in self.items_by_tile:
                    self.items_by_tile[tile_key] = []
                self.items_by_tile[tile_key].append(world_item)
        
        print(f"Loaded {len(self.items)} world items from cache")

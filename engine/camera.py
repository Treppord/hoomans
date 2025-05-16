import pygame

class Camera:
    """Camera system for handling zooming and panning"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 2.0
        self.drag_start = None
        self.dragging = False
        self.follow_target = None
    
    def update_screen_size(self, width, height):
        """Update camera parameters when screen size changes"""
        # Store old center point in world coordinates
        old_center_x = (self.width / 2) / self.zoom + self.offset_x
        old_center_y = (self.height / 2) / self.zoom + self.offset_y
        
        # Update dimensions
        self.width = width
        self.height = height
        
        # Adjust offset to keep the same center point
        self.offset_x = old_center_x - (self.width / 2) / self.zoom
        self.offset_y = old_center_y - (self.height / 2) / self.zoom
        
        # If we have a follow target, immediately center on it
        if self.follow_target:
            self.center_on_target()

        
    def apply(self, x, y, width, height):
        """Apply camera transformations to a rectangle"""
        # Apply zoom and offset
        scaled_x = (x - self.offset_x) * self.zoom
        scaled_y = (y - self.offset_y) * self.zoom
        scaled_width = width * self.zoom
        scaled_height = height * self.zoom
        
        return (scaled_x, scaled_y, scaled_width, scaled_height)
    
    def reverse_apply(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x / self.zoom) + self.offset_x
        world_y = (screen_y / self.zoom) + self.offset_y
        return (world_x, world_y)
    
    def set_follow_target(self, entity):
        """Set an entity for the camera to follow"""
        self.follow_target = entity
        if entity:
            self.center_on_target()
    
    def center_on_target(self):
        """Center the camera on the follow target"""
        if not self.follow_target:
            return
            
        # Calculate the center position of the target in world coordinates
        target_center_x = self.follow_target.x + (self.follow_target.width / 2)
        target_center_y = self.follow_target.y + (self.follow_target.height / 2)
        
        # Calculate the offset needed to center the target on the screen
        self.offset_x = target_center_x - (self.width / (2 * self.zoom))
        self.offset_y = target_center_y - (self.height / (2 * self.zoom))
    
    def update(self):
        """Update camera position to follow target if set"""
        if self.follow_target and not self.dragging:
            self.center_on_target()
    
    def start_drag(self, x, y):
        """Start dragging the camera"""
        self.drag_start = (x, y)
        self.dragging = True
    
    def update_drag(self, x, y):
        """Update camera position while dragging"""
        if self.dragging and self.drag_start:
            dx = (x - self.drag_start[0]) / self.zoom
            dy = (y - self.drag_start[1]) / self.zoom
            self.offset_x -= dx
            self.offset_y -= dy
            self.drag_start = (x, y)
    
    def stop_drag(self):
        """Stop dragging the camera"""
        self.dragging = False
        self.drag_start = None
        
        # If we have a follow target, immediately center on it when drag ends
        if self.follow_target:
            self.center_on_target()
    
    def zoom_in(self, amount=0.1):
        """Zoom in by the specified amount"""
        old_zoom = self.zoom
        self.zoom = min(self.max_zoom, self.zoom + amount)
        
        # Adjust offset to keep the center point fixed
        if old_zoom != self.zoom:
            center_x = self.width / 2
            center_y = self.height / 2
            
            world_center_x = (center_x / old_zoom) + self.offset_x
            world_center_y = (center_y / old_zoom) + self.offset_y
            
            new_screen_center_x = world_center_x * self.zoom
            new_screen_center_y = world_center_y * self.zoom
            
            self.offset_x += (center_x - new_screen_center_x) / self.zoom
            self.offset_y += (center_y - new_screen_center_y) / self.zoom
    
    def zoom_out(self, amount=0.1):
        """Zoom out by the specified amount"""
        old_zoom = self.zoom
        self.zoom = max(self.min_zoom, self.zoom - amount)
        
        # Adjust offset to keep the center point fixed
        if old_zoom != self.zoom:
            center_x = self.width / 2
            center_y = self.height / 2
            
            world_center_x = (center_x / old_zoom) + self.offset_x
            world_center_y = (center_y / old_zoom) + self.offset_y
            
            new_screen_center_x = world_center_x * self.zoom
            new_screen_center_y = world_center_y * self.zoom
            
            self.offset_x += (center_x - new_screen_center_x) / self.zoom
            self.offset_y += (center_y - new_screen_center_y) / self.zoom
    
    def should_draw_grid(self):
        """Determine if grid lines should be drawn based on zoom level"""
        return self.zoom >= 0.5


    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        # Apply zoom and offset
        screen_x = (world_x - self.offset_x) * self.zoom
        screen_y = (world_y - self.offset_y) * self.zoom
        return (screen_x, screen_y)

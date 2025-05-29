"""
Camera system for the map editor
Handles viewport, zoom, and coordinate transformations
"""

import pygame
from typing import Tuple

class EditorCamera:
    """Camera for the map editor with zoom and pan capabilities"""
    
    def __init__(self, viewport_width: int, viewport_height: int):
        """Initialize the editor camera
        
        Args:
            viewport_width: Width of the viewport in pixels
            viewport_height: Height of the viewport in pixels
        """
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport_rect = pygame.Rect(0, 0, viewport_width, viewport_height)
        
        # Camera position (world coordinates)
        self.x = 0.0
        self.y = 0.0
        
        # Zoom level
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 8.0
        
        # Pan state
        self.is_panning = False
        self.pan_start_pos = (0, 0)
        self.pan_start_camera = (0, 0)
        
        # Movement speed
        self.pan_speed = 1.0
        self.zoom_speed = 0.1
    
    def set_viewport(self, rect: pygame.Rect):
        """Set the viewport rectangle"""
        self.viewport_rect = rect
        self.viewport_width = rect.width
        self.viewport_height = rect.height
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.zoom + self.viewport_rect.x
        screen_y = (world_y - self.y) * self.zoom + self.viewport_rect.y
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - self.viewport_rect.x) / self.zoom + self.x
        world_y = (screen_y - self.viewport_rect.y) / self.zoom + self.y
        return world_x, world_y
    
    def apply(self, world_x: float, world_y: float, width: float, height: float) -> Tuple[float, float, float, float]:
        """Apply camera transformation to a rectangle - compatible with entity tile rendering"""
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        screen_width = width * self.zoom
        screen_height = height * self.zoom
        return screen_x, screen_y, screen_width, screen_height
    
    def reverse_apply(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Reverse camera transformation (screen to world)"""
        return self.screen_to_world(screen_x, screen_y)
    
    def zoom_in(self, factor: float = None):
        """Zoom in by the specified factor"""
        if factor is None:
            factor = 1.0 + self.zoom_speed
        
        old_zoom = self.zoom
        self.zoom = min(self.max_zoom, self.zoom * factor)
        
        # Adjust position to zoom towards center
        if self.zoom != old_zoom:
            center_x = self.viewport_width / 2
            center_y = self.viewport_height / 2
            world_center_x, world_center_y = self.screen_to_world(center_x, center_y)
            
            # Recalculate position to keep center point stable
            self.x = world_center_x - center_x / self.zoom
            self.y = world_center_y - center_y / self.zoom
    
    def zoom_out(self, factor: float = None):
        """Zoom out by the specified factor"""
        if factor is None:
            factor = 1.0 - self.zoom_speed
        
        old_zoom = self.zoom
        self.zoom = max(self.min_zoom, self.zoom * factor)
        
        # Adjust position to zoom towards center
        if self.zoom != old_zoom:
            center_x = self.viewport_width / 2
            center_y = self.viewport_height / 2
            world_center_x, world_center_y = self.screen_to_world(center_x, center_y)
            
            # Recalculate position to keep center point stable
            self.x = world_center_x - center_x / self.zoom
            self.y = world_center_y - center_y / self.zoom
    
    def zoom_to_point(self, screen_x: float, screen_y: float, zoom_factor: float):
        """Zoom towards a specific screen point"""
        # Get world coordinates of the zoom point
        world_x, world_y = self.screen_to_world(screen_x, screen_y)
        
        # Apply zoom
        old_zoom = self.zoom
        if zoom_factor > 1.0:
            self.zoom = min(self.max_zoom, self.zoom * zoom_factor)
        else:
            self.zoom = max(self.min_zoom, self.zoom * zoom_factor)
        
        # Adjust camera position to keep the zoom point stable
        if self.zoom != old_zoom:
            new_screen_x, new_screen_y = self.world_to_screen(world_x, world_y)
            offset_x = (new_screen_x - screen_x) / self.zoom
            offset_y = (new_screen_y - screen_y) / self.zoom
            self.x += offset_x
            self.y += offset_y
    
    def start_pan(self, screen_x: float, screen_y: float):
        """Start panning from the specified screen position"""
        self.is_panning = True
        self.pan_start_pos = (screen_x, screen_y)
        self.pan_start_camera = (self.x, self.y)
    
    def update_pan(self, screen_x: float, screen_y: float):
        """Update pan based on current mouse position"""
        if not self.is_panning:
            return
        
        # Calculate offset in screen space
        dx = screen_x - self.pan_start_pos[0]
        dy = screen_y - self.pan_start_pos[1]
        
        # Convert to world space and apply
        world_dx = dx / self.zoom
        world_dy = dy / self.zoom
        
        self.x = self.pan_start_camera[0] - world_dx
        self.y = self.pan_start_camera[1] - world_dy
    
    def stop_pan(self):
        """Stop panning"""
        self.is_panning = False
    
    def move(self, dx: float, dy: float):
        """Move the camera by the specified amount in world coordinates"""
        self.x += dx
        self.y += dy
    
    def center_on(self, world_x: float, world_y: float):
        """Center the camera on the specified world coordinates"""
        self.x = world_x - (self.viewport_width / 2) / self.zoom
        self.y = world_y - (self.viewport_height / 2) / self.zoom
    
    def get_visible_bounds(self) -> Tuple[float, float, float, float]:
        """Get the visible world bounds (left, top, right, bottom)"""
        left, top = self.screen_to_world(0, 0)
        right, bottom = self.screen_to_world(self.viewport_width, self.viewport_height)
        return left, top, right, bottom
    
    def should_draw_grid(self) -> bool:
        """Check if the grid should be drawn at current zoom level"""
        return self.zoom >= 0.5  # Only draw grid when zoomed in enough
    
    def handle_event(self, event) -> bool:
        """Handle camera-related events"""
        if event.type == pygame.MOUSEWHEEL:
            # Zoom with mouse wheel
            mouse_pos = pygame.mouse.get_pos()
            # Adjust mouse position relative to viewport
            viewport_mouse_x = mouse_pos[0] - self.viewport_rect.x
            viewport_mouse_y = mouse_pos[1] - self.viewport_rect.y
            
            # Only zoom if mouse is within viewport
            if (0 <= viewport_mouse_x <= self.viewport_width and 
                0 <= viewport_mouse_y <= self.viewport_height):
                
                zoom_factor = 1.1 if event.y > 0 else 0.9
                self.zoom_to_point(viewport_mouse_x, viewport_mouse_y, zoom_factor)
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button
                self.start_pan(event.pos[0] - self.viewport_rect.x, 
                              event.pos[1] - self.viewport_rect.y)
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:  # Middle mouse button
                self.stop_pan()
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_panning:
                self.update_pan(event.pos[0] - self.viewport_rect.x, 
                               event.pos[1] - self.viewport_rect.y)
                return True
        
        elif event.type == pygame.KEYDOWN:
            # Camera movement with arrow keys
            move_speed = 32 / self.zoom  # Adjust speed based on zoom
            
            if event.key == pygame.K_LEFT:
                self.move(-move_speed, 0)
                return True
            elif event.key == pygame.K_RIGHT:
                self.move(move_speed, 0)
                return True
            elif event.key == pygame.K_UP:
                self.move(0, -move_speed)
                return True
            elif event.key == pygame.K_DOWN:
                self.move(0, move_speed)
                return True
            elif event.key == pygame.K_HOME:
                # Reset camera to origin
                self.x = 0
                self.y = 0
                self.zoom = 1.0
                return True
        
        return False

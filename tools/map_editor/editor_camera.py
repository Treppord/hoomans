"""
Camera system for the map editor
Handles panning, zooming, and coordinate transformations
"""

import pygame
import math

class EditorCamera:
    """Camera for the map editor with pan and zoom functionality"""
    
    def __init__(self, screen_width, screen_height):
        """Initialize the editor camera"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Camera position (world coordinates)
        self.x = 0
        self.y = 0
        
        # Zoom level
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 8.0
        
        # Pan state
        self.is_panning = False
        self.pan_start_pos = (0, 0)
        self.pan_start_camera = (0, 0)
        
        # Movement speed
        self.pan_speed = 5.0
        self.zoom_speed = 0.1
        
        # Viewport (can be set to limit rendering area)
        self.viewport = pygame.Rect(0, 0, screen_width, screen_height)
        
        print("Editor camera initialized")
    
    def set_viewport(self, rect):
        """Set the camera viewport"""
        self.viewport = rect
    
    def handle_event(self, event):
        """Handle camera input events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button
                self.is_panning = True
                self.pan_start_pos = event.pos
                self.pan_start_camera = (self.x, self.y)
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.is_panning = False
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_panning:
                dx = event.pos[0] - self.pan_start_pos[0]
                dy = event.pos[1] - self.pan_start_pos[1]
                
                self.x = self.pan_start_camera[0] - dx / self.zoom
                self.y = self.pan_start_camera[1] - dy / self.zoom
                return True
        
        elif event.type == pygame.MOUSEWHEEL:
            # Zoom at mouse position
            if self.viewport.collidepoint(pygame.mouse.get_pos()):
                mouse_pos = pygame.mouse.get_pos()
                world_pos_before = self.screen_to_world(mouse_pos[0], mouse_pos[1])
                
                # Apply zoom
                zoom_factor = 1.1 if event.y > 0 else 0.9
                new_zoom = self.zoom * zoom_factor
                new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
                
                if new_zoom != self.zoom:
                    self.zoom = new_zoom
                    
                    # Adjust camera position to zoom at mouse cursor
                    world_pos_after = self.screen_to_world(mouse_pos[0], mouse_pos[1])
                    self.x += world_pos_before[0] - world_pos_after[0]
                    self.y += world_pos_before[1] - world_pos_after[1]
                
                return True
        
        elif event.type == pygame.KEYDOWN:
            # Keyboard panning
            if event.key == pygame.K_w:
                self.y -= self.pan_speed / self.zoom
                return True
            elif event.key == pygame.K_s:
                self.y += self.pan_speed / self.zoom
                return True
            elif event.key == pygame.K_a:
                self.x -= self.pan_speed / self.zoom
                return True
            elif event.key == pygame.K_d:
                self.x += self.pan_speed / self.zoom
                return True
        
        return False
    
    def update(self):
        """Update camera state"""
        # Handle continuous keyboard input
        keys = pygame.key.get_pressed()
        pan_speed = self.pan_speed / self.zoom
        
        if keys[pygame.K_w]:
            self.y -= pan_speed
        if keys[pygame.K_s]:
            self.y += pan_speed
        if keys[pygame.K_a]:
            self.x -= pan_speed
        if keys[pygame.K_d]:
            self.x += pan_speed
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.zoom + self.viewport.left
        screen_y = (world_y - self.y) * self.zoom + self.viewport.top
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - self.viewport.left) / self.zoom + self.x
        world_y = (screen_y - self.viewport.top) / self.zoom + self.y
        return (world_x, world_y)
    
    def apply(self, world_x, world_y, width, height):
        """Apply camera transformation (compatible with game engine camera)"""
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        screen_width = width * self.zoom
        screen_height = height * self.zoom
        return (screen_x, screen_y, screen_width, screen_height)
    
    def reverse_apply(self, screen_x, screen_y):
        """Reverse camera transformation (compatible with game engine camera)"""
        return self.screen_to_world(screen_x, screen_y)
    
    def should_draw_grid(self):
        """Determine if grid should be drawn based on zoom level"""
        return self.zoom >= 0.5

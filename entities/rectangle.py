import pygame
import os
import math

class Rectangle:
    """Base class for all rectangular entities in the game"""
    
import pygame
import os
import math
import hashlib

class Rectangle:
    """Base class for all rectangular entities in the game"""
    
    def __init__(self, grid_x, grid_y, color=(255, 255, 255), speed=1, controllable=False):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.color = color
        self.speed = speed
        self.controllable = controllable
        
        # For smooth movement
        self.target_grid_x = grid_x
        self.target_grid_y = grid_y
        self.is_moving = False
        
        # For visual interpolation (smooth rendering)
        self.visual_x = float(grid_x)
        self.visual_y = float(grid_y)
        self.move_lerp_factor = 0.2  # Adjust for smoother/faster visual transitions
        
        # For animation
        self.sprite_sheet = None
        self.animation_frames = []
        self.current_frame = 0
        self.animation_speed = 0.1  # Adjust as needed
        self.animation_timer = 0
        self.load_sprite_sheet()
        
        # For CNA data
        self.cna_data = None
        self.cna_file = None
        
        # Add properties for camera compatibility
        self.width = 16
        self.height = 16
        
        # Generate a persistent ID
        self.entity_id = self.generate_persistent_id()
    
    def generate_persistent_id(self):
        """Generate a persistent ID based on entity characteristics"""
        # Create a string with entity properties that should remain consistent
        id_string = f"{self.__class__.__name__}_{self.grid_x}_{self.grid_y}_{self.color}_{self.controllable}"
        
        # If CNA file exists, include it in the ID calculation
        if hasattr(self, 'cna_file') and self.cna_file:
            id_string += f"_{os.path.basename(self.cna_file)}"
        
        # Hash the string to create a consistent ID
        hash_object = hashlib.md5(id_string.encode())
        # Return a formatted binary-like string (first 16 chars of hex digest)
        return f"0b{hash_object.hexdigest()[:16]}"
    
    def get_entity_id(self):
        """Get the persistent entity ID"""
        return self.entity_id

    
    # Add properties for camera compatibility
    @property
    def x(self):
        return self.visual_x * 16  # Use visual position for rendering
    
    @property
    def y(self):
        return self.visual_y * 16  # Use visual position for rendering
    
    def load_sprite_sheet(self):
        """Load the sprite sheet and extract frames"""
        try:
            # Get the path to the sprite sheet
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sprite_path = os.path.join(project_root, "assets", "ai_sheet.png")
            
            # Load the sprite sheet
            self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
            
            # Extract the two frames (each 16x16)
            frame1 = self.sprite_sheet.subsurface((0, 0, 16, 16))
            frame2 = self.sprite_sheet.subsurface((16, 0, 16, 16))
            
            # Store the frames
            self.animation_frames = [frame1, frame2]
            
            print(f"Loaded sprite sheet with {len(self.animation_frames)} frames")
        except Exception as e:
            print(f"Error loading sprite sheet: {e}")
            # Create fallback frames (colored squares)
            self.animation_frames = [
                pygame.Surface((16, 16), pygame.SRCALPHA),
                pygame.Surface((16, 16), pygame.SRCALPHA)
            ]
            for frame in self.animation_frames:
                frame.fill(self.color)
    
    def update_animation(self, delta_time=1/60):
        """Update the animation frame"""
        self.animation_timer += delta_time * 0.25
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
    
    def apply_color_tint(self, frame):
        """Apply color tint to the sprite based on entity color"""
        # Create a copy of the frame to modify
        tinted_frame = frame.copy()
        
        # Get the white color to replace (255, 255, 255)
        white_color = (255, 255, 255)
        
        # Replace white pixels with the entity's color
        for y in range(tinted_frame.get_height()):
            for x in range(tinted_frame.get_width()):
                pixel_color = tinted_frame.get_at((x, y))
                # If the pixel is white (or close to white), replace it with the entity color
                if (pixel_color[0] > 240 and pixel_color[1] > 240 and pixel_color[2] > 240):
                    # Keep the alpha value
                    alpha = pixel_color[3]
                    new_color = (self.color[0], self.color[1], self.color[2], alpha)
                    tinted_frame.set_at((x, y), new_color)
        
        return tinted_frame
    
    def load_cna_file(self, cna_file_path):
        """Load CNA data from a file and update entity attributes"""
        self.cna_file = cna_file_path
        try:
            from cna_utils import CNACodec
            self.cna_data = CNACodec.load_from_file(cna_file_path)
            
            # Update entity color based on CNA data
            if self.cna_data:
                from cna_utils import calculate_entity_color
                self.color = calculate_entity_color(self.cna_data)
                print(f"Updated entity color to {self.color} based on CNA data")
        except Exception as e:
            print(f"Error loading CNA file: {e}")
    
    def update(self):
        """Update entity state"""
        # Update visual position with smooth interpolation
        self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
        self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
        
        # Update animation
        self.update_animation()


        # Check if we're near water and replenish thirst if needed
        if hasattr(self, 'check_and_replenish_thirst'):
            self.check_and_replenish_thirst()
            
        # Handle movement towards target
        if self.is_moving:
            # Check if we've reached the target
            if self.grid_x == self.target_grid_x and self.grid_y == self.target_grid_y:
                self.is_moving = False
            else:
                # Move towards target one tile at a time
                if self.grid_x < self.target_grid_x:
                    self.grid_x += self.speed
                elif self.grid_x > self.target_grid_x:
                    self.grid_x -= self.speed
                    
                if self.grid_y < self.target_grid_y:
                    self.grid_y += self.speed
                elif self.grid_y > self.target_grid_y:
                    self.grid_y -= self.speed
        
        # Update visual position with smooth interpolation
        self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
        self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
        
        

    
    def render(self, screen, camera):
        """Render the entity with camera transformations"""
        # Calculate screen position using camera and visual position
        screen_x, screen_y, width, height = camera.apply(
            self.visual_x * 16, self.visual_y * 16, 16, 16
        )
        
        # Skip rendering if off-screen
        if (screen_x + width < 0 or screen_x > screen.get_width() or
            screen_y + height < 0 or screen_y > screen.get_height()):
            return
        
        # Get the current animation frame
        current_frame = self.animation_frames[self.current_frame]
        
        # Apply color tint
        tinted_frame = self.apply_color_tint(current_frame)
        
        # Scale the frame if needed
        if width != 16 or height != 16:
            tinted_frame = pygame.transform.scale(tinted_frame, (int(width), int(height)))
        
        # Draw the sprite
        screen.blit(tinted_frame, (screen_x, screen_y))
    
    def contains_point(self, screen_x, screen_y, camera):
        """Check if a screen point is within this entity"""
        entity_x, entity_y, width, height = camera.apply(
            self.visual_x * 16, self.visual_y * 16, 16, 16
        )
        
        return (entity_x <= screen_x <= entity_x + width and
                entity_y <= screen_y <= entity_y + height)

    def check_and_replenish_thirst(self):
        """Check if entity is adjacent to water and replenish thirst if needed"""
        # Skip if entity doesn't have thirst attribute
        if not hasattr(self, 'thirst'):
            return
            
        # Skip if thirst is already full
        if self.thirst >= 10:
            return
            
        # Get the world map
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        # Check if we're adjacent to water
        if world_map and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
            # Get current time
            current_time = pygame.time.get_ticks()
            
            # Only drink every 2 seconds to prevent instant refill
            if not hasattr(self, 'last_drink_time') or current_time - self.last_drink_time > 2000:
                self.thirst += 1
                self.last_drink_time = current_time
                
                # Print message
                entity_type = "Player" if hasattr(self, 'controllable') and self.controllable else "NPC"
                print(f"{entity_type} drank water, thirst increased to {self.thirst}")
                
                # Show a speech bubble for NPCs
                if entity_type == "NPC" and hasattr(SimpleGameEngine.instance, 'ui'):
                    if self.thirst == 10:
                        SimpleGameEngine.instance.ui.add_text_bubble("Ahh, my thirst is quenched!", self, duration=2.0)
                    else:
                        SimpleGameEngine.instance.ui.add_text_bubble("*drinks water*", self, duration=1.0)

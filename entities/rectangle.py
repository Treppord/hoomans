import pygame
from entities.entity import Entity

class Rectangle(Entity):
    def __init__(self, grid_x, grid_y, color=(255, 0, 0), speed=1, controllable=False):
        # Convert grid coordinates to pixel coordinates
        x = grid_x * 16
        y = grid_y * 16
        super().__init__(x, y)
        
        # Store grid position
        self.grid_x = grid_x
        self.grid_y = grid_y
        
        # Make entity slightly smaller than the tile
        self.width = 12
        self.height = 12
        
        # Center the entity within the tile
        self.x_offset = (16 - self.width) // 2
        self.y_offset = (16 - self.height) // 2
        
        self.original_color = color  # Store original color
        self.color = color
        self.speed = speed  # Speed in grid cells per update
        self.controllable = controllable  # Flag to indicate if this entity is player-controlled

        
        # Target grid position for smooth movement
        self.target_grid_x = grid_x
        self.target_grid_y = grid_y
        
        # Flag to track if we're currently moving
        self.is_moving = False
        
        # Initialize thirst attributes
        self.thirst = 5
        self.last_thirst_update = pygame.time.get_ticks()
        self.last_drink_time = 0
    
    def update(self):
        """Update object state"""
        prev_x, prev_y = self.x, self.y

        # If we have a target position, move towards it
        if self.is_moving:
            # Update grid position
            if self.grid_x < self.target_grid_x:
                self.grid_x += 1
            elif self.grid_x > self.target_grid_x:
                self.grid_x -= 1
                
            if self.grid_y < self.target_grid_y:
                self.grid_y += 1
            elif self.grid_y > self.target_grid_y:
                self.grid_y -= 1
            
            # Check if we've reached the target
            if self.grid_x == self.target_grid_x and self.grid_y == self.target_grid_y:
                self.is_moving = False
        
        # Update pixel position based on grid position
        self.x = self.grid_x * 16
        self.y = self.grid_y * 16
        
        # Check for drinking if we have thirst attribute
        current_time = pygame.time.get_ticks()
        
        # Try to drink if we're near water and it's been at least 1 second since last drink
        if current_time - self.last_drink_time > 1000:  # 1 second
            # Get the world map from the game engine
            from engine.core import SimpleGameEngine
            world_map = None
            if hasattr(SimpleGameEngine, 'instance'):
                world_map = SimpleGameEngine.instance.world_map
            
            if world_map and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
                if self.thirst < 5:  # Max thirst is 5
                    self.thirst += 1
                    print(f"Entity drank water, thirst increased to {self.thirst}")
                    
                    # Add a text bubble for the player
                    if hasattr(self, 'controllable') and self.controllable and hasattr(SimpleGameEngine, 'instance'):
                        if hasattr(SimpleGameEngine.instance, 'ui'):
                            SimpleGameEngine.instance.ui.add_text_bubble("*Slurp*", self, duration=1.0)
                
                self.last_drink_time = current_time
    
    def perform_action(self):
        """Perform an action when the action button is pressed"""
        # Store current color
        current_color = self.color
        
        # Change color temporarily as a visual indicator
        self.color = (255, 255, 0)  # Yellow flash
        
        # You could add more action logic here
        
        # Reset color after a short delay (in a real game, you'd use a timer)
        # For now, we'll use a simple approach
        import pygame
        pygame.time.delay(100)  # 100ms delay
        
        # Restore the original color (which might be CNA-based)
        self.color = current_color
    
    def interact(self):
        """Interact with objects or tiles near the entity"""
        # This would be implemented based on game mechanics
        pass
    
    def render(self, screen, camera):
        """Render the object with camera transformations"""
        # Apply camera transformation to get screen coordinates
        rect_x, rect_y, rect_width, rect_height = camera.apply(
            self.x + self.x_offset, 
            self.y + self.y_offset, 
            self.width, 
            self.height
        )
        
        # Draw the rectangle at the transformed position
        pygame.draw.rect(screen, self.color, (rect_x, rect_y, rect_width, rect_height))
    
    def contains_point(self, screen_x, screen_y, camera):
        """Check if this entity contains the given screen point (for click detection)"""
        # Apply camera transformation to get screen coordinates
        rect_x, rect_y, rect_width, rect_height = camera.apply(
            self.x + self.x_offset, 
            self.y + self.y_offset, 
            self.width, 
            self.height
        )
        
        # Check if point is inside rectangle
        return (rect_x <= screen_x <= rect_x + rect_width and 
                rect_y <= screen_y <= rect_y + rect_height)

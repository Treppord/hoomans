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
        
        self.color = color
        self.speed = speed  # Speed in grid cells per update
        self.controllable = controllable  # Flag to indicate if this entity is player-controlled

        
        # Target grid position for smooth movement
        self.target_grid_x = grid_x
        self.target_grid_y = grid_y
        
        # Flag to track if we're currently moving
        self.is_moving = False
    
    def update(self):
        """Update object state"""
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
    
    def perform_action(self):
        """Perform an action when the action button is pressed"""
        # Change color temporarily as a visual indicator
        self.color = (255, 255, 0)  # Yellow flash
        
        # You could add more action logic here
        
        # Reset color after a short delay (in a real game, you'd use a timer)
        self.color = (255, 0, 0)
    
    def interact(self):
        """Interact with objects or tiles near the entity"""
        # This would be implemented based on game mechanics
        pass
    
    def render(self, screen):
        """Render the object"""
        # Draw the rectangle centered within its grid cell
        pygame.draw.rect(screen, self.color, 
                        (self.x + self.x_offset, 
                         self.y + self.y_offset, 
                         self.width, self.height))

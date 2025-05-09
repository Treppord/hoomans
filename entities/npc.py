from entities.rectangle import Rectangle
import pygame

class NPC(Rectangle):
    """An NPC entity controlled by AI"""
    
    def __init__(self, grid_x, grid_y, color=(0, 255, 0), speed=1, ai_controller=None):
        super().__init__(grid_x, grid_y, color, speed, controllable=False)
        self.ai_controller = ai_controller
        
        # Add thirst attribute (0-5 scale)
        self.thirst = 5  # Start with full thirst
        self.last_thirst_update = 0  # Track time for thirst decrease
        self.last_drink_time = 0  # Track time for drinking
        
        # If an AI controller was provided, set this entity as its target
        if self.ai_controller:
            self.ai_controller.set_entity(self)
    
    def set_ai_controller(self, ai_controller):
        """Set the AI controller for this NPC"""
        self.ai_controller = ai_controller
        self.ai_controller.set_entity(self)
        
    def render(self, screen, camera):
        """Render the NPC with camera transformations"""
        super().render(screen, camera)
    
    def update(self):
        """Update entity state"""
        super().update()
        
        # Update thirst over time
        current_time = pygame.time.get_ticks()
        
        # Decrease thirst every 10 seconds
        if current_time - self.last_thirst_update > 10000:  # 10 seconds
            if self.thirst > 0:
                self.thirst -= 1
                print(f"NPC thirst decreased to {self.thirst}")
            self.last_thirst_update = current_time
            
    def apply_ai_decision(self, decision):
        """Apply a decision from the AI Universe Controller"""
        # Handle movement
        if decision.action == "move_left" and not self.is_moving:
            self.target_grid_x = self.grid_x - 1
            self.is_moving = True
        elif decision.action == "move_right" and not self.is_moving:
            self.target_grid_x = self.grid_x + 1
            self.is_moving = True
        elif decision.action == "move_up" and not self.is_moving:
            self.target_grid_y = self.grid_y - 1
            self.is_moving = True
        elif decision.action == "move_down" and not self.is_moving:
            self.target_grid_y = self.grid_y + 1
            self.is_moving = True
        elif decision.action == "drink" and not self.is_moving:
            # For drinking, we don't need to move, just update the last_drink_time
            # to trigger the drinking logic in the update method
            self.last_drink_time = 0  # This will make the NPC drink on next update
        
        # If we have specific target coordinates, use those
        if decision.target_x is not None and decision.target_y is not None:
            self.target_grid_x = decision.target_x
            self.target_grid_y = decision.target_y
            self.is_moving = True
        
        # Return True if we applied a movement
        return self.is_moving

from entities.rectangle import Rectangle
import pygame
import random

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
        """Apply an AI decision to this NPC"""
        # Handle basic actions
        if decision.action == "move_left":
            self.target_grid_x = self.grid_x - 1
            self.is_moving = True
        elif decision.action == "move_right":
            self.target_grid_x = self.grid_x + 1
            self.is_moving = True
        elif decision.action == "move_up":
            self.target_grid_y = self.grid_y - 1
            self.is_moving = True
        elif decision.action == "move_down":
            self.target_grid_y = self.grid_y + 1
            self.is_moving = True
        elif decision.action == "drink" and self.thirst < 5:
            # Check if we're adjacent to water
            from engine.core import SimpleGameEngine
            world_map = None
            if hasattr(SimpleGameEngine, 'instance'):
                world_map = SimpleGameEngine.instance.world_map
            
            if world_map and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
                self.thirst += 1
                print(f"NPC drank water, thirst increased to {self.thirst}")
        
        # Handle fast movement for critical needs
        if decision.is_fast_movement and not self.is_moving:
            # Determine how many steps to take (2-3 when critically thirsty/hungry)
            steps = random.randint(2, 3)
            
            # Calculate target position based on action and steps
            if decision.action == "move_left":
                self.target_grid_x = max(0, self.grid_x - steps)
                self.is_moving = True
            elif decision.action == "move_right":
                self.target_grid_x = self.grid_x + steps
                self.is_moving = True
            elif decision.action == "move_up":
                self.target_grid_y = max(0, self.grid_y - steps)
                self.is_moving = True
            elif decision.action == "move_down":
                self.target_grid_y = self.grid_y + steps
                self.is_moving = True
                
    def respond_to_chat(self, player_message):
        """Generate a response to a player's chat message"""
        # This is handled by the AI Universe Controller
        pass

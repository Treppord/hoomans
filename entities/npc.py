from entities.rectangle import Rectangle

class NPC(Rectangle):
    """An NPC entity controlled by AI"""
    
    def __init__(self, grid_x, grid_y, color=(0, 255, 0), speed=1, ai_controller=None):
        super().__init__(grid_x, grid_y, color, speed, controllable=False)
        self.ai_controller = ai_controller
        
        # If an AI controller was provided, set this entity as its target
        if self.ai_controller:
            self.ai_controller.set_entity(self)
    
    def set_ai_controller(self, ai_controller):
        """Set the AI controller for this NPC"""
        self.ai_controller = ai_controller
        self.ai_controller.set_entity(self)
import random

class AIController:
    """Base AI controller class that can be extended for different AI behaviors"""
    
    def __init__(self, entity=None):
        self.entity = entity
        self.thinking_time = 0
        self.decision_cooldown = 30  # Frames between decisions
    
    def set_entity(self, entity):
        """Set the entity this AI controls"""
        self.entity = entity
    
    def think(self, world_map, entities):
        """Process AI logic - override in subclasses"""
        pass
    
    def update(self, world_map, entities):
        """Update AI state and make decisions"""
        if not self.entity:
            return
            
        # Only think periodically to save processing
        self.thinking_time += 1
        if self.thinking_time >= self.decision_cooldown:
            self.thinking_time = 0
            self.think(world_map, entities)


class RandomWanderAI(AIController):
    """Simple AI that makes entities wander randomly"""
    
    def think(self, world_map, entities):
        """Make a random movement decision"""
        if not self.entity or not hasattr(self.entity, 'is_moving') or self.entity.is_moving:
            return
            
        # Choose a random direction
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = random.choice(directions)
        
        # Set target position
        target_x = self.entity.grid_x + dx
        target_y = self.entity.grid_y + dy
        
        # Check if target is valid (not a wall)
        if world_map and not world_map.is_wall(target_x, target_y):
            self.entity.target_grid_x = target_x
            self.entity.target_grid_y = target_y
            self.entity.is_moving = True


class FollowPlayerAI(AIController):
    """AI that makes entities follow the player"""
    
    def __init__(self, entity=None, detection_range=5):
        super().__init__(entity)
        self.detection_range = detection_range
    
    def think(self, world_map, entities):
        """Decide whether to follow the player or wander"""
        if not self.entity or not hasattr(self.entity, 'is_moving') or self.entity.is_moving:
            return
            
        # Find the player
        player = None
        for entity in entities:
            if hasattr(entity, 'controllable') and entity.controllable:
                player = entity
                break
                
        if not player:
            return
            
        # Calculate distance to player
        dx = player.grid_x - self.entity.grid_x
        dy = player.grid_y - self.entity.grid_y
        distance = abs(dx) + abs(dy)  # Manhattan distance
        
        if distance <= self.detection_range:
            # Player is in range, move towards them
            if abs(dx) > abs(dy):
                # Move horizontally
                target_x = self.entity.grid_x + (1 if dx > 0 else -1)
                target_y = self.entity.grid_y
            else:
                # Move vertically
                target_x = self.entity.grid_x
                target_y = self.entity.grid_y + (1 if dy > 0 else -1)
                
            # Check if target is valid (not a wall)
            if world_map and not world_map.is_wall(target_x, target_y):
                self.entity.target_grid_x = target_x
                self.entity.target_grid_y = target_y
                self.entity.is_moving = True
        else:
            # Player is out of range, wander randomly
            RandomWanderAI.think(self, world_map, entities)


class AIManager:
    """Manages all AI controllers in the game"""
    
    def __init__(self):
        self.controllers = []
    
    def add_controller(self, controller):
        """Add an AI controller to be managed"""
        self.controllers.append(controller)
        return controller
    
    def update(self, world_map, entities):
        """Update all AI controllers"""
        for controller in self.controllers:
            controller.update(world_map, entities)
            
class WaterSeekingAI(AIController):
    """AI that makes entities seek water when thirsty"""
    
    def __init__(self, entity=None, detection_range=8):
        super().__init__(entity)
        self.detection_range = detection_range
        self.target_water = None
        self.drinking = False
        self.decision_cooldown = 15  # Shorter cooldown for more responsive behavior
    
    def think(self, world_map, entities):
        """Decide whether to seek water or wander"""
        if not self.entity or not hasattr(self.entity, 'is_moving') or self.entity.is_moving:
            return
            
        # Check if entity has thirst attribute
        if not hasattr(self.entity, 'thirst'):
            # If no thirst attribute, just wander randomly
            RandomWanderAI.think(self, world_map, entities)
            return
            
        # If entity is not thirsty (thirst > 1), wander randomly
        if self.entity.thirst > 1:
            self.drinking = False
            self.target_water = None
            RandomWanderAI.think(self, world_map, entities)
            return
            
        # If already adjacent to water, stay and drink
        if world_map.is_adjacent_to_water(self.entity.grid_x, self.entity.grid_y):
            self.drinking = True
            # Don't move, just stay and drink
            return
            
        # If we have a target water location, move towards it
        if self.target_water:
            target_x, target_y = self.target_water
            
            # If we've reached the target, clear it
            if self.entity.grid_x == target_x and self.entity.grid_y == target_y:
                self.target_water = None
                return
                
            # Move towards the target
            if abs(target_x - self.entity.grid_x) > abs(target_y - self.entity.grid_y):
                # Move horizontally
                target_x = self.entity.grid_x + (1 if target_x > self.entity.grid_x else -1)
                target_y = self.entity.grid_y
            else:
                # Move vertically
                target_x = self.entity.grid_x
                target_y = self.entity.grid_y + (1 if target_y > self.entity.grid_y else -1)
                
            # Check if target is valid (not a wall)
            if world_map and not world_map.is_wall(target_x, target_y):
                self.entity.target_grid_x = target_x
                self.entity.target_grid_y = target_y
                self.entity.is_moving = True
            return
            
        # Find nearest water
        water_pos = world_map.find_nearest_water(
            self.entity.grid_x, self.entity.grid_y, self.detection_range
        )
        
        if water_pos:
            # Found water, set it as our target
            self.target_water = water_pos
            print(f"Entity found water at {water_pos}, moving towards it")
        else:
            # No water found, wander randomly
            RandomWanderAI.think(self, world_map, entities)

import random
import pygame
from engine.constants import TimeConstants


class AIController:
    """Base AI controller class that can be extended for different AI behaviors"""
    
    def __init__(self, entity=None):
        self.entity = entity
        self.thinking_time = 0
        self.decision_cooldown = TimeConstants.AI_DECISION_COOLDOWN
    
    def set_entity(self, entity):
        """Set the entity this AI controls"""
        self.entity = entity
    
    def think(self, world_map, entities):
        """Make a random movement decision with food-specific behavior"""
        if not self.entity or not hasattr(self.entity, 'is_moving') or self.entity.is_moving:
            return
            
        # Check if any NPC is nearby and try to avoid them
        nearby_npc = None
        for entity in entities:
            if hasattr(entity, '__class__') and entity.__class__.__name__ == 'NPC':
                # Calculate distance to NPC
                dx = abs(entity.grid_x - self.entity.grid_x)
                dy = abs(entity.grid_y - self.entity.grid_y)
                
                # If NPC is within 2 tiles, try to move away
                if dx <= 2 and dy <= 2:
                    nearby_npc = entity
                    break
        
        if nearby_npc:
            # Try to move away from the NPC
            dx = self.entity.grid_x - nearby_npc.grid_x
            dy = self.entity.grid_y - nearby_npc.grid_y
            
            # Determine which direction to move (away from NPC)
            if abs(dx) > abs(dy):
                # Move horizontally away
                target_x = self.entity.grid_x + (1 if dx > 0 else -1)
                target_y = self.entity.grid_y
            else:
                # Move vertically away
                target_x = self.entity.grid_x
                target_y = self.entity.grid_y + (1 if dy > 0 else -1)
            
            # Check if target is valid (not a wall or water)
            if world_map:
                # Ensure target is within map bounds
                if 0 <= target_x < world_map.width and 0 <= target_y < world_map.height:
                    # Check if target is walkable
                    if not hasattr(world_map, 'is_wall') or not world_map.is_wall(target_x, target_y):
                        # Check if target is not water
                        if not hasattr(world_map, 'get_tile') or not (hasattr(world_map.get_tile(target_x, target_y), 'is_water') and world_map.get_tile(target_x, target_y).is_water()):
                            # Set the target position
                            self.entity.target_grid_x = target_x
                            self.entity.target_grid_y = target_y
                            self.entity.is_moving = True
                            return
        
        # Only move occasionally (food is more stationary than NPCs)
        if random.random() > self.wander_probability:
            return
            
        # Get current time
        current_time = pygame.time.get_ticks()
        
        # Only change direction after cooldown
        if current_time - self.last_direction_change < self.direction_change_cooldown:
            return
            
        self.last_direction_change = current_time
            
        # Choose a random direction
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = random.choice(directions)
        
        # Set target position (shorter movement range)
        move_distance = random.randint(1, 2)  # Food moves shorter distances
        target_x = self.entity.grid_x + (dx * move_distance)
        target_y = self.entity.grid_y + (dy * move_distance)
        
        # Check if target is valid (not a wall or water)
        if world_map:
            # Ensure target is within map bounds
            if target_x < 0 or target_x >= world_map.width or target_y < 0 or target_y >= world_map.height:
                return
                
            # Check if target is walkable
            if hasattr(world_map, 'is_wall') and world_map.is_wall(target_x, target_y):
                return
                
            # Check if target is water (food shouldn't go in water)
            if hasattr(world_map, 'get_tile'):
                tile = world_map.get_tile(target_x, target_y)
                if tile and hasattr(tile, 'is_water') and tile.is_water():
                    return
        
        # Set the target position
        self.entity.target_grid_x = target_x
        self.entity.target_grid_y = target_y
        self.entity.is_moving = True

    
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

class FoodWanderAI(AIController):
    """AI that makes food entities wander randomly with specific behavior"""
    
    def __init__(self, entity=None, wander_probability=0.2):
        super().__init__(entity)
        self.wander_probability = wander_probability
        self.decision_cooldown = TimeConstants.AI_DECISION_COOLDOWN * 2  # Longer cooldown for food
        self.last_direction_change = 0
        self.direction_change_cooldown = TimeConstants.FOOD_DIRECTION_CHANGE_COOLDOWN
    
    def think(self, world_map, entities):
        """Make a random movement decision with food-specific behavior"""
        if not self.entity or not hasattr(self.entity, 'is_moving') or self.entity.is_moving:
            return
            
        # Only move occasionally (food is more stationary than NPCs)
        if random.random() > self.wander_probability:
            return
            
        # Get current time
        current_time = pygame.time.get_ticks()
        
        # Only change direction after cooldown
        if current_time - self.last_direction_change < self.direction_change_cooldown:
            return
            
        self.last_direction_change = current_time
            
        # Choose a random direction
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = random.choice(directions)
        
        # Set target position (shorter movement range)
        move_distance = random.randint(1, 2)  # Food moves shorter distances
        target_x = self.entity.grid_x + (dx * move_distance)
        target_y = self.entity.grid_y + (dy * move_distance)
        
        # Check if target is valid (not a wall or water)
        if world_map:
            # Ensure target is within map bounds
            if target_x < 0 or target_x >= world_map.width or target_y < 0 or target_y >= world_map.height:
                return
                
            # Check if target is walkable
            if hasattr(world_map, 'is_wall') and world_map.is_wall(target_x, target_y):
                return
                
            # Check if target is water (food shouldn't go in water)
            if hasattr(world_map, 'get_tile'):
                tile = world_map.get_tile(target_x, target_y)
                if tile and hasattr(tile, 'is_water') and tile.is_water():
                    return
        
        # Set the target position
        self.entity.target_grid_x = target_x
        self.entity.target_grid_y = target_y
        self.entity.is_moving = True

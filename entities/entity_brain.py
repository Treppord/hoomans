import random
import math
from enum import Enum

class Trait(Enum):
    INTELLIGENCE = 0
    SOCIABILITY = 1
    AGGRESSION = 2
    CURIOSITY = 3
    ENERGY = 4

class Need(Enum):
    HUNGER = 0
    THIRST = 1
    REST = 2
    SOCIAL = 3
    SAFETY = 4

class EntityBrain:
    """Brain that controls entity behavior based on CNA attributes"""
    
    def __init__(self, entity):
        self.entity = entity
        self.traits = {}
        self.needs = {}
        self.memories = []
        self.relationships = {}
        self.current_goal = None
        self.decision_cooldown = 0
        
        # Initialize with default values
        for trait in Trait:
            self.traits[trait] = 0.5
            
        for need in Need:
            self.needs[need] = 1.0  # Start with all needs satisfied
        
        # Apply CNA attributes if available
        if hasattr(entity, 'cna_data') and entity.cna_data:
            self.apply_cna_attributes()
    
    def apply_cna_attributes(self):
        """Apply CNA attributes to brain traits"""
        cna = self.entity.cna_data
        
        # Map personality traits to our brain traits
        if hasattr(cna, 'personality_traits') and len(cna.personality_traits) >= 5:
            self.traits[Trait.INTELLIGENCE] = cna.personality_traits[0]
            self.traits[Trait.SOCIABILITY] = cna.personality_traits[1]
            self.traits[Trait.AGGRESSION] = cna.personality_traits[2]
            self.traits[Trait.CURIOSITY] = cna.personality_traits[3]
            self.traits[Trait.ENERGY] = cna.personality_traits[4]
        
        # Apply intelligence factor
        if hasattr(cna, 'intelligence_factor'):
            self.traits[Trait.INTELLIGENCE] = cna.intelligence_factor / 1.5  # Normalize to 0-1 range
        
        # Apply adaptability to curiosity
        if hasattr(cna, 'adaptability'):
            self.traits[Trait.CURIOSITY] = cna.adaptability / 1.5  # Normalize to 0-1 range
    
    def update_needs(self, delta_time):
        """Update needs based on time passing"""
        # Hunger and thirst decrease over time
        self.needs[Need.HUNGER] = max(0, self.needs[Need.HUNGER] - 0.01 * delta_time)
        self.needs[Need.THIRST] = max(0, self.needs[Need.THIRST] - 0.02 * delta_time)
        
        # Energy decreases based on activity
        if hasattr(self.entity, 'is_moving') and self.entity.is_moving:
            self.needs[Need.REST] = max(0, self.needs[Need.REST] - 0.015 * delta_time)
        else:
            self.needs[Need.REST] = min(1.0, self.needs[Need.REST] + 0.005 * delta_time)
        
        # Social need changes based on nearby entities
        if len(self.get_nearby_entities()) > 0:
            self.needs[Need.SOCIAL] = min(1.0, self.needs[Need.SOCIAL] + 0.01 * delta_time)
        else:
            self.needs[Need.SOCIAL] = max(0, self.needs[Need.SOCIAL] - 0.005 * delta_time)
    
    def get_nearby_entities(self, max_distance=5):
        """Get entities within a certain distance"""
        nearby = []
        
        # Get all entities from the game engine
        from engine.core import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance'):
            return nearby
            
        engine = SimpleGameEngine.instance
        
        for entity in engine.objects:
            if entity == self.entity:
                continue
                
            if hasattr(entity, 'grid_x') and hasattr(entity, 'grid_y'):
                distance = abs(entity.grid_x - self.entity.grid_x) + abs(entity.grid_y - self.entity.grid_y)
                if distance <= max_distance:
                    nearby.append((entity, distance))
        
        return nearby
    
    def decide_action(self):
        """Decide what action to take based on needs and traits"""
        # Reduce decision frequency
        if self.decision_cooldown > 0:
            self.decision_cooldown -= 1
            return
            
        self.decision_cooldown = 10  # Make decisions every 10 updates
        
        # Find the most pressing need
        most_pressing_need = None
        lowest_value = 1.0
        
        for need, value in self.needs.items():
            if value < lowest_value:
                lowest_value = value
                most_pressing_need = need
        
        # If a need is below threshold, address it
        if lowest_value < 0.3:
            if most_pressing_need == Need.THIRST:
                self.seek_water()
            elif most_pressing_need == Need.HUNGER:
                self.seek_food()
            elif most_pressing_need == Need.REST:
                self.rest()
            elif most_pressing_need == Need.SOCIAL:
                self.seek_company()
            return
            
        # If no pressing needs, behavior is determined by traits
        if random.random() < self.traits[Trait.CURIOSITY]:
            self.explore()
        elif random.random() < self.traits[Trait.SOCIABILITY]:
            self.seek_company()
        else:
            self.wander()
    
    def seek_water(self):
        """Seek water to drink"""
        # Get the world map
        from engine.core import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance'):
            return
            
        engine = SimpleGameEngine.instance
        world_map = engine.world_map
        
        if not world_map:
            return
            
        # Find nearest water
        detection_range = 8 + int(self.traits[Trait.INTELLIGENCE] * 4)  # Smarter entities can see further
        water_pos = world_map.find_nearest_water(
            self.entity.grid_x, self.entity.grid_y, detection_range
        )
        
        if water_pos:
            # Move towards water
            self.move_towards(water_pos[0], water_pos[1])
        else:
            # If no water found, explore
            self.explore()
    
    def seek_food(self):
        """Seek food to eat"""
        # In this simple version, food is not implemented yet
        # For now, just wander
        self.wander()
    
    def rest(self):
        """Rest to regain energy"""
        # Just stay in place
        pass
    
    def seek_company(self):
        """Seek other entities for social interaction"""
        nearby = self.get_nearby_entities()
        
        if not nearby:
            # No one nearby, wander
            self.wander()
            return
            
        # Find the closest entity
        closest = min(nearby, key=lambda x: x[1])
        target_entity = closest[0]
        
        # Move towards the entity
        self.move_towards(target_entity.grid_x, target_entity.grid_y)
    
    def explore(self):
        """Explore the environment"""
        # Pick a random direction but with some intelligence
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        # Get the world map
        from engine.core import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance'):
            return
            
        engine = SimpleGameEngine.instance
        world_map = engine.world_map
        
        if not world_map:
            self.wander()
            return
            
        # Try to find an unexplored direction
        valid_directions = []
        
        for dx, dy in directions:
            target_x = self.entity.grid_x + dx
            target_y = self.entity.grid_y + dy
            
            # Check if target is valid (not a wall)
            if (0 <= target_x < world_map.width and 
                0 <= target_y < world_map.height and
                not world_map.is_wall(target_x, target_y)):
                valid_directions.append((dx, dy))
        
        if valid_directions:
            # Choose a direction with some randomness
            dx, dy = random.choice(valid_directions)
            
            # Set target position
            self.entity.target_grid_x = self.entity.grid_x + dx
            self.entity.target_grid_y = self.entity.grid_y + dy
            self.entity.is_moving = True
    
    def wander(self):
        """Wander randomly"""
        # Choose a random direction
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = random.choice(directions)
        
        # Set target position
        self.entity.target_grid_x = self.entity.grid_x + dx
        self.entity.target_grid_y = self.entity.grid_y + dy
        self.entity.is_moving = True
    
    def move_towards(self, target_x, target_y):
        """Move towards a target position"""
        if self.entity.is_moving:
            return
            
        # Determine direction to move
        dx = 0
        dy = 0
        
        if target_x > self.entity.grid_x:
            dx = 1
        elif target_x < self.entity.grid_x:
            dx = -1
            
        if target_y > self.entity.grid_y:
            dy = 1
        elif target_y < self.entity.grid_y:
            dy = -1
            
        # Prioritize the larger difference
        if abs(target_x - self.entity.grid_x) > abs(target_y - self.entity.grid_y):
            dy = 0
        else:
            dx = 0
            
        # Set target position
        self.entity.target_grid_x = self.entity.grid_x + dx
        self.entity.target_grid_y = self.entity.grid_y + dy
        self.entity.is_moving = True
    
    def add_memory(self, memory):
        """Add a memory to the entity's memory"""
        self.memories.append({
            'content': memory,
            'time': 0  # Current time
        })
        
        # Limit memory size
        if len(self.memories) > 20:
            self.memories.pop(0)
    
    def update_relationship(self, other_entity, change):
        """Update relationship with another entity"""
        if other_entity not in self.relationships:
            self.relationships[other_entity] = 0
            
        self.relationships[other_entity] += change
        self.relationships[other_entity] = max(-1, min(1, self.relationships[other_entity]))
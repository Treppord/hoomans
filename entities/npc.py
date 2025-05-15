from entities.rectangle import Rectangle
import pygame
import random
import hashlib
import os
from engine.constants import TimeConstants, GameBalanceConstants
from speech_constants import SpeechConstants


class NPC(Rectangle):
    """An NPC entity controlled by AI"""
    
    def __init__(self, grid_x, grid_y, color=(0, 255, 0), speed=1, ai_controller=None):
        super().__init__(grid_x, grid_y, color, speed, controllable=False)
        self.ai_controller = ai_controller
        
        # Add thirst attribute (0-10 scale)
        self.thirst = GameBalanceConstants.STARTING_THIRST // 2  # Start with half thirst
        self.last_thirst_update = 0
        self.last_drink_time = 0

        # Add hunger attribute (0-10 scale)
        self.hunger = GameBalanceConstants.STARTING_HUNGER // 2  # Start with half hunger
        self.last_hunger_update = 0
        self.last_eat_time = 0
        
        # Debug tracking for player detection
        self.debug_player_detected = False
        self.debug_last_player_id = None
        
        # Advice following attributes
        self.advice_remaining_distance = 0
        self.advice_direction = None
        
        # Exploration attributes
        self.exploration_mode = "idle"  # idle, exploring, returning
        self.exploration_target_x = None
        self.exploration_target_y = None
        self.last_exploration_time = 0
        self.explored_tiles = set()  # Set of (x, y) coordinates that have been explored
        self.interesting_locations = {}  # Dict of location_type -> list of (x, y) coordinates
        self.home_location = (grid_x, grid_y)  # Starting position as home base
        self.curiosity = random.uniform(0.5, 1.0)  # How curious/exploratory this NPC is
        self.last_memory_record_time = 0  # Time of last memory recording
        self.memory_cooldown = 10000  # Milliseconds between memory recordings (10 seconds)
        
        # Add state for handling chat questions
        self.is_responding_to_chat = False
        self.paused_state = None  # Will store the state before being paused
        self.chat_response_time = 0
        self.last_chat_response_id = None  # Track the last chat response to avoid duplicates
        self.chat_cooldown = TimeConstants.CHAT_RESPONSE_COOLDOWN
        
        self.heading_to_known_water = False  # Add this line to fix the error
        self.heading_to_food = False  # Also initialize food-seeking attribute

        
        # If an AI controller was provided, set this entity as its target
        if self.ai_controller:
            self.ai_controller.set_entity(self)


    def update(self):
        """Update entity state"""
        # Get current time for timing controls
        current_time = pygame.time.get_ticks()
        
        # Check if we're responding to chat - if so, pause other actions
        if self.is_responding_to_chat:
            # Only update visual position with smooth interpolation
            self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
            self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
            
            # Update animation (from Rectangle class)
            self.update_animation()
            
            # Check if we've been waiting too long (timeout after 10 seconds)
            if current_time - self.chat_response_time > TimeConstants.CHAT_RESPONSE_TIMEOUT:
                print(f"DEBUG: NPC {self.get_entity_id()} chat response timed out, resuming normal activities")
                self.is_responding_to_chat = False
                self._resume_paused_state()
            
            return  # Skip the rest of the update while responding to chat
        
        # Update visual position with smooth interpolation (from Rectangle class)
        self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
        self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
        
        # Update animation (from Rectangle class)
        self.update_animation()
        
        # Check if we're critically thirsty and should seek water from world cache
        if hasattr(self, 'thirst') and self.thirst <= 2 and not self.is_moving:
            
            # Try to find water from world cache
            from engine.core import SimpleGameEngine
            if (hasattr(SimpleGameEngine, 'instance') and 
                hasattr(SimpleGameEngine.instance, 'world_cache')):
                
                world_cache = SimpleGameEngine.instance.world_cache
                water_locations = world_cache.get_discovered_locations('water')
                
                if water_locations:
                    # Find the nearest water location
                    nearest_water = min(water_locations, 
                                      key=lambda loc: abs(loc["x"] - self.grid_x) + abs(loc["y"] - self.grid_y))
                    
                    print(f"DEBUG: Thirsty NPC {self.get_entity_id()} found water in world cache at ({nearest_water['x']}, {nearest_water['y']})")
                    
                    # Get world map for tile checking
                    world_map = None
                    if hasattr(SimpleGameEngine, 'instance'):
                        world_map = SimpleGameEngine.instance.world_map
                    
                    # Instead of going directly to water, go adjacent to it
                    water_x = nearest_water["x"]
                    water_y = nearest_water["y"]
                    
                    # Check all four adjacent positions to find a walkable one
                    adjacent_positions = [
                        (water_x + 1, water_y),
                        (water_x - 1, water_y),
                        (water_x, water_y + 1),
                        (water_x, water_y - 1)
                    ]
                    
                    # Find a walkable adjacent position
                    walkable_position = None
                    for pos_x, pos_y in adjacent_positions:
                        if world_map and hasattr(world_map, 'get_tile'):
                            tile = world_map.get_tile(pos_x, pos_y)
                            if tile and hasattr(tile, 'is_walkable') and tile.is_walkable() and not (hasattr(tile, 'is_water') and tile.is_water()):
                                walkable_position = (pos_x, pos_y)
                                break
                    
                    # If we found a walkable position, go there
                    if walkable_position:
                        # Instead of teleporting, move one step toward the adjacent position
                        dx = walkable_position[0] - self.grid_x
                        dy = walkable_position[1] - self.grid_y
                        
                        # Decide whether to move horizontally or vertically first
                        if abs(dx) > abs(dy):
                            # Move horizontally
                            self.target_grid_x = self.grid_x + (1 if dx > 0 else -1 if dx < 0 else 0)
                            self.target_grid_y = self.grid_y
                        else:
                            # Move vertically
                            self.target_grid_x = self.grid_x
                            self.target_grid_y = self.grid_y + (1 if dy > 0 else -1 if dy < 0 else 0)
                        
                        # Store the final destination for future steps
                        self.final_destination_x = walkable_position[0]
                        self.final_destination_y = walkable_position[1]
                        self.is_moving = True
                        self.heading_to_known_water = True
                        
                        # Initialize movement timer
                        self.last_move_time = current_time
                        
                        # Show a speech bubble about going to water
                        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.WATER_FOUND_SPEECHES), self, duration=2.0)
        # Check if we're critically hungry and should seek food
        if hasattr(self, 'hunger') and self.hunger <= 3 and not self.is_moving:
            # Try to find food nearby
            self.start_searching_for_food()
            
            # If we're heading to food, override other actions
            if hasattr(self, 'heading_to_food') and self.heading_to_food:
                return
        
        # Check if we're standing on water (emergency situation)
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        if world_map and hasattr(world_map, 'get_tile'):
            current_tile = world_map.get_tile(self.grid_x, self.grid_y)
            if current_tile and hasattr(current_tile, 'is_water') and current_tile.is_water():
                # We're standing on water! This is bad!
                print(f"DEBUG: NPC {self.get_entity_id()} is standing on water at ({self.grid_x}, {self.grid_y})!")
                
                # Save this water location to the world cache
                if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'world_cache'):
                    SimpleGameEngine.instance.world_cache.add_location_discovery(
                        self.get_entity_id(),
                        'water',
                        self.grid_x,
                        self.grid_y,
                        "Water source"
                    )
                    print(f"DEBUG: NPC {self.get_entity_id()} recorded water location at ({self.grid_x}, {self.grid_y})")
                
                # If we were heading to known water, we can drink here
                if hasattr(self, 'heading_to_known_water') and self.heading_to_known_water:
                    # We've reached water, drink it until thirst is 10
                    while self.thirst < 10:
                        self.thirst = min(10, self.thirst + 2)
                        print(f"NPC {self.get_entity_id()} drinking from water source, thirst increased to {self.thirst}")
                    
                    # Set the last drink time
                    self.last_drink_time = pygame.time.get_ticks()
                    
                    # Show a speech bubble about finding water
                    if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                        water_speeches = [
                            "Ah, refreshing water!",
                            "Finally, water!",
                            "This water is just what I needed.",
                            "So good to drink water when you're thirsty!"
                        ]
                        SimpleGameEngine.instance.ui.add_text_bubble(random.choice(water_speeches), self, duration=2.0)
                    
                    # After drinking, start exploring
                    self.start_exploring()
                    
                    # Reset heading to water flag
                    self.heading_to_known_water = False
                else:
                    # We weren't looking for water, so we need to get out!
                    # Step back to previous position if we have it
                    if hasattr(self, 'previous_grid_x') and hasattr(self, 'previous_grid_y'):
                        self.grid_x = self.previous_grid_x
                        self.grid_y = self.previous_grid_y
                        print(f"DEBUG: NPC {self.get_entity_id()} stepped back from water to ({self.grid_x}, {self.grid_y})")
                    else:
                        # Find the nearest land tile
                        nearest_land_x = None
                        nearest_land_y = None
                        min_distance = float('inf')
                        
                        # Search in a 5-tile radius
                        for y in range(self.grid_y - 5, self.grid_y + 6):
                            for x in range(self.grid_x - 5, self.grid_x + 6):
                                if 0 <= x < world_map.width and 0 <= y < world_map.height:
                                    tile = world_map.get_tile(x, y)
                                    if tile and hasattr(tile, 'is_walkable') and tile.is_walkable() and not (hasattr(tile, 'is_water') and tile.is_water()):
                                        distance = abs(x - self.grid_x) + abs(y - self.grid_y)
                                        if distance < min_distance:
                                            min_distance = distance
                                            nearest_land_x = x
                                            nearest_land_y = y
                        
                        # If we found land, move towards it
                        if nearest_land_x is not None and nearest_land_y is not None:
                            # Determine which direction to move (one step at a time)
                            dx = nearest_land_x - self.grid_x
                            dy = nearest_land_y - self.grid_y
                            
                            if abs(dx) > abs(dy):
                                # Move horizontally first
                                self.target_grid_x = self.grid_x + (1 if dx > 0 else -1)
                                self.target_grid_y = self.grid_y
                            else:
                                # Move vertically first
                                self.target_grid_x = self.grid_x
                                self.target_grid_y = self.grid_y + (1 if dy > 0 else -1)
                    
                    # Cancel current action and clear destination
                    if hasattr(self, 'final_destination_x'):
                        delattr(self, 'final_destination_x')
                    if hasattr(self, 'final_destination_y'):
                        delattr(self, 'final_destination_y')
                    
                    # Add a "water avoidance" memory to prevent going back to this location
                    if not hasattr(self, 'water_avoidance_locations'):
                        self.water_avoidance_locations = set()
                    self.water_avoidance_locations.add((self.grid_x, self.grid_y))
                    
                    # Start a new exploration in a different direction
                    self.start_exploring()
                    
                    # Set moving state
                    self.is_moving = True
                    
                    # Show a speech bubble about escaping water
                    if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                        SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.WATER_ESCAPE_SPEECHES), self, duration=1.5)
        # Handle movement with timing control (1 tile per second)
        if self.is_moving:
            # Only move if enough time has passed (1000ms = 1 second)
            if not hasattr(self, 'last_move_time'):
                self.last_move_time = current_time
                
            if current_time - self.last_move_time >= TimeConstants.NPC_MOVE_COOLDOWN:
                # Calculate direction to target
                dx = self.target_grid_x - self.grid_x
                dy = self.target_grid_y - self.grid_y
                
                # Check if we've reached the current target
                if dx == 0 and dy == 0:
                    # If we have a final destination and haven't reached it yet
                    if (hasattr(self, 'final_destination_x') and hasattr(self, 'final_destination_y') and
                        (self.grid_x != self.final_destination_x or self.grid_y != self.final_destination_y)):
                        
                        # Calculate next step toward final destination
                        dx = self.final_destination_x - self.grid_x
                        dy = self.final_destination_y - self.grid_y
                        
                        if abs(dx) > abs(dy):
                            # Move horizontally
                            self.target_grid_x = self.grid_x + (1 if dx > 0 else -1 if dx < 0 else 0)
                            self.target_grid_y = self.grid_y
                        else:
                            # Move vertically
                            self.target_grid_x = self.grid_x
                            self.target_grid_y = self.grid_y + (1 if dy > 0 else -1 if dy < 0 else 0)
                        
                        # Continue moving
                        self.is_moving = True
                    else:
                        # We've reached our final destination
                        self.is_moving = False
                        
                        # Check if we were heading to known water
                        if hasattr(self, 'heading_to_known_water') and self.heading_to_known_water:
                            # Check if we're adjacent to water
                            from engine.core import SimpleGameEngine
                            world_map = None
                            if hasattr(SimpleGameEngine, 'instance'):
                                world_map = SimpleGameEngine.instance.world_map
                            
                            if world_map and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
                                # We've reached water, drink it until thirst is 10
                                while self.thirst < 10:
                                    self.thirst = min(10, self.thirst + 2)
                                    print(f"NPC {self.get_entity_id()} drinking from water source, thirst increased to {self.thirst}")
                                
                                # Set the last drink time
                                self.last_drink_time = pygame.time.get_ticks()
                                
                                # Show a speech bubble about finding water
                                if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                                    SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.WATER_SEEKING_SPEECHES), self, duration=2.0)
                                # After drinking, start exploring
                                self.start_exploring()
                            
                            # Reset heading to water flag
                            self.heading_to_known_water = False
                else:
                    # Store current position before moving
                    self.previous_grid_x = self.grid_x
                    self.previous_grid_y = self.grid_y
                    
                    # Determine movement direction
                    if dx != 0:
                        move_x = 1 if dx > 0 else -1
                        next_x = self.grid_x + move_x
                        next_y = self.grid_y
                    elif dy != 0:
                        move_y = 1 if dy > 0 else -1
                        next_x = self.grid_x
                        next_y = self.grid_y + move_y
                    else:
                        # Already at target
                        self.is_moving = False
                        return
                    
                    # Check if the next position is valid
                    from engine.core import SimpleGameEngine
                    world_map = None
                    if hasattr(SimpleGameEngine, 'instance'):
                        world_map = SimpleGameEngine.instance.world_map
                    
                    # Check if the tile is walkable
                    can_walk = True
                    if world_map and hasattr(world_map, 'get_tile'):
                        tile = world_map.get_tile(next_x, next_y)
                        if tile and hasattr(tile, 'is_walkable'):
                            can_walk = tile.is_walkable()
                            
                            # Also check if this is a water tile we should avoid
                            if can_walk and hasattr(tile, 'is_water') and tile.is_water() and not self.heading_to_known_water:
                                # Don't walk into water unless we're specifically looking for it
                                can_walk = False
                                print(f"DEBUG: NPC {self.get_entity_id()} avoiding walking into water at ({next_x}, {next_y})")
                    
                    # Also check if this position is in our water avoidance list
                    if can_walk and hasattr(self, 'water_avoidance_locations') and (next_x, next_y) in self.water_avoidance_locations:
                        can_walk = False
                        print(f"DEBUG: NPC {self.get_entity_id()} avoiding known water location at ({next_x}, {next_y})")
                    
                    if can_walk:
                        # Move to the next position
                        self.grid_x = next_x
                        self.grid_y = next_y
                        
                        # Update visual position directly
                        self.visual_x = float(self.grid_x)
                        self.visual_y = float(self.grid_y)
                        
                        # Reset the movement timer
                        self.last_move_time = current_time
                    else:
                        # Can't move to the next position, stop moving
                        self.is_moving = False
                        
                        # If we were heading to a destination, clear it
                        if hasattr(self, 'final_destination_x'):
                            delattr(self, 'final_destination_x')
                        if hasattr(self, 'final_destination_y'):
                            delattr(self, 'final_destination_y')
                        
                        # Start exploring in a new direction
                        self.start_exploring()
        
        # Check if we're fully hydrated but not moving - start exploring
        if hasattr(self, 'thirst') and self.thirst >= 9 and not self.is_moving:
            # If we've been idle for more than 3 seconds after drinking, start exploring
            if (hasattr(self, 'last_drink_time') and 
                current_time - self.last_drink_time > 3000):
                print(f"DEBUG: NPC {self.get_entity_id()} is fully hydrated and idle, starting exploration")
                self.start_exploring_away_from_water()
        
        # Decrease thirst every 10 seconds
        if current_time - self.last_thirst_update > TimeConstants.THIRST_DECREASE_INTERVAL:
            if self.thirst > 0:
                self.thirst -= 1
                print(f"NPC {self.get_entity_id()} thirst decreased to {self.thirst}")
            self.last_thirst_update = current_time

        # Decrease hunger every 15 seconds (hunger decreases more slowly than thirst)
        if current_time - self.last_hunger_update > TimeConstants.HUNGER_DECREASE_INTERVAL:
            if self.hunger > 0:
                self.hunger -= 1
                print(f"NPC {self.get_entity_id()} hunger decreased to {self.hunger}")
            self.last_hunger_update = current_time


    def start_exploring_away_from_water(self):
        """Start exploring in a direction away from water sources"""
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        # Get current position
        current_x = self.grid_x
        current_y = self.grid_y
        
        # Find nearby water tiles to avoid
        water_tiles = []
        
        # Check if we're adjacent to water
        if world_map:
            # Check in a 3x3 grid around the NPC
            for y in range(current_y - 1, current_y + 2):
                for x in range(current_x - 1, current_x + 2):
                    # Check if position is within map bounds
                    if 0 <= x < world_map.width and 0 <= y < world_map.height:
                        tile = world_map.get_tile(x, y)
                        if tile and hasattr(tile, 'is_water') and tile.is_water():
                            water_tiles.append((x, y))
        
        # If we found water tiles, avoid them
        if water_tiles:
            print(f"DEBUG: NPC {self.get_entity_id()} avoiding {len(water_tiles)} nearby water tiles when exploring")
            
            # Calculate average water position
            avg_water_x = sum(x for x, y in water_tiles) / len(water_tiles)
            avg_water_y = sum(y for x, y in water_tiles) / len(water_tiles)
            
            # Choose a direction away from water
            dx = current_x - avg_water_x
            dy = current_y - avg_water_y
            
            # Determine primary direction (horizontal or vertical)
            if abs(dx) > abs(dy):
                # Move horizontally away from water
                direction = "right" if dx > 0 else "left"
            else:
                # Move vertically away from water
                direction = "down" if dy > 0 else "up"
            
            # Set exploration distance
            distance = random.randint(8, 15)  # Explore 8-15 tiles away from water
            
            # Calculate target position
            if direction == "right":
                target_x = min(current_x + distance, world_map.width - 1 if world_map else 100)
                target_y = current_y
            elif direction == "left":
                target_x = max(current_x - distance, 0)
                target_y = current_y
            elif direction == "up":
                target_x = current_x
                target_y = max(current_y - distance, 0)
            elif direction == "down":
                target_x = current_x
                target_y = min(current_y + distance, world_map.height - 1 if world_map else 100)
            
            # Set target position
            self.target_grid_x = target_x
            self.target_grid_y = target_y
            
            # Set the NPC to moving state
            self.is_moving = True
            print(f"DEBUG: NPC {self.get_entity_id()} exploring {distance} tiles {direction} away from water")
            
            # Show a speech bubble about exploring
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.EXPLORING_SPEECHES), self, duration=2.0)

        else:
            # No water nearby, just use regular exploration
            self.start_exploring()


            

    def start_exploring(self):
        """Start exploring in a random direction"""
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        # Choose a random direction and distance
        import random
        directions = ["right", "left", "up", "down"]
        
        # Try up to 4 times to find a direction that doesn't lead to known water
        for _ in range(4):
            direction = random.choice(directions)
            distance = random.randint(5, 15)  # Explore 5-15 tiles in a random direction
            
            # Calculate target position based on direction
            target_x = self.grid_x
            target_y = self.grid_y
            
            if direction == "right":
                target_x = min(self.grid_x + distance, world_map.width - 1 if world_map else 100)
            elif direction == "left":
                target_x = max(self.grid_x - distance, 0)
            elif direction == "up":
                target_y = max(self.grid_y - distance, 0)
            elif direction == "down":
                target_y = min(self.grid_y + distance, world_map.height - 1 if world_map else 100)
            
            # Check if this target is in our water avoidance list
            if hasattr(self, 'water_avoidance_locations') and (target_x, target_y) in self.water_avoidance_locations:
                # This direction leads to water, try another one
                continue
            
            # Set target position
            self.target_grid_x = target_x
            self.target_grid_y = target_y
            break
        else:
            # If all directions lead to water, just move one step in a random direction
            direction = random.choice(directions)
            if direction == "right":
                self.target_grid_x = min(self.grid_x + 1, world_map.width - 1 if world_map else 100)
                self.target_grid_y = self.grid_y
            elif direction == "left":
                self.target_grid_x = max(self.grid_x - 1, 0)
                self.target_grid_y = self.grid_y
            elif direction == "up":
                self.target_grid_x = self.grid_x
                self.target_grid_y = max(self.grid_y - 1, 0)
            elif direction == "down":
                self.target_grid_x = self.grid_x
                self.target_grid_y = min(self.grid_y + 1, world_map.height - 1 if world_map else 100)
        
        # Set the NPC to moving state
        self.is_moving = True
        print(f"DEBUG: NPC {self.get_entity_id()} exploring {distance if 'distance' in locals() else 1} tiles {direction}")
        
        # Show a speech bubble about exploring
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.EXPLORING_SPEECHES), self, duration=2.0)




    def start_exploring_for_forest(self):
        """Start exploring to find forest tiles"""
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        # Check if we already know about forest locations
        if hasattr(self, 'interesting_locations') and 'forest' in self.interesting_locations and self.interesting_locations['forest']:
            # We already know about forest locations, head to the nearest one
            nearest_forest = min(self.interesting_locations['forest'], 
                               key=lambda loc: abs(loc[0] - self.grid_x) + abs(loc[1] - self.grid_y))
            forest_x, forest_y = nearest_forest
            
            print(f"DEBUG: NPC {self.get_entity_id()} heading to known forest at ({forest_x}, {forest_y})")
            
            # Set target to the forest location
            self.target_grid_x = forest_x
            self.target_grid_y = forest_y
            self.is_moving = True
            
            # Show a speech bubble about heading to forest
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                forest_speeches = [
                    "I know where to find a forest.",
                    "I'll head to that forest I found earlier.",
                    "Time to explore the forest.",
                    "The forest should be this way."
                ]
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(forest_speeches), self, duration=2.0)
            
            return
        
        # If we don't know any forest locations, search in a wider area
        if world_map:
            # Look for forest tiles in a larger radius (up to 20 tiles away)
            forest_tiles = []
            search_radius = 20
            
            for y in range(max(0, self.grid_y - search_radius), min(world_map.height, self.grid_y + search_radius + 1)):
                for x in range(max(0, self.grid_x - search_radius), min(world_map.width, self.grid_x + search_radius + 1)):
                    tile = world_map.get_tile(x, y)
                    if tile and hasattr(tile, 'type') and tile.type == 'forest':
                        # Found a forest tile
                        forest_tiles.append((x, y))
            
            if forest_tiles:
                # Found forest tiles, head to the nearest one
                nearest_forest = min(forest_tiles, key=lambda loc: abs(loc[0] - self.grid_x) + abs(loc[1] - self.grid_y))
                forest_x, forest_y = nearest_forest
                
                print(f"DEBUG: NPC {self.get_entity_id()} discovered forest at ({forest_x}, {forest_y})")
                
                # Add to interesting locations
                if not hasattr(self, 'interesting_locations'):
                    self.interesting_locations = {}
                if 'forest' not in self.interesting_locations:
                    self.interesting_locations['forest'] = []
                
                # Check if we already have this location
                location_exists = False
                for loc in self.interesting_locations.get('forest', []):
                    if loc[0] == forest_x and loc[1] == forest_y:
                        location_exists = True
                        break
                
                if not location_exists:
                    self.interesting_locations['forest'].append((forest_x, forest_y))
                    
                    # Record in world cache if available
                    from engine.core import SimpleGameEngine
                    if (hasattr(SimpleGameEngine, 'instance') and 
                        hasattr(SimpleGameEngine.instance, 'world_cache')):
                        SimpleGameEngine.instance.world_cache.add_location_discovery(
                            str(id(self)),
                            'forest',
                            forest_x,
                            forest_y,
                            "Forest area"
                        )
                
                # Set target to the forest location
                self.target_grid_x = forest_x
                self.target_grid_y = forest_y
                self.is_moving = True
                
                # Show a speech bubble about finding forest
                if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                    forest_speeches = [
                        "I see a forest in the distance!",
                        "There's a forest over there.",
                        "I should check out that forest.",
                        "A forest! Let's explore it."
                    ]
                    SimpleGameEngine.instance.ui.add_text_bubble(random.choice(forest_speeches), self, duration=2.0)
                
                return
        
        # If no forest found, just explore randomly
        self.start_exploring()

    
    
    def get_entity_id(self):
        """Get the persistent entity ID"""
        # If we have a CNA file, use it to make the ID more specific
        if hasattr(self, 'cna_file') and self.cna_file:
            cna_filename = os.path.basename(self.cna_file)
            # Create a more specific ID for NPCs with CNA data
            id_string = f"NPC_{cna_filename}"
            hash_object = hashlib.md5(id_string.encode())
            return f"0b{hash_object.hexdigest()[:16]}"
        # Otherwise use the base class implementation
        return super().get_entity_id()
    
    def start_exploring(self):
        """Start exploring in a random direction"""
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        # Choose a random direction and distance
        import random
        directions = ["right", "left", "up", "down"]
        
        # Try up to 4 times to find a direction that doesn't lead to known water
        for _ in range(4):
            direction = random.choice(directions)
            distance = random.randint(5, 15)  # Explore 5-15 tiles in a random direction
            
            # Calculate target position based on direction
            target_x = self.grid_x
            target_y = self.grid_y
            
            if direction == "right":
                target_x = min(self.grid_x + distance, world_map.width - 1 if world_map else 100)
            elif direction == "left":
                target_x = max(self.grid_x - distance, 0)
            elif direction == "up":
                target_y = max(self.grid_y - distance, 0)
            elif direction == "down":
                target_y = min(self.grid_y + distance, world_map.height - 1 if world_map else 100)
            
            # Check if this target is in our water avoidance list
            if hasattr(self, 'water_avoidance_locations') and (target_x, target_y) in self.water_avoidance_locations:
                # This direction leads to water, try another one
                continue
            
            # Set target position
            self.target_grid_x = target_x
            self.target_grid_y = target_y
            break
        else:
            # If all directions lead to water, just move one step in a random direction
            direction = random.choice(directions)
            if direction == "right":
                self.target_grid_x = min(self.grid_x + 1, world_map.width - 1 if world_map else 100)
                self.target_grid_y = self.grid_y
            elif direction == "left":
                self.target_grid_x = max(self.grid_x - 1, 0)
                self.target_grid_y = self.grid_y
            elif direction == "up":
                self.target_grid_x = self.grid_x
                self.target_grid_y = max(self.grid_y - 1, 0)
            elif direction == "down":
                self.target_grid_x = self.grid_x
                self.target_grid_y = min(self.grid_y + 1, world_map.height - 1 if world_map else 100)
        
        # Set the NPC to moving state
        self.is_moving = True
        print(f"DEBUG: NPC {self.get_entity_id()} exploring {distance if 'distance' in locals() else 1} tiles {direction}")
        
        # Show a speech bubble about exploring
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.EXPLORING_SPEECHES), self, duration=2.0)



    def render(self, screen, camera):
        """Render the NPC with camera transformations"""
        super().render(screen, camera)
        
        # Optionally add visual indicators for exploration mode
        if hasattr(self, 'exploration_mode') and self.exploration_mode != "idle":
            # Get screen position
            screen_x, screen_y = camera.world_to_screen(self.x, self.y)
            
            # Draw a small indicator above the NPC
            indicator_color = (255, 255, 0) if self.exploration_mode == "exploring" else (0, 255, 255)
            pygame.draw.circle(screen, indicator_color, (screen_x, screen_y - 5), 2)
    
    def debug_player_visibility(self, player_id, can_see_player):
        """Debug method to track player visibility changes"""
        if can_see_player and not self.debug_player_detected:
            # Player just entered detection range
            self.debug_player_detected = True
            self.debug_last_player_id = player_id
            print(f"DEBUG: NPC {id(self)} detected player {player_id} in vicinity")
        elif not can_see_player and self.debug_player_detected and self.debug_last_player_id == player_id:
            # Player just left detection range
            self.debug_player_detected = False
            print(f"DEBUG: NPC {id(self)} lost sight of player {player_id}")
            
    def _pause_for_chat(self):
        """Pause current activities to respond to chat"""
        # Store current state
        self.paused_state = {
            'is_moving': self.is_moving,
            'target_grid_x': self.target_grid_x if hasattr(self, 'target_grid_x') else None,
            'target_grid_y': self.target_grid_y if hasattr(self, 'target_grid_y') else None,
            'exploration_mode': self.exploration_mode,
            'exploration_target_x': self.exploration_target_x,
            'exploration_target_y': self.exploration_target_y
        }
        
        # If we were heading to known water, store that too
        if hasattr(self, 'heading_to_known_water') and self.heading_to_known_water:
            self.paused_state['heading_to_known_water'] = True
            self.paused_state['known_water_x'] = self.known_water_x if hasattr(self, 'known_water_x') else None
            self.paused_state['known_water_y'] = self.known_water_y if hasattr(self, 'known_water_y') else None
        
        # If we were following advice, store that too
        if hasattr(self, 'following_advice') and self.following_advice:
            self.paused_state['following_advice'] = True
            self.paused_state['advice_direction'] = self.advice_direction
            self.paused_state['advice_remaining_distance'] = self.advice_remaining_distance
        
        # Pause movement
        self.is_moving = False
        
        # Set chat response state
        self.is_responding_to_chat = True
        self.chat_response_time = pygame.time.get_ticks()
        
        print(f"DEBUG: NPC {self.get_entity_id()} paused activities to respond to chat")

    def _resume_paused_state(self):
        """Resume activities after responding to chat"""
        if not self.paused_state:
            return
        
        # Restore movement state
        self.is_moving = self.paused_state.get('is_moving', False)
        if self.paused_state.get('target_grid_x') is not None:
            self.target_grid_x = self.paused_state.get('target_grid_x')
        if self.paused_state.get('target_grid_y') is not None:
            self.target_grid_y = self.paused_state.get('target_grid_y')
        
        # Restore exploration state
        self.exploration_mode = self.paused_state.get('exploration_mode', 'idle')
        self.exploration_target_x = self.paused_state.get('exploration_target_x')
        self.exploration_target_y = self.paused_state.get('exploration_target_y')
        
        # Restore water seeking state if applicable
        if self.paused_state.get('heading_to_known_water'):
            self.heading_to_known_water = True
            if self.paused_state.get('known_water_x') is not None:
                self.known_water_x = self.paused_state.get('known_water_x')
            if self.paused_state.get('known_water_y') is not None:
                self.known_water_y = self.paused_state.get('known_water_y')
        
        # Restore advice following state if applicable
        if self.paused_state.get('following_advice'):
            self.following_advice = True
            self.advice_direction = self.paused_state.get('advice_direction')
            self.advice_remaining_distance = self.paused_state.get('advice_remaining_distance')
        
        # Clear paused state
        self.paused_state = None
        
        print(f"DEBUG: NPC {self.get_entity_id()} resumed activities after chat response")
            
            
    def apply_ai_decision(self, decision):
        """Apply an AI decision to this NPC"""
        # Check if this is a chat response - highest priority
        if decision.action == "respond_to_chat":
            # Get current time for cooldown check
            current_time = pygame.time.get_ticks()
            
            # Check if we've already processed a chat response recently
            if (hasattr(self, 'last_chat_response_time') and 
                current_time - self.last_chat_response_time < self.chat_cooldown):
                print(f"DEBUG: NPC {self.get_entity_id()} ignoring duplicate chat response (cooldown active)")
                return
            
            # Just display the speech bubble and don't change any other state
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                SimpleGameEngine.instance.ui.add_text_bubble(decision.speech, self, duration=4.0)
                print(f"DEBUG: NPC {self.get_entity_id()} responding to chat: '{decision.speech}'")
            
            # Update last chat response time
            self.last_chat_response_time = current_time
            
            # Resume paused activities after responding
            self.is_responding_to_chat = False
            self._resume_paused_state()
            return
        
        # If we're responding to chat, don't process other decisions
        if self.is_responding_to_chat:
            print(f"DEBUG: NPC {self.get_entity_id()} ignoring decision while responding to chat")
            return

        
        # For other actions, continue with the existing implementation
        # Check if this is advice to move multiple tiles
        if hasattr(decision, 'following_advice') and decision.following_advice:
            if hasattr(decision, 'advice_direction') and hasattr(decision, 'advice_distance'):
                direction = decision.advice_direction
                distance = decision.advice_distance
                
                print(f"DEBUG: NPC {self.get_entity_id()} following advice to move {distance} tiles {direction}")
                
                # Set target position based on advice
                if direction == "right":
                    self.target_grid_x = self.grid_x + distance
                    self.target_grid_y = self.grid_y
                elif direction == "left":
                    self.target_grid_x = self.grid_x - distance
                    self.target_grid_y = self.grid_y
                elif direction == "up":
                    self.target_grid_x = self.grid_x
                    self.target_grid_y = self.grid_y - distance
                elif direction == "down":
                    self.target_grid_x = self.grid_x
                    self.target_grid_y = self.grid_y + distance
                
                # Set the NPC to moving state
                self.is_moving = True
                
                # Store the advice for future reference
                self.following_advice = True
                self.advice_direction = direction
                self.advice_remaining_distance = distance
                
                return
        if hasattr(decision, 'is_escaping_water') and decision.is_escaping_water:
            # Apply the movement action immediately
            if decision.action == "move_left":
                self.target_grid_x = self.grid_x - 1
                self.target_grid_y = self.grid_y
            elif decision.action == "move_right":
                self.target_grid_x = self.grid_x + 1
                self.target_grid_y = self.grid_y
            elif decision.action == "move_up":
                self.target_grid_x = self.grid_x
                self.target_grid_y = self.grid_y - 1
            elif decision.action == "move_down":
                self.target_grid_x = self.grid_x
                self.target_grid_y = self.grid_y + 1
            
            # Set the NPC to moving state
            self.is_moving = True
            
            # Show a speech bubble about escaping water
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.WATER_ESCAPE_SPEECHES), self, duration=1.5)
            return
        if hasattr(decision, 'is_heading_to_known_water') and decision.is_heading_to_known_water:
            # If we have target coordinates, set them as our destination
            if decision.target_x is not None and decision.target_y is not None:
                self.target_grid_x = decision.target_x
                self.target_grid_y = decision.target_y
                self.is_moving = True
                
                # Store that we're heading to water
                self.heading_to_known_water = True
                self.known_water_x = decision.target_x
                self.known_water_y = decision.target_y
                
                print(f"DEBUG: NPC {self.get_entity_id()} is heading to known water at ({decision.target_x}, {decision.target_y})")
                return
        # Check if this is advice to move multiple tiles
        if hasattr(decision, 'following_advice') and decision.following_advice:
            if hasattr(decision, 'advice_direction') and hasattr(decision, 'advice_distance'):
                direction = decision.advice_direction
                distance = decision.advice_distance
                
                print(f"DEBUG: NPC {id(self)} following advice to move {distance} tiles {direction}")
                
                # Set target position based on advice
                if direction == "right":
                    self.target_grid_x = self.grid_x + distance
                    self.target_grid_y = self.grid_y
                elif direction == "left":
                    self.target_grid_x = self.grid_x - distance
                    self.target_grid_y = self.grid_y
                elif direction == "up":
                    self.target_grid_x = self.grid_x
                    self.target_grid_y = self.grid_y - distance
                elif direction == "down":
                    self.target_grid_x = self.grid_x
                    self.target_grid_y = self.grid_y + distance
                
                # Set the NPC to moving state
                self.is_moving = True
                
                # Store the advice for future reference
                self.following_advice = True
                self.advice_direction = direction
                self.advice_remaining_distance = distance
                
                return
        
        # Handle exploration command
        if decision.action == "explore":
            # If specific coordinates were provided, use them
            if hasattr(decision, 'target_x') and hasattr(decision, 'target_y') and decision.target_x is not None and decision.target_y is not None:
                self.target_grid_x = decision.target_x
                self.target_grid_y = decision.target_y
                self.is_moving = True
                print(f"DEBUG: NPC {id(self)} exploring to specific coordinates ({decision.target_x}, {decision.target_y})")
                return
            
            # Otherwise, start exploring in a random direction
            self.start_exploring()
            return
        
        # Check if the NPC is thirsty and knows water locations
        if hasattr(self, 'thirst') and self.thirst <= 3 and hasattr(self, 'interesting_locations'):
            # Check if the NPC knows any water locations
            if 'water' in self.interesting_locations and self.interesting_locations['water']:
                # Get the nearest known water source
                nearest_water = min(self.interesting_locations['water'], 
                                   key=lambda loc: abs(loc[0] - self.grid_x) + abs(loc[1] - self.grid_y))
                water_x, water_y = nearest_water
                
                print(f"DEBUG: Thirsty NPC {id(self)} remembers water at ({water_x}, {water_y}), currently at ({self.grid_x}, {self.grid_y})")
                
                # If not already at the water source, move towards it
                if abs(water_x - self.grid_x) > 1 or abs(water_y - self.grid_y) > 1:
                    # Determine direction to move
                    if not self.is_moving:
                        if abs(water_x - self.grid_x) > abs(water_y - self.grid_y):
                            # Move horizontally first
                            if water_x > self.grid_x:
                                self.target_grid_x = self.grid_x + 1
                            else:
                                self.target_grid_x = self.grid_x - 1
                        else:
                            # Move vertically first
                            if water_y > self.grid_y:
                                self.target_grid_y = self.grid_y + 1
                            else:
                                self.target_grid_y = self.grid_y - 1
                        self.is_moving = True
                        
                        # Show a speech bubble about going to water
                        from engine.core import SimpleGameEngine
                        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.WATER_SEEKING_SPEECHES), self, duration=2.0)
                    # Override the AI decision
                    return
                else:
                    # At water source, drink
                    from engine.core import SimpleGameEngine
                    world_map = None
                    if hasattr(SimpleGameEngine, 'instance'):
                        world_map = SimpleGameEngine.instance.world_map
                    
                    if world_map and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
                        # Drink until thirst is 10
                        while self.thirst < 10:
                            self.thirst = min(10, self.thirst + 2)
                            print(f"NPC drank water from remembered source, thirst increased to {self.thirst}")
                        
                        # Set the last drink time
                        self.last_drink_time = pygame.time.get_ticks()
                        
                        # Show a speech bubble about drinking
                        from engine.core import SimpleGameEngine
                        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                            drinking_speeches = [
                                "Ah, refreshing water!",
                                "Finally, water!",
                                "This water tastes so good when you're thirsty.",
                                "I'm glad I remembered this water source.",
                                "Water, sweet water!"
                            ]
                            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(drinking_speeches), self, duration=2.0)
                        
                        # After drinking, start exploring for forest
                        self.start_exploring_for_forest()
                        
                        # Override the AI decision
                        return
        
        # Check if the NPC is hungry and should seek food
        if hasattr(self, 'hunger') and self.hunger <= 3 and not self.is_moving:
            # Try to find food nearby
            if self.start_searching_for_food():
                # Successfully found and targeting food
                return

        # Continue with the original decision handling
        # Check if this is a special action from NPCActionHandler
        if decision.action in ["follow_player", "stop_following", "give_item", "trade", "show_info"]:
            from entities.npc_actions import NPCActionExecutor
            from engine.core import SimpleGameEngine
            
            # Get game engine instance
            game_engine = None
            if hasattr(SimpleGameEngine, 'instance'):
                game_engine = SimpleGameEngine.instance
            
            # Create an ActionResponse object
            from entities.npc_actions import ActionResponse
            action_response = ActionResponse(
                action=decision.action,
                speech=decision.speech,
                target_id=getattr(decision, 'target_id', None),
                mood_change=decision.mood_change
            )
            
            # Execute the action
            if NPCActionExecutor.execute_action(self, action_response, game_engine):
                return
        
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
                # Drink until thirst is 10
                while self.thirst < 10:
                    self.thirst = min(10, self.thirst + 2)
                    print(f"NPC drank water, thirst increased to {self.thirst}")
                
                # Set the last drink time
                self.last_drink_time = pygame.time.get_ticks()
                
                # If thirst is now satisfied, start exploring for forest
                if self.thirst >= 5:
                    # After drinking, start exploring for forest
                    self.start_exploring_for_forest()
                    
                    # Show a speech bubble about exploring
                    from engine.core import SimpleGameEngine
                    if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                        SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.EXPLORING_SPEECHES), self, duration=2.0)

        elif decision.action == "eat" and self.hunger < 5:
            # Handle eating (for now, just increase hunger without requiring food source)
            self.hunger = min(10, self.hunger + 3)
            print(f"NPC {self.get_entity_id()} ate food, hunger increased to {self.hunger}")
            
            # Set the last eat time
            self.last_eat_time = pygame.time.get_ticks()
            
            # Show a speech bubble about eating
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.EATING_SPEECHES), self, duration=2.0)


        
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
        
    def get_memory_summary(self):
        """Get a summary of this NPC's memories and knowledge"""
        summary = {
            "explored_tiles": len(self.explored_tiles),
            "interesting_locations": {}
        }
        
        # Summarize interesting locations
        for location_type, locations in self.interesting_locations.items():
            summary["interesting_locations"][location_type] = len(locations)
        
        return summary

    def start_searching_for_food(self):
        """Start searching for food when hungry"""
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        # Get current position
        current_x = self.grid_x
        current_y = self.grid_y
        
        # Find nearby food entities
        food_entities = []
        view_range = GameBalanceConstants.NPC_FOOD_VIEW_RANGE
        
        if hasattr(SimpleGameEngine, 'instance') and SimpleGameEngine.instance:
            for obj in SimpleGameEngine.instance.objects:
                # Check if this is a food entity
                if hasattr(obj, '__class__') and obj.__class__.__name__ == 'FoodNPC':
                    # Calculate distance to food
                    dx = abs(obj.grid_x - current_x)
                    dy = abs(obj.grid_y - current_y)
                    
                    # Check if food is within view range
                    if dx <= view_range and dy <= view_range:
                        food_entities.append(obj)
        
        if food_entities:
            # Found food entities, head to the nearest one
            nearest_food = min(food_entities, 
                             key=lambda food: abs(food.grid_x - current_x) + abs(food.grid_y - current_y))
            
            print(f"DEBUG: NPC {self.get_entity_id()} found food at ({nearest_food.grid_x}, {nearest_food.grid_y})")
            
            # Set target to the food location
            self.target_grid_x = nearest_food.grid_x
            self.target_grid_y = nearest_food.grid_y
            self.is_moving = True
            self.heading_to_food = True
            
            # Show a speech bubble about finding food
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(SpeechConstants.FOOD_SEEKING_SPEECHES), self, duration=2.0)

            return True
        else:
            # No food found, explore randomly to look for food
            print(f"DEBUG: NPC {self.get_entity_id()} searching for food, none found in view range")
            self.start_exploring()
            return False

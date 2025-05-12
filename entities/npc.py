from entities.rectangle import Rectangle
import pygame
import random
import hashlib
import os

class NPC(Rectangle):
    """An NPC entity controlled by AI"""
    
    def __init__(self, grid_x, grid_y, color=(0, 255, 0), speed=1, ai_controller=None):
        super().__init__(grid_x, grid_y, color, speed, controllable=False)
        self.ai_controller = ai_controller
        
        # Add thirst attribute (0-10 scale)
        self.thirst = 4  # Start with full thirst
        self.last_thirst_update = 0  # Track time for thirst decrease
        self.last_drink_time = 0  # Track time for drinking
        
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
        
        # If an AI controller was provided, set this entity as its target
        if self.ai_controller:
            self.ai_controller.set_entity(self)
    
    def update(self):
        """Update entity state"""
        
        # Call the parent class update first, but we'll handle movement ourselves
        # Get the current time for timing controls
        current_time = pygame.time.get_ticks()
        
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
                    
                    # Instead of teleporting, move one step toward the water
                    dx = nearest_water["x"] - self.grid_x
                    dy = nearest_water["y"] - self.grid_y
                    
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
                    self.final_destination_x = nearest_water["x"]
                    self.final_destination_y = nearest_water["y"]
                    self.is_moving = True
                    self.heading_to_known_water = True
                    
                    # Initialize movement timer
                    self.last_move_time = current_time
                    
                    # Show a speech bubble about going to water
                    if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                        water_seeking_speeches = [
                            "I know there's water nearby.",
                            "I need to find that water source.",
                            "I remember seeing water in this area.",
                            "I'm so thirsty, I need to find that water."
                        ]
                        SimpleGameEngine.instance.ui.add_text_bubble(random.choice(water_seeking_speeches), self, duration=2.0)
        
        
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
                
                # Find the nearest land tile
                nearest_land_x = None
                nearest_land_y = None
                min_distance = float('inf')
                
                # Search in a 5-tile radius
                for y in range(self.grid_y - 5, self.grid_y + 6):
                    for x in range(self.grid_x - 5, self.grid_x + 6):
                        tile = world_map.get_tile(x, y)
                        if tile and hasattr(tile, 'is_walkable') and tile.is_walkable() and not tile.is_water():
                            distance = abs(x - self.grid_x) + abs(y - self.grid_y)
                            if distance < min_distance:
                                min_distance = distance
                                nearest_land_x = x
                                nearest_land_y = y
                
                # If we found land, move towards it
                if nearest_land_x is not None and nearest_land_y is not None:
                    # Only start moving if we're not already moving
                    if not self.is_moving:
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
                        
                        self.is_moving = True
                        
                        # Show a speech bubble about escaping water
                        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                            water_escape_speeches = [
                                "I need to get out of this water!",
                                "Help! I'm in water!",
                                "This water is too deep!",
                                "I can't swim!"
                            ]
                            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(water_escape_speeches), self, duration=1.5)
        
        # Handle movement with timing control (1 tile per second)
        if self.is_moving:
            # Only move if enough time has passed (1000ms = 1 second)
            if not hasattr(self, 'last_move_time'):
                self.last_move_time = current_time
                
            if current_time - self.last_move_time >= 1000:  # 1 second delay
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
                                    water_speeches = [
                                        "Ah, refreshing water!",
                                        "Finally, water!",
                                        "This water is just what I needed.",
                                        "So good to drink water when you're thirsty!"
                                    ]
                                    SimpleGameEngine.instance.ui.add_text_bubble(random.choice(water_speeches), self, duration=2.0)
                                
                                # After drinking, start exploring for forest
                                self.start_exploring_for_forest()
                            
                            # Reset heading to water flag
                            self.heading_to_known_water = False
                else:
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
        
        
        
        # Decrease thirst every 10 seconds
        if current_time - self.last_thirst_update > 10000:  # 10 seconds
            if self.thirst > 0:
                self.thirst -= 1
                print(f"NPC thirst decreased to {self.thirst}")
            self.last_thirst_update = current_time
            





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
            id_string = f"NPC_{cna_filename}_{self.grid_x}_{self.grid_y}"
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
        direction = random.choice(directions)
        distance = random.randint(5, 15)  # Explore 5-15 tiles in a random direction
        
        # Set target position based on direction
        if direction == "right":
            self.target_grid_x = min(self.grid_x + distance, world_map.width - 1 if world_map else 100)
            self.target_grid_y = self.grid_y
        elif direction == "left":
            self.target_grid_x = max(self.grid_x - distance, 0)
            self.target_grid_y = self.grid_y
        elif direction == "up":
            self.target_grid_x = self.grid_x
            self.target_grid_y = max(self.grid_y - distance, 0)
        elif direction == "down":
            self.target_grid_x = self.grid_x
            self.target_grid_y = min(self.grid_y + distance, world_map.height - 1 if world_map else 100)
        
        # Set the NPC to moving state
        self.is_moving = True
        print(f"DEBUG: NPC {self.get_entity_id()} exploring {distance} tiles {direction}")
        
        # Show a speech bubble about exploring
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
            exploring_speeches = [
                "Time to explore!",
                "Let's see what's out there.",
                "I wonder what I'll find over there...",
                "Exploring is fun!",
                "I'm going on an adventure!"
            ]
            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(exploring_speeches), self, duration=2.0)


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
            
    def apply_ai_decision(self, decision):
        """Apply an AI decision to this NPC"""
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
                water_escape_speeches = [
                    "I need to get out of this water!",
                    "Help! I'm in water!",
                    "This water is too deep!",
                    "I can't swim!"
                ]
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(water_escape_speeches), self, duration=1.5)
            
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
                            water_seeking_speeches = [
                                "I know where to find water.",
                                "I remember seeing water nearby.",
                                "I'll head to that water source I found earlier.",
                                "Good thing I know where water is.",
                                "I'll go to the water I discovered before."
                            ]
                            SimpleGameEngine.instance.ui.add_text_bubble(random.choice(water_seeking_speeches), self, duration=2.0)
                    
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
                        exploring_speeches = [
                            "Now that I've had some water, time to explore!",
                            "Feeling refreshed! Let's see what's out there.",
                            "That was refreshing. Now to continue my journey.",
                            "Water break done, back to exploring!",
                            "I wonder what I'll find over there..."
                        ]
                        SimpleGameEngine.instance.ui.add_text_bubble(random.choice(exploring_speeches), self, duration=2.0)
        
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

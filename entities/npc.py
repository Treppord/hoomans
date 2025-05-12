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
        super().update()
        
        # Handle movement
        if self.is_moving:
            # Calculate direction to target
            dx = self.target_grid_x - self.grid_x
            dy = self.target_grid_y - self.grid_y
            
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
                
                # Check if we've reached the target
                if self.grid_x == self.target_grid_x and self.grid_y == self.target_grid_y:
                    self.is_moving = False
                    
                    # If we were following advice, check if we've found what we were looking for
                    if hasattr(self, 'following_advice') and self.following_advice:
                        # Check if we've found water (if we're thirsty)
                        if hasattr(self, 'thirst') and self.thirst <= 3:
                            if world_map and hasattr(world_map, 'is_adjacent_to_water') and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
                                # Drink water
                                self.thirst += 2
                                print(f"NPC found water via advice, thirst increased to {self.thirst}")
                                
                                # Show a speech bubble about finding water
                                from engine.core import SimpleGameEngine
                                if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                                    water_speeches = [
                                        "Ah, water! Just what I needed!",
                                        "Found water! Thank you for the advice!",
                                        "Water! Your directions were spot on!",
                                        "I'm so glad I followed your advice. Water!"
                                    ]
                                    SimpleGameEngine.instance.ui.add_text_bubble(random.choice(water_speeches), self, duration=2.0)
                                
                                # After drinking, start exploring
                                self.start_exploring()
                        
                        # Reset advice following
                        self.following_advice = False
            else:
                # Can't move to the next position, stop moving
                self.is_moving = False
        
        # Update thirst over time
        current_time = pygame.time.get_ticks()
        
        # Decrease thirst every 10 seconds
        if current_time - self.last_thirst_update > 10000:  # 10 seconds
            if self.thirst > 0:
                self.thirst -= 1
                print(f"NPC thirst decreased to {self.thirst}")
            self.last_thirst_update = current_time
    
    
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
        print(f"DEBUG: NPC {id(self)} exploring {distance} tiles {direction}")
        
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
                        self.thirst += 2  # Increase thirst more when drinking from remembered source
                        print(f"NPC drank water from remembered source, thirst increased to {self.thirst}")
                        if self.thirst >= 5:
                            self.start_exploring()
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
                        
                        # After drinking, start exploring
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
                        print(f"DEBUG: NPC {id(self)} exploring {distance} tiles {direction} after drinking")
                        
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
                self.thirst += 1
                print(f"NPC drank water, thirst increased to {self.thirst}")
                
                # If thirst is now satisfied, start exploring
                if self.thirst >= 5:
                    # After drinking, start exploring
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
                    print(f"DEBUG: NPC {id(self)} exploring {distance} tiles {direction} after drinking")
                    
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

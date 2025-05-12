from entities.rectangle import Rectangle
import pygame
import random
import time

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
        
        # Update thirst over time
        current_time = pygame.time.get_ticks()
        
        # Decrease thirst every 10 seconds
        if current_time - self.last_thirst_update > 10000:  # 10 seconds
            if self.thirst > 0:
                self.thirst -= 1
                print(f"NPC thirst decreased to {self.thirst}")
            self.last_thirst_update = current_time
        
        # If we've finished moving and have remaining advice distance, continue moving
        if hasattr(self, 'advice_remaining_distance') and self.advice_remaining_distance > 0 and not self.is_moving:
            if hasattr(self, 'advice_direction'):
                if self.advice_direction == "left":
                    self.target_grid_x = self.grid_x - 1
                    self.is_moving = True
                elif self.advice_direction == "right":
                    self.target_grid_x = self.grid_x + 1
                    self.is_moving = True
                elif self.advice_direction == "up":
                    self.target_grid_y = self.grid_y - 1
                    self.is_moving = True
                elif self.advice_direction == "down":
                    self.target_grid_y = self.grid_y + 1
                    self.is_moving = True
                
                self.advice_remaining_distance -= 1
                
                # If we've reached the destination, check for what we were looking for
                if self.advice_remaining_distance == 0:
                    from engine.core import SimpleGameEngine
                    if hasattr(SimpleGameEngine, 'instance'):
                        game_engine = SimpleGameEngine.instance
                        # Check if we found what we were looking for (e.g., water)
                        if game_engine.world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
                            print(f"DEBUG: NPC {id(self)} found water as advised by player!")
                            
                            # Record the water source discovery in world cache
                            if hasattr(game_engine, 'world_cache'):
                                # Find the actual water tile
                                water_x, water_y = None, None
                                for dx, dy in [(0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)]:
                                    nx, ny = self.grid_x + dx, self.grid_y + dy
                                    if game_engine.world_map.get_tile(nx, ny) and game_engine.world_map.get_tile(nx, ny).is_water():
                                        water_x, water_y = nx, ny
                                        break
                                
                                if water_x is not None and water_y is not None:
                                    # Record the discovery in world cache
                                    game_engine.world_cache.add_location_discovery(
                                        str(id(self)),  # Use string representation of NPC's ID
                                        "water",        # Location type
                                        water_x,        # X coordinate
                                        water_y,        # Y coordinate
                                        "Water source found via player advice"  # Name
                                    )
                                    
                                    # Add to interesting locations
                                    if "water" not in self.interesting_locations:
                                        self.interesting_locations["water"] = []
                                    self.interesting_locations["water"].append((water_x, water_y))
                            
                            # Update AI universe state to reflect this
                            if hasattr(game_engine, 'ai_universe'):
                                game_engine.ai_universe.update_agent_state(
                                    agent_id=str(id(self)),
                                    advice_followed=True,
                                    advice_success=True,
                                    memory_event="Found water where the player said it would be."
                                )
                                
                            # If we're thirsty, drink immediately
                            if self.thirst < 5:
                                self.thirst += 1
                                print(f"NPC drank water, thirst increased to {self.thirst}")
                                
                                # Show a speech bubble
                                if hasattr(game_engine, 'ui'):
                                    game_engine.ui.add_text_bubble("Ah, refreshing water! Thank you for the advice.", self, duration=3.0)
                        else:
                            print(f"DEBUG: NPC {id(self)} did not find what they were looking for at the advised location.")
                            # Update AI universe state
                            if hasattr(game_engine, 'ai_universe'):
                                game_engine.ai_universe.update_agent_state(
                                    agent_id=str(id(self)),
                                    advice_followed=True,
                                    advice_success=False,
                                    memory_event="Did not find what the player said would be here."
                                )
                            
                            # Show a speech bubble
                            if hasattr(game_engine, 'ui'):
                                game_engine.ui.add_text_bubble("Hmm, I don't see what you mentioned here.", self, duration=3.0)
        
        # Handle exploration when not moving and needs are satisfied
        if not self.is_moving and self.thirst >= 5 and current_time - self.last_exploration_time > 5000:  # 5 seconds cooldown
            self.last_exploration_time = current_time
            
            # Get game engine instance
            from engine.core import SimpleGameEngine
            game_engine = None
            if hasattr(SimpleGameEngine, 'instance'):
                game_engine = SimpleGameEngine.instance
            
            if game_engine and game_engine.world_map:
                # Record current tile in explored tiles
                self.explored_tiles.add((self.grid_x, self.grid_y))
                
                # Check current tile type and record if interesting
                current_tile = game_engine.world_map.get_tile(self.grid_x, self.grid_y)
                if current_tile:
                    tile_type = current_tile.type
                    
                    # Record interesting tile types
                    if tile_type in ["forest", "mountain", "water"]:
                        if current_time - self.last_memory_record_time > self.memory_cooldown:
                            self.last_memory_record_time = current_time
                            
                            # Record in world cache
                            if hasattr(game_engine, 'world_cache'):
                                game_engine.world_cache.add_location_discovery(
                                    str(id(self)),
                                    tile_type,
                                    self.grid_x,
                                    self.grid_y,
                                    f"{tile_type.capitalize()} area"
                                )
                            
                            # Add to interesting locations
                            if tile_type not in self.interesting_locations:
                                self.interesting_locations[tile_type] = []
                            self.interesting_locations[tile_type].append((self.grid_x, self.grid_y))
                            
                            # Show a speech bubble for discovery
                            if hasattr(game_engine, 'ui'):
                                discovery_speeches = {
                                    "forest": ["This forest looks interesting.", "I should remember this forest location."],
                                    "mountain": ["These mountains are impressive.", "I'll remember this mountain range."],
                                    "water": ["Water! I should remember this spot.", "I found a water source here."]
                                }
                                if tile_type in discovery_speeches:
                                    game_engine.ui.add_text_bubble(random.choice(discovery_speeches[tile_type]), self, duration=2.0)
                
                # Choose exploration behavior based on needs and curiosity
                if self.exploration_mode == "idle":
                    # Decide whether to start exploring
                    if random.random() < self.curiosity * 0.3:  # 30% chance * curiosity factor
                        self.exploration_mode = "exploring"
                        
                        # Choose a random direction to explore
                        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                        dx, dy = random.choice(directions)
                        
                        # Set exploration target a few tiles away
                        explore_distance = random.randint(3, 8)
                        self.exploration_target_x = self.grid_x + (dx * explore_distance)
                        self.exploration_target_y = self.grid_y + (dy * explore_distance)
                        
                        # Ensure target is within map bounds
                        if game_engine.world_map:
                            map_width = game_engine.world_map.width
                            map_height = game_engine.world_map.height
                            self.exploration_target_x = max(0, min(map_width - 1, self.exploration_target_x))
                            self.exploration_target_y = max(0, min(map_height - 1, self.exploration_target_y))
                        
                        print(f"DEBUG: NPC {id(self)} starting exploration to ({self.exploration_target_x}, {self.exploration_target_y})")
                
                elif self.exploration_mode == "exploring":
                    # Check if we've reached the exploration target
                    if (self.grid_x == self.exploration_target_x and 
                        self.grid_y == self.exploration_target_y):
                        
                        # Target reached, decide whether to return home or explore more
                        if random.random() < 0.3:  # 30% chance to return home
                            self.exploration_mode = "returning"
                            self.exploration_target_x = self.home_location[0]
                            self.exploration_target_y = self.home_location[1]
                            print(f"DEBUG: NPC {id(self)} returning home to ({self.exploration_target_x}, {self.exploration_target_y})")
                        else:
                            # Continue exploring in a new direction
                            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                            dx, dy = random.choice(directions)
                            
                            # Set exploration target a few tiles away
                            explore_distance = random.randint(3, 8)
                            self.exploration_target_x = self.grid_x + (dx * explore_distance)
                            self.exploration_target_y = self.grid_y + (dy * explore_distance)
                            
                            # Ensure target is within map bounds
                            if game_engine.world_map:
                                map_width = game_engine.world_map.width
                                map_height = game_engine.world_map.height
                                self.exploration_target_x = max(0, min(map_width - 1, self.exploration_target_x))
                                self.exploration_target_y = max(0, min(map_height - 1, self.exploration_target_y))
                            
                            print(f"DEBUG: NPC {id(self)} continuing exploration to ({self.exploration_target_x}, {self.exploration_target_y})")
                    
                    # Move towards exploration target
                    else:
                        # Only move if not already moving
                        if not self.is_moving:
                            # Determine direction to move
                            if self.grid_x < self.exploration_target_x:
                                self.target_grid_x = self.grid_x + 1
                                self.is_moving = True
                            elif self.grid_x > self.exploration_target_x:
                                self.target_grid_x = self.grid_x - 1
                                self.is_moving = True
                            elif self.grid_y < self.exploration_target_y:
                                self.target_grid_y = self.grid_y + 1
                                self.is_moving = True
                            elif self.grid_y > self.exploration_target_y:
                                self.target_grid_y = self.grid_y - 1
                                self.is_moving = True
                
                elif self.exploration_mode == "returning":
                    # Check if we've reached home
                    if (self.grid_x == self.home_location[0] and 
                        self.grid_y == self.home_location[1]):
                        
                        # Home reached, go back to idle
                        self.exploration_mode = "idle"
                        print(f"DEBUG: NPC {id(self)} returned home, now idle")
                        
                        # Maybe say something about the exploration
                        if hasattr(game_engine, 'ui') and random.random() < 0.7:
                            home_speeches = [
                                "Home sweet home!",
                                "It's good to be back.",
                                "That was an interesting journey.",
                                "I've explored some new areas.",
                                "I should organize what I've discovered."
                            ]
                            game_engine.ui.add_text_bubble(random.choice(home_speeches), self, duration=2.0)
                    
                    # Move towards home
                    else:
                        # Only move if not already moving
                        if not self.is_moving:
                            # Determine direction to move
                            # Determine direction to move
                            if self.grid_x < self.home_location[0]:
                                self.target_grid_x = self.grid_x + 1
                                self.is_moving = True
                            elif self.grid_x > self.home_location[0]:
                                self.target_grid_x = self.grid_x - 1
                                self.is_moving = True
                            elif self.grid_y < self.home_location[1]:
                                self.target_grid_y = self.grid_y + 1
                                self.is_moving = True
                            elif self.grid_y > self.home_location[1]:
                                self.target_grid_y = self.grid_y - 1
                                self.is_moving = True
    
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
        
        # Check if this is a decision to follow player advice
        if hasattr(decision, 'following_advice') and decision.following_advice:
            self.advice_direction = getattr(decision, 'advice_direction', None)
            self.advice_remaining_distance = getattr(decision, 'advice_remaining_distance', 0)
            print(f"DEBUG: NPC {id(self)} received advice to move {self.advice_remaining_distance} tiles {self.advice_direction}")
            
            # Start following the advice immediately
            if self.advice_direction == "left":
                self.target_grid_x = self.grid_x - 1
                self.is_moving = True
            elif self.advice_direction == "right":
                self.target_grid_x = self.grid_x + 1
                self.is_moving = True
            elif self.advice_direction == "up":
                self.target_grid_y = self.grid_y - 1
                self.is_moving = True
            elif self.advice_direction == "down":
                self.target_grid_y = self.grid_y + 1
                self.is_moving = True
            
            self.advice_remaining_distance -= 1
            return
        
        # Handle exploration decisions
        if decision.action == "explore":
            # Set exploration mode
            self.exploration_mode = "exploring"
            
            # Set target if provided
            if decision.target_x is not None and decision.target_y is not None:
                self.exploration_target_x = decision.target_x
                self.exploration_target_y = decision.target_y
            else:
                # Choose a random direction
                from engine.core import SimpleGameEngine
                game_engine = None
                if hasattr(SimpleGameEngine, 'instance'):
                    game_engine = SimpleGameEngine.instance
                
                if game_engine and game_engine.world_map:
                    # Choose a random direction to explore
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    dx, dy = random.choice(directions)
                    
                    # Set exploration target a few tiles away
                    explore_distance = random.randint(3, 8)
                    self.exploration_target_x = self.grid_x + (dx * explore_distance)
                    self.exploration_target_y = self.grid_y + (dy * explore_distance)
                    
                    # Ensure target is within map bounds
                    map_width = game_engine.world_map.width
                    map_height = game_engine.world_map.height
                    self.exploration_target_x = max(0, min(map_width - 1, self.exploration_target_x))
                    self.exploration_target_y = max(0, min(map_height - 1, self.exploration_target_y))
            
            print(f"DEBUG: NPC {id(self)} starting exploration to ({self.exploration_target_x}, {self.exploration_target_y})")
            return
        
        # Handle return home decision
        if decision.action == "return_home":
            self.exploration_mode = "returning"
            self.exploration_target_x = self.home_location[0]
            self.exploration_target_y = self.home_location[1]
            print(f"DEBUG: NPC {id(self)} returning home to ({self.exploration_target_x}, {self.exploration_target_y})")
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
        elif decision.action == "drink" and self.thirst < 10:
            # Check if we're adjacent to water
            from engine.core import SimpleGameEngine
            world_map = None
            if hasattr(SimpleGameEngine, 'instance'):
                world_map = SimpleGameEngine.instance.world_map
            
            if world_map and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
                self.thirst += 1
                print(f"NPC drank water, thirst increased to {self.thirst}")
                
                # Record water source in memory if not already recorded
                game_engine = SimpleGameEngine.instance
                if hasattr(game_engine, 'world_cache'):
                    # Find the actual water tile
                    water_x, water_y = None, None
                    for dx, dy in [(0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = self.grid_x + dx, self.grid_y + dy
                        if world_map.get_tile(nx, ny) and world_map.get_tile(nx, ny).is_water():
                            water_x, water_y = nx, ny
                            break
                    
                    if water_x is not None and water_y is not None:
                        # Add to interesting locations if not already there
                        if "water" not in self.interesting_locations:
                            self.interesting_locations["water"] = []
                        
                        # Check if this location is already recorded
                        location_exists = False
                        for x, y in self.interesting_locations["water"]:
                            if x == water_x and y == water_y:
                                location_exists = True
                                break
                        
                        if not location_exists:
                            self.interesting_locations["water"].append((water_x, water_y))
                            
                            # Record the discovery in world cache
                            current_time = pygame.time.get_ticks()
                            if current_time - self.last_memory_record_time > self.memory_cooldown:
                                self.last_memory_record_time = current_time
                                game_engine.world_cache.add_location_discovery(
                                    str(id(self)),
                                    "water",
                                    water_x,
                                    water_y,
                                    "Water source"
                                )
        
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

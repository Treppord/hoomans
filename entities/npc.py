from entities.rectangle import Rectangle
import pygame
import random

from entities.rectangle import Rectangle
import pygame
import random

class NPC(Rectangle):
    """An NPC entity controlled by AI"""
    
    def __init__(self, grid_x, grid_y, color=(0, 255, 0), speed=1, ai_controller=None):
        super().__init__(grid_x, grid_y, color, speed, controllable=False)
        self.ai_controller = ai_controller
        
        # Add thirst attribute (0-5 scale)
        self.thirst = 10  # Start with full thirst
        self.last_thirst_update = 0  # Track time for thirst decrease
        self.last_drink_time = 0  # Track time for drinking
        
        # Debug tracking for player detection
        self.debug_player_detected = False
        self.debug_last_player_id = None
        
        # Advice following attributes
        self.advice_remaining_distance = 0
        self.advice_direction = None
        
        # If an AI controller was provided, set this entity as its target
        if self.ai_controller:
            self.ai_controller.set_entity(self)
    
    def update(self):
        """Update entity state"""
        super().update()
        
        # If we've finished moving and have remaining advice distance, continue moving
        if hasattr(self, 'advice_remaining_distance') and self.advice_remaining_distance > 0 and not self.is_moving:
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
                            game_engine.world_cache.add_discovered_location(
                                str(id(self)),
                                "water",
                                self.grid_x,
                                self.grid_y,
                                "Water source found via player advice"
                            )
                        
                        # Update AI universe state to reflect this
                        if hasattr(game_engine, 'ai_universe'):
                            game_engine.ai_universe.update_agent_state(
                                agent_id=str(id(self)),
                                advice_followed=True,
                                advice_success=True,
                                memory_event="Found water where the player said it would be."
                            )
                            
                        # If we're thirsty, drink immediately
                        if self.thirst < 10:
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
        
        # Update thirst over time
        current_time = pygame.time.get_ticks()
        
        # Decrease thirst every 10 seconds
        if current_time - self.last_thirst_update > 20000:  # 20 seconds
            if self.thirst > 0:
                self.thirst -= 1
                print(f"NPC thirst decreased to {self.thirst}")
            self.last_thirst_update = current_time
    
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
        
        # Handle player advice-based movement
        if hasattr(decision, 'following_advice') and decision.following_advice:
            # Get the direction and distance from the advice
            direction = getattr(decision, 'advice_direction', None)
            distance = getattr(decision, 'advice_distance', 1)
            
            # Cap distance to a reasonable value to prevent overshooting
            distance = min(distance, 5)
            
            if direction == "left":
                self.target_grid_x = self.grid_x - 1
                self.is_moving = True
                # Store the remaining distance to move
                self.advice_remaining_distance = distance - 1
                self.advice_direction = direction
            elif direction == "right":
                self.target_grid_x = self.grid_x + 1
                self.is_moving = True
                self.advice_remaining_distance = distance - 1
                self.advice_direction = direction
            elif direction == "up":
                self.target_grid_y = self.grid_y - 1
                self.is_moving = True
                self.advice_remaining_distance = distance - 1
                self.advice_direction = direction
            elif direction == "down":
                self.target_grid_y = self.grid_y + 1
                self.is_moving = True
                self.advice_remaining_distance = distance - 1
                self.advice_direction = direction
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
        
        # Handle fast movement for critical needs
        if hasattr(decision, 'is_fast_movement') and decision.is_fast_movement and not self.is_moving:
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

    
    def set_ai_controller(self, ai_controller):
        """Set the AI controller for this NPC"""
        self.ai_controller = ai_controller
        self.ai_controller.set_entity(self)
    


        
    def render(self, screen, camera):
        """Render the NPC with camera transformations"""
        super().render(screen, camera)
    
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
            



                
    def respond_to_chat(self, player_message):
        """Generate a response to a player's chat message"""
        # This is handled by the AI Universe Controller
        pass

"""Game loop management and update logic"""
import pygame
from entities.npc import NPC
from ai.controllers.ai_universe_controller import WorldStateCollector
import random

class GameLoop:
    """Handles the main game update loop and logic"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.last_update_time = 0
    
    def update(self):
        """Update game logic"""
        if self.game_engine.state_manager.is_state(self.game_engine.state_manager.game_state_constants.MAIN_MENU):
            return
            
        if self.game_engine.state_manager.is_state(self.game_engine.state_manager.game_state_constants.PAUSED):
            return
        
        # Calculate delta time
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_update_time) / 1000.0  # Convert to seconds
        self.last_update_time = current_time
        
        # Update theme manager
        self.game_engine.theme_manager.update(delta_time)
        
        # Add ambient particles
        self.game_engine.theme_manager.add_ambient_particles(self.game_engine.camera, count=1)
        
        # Update camera
        self.game_engine.camera.update()

        # Update game time
        self.game_engine.data.add_to_value("game_time", 1)
        
        # Process AI decisions first to prioritize chat responses
        self._process_ai_decisions()
        
        # Update all game objects - use EntityManager if available
        if self.game_engine.entity_manager:
            # Use entity manager to update all entities
            self.game_engine.entity_manager.update_all_entities()
            entities = self.game_engine.entity_manager.get_all_entities()
        else:
            # Fallback to direct object updates
            entities = self.game_engine.objects
            for obj in entities:
                if hasattr(obj, 'update'):
                    obj.update()
        
        # Handle player-specific updates
        self._update_player_stats(entities)
        
        # Update AI Universe for NPCs
        self._update_ai_universe(entities)
        
        # Update AI for all NPCs (keep the existing AI system as fallback)
        self.game_engine.ai_manager.update(self.game_engine.world_map, entities)
        
        # Update physics for all objects
        self.game_engine.physics.update(entities)
        
        # Handle periodic stat decreases
        self._handle_periodic_stat_decreases()
    
    def _process_ai_decisions(self):
        """Process AI decisions and apply them to entities"""
        if not hasattr(self.game_engine, 'ai_universe'):
            return
            
        decisions = self.game_engine.ai_universe.get_pending_decisions()
        for decision in decisions:
            print(f"DEBUG: Processing decision for agent {decision.agent_id}, action={decision.action}, speech='{decision.speech}'")
            
            # Find the corresponding object
            found_object = False
            entities = self.game_engine.entity_manager.get_all_entities() if self.game_engine.entity_manager else self.game_engine.objects
            
            for obj in entities:
                # Try both direct ID comparison and entity_id comparison
                if (obj.get_entity_id() == decision.agent_id or 
                    str(id(obj)) == decision.agent_id):
                    found_object = True
                    # Apply the decision to the NPC
                    if isinstance(obj, NPC):
                        obj.apply_ai_decision(decision)
                    
                    # Handle speech with text bubbles
                    if decision.speech and hasattr(self.game_engine, 'ui'):
                        print(f"DEBUG: Adding text bubble for speech: '{decision.speech}'")
                        self.game_engine.ui.add_text_bubble(decision.speech, obj, duration=3.0)
                    elif not decision.speech:
                        print(f"DEBUG: No speech to display for agent {decision.agent_id}")
                    
                    # Add debug output to help diagnose ID issues
                    print(f"DEBUG: Matched agent ID {decision.agent_id} to object with entity_id {obj.get_entity_id()}")
                    break
            
            if not found_object:
                print(f"DEBUG: Could not find object for agent {decision.agent_id}")
                # Add more debug info to help diagnose the issue
                entity_ids = [obj.get_entity_id() for obj in entities if hasattr(obj, 'get_entity_id')]
                print(f"DEBUG: Available entity IDs: {entity_ids}")
    
    def _update_player_stats(self, entities):
        """Update player statistics in the data manager"""
        player = self.game_engine.entity_manager.get_player() if self.game_engine.entity_manager else self.game_engine.player
        
        if player:
            # Update player thirst in data manager if player exists
            if hasattr(player, 'thirst'):
                self.game_engine.data.get_player_stat("thirst").set(player.thirst)
                
            if hasattr(player, 'hunger'):
                self.game_engine.data.get_player_stat("hunger").set(player.hunger)
            
            # Special check for player to ensure animation state is correct
            if hasattr(player, 'controllable') and player.controllable:
                # Check if any movement keys are pressed
                keys = pygame.key.get_pressed()
                movement_keys = [
                    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                    pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s
                ]
                
                # If any movement key is pressed, force the walk animation
                if any(keys[key] for key in movement_keys):
                    player.force_walk_animation = True
                    player.walk_animation_start_time = pygame.time.get_ticks()
                    player.is_moving = True
    
    def _update_ai_universe(self, entities):
        """Update AI Universe with current world state"""
        if not hasattr(self.game_engine, 'ai_universe'):
            return
            
        for obj in entities:
            if isinstance(obj, NPC) and hasattr(obj, 'grid_x') and hasattr(obj, 'grid_y'):
                # Collect world state for this NPC
                nearby_tiles = WorldStateCollector.collect_nearby_tiles(
                    self.game_engine.world_map, obj.grid_x, obj.grid_y, radius=5)
                nearby_entities = WorldStateCollector.collect_nearby_entities(
                    entities, obj.grid_x, obj.grid_y, radius=5)
                
                # Update agent state in AI universe
                self.game_engine.ai_universe.update_agent_state(
                    agent_id=obj.get_entity_id(),  # Use persistent entity ID
                    grid_x=obj.grid_x,
                    grid_y=obj.grid_y,
                    thirst=obj.thirst if hasattr(obj, 'thirst') else 5,
                    hunger=getattr(obj, 'hunger', 5),
                    health=getattr(obj, 'health', 5),
                    nearby_tiles=nearby_tiles,
                    nearby_entities=nearby_entities,
                    cna_file=obj.cna_file if hasattr(obj, 'cna_file') else None
                )
        
        # Check for NPC-to-NPC interactions
        self._handle_npc_interactions(entities)
    
    def _handle_npc_interactions(self, entities):
        """Handle NPC-to-NPC interactions"""
        for obj1 in entities:
            if isinstance(obj1, NPC) and hasattr(obj1, 'grid_x') and hasattr(obj1, 'grid_y'):
                # Only check for interaction occasionally (10% chance per frame)
                if random.random() < 0.1:
                    for obj2 in entities:
                        if (obj1 != obj2 and isinstance(obj2, NPC) and 
                            hasattr(obj2, 'grid_x') and hasattr(obj2, 'grid_y')):
                            # Calculate distance between NPCs
                            distance = abs(obj1.grid_x - obj2.grid_x) + abs(obj1.grid_y - obj2.grid_y)
                            
                            # If NPCs are close to each other, initiate conversation
                            if distance <= 8:
                                # Only 20% chance to actually start conversation when in range
                                if random.random() < 0.2 and hasattr(self.game_engine, 'ai_universe'):
                                    # Create a special state update for NPC-to-NPC chat
                                    self.game_engine.ai_universe.update_agent_state(
                                        agent_id=obj1.get_entity_id(),  # Use persistent entity ID
                                        grid_x=obj1.grid_x,
                                        grid_y=obj1.grid_y,
                                        npc_interaction=True,
                                        other_npc_id=obj2.get_entity_id()  # Use persistent entity ID
                                    )
                                    # Only one NPC needs to initiate
                                    break
    
    def _handle_periodic_stat_decreases(self):
        """Handle periodic decreases in hunger and thirst"""
        # Example: slowly decrease hunger and thirst over time
        if self.game_engine.data.get_value("game_time").value % 1200 == 0:  # Every 20 seconds (at 60 FPS)
            if self.game_engine.data.get_player_stat("hunger").value > 0:
                self.game_engine.data.get_player_stat("hunger").subtract(1)
            if self.game_engine.data.get_player_stat("thirst").value > 0:
                self.game_engine.data.get_player_stat("thirst").subtract(1)
                
                # Also update player entity's thirst if it exists
                player = self.game_engine.entity_manager.get_player() if self.game_engine.entity_manager else self.game_engine.player
                if player and hasattr(player, 'thirst') and player.thirst > 0:
                    player.thirst -= 1

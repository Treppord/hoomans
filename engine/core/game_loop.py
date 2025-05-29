"""Game loop and update management"""
import pygame
import random
from engine.config.config_loader import get_config_loader

class GameLoop:
    """Manages the main game loop and update cycles"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.config = get_config_loader()
        
        # Load timing settings
        gameplay_config = self.config.get_setting('game_settings', 'gameplay', default={})
        game_stats_config = self.config.get_setting('game_settings', 'game_stats', default={})
        
        self.hunger_decrease_interval = game_stats_config.get('hunger_decrease_interval', 1200)
        self.thirst_decrease_interval = game_stats_config.get('thirst_decrease_interval', 1200)
        self.npc_interaction_distance = gameplay_config.get('npc_interaction_distance', 8)
        self.npc_conversation_trigger_chance = gameplay_config.get('npc_conversation_trigger_chance', 0.1)
        self.npc_conversation_chance = gameplay_config.get('npc_conversation_chance', 0.2)
        
        self.last_update_time = 0
    
    def update(self):
        """Update game logic"""
        current_state = self.game_engine.state_manager.get_state()
        
        if current_state == self.game_engine.state_manager.game_state_constants.MAIN_MENU:
            return
        
        if current_state == self.game_engine.state_manager.game_state_constants.PAUSED:
            return
        
        # Calculate delta time
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_update_time) / 1000.0
        self.last_update_time = current_time
        
        # Update theme manager
        self.game_engine.theme_manager.update(delta_time)
        self.game_engine.theme_manager.add_ambient_particles(self.game_engine.camera, count=1)
        
        # Update camera
        self.game_engine.camera.update()
        
        # Update game time
        self.game_engine.data.add_to_value("game_time", 1)
        
        # Process AI decisions
        self._process_ai_decisions()
        
        # Update game objects
        self._update_game_objects()
        
        # Update player stats
        self._update_player_stats()
        
        # Update AI Universe for NPCs
        self._update_ai_universe()
        
        # Update AI manager
        self.game_engine.ai_manager.update(self.game_engine.world_map, self.game_engine.objects)
        
        # Update physics
        self.game_engine.physics.update(self.game_engine.objects)
        
        # Handle periodic stat decreases
        self._handle_periodic_stat_changes()
    
    def _process_ai_decisions(self):
        """Process AI decisions for NPCs"""
        if hasattr(self.game_engine, 'ai_universe'):
            decisions = self.game_engine.ai_universe.get_pending_decisions()
            for decision in decisions:
                print(f"DEBUG: Processing decision for agent {decision.agent_id}, action={decision.action}, speech='{decision.speech}'")
                
                found_object = False
                for obj in self.game_engine.objects:
                    if (obj.get_entity_id() == decision.agent_id or 
                        str(id(obj)) == decision.agent_id):
                        found_object = True
                        
                        # Apply the decision to the NPC
                        if hasattr(obj, '__class__') and 'NPC' in obj.__class__.__name__:
                            obj.apply_ai_decision(decision)
                        
                        # Handle speech with text bubbles
                        if decision.speech and hasattr(self.game_engine, 'ui'):
                            print(f"DEBUG: Adding text bubble for speech: '{decision.speech}'")
                            self.game_engine.ui.add_text_bubble(decision.speech, obj, duration=3.0)
                        
                        print(f"DEBUG: Matched agent ID {decision.agent_id} to object with entity_id {obj.get_entity_id()}")
                        break
                
                if not found_object:
                    print(f"DEBUG: Could not find object for agent {decision.agent_id}")
    
    def _update_game_objects(self):
        """Update all game objects"""
        for obj in self.game_engine.objects:
            if hasattr(obj, 'update'):
                obj.update()
                
                # Special check for player animation state
                if hasattr(obj, 'controllable') and obj.controllable:
                    keys = pygame.key.get_pressed()
                    movement_keys = [
                        pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                        pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s
                    ]
                    
                    if any(keys[key] for key in movement_keys):
                        obj.force_walk_animation = True
                        obj.walk_animation_start_time = pygame.time.get_ticks()
                        obj.is_moving = True
    
    def _update_player_stats(self):
        """Update player stats in data manager"""
        if self.game_engine.player:
            if hasattr(self.game_engine.player, 'thirst'):
                self.game_engine.data.get_player_stat("thirst").set(self.game_engine.player.thirst)
            
            if hasattr(self.game_engine.player, 'hunger'):
                self.game_engine.data.get_player_stat("hunger").set(self.game_engine.player.hunger)
    
    def _update_ai_universe(self):
        """Update AI Universe for NPCs"""
        if not hasattr(self.game_engine, 'ai_universe'):
            return
        
        # Update agent states
        for obj in self.game_engine.objects:
            if hasattr(obj, '__class__') and 'NPC' in obj.__class__.__name__:
                if hasattr(obj, 'grid_x') and hasattr(obj, 'grid_y'):
                    # Import here to avoid circular imports
                    try:
                        from ai.controllers.ai_universe_controller import WorldStateCollector
                        
                        nearby_tiles = WorldStateCollector.collect_nearby_tiles(
                            self.game_engine.world_map, obj.grid_x, obj.grid_y, radius=5)
                        nearby_entities = WorldStateCollector.collect_nearby_entities(
                            self.game_engine.objects, obj.grid_x, obj.grid_y, radius=5)
                        
                        self.game_engine.ai_universe.update_agent_state(
                            agent_id=obj.get_entity_id(),
                            grid_x=obj.grid_x,
                            grid_y=obj.grid_y,
                            thirst=obj.thirst if hasattr(obj, 'thirst') else 5,
                            hunger=getattr(obj, 'hunger', 5),
                            health=getattr(obj, 'health', 5),
                            nearby_tiles=nearby_tiles,
                            nearby_entities=nearby_entities,
                            cna_file=obj.cna_file if hasattr(obj, 'cna_file') else None
                        )
                    except ImportError:
                        # WorldStateCollector not available, skip this update
                        pass
        
        # Check for NPC-to-NPC interactions
        self._handle_npc_interactions()
    
    def _handle_npc_interactions(self):
        """Handle NPC-to-NPC interactions"""
        for obj1 in self.game_engine.objects:
            if hasattr(obj1, '__class__') and 'NPC' in obj1.__class__.__name__:
                if hasattr(obj1, 'grid_x') and hasattr(obj1, 'grid_y'):
                    # Only check for interaction occasionally (10% chance per frame)
                    if random.random() < self.npc_conversation_trigger_chance:
                        for obj2 in self.game_engine.objects:
                            if (obj1 != obj2 and hasattr(obj2, '__class__') and 'NPC' in obj2.__class__.__name__ and 
                                hasattr(obj2, 'grid_x') and hasattr(obj2, 'grid_y')):
                                # Calculate distance between NPCs
                                distance = abs(obj1.grid_x - obj2.grid_x) + abs(obj1.grid_y - obj2.grid_y)
                                
                                # If NPCs are close to each other, initiate conversation
                                if distance <= self.npc_interaction_distance:
                                    # Only 20% chance to actually start conversation when in range
                                    if random.random() < self.npc_conversation_chance and hasattr(self.game_engine, 'ai_universe'):
                                        # Create a special state update for NPC-to-NPC chat
                                        self.game_engine.ai_universe.update_agent_state(
                                            agent_id=obj1.get_entity_id(),
                                            grid_x=obj1.grid_x,
                                            grid_y=obj1.grid_y,
                                            npc_interaction=True,
                                            other_npc_id=obj2.get_entity_id()
                                        )
                                        # Only one NPC needs to initiate
                                        break
    
    def _handle_periodic_stat_changes(self):
        """Handle periodic stat decreases"""
        game_time = self.game_engine.data.get_value("game_time").value
        
        if game_time % self.hunger_decrease_interval == 0:
            if self.game_engine.data.get_player_stat("hunger").value > 0:
                self.game_engine.data.get_player_stat("hunger").subtract(1)
            if self.game_engine.data.get_player_stat("thirst").value > 0:
                self.game_engine.data.get_player_stat("thirst").subtract(1)
                
                # Also update player entity's thirst if it exists
                if self.game_engine.player and hasattr(self.game_engine.player, 'thirst') and self.game_engine.player.thirst > 0:
                    self.game_engine.player.thirst -= 1

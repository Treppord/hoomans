import pygame
import sys
from engine.physics import PhysicsEngine
from engine.input_handler import InputHandler
from engine.ai import AIManager
from engine.data_manager import DataManager
from engine.ui import UIManager, StatsPanel, ChatInputBox
from engine.camera import Camera
from entities.npc import NPC
from ai_universe_controller import WorldStateCollector
import random

class SimpleGameEngine:
    def __init__(self, title="Simple Game Engine", width=800, height=600, fps=60):
        # Initialize pygame
        pygame.init()
        
        # Set up the display
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        
        # Store instance reference
        SimpleGameEngine.instance = self
        
        # Set up the clock for controlling frame rate
        self.clock = pygame.time.Clock()
        self.fps = fps
        
        # Initialize camera
        self.camera = Camera(width, height)
        
        # Game objects storage
        self.objects = []
        
        # World map
        self.world_map = None
        
        # Initialize physics engine
        self.physics = PhysicsEngine()
        
        # Initialize input handler
        self.input_handler = InputHandler()
        
        # Initialize AI manager
        self.ai_manager = AIManager()
        
        # Initialize data manager
        self.data = DataManager()
        
        # Initialize UI manager
        self.ui = UIManager(width, height)
        
        # Player reference (will be set when player is added)
        self.player = None
        
        # Paused state
        self.paused = False
        
        # Set up initial game values
        self.setup_game_data()
        
        # Set up UI elements
        self.setup_ui()
        
        # Game state
        self.running = False
        
    def setup_game_data(self):
        """Set up initial game values"""
        # Create player stats
        self.data.create_player_stat("health", 20, 0, 20)
        self.data.create_player_stat("hunger", 10, 0, 10)
        self.data.create_player_stat("thirst", 5, 0, 5)
        self.data.create_player_stat("score", 0, 0, None)
        
        # Create game values
        self.data.create_value("game_time", 0)
        self.data.create_value("enemies_defeated", 0)
        
        # Add some starting inventory
        self.data.add_inventory_item("health_potion", 3)
    
    def setup_ui(self):
        """Set up UI elements"""
        # Add stats panel in top right corner
        stats_panel_width = 200
        stats_panel_height = 120
        stats_panel_x = self.width - stats_panel_width - 10  # 10px from right edge
        stats_panel_y = 10  # 10px from top edge
        
        self.ui.add_element(
            StatsPanel(stats_panel_x, stats_panel_y, stats_panel_width, stats_panel_height, self.data)
        )
        
        # Add chat input box in bottom right corner
        chat_input_width = 400
        chat_input_height = 40
        chat_input_x = self.width - chat_input_width - 10  # 10px from right edge
        chat_input_y = self.height - chat_input_height - 10  # 10px from bottom edge
        
        self.chat_input = self.ui.add_element(
            ChatInputBox(
                chat_input_x, 
                chat_input_y, 
                chat_input_width, 
                chat_input_height,
                callback=self.handle_chat_message
            )
        )
        
    def handle_chat_message(self, message):
        """Handle a chat message from the player"""
        if self.player:
            print(f"Chat message: {message}")  # Debug output
            self.ui.add_text_bubble(message, self.player, duration=5.0)
            
            # Find NPCs in vicinity and have them respond
            self.process_npc_responses_to_chat(message)
            
            # When chat is closed, reset chat mode in input handler
            self.input_handler.set_chat_mode(False)
    
    def process_npc_responses_to_chat(self, message):
        """Process NPC responses to player chat messages"""
        if not self.player:
            return
            
        # Define vicinity range (in grid cells)
        vicinity_range = 8
        
        # Find NPCs within range
        nearby_npcs = []
        for obj in self.objects:
            if isinstance(obj, NPC) and hasattr(obj, 'grid_x') and hasattr(obj, 'grid_y'):
                # Calculate Manhattan distance
                distance = abs(obj.grid_x - self.player.grid_x) + abs(obj.grid_y - self.player.grid_y)
                if distance <= vicinity_range:
                    nearby_npcs.append(obj)
        
        # Debug output
        print(f"DEBUG: Found {len(nearby_npcs)} NPCs in chat vicinity of player")
        
        # If no NPCs in range, return
        if not nearby_npcs:
            return
            
        # For each nearby NPC, generate a response via AI Universe
        if hasattr(self, 'ai_universe'):
            for npc in nearby_npcs:
                # Debug output
                print(f"DEBUG: Requesting chat response from NPC {id(npc)} at position ({npc.grid_x}, {npc.grid_y})")
                
                # Create a special state update to trigger a response
                self.ai_universe.update_agent_state(
                    agent_id=str(id(npc)),
                    grid_x=npc.grid_x,
                    grid_y=npc.grid_y,
                    player_message=message,
                    should_respond=True
                )

                

        
    def set_world_map(self, world_map):
        """Set the world map for the game"""
        self.world_map = world_map
        self.physics.set_world_map(world_map)
        
    def add_object(self, obj):
        """Add a game object to the world"""
        self.objects.append(obj)
        
        # If this is a player-controlled object, store a reference
        if hasattr(obj, 'controllable') and obj.controllable:
            self.player = obj
            self.camera.set_follow_target(obj)

            
        return obj
        
    def add_ai_controller(self, controller):
        """Add an AI controller to the game"""
        return self.ai_manager.add_controller(controller)
        
    def handle_events(self):
        """Process all input events"""
        # Process pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # Let UI handle events first (for active chat input)
            if self.ui.handle_event(event):
                continue
                
            # Check for spacebar to toggle pause
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not self.input_handler.chat_mode:
                self.paused = not self.paused
                print(f"Game {'paused' if self.paused else 'resumed'}")
                continue
                
            # Direct check for T key to toggle chat
            if event.type == pygame.KEYDOWN and event.key == pygame.K_t and not self.input_handler.chat_mode:
                print("Chat mode activated")  # Debug output
                self.input_handler.chat_mode = True
                self.chat_input.toggle()
                continue
                
            # Handle mouse wheel for zooming
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.camera.zoom_in(0.1)
                    print(f"Zoomed in: {self.camera.zoom:.2f}")
                elif event.y < 0:
                    self.camera.zoom_out(0.1)
                    print(f"Zoomed out: {self.camera.zoom:.2f}")
                continue
                
            # Handle mouse buttons for panning
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if we're clicking on the map (not UI)
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if any entity was clicked
                    entity_clicked = False
                    for obj in self.objects:
                        if hasattr(obj, 'contains_point') and obj.contains_point(mouse_pos[0], mouse_pos[1], self.camera):
                            print(f"Entity clicked: {obj.__class__.__name__}")
                            self.ui.show_entity_info(obj)
                            entity_clicked = True
                            break
                    
                    # If no entity was clicked, start panning
                    if not entity_clicked:
                        self.camera.start_drag(mouse_pos[0], mouse_pos[1])
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.camera.stop_drag()
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.camera.dragging:
                    self.camera.update_drag(event.pos[0], event.pos[1])
        
        # Update input handler for continuous key state
        self.input_handler.update()
        
        # Only handle movement if not in chat mode and not paused
        if not self.input_handler.chat_mode and not self.paused:
            for obj in self.objects:
                self.input_handler.handle_entity_movement(obj)
                self.input_handler.handle_entity_action(obj)
                self.input_handler.handle_entity_interaction(obj)
    
    def update(self):
        """Update game logic"""
        if self.paused:
            return
            
        self.camera.update()

        # Update game time
        self.data.add_to_value("game_time", 1)
        
        # Update AI Universe for NPCs
        if hasattr(self, 'ai_universe'):
            for obj in self.objects:
                if isinstance(obj, NPC) and hasattr(obj, 'grid_x') and hasattr(obj, 'grid_y'):
                    # Collect world state for this NPC
                    nearby_tiles = WorldStateCollector.collect_nearby_tiles(
                        self.world_map, obj.grid_x, obj.grid_y, radius=5)
                    nearby_entities = WorldStateCollector.collect_nearby_entities(
                        self.objects, obj.grid_x, obj.grid_y, radius=5)
                    
                    # Update agent state in AI universe
                    self.ai_universe.update_agent_state(
                        agent_id=str(id(obj)),  # Use object ID as agent ID
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
            for obj1 in self.objects:
                if isinstance(obj1, NPC) and hasattr(obj1, 'grid_x') and hasattr(obj1, 'grid_y'):
                    # Only check for interaction occasionally (10% chance per frame)
                    if random.random() < 0.1:
                        for obj2 in self.objects:
                            if (obj1 != obj2 and isinstance(obj2, NPC) and 
                                hasattr(obj2, 'grid_x') and hasattr(obj2, 'grid_y')):
                                # Calculate distance between NPCs
                                distance = abs(obj1.grid_x - obj2.grid_x) + abs(obj1.grid_y - obj2.grid_y)
                                
                                # If NPCs are close to each other, initiate conversation
                                if distance <= 8:
                                    # Only 20% chance to actually start conversation when in range
                                    if random.random() < 0.2 and hasattr(self, 'ai_universe'):
                                        # Create a special state update for NPC-to-NPC chat
                                        self.ai_universe.update_agent_state(
                                            agent_id=str(id(obj1)),
                                            grid_x=obj1.grid_x,
                                            grid_y=obj1.grid_y,
                                            npc_interaction=True,
                                            other_npc_id=str(id(obj2))
                                        )
                                        # Only one NPC needs to initiate
                                        break
            
            # Process AI decisions
            decisions = self.ai_universe.get_pending_decisions()
            for decision in decisions:
                print(f"DEBUG: Processing decision for agent {decision.agent_id}, action={decision.action}, speech='{decision.speech}'")
                # Find the corresponding object
                found_object = False
                for obj in self.objects:
                    if str(id(obj)) == decision.agent_id:
                        found_object = True
                        # Apply the decision to the NPC
                        if isinstance(obj, NPC):
                            obj.apply_ai_decision(decision)
                        
                        # Handle speech with text bubbles
                        if decision.speech and hasattr(self, 'ui'):
                            print(f"DEBUG: Adding text bubble for speech: '{decision.speech}'")
                            self.ui.add_text_bubble(decision.speech, obj, duration=3.0)
                        elif not decision.speech:
                            print(f"DEBUG: No speech to display for agent {decision.agent_id}")
                        
                        break
                
                if not found_object:
                    print(f"DEBUG: Could not find object for agent {decision.agent_id}")
        
        # Update AI for all NPCs (keep the existing AI system as fallback)
        self.ai_manager.update(self.world_map, self.objects)
        
        # Update physics for all objects
        self.physics.update(self.objects)
        
        # Update player thirst in data manager if player exists
        if self.player and hasattr(self.player, 'thirst'):
            self.data.get_player_stat("thirst").set(self.player.thirst)
        
        # Example: slowly decrease hunger and thirst over time
        if self.data.get_value("game_time").value % 600 == 0:  # Every 10 seconds (at 60 FPS)
            if self.data.get_player_stat("hunger").value > 0:
                self.data.get_player_stat("hunger").subtract(1)
            if self.data.get_player_stat("thirst").value > 0:
                self.data.get_player_stat("thirst").subtract(1)
                
                # Also update player entity's thirst if it exists
                if self.player and hasattr(self.player, 'thirst') and self.player.thirst > 0:
                    self.player.thirst -= 1
                    print(f"Player thirst decreased to {self.player.thirst}")




    
    def render(self):
        """Render all game objects"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Draw the world map first
        if self.world_map:
            self.world_map.render(self.screen, self.camera)
        
        # Draw all objects
        for obj in self.objects:
            if hasattr(obj, 'render'):
                obj.render(self.screen, self.camera)
        
        # Draw UI elements last (on top)
        self.ui.render(self.screen)
        
        # Update the display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        self.running = True
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(self.fps)
        
        # Clean up
        if hasattr(self, 'ai_universe'):
            self.ai_universe.stop()
            
        pygame.quit()
        sys.exit()
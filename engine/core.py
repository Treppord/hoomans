import pygame
import sys
from engine.physics import PhysicsEngine
from engine.input_handler import InputHandler
from engine.ai import AIManager
from engine.data_manager import DataManager
from engine.ui import UIManager, StatsPanel, ChatInputBox

class SimpleGameEngine:
    def __init__(self, title="Simple Game Engine", width=800, height=600, fps=60):
        # Initialize pygame
        pygame.init()
        
        # Set up the display
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        
        # Set up the clock for controlling frame rate
        self.clock = pygame.time.Clock()
        self.fps = fps
        
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
        self.data.create_player_stat("thirst", 10, 0, 10)
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
            # When chat is closed, reset chat mode in input handler
            self.input_handler.set_chat_mode(False)
        
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
                
            # Direct check for T key to toggle chat
            if event.type == pygame.KEYDOWN and event.key == pygame.K_t and not self.input_handler.chat_mode:
                print("Chat mode activated")  # Debug output
                self.input_handler.chat_mode = True
                self.chat_input.toggle()
                continue
        
        # Update input handler for continuous key state
        self.input_handler.update()
        
        # Only handle movement if not in chat mode
        if not self.input_handler.chat_mode:
            for obj in self.objects:
                self.input_handler.handle_entity_movement(obj)
                self.input_handler.handle_entity_action(obj)
                self.input_handler.handle_entity_interaction(obj)
    
    def update(self):
        """Update game logic"""
        # Update game time
        self.data.add_to_value("game_time", 1)
        
        # Update AI for all NPCs
        self.ai_manager.update(self.world_map, self.objects)
        
        # Update physics for all objects
        self.physics.update(self.objects)
        
        # Example: slowly decrease hunger and thirst over time
        if self.data.get_value("game_time").value % 600 == 0:  # Every 10 seconds (at 60 FPS)
            if self.data.get_player_stat("hunger").value > 0:
                self.data.get_player_stat("hunger").subtract(1)
            if self.data.get_player_stat("thirst").value > 0:
                self.data.get_player_stat("thirst").subtract(1)
    
    def render(self):
        """Render all game objects"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Draw the world map first
        if self.world_map:
            self.world_map.render(self.screen)
        
        # Draw all objects
        for obj in self.objects:
            if hasattr(obj, 'render'):
                obj.render(self.screen)
        
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
        pygame.quit()
        sys.exit()

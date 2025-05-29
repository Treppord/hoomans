"""Chat and NPC interaction management"""
import time
from engine.config.config_loader import get_config_loader

class ChatManager:
    """Manages chat functionality and NPC interactions"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.config = get_config_loader()
        
        # Load chat settings
        gameplay_config = self.config.get_setting('game_settings', 'gameplay', default={})
        self.chat_range = gameplay_config.get('chat_range', 5)
        self.vicinity_range = gameplay_config.get('vicinity_range', 8)
        self.npc_interaction_distance = gameplay_config.get('npc_interaction_distance', 8)
        self.npc_conversation_chance = gameplay_config.get('npc_conversation_chance', 0.2)
        self.npc_conversation_trigger_chance = gameplay_config.get('npc_conversation_trigger_chance', 0.1)
    
    def handle_chat_message(self, message):
        """Handle a chat message from the player"""
        if not self.game_engine.player:
            return
        
        print(f"Chat message: {message}")
        
        # Check for commands first
        if message.startswith("/"):
            self.process_command(message[1:])
            self.game_engine.input_manager.set_chat_mode(False)
            return
        
        # Add text bubble and process NPC responses
        bubble = self.game_engine.ui.add_text_bubble(message, self.game_engine.player, duration=5.0)
        self.process_npc_responses_to_chat(message)
        
        # Reset chat mode
        self.game_engine.input_manager.set_chat_mode(False)
    
    def process_npc_responses_to_chat(self, message):
        """Process NPC responses to player chat messages"""
        if not self.game_engine.player:
            return
        
        # Find NPCs within range
        nearby_npcs = []
        for obj in self.game_engine.objects:
            if hasattr(obj, '__class__') and 'NPC' in obj.__class__.__name__:
                if hasattr(obj, 'grid_x') and hasattr(obj, 'grid_y'):
                    distance = abs(obj.grid_x - self.game_engine.player.grid_x) + abs(obj.grid_y - self.game_engine.player.grid_y)
                    if distance <= self.vicinity_range:
                        nearby_npcs.append(obj)
        
        print(f"DEBUG: Found {len(nearby_npcs)} NPCs in chat vicinity of player")
        # If no NPCs in range, return
        if not nearby_npcs:
            return
            
        # For each nearby NPC, generate a response via AI Universe
        if hasattr(self.game_engine, 'ai_universe'):
            for npc in nearby_npcs:
                print(f"DEBUG: Requesting chat response from NPC {npc.get_entity_id()} at position ({npc.grid_x}, {npc.grid_y})")
                
                # Create a special state update to trigger a response
                self.game_engine.ai_universe.update_agent_state(
                    agent_id=npc.get_entity_id(),
                    grid_x=npc.grid_x,
                    grid_y=npc.grid_y,
                    player_message=message,
                    should_respond=True
                )
                
                # Check if the message contains advice about water or other resources
                if ("water" in message.lower() or "thirsty" in message.lower()) and hasattr(npc, 'thirst') and npc.thirst <= 2:
                    self.game_engine.ai_universe.update_agent_state(
                        agent_id=npc.get_entity_id(),
                        needs_advice=True,
                        advice_topic="water",
                        advice_urgency=5 - npc.thirst
                    )
                    print(f"DEBUG: NPC {npc.get_entity_id()} is thirsty and received potential water advice")

    def process_command(self, command):
        """Process debug commands"""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == "debug_map":
            if hasattr(self.game_engine, 'world_map'):
                self.game_engine.world_map.enable_debug_mode()
                print("Map debug mode enabled. Next map generation will create debug files.")
            else:
                print("No world map available")
        
        elif cmd == "regen_map":
            if hasattr(self.game_engine, 'world_map'):
                seed = int(parts[1]) if len(parts) > 1 else None
                self.game_engine.world_map.generate_realistic_map(seed=seed)
                print(f"Map regenerated with seed: {seed}")
            else:
                print("No world map available")
        
        elif cmd == "help":
            print("Available commands:")
            print("  debug_map - Enable debug visualization")
            print("  regen_map [seed] - Regenerate map with optional seed")
            print("  help - Show this help")

import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NPCActions")

@dataclass
class ActionResponse:
    """Represents an NPC's response to a player command or interaction"""
    action: str  # The action to perform (e.g., "follow_player", "stop_following", etc.)
    speech: str  # What the NPC says in response
    duration: Optional[int] = None  # How long to perform the action (in seconds), None for indefinite
    target_id: Optional[str] = None  # ID of the target entity (e.g., player ID)
    mood_change: float = 0.0  # How this affects NPC's mood (-1 to 1)

class NPCActionHandler:
    """Handles standard actions an NPC can perform based on AI responses or player commands"""
    
    # Define standard actions
    ACTIONS = {
        # Movement actions
        "follow_player": {
            "description": "Follow the player around",
            "responses": [
                "I'll follow you.",
                "Lead the way!",
                "Sure, I'll come with you.",
                "Right behind you.",
                "I'll stick with you for a while."
            ]
        },
        "stop_following": {
            "description": "Stop following the player",
            "responses": [
                "I'll wait here.",
                "I'll stop following you.",
                "I'll stay here then.",
                "Alright, I'll go my own way.",
                "I'll leave you be."
            ]
        },
        "give_item": {
            "description": "Give an item to the player",
            "responses": [
                "Here, take this.",
                "I want you to have this.",
                "This might be useful for you.",
                "Please accept this gift.",
                "I found this earlier, you can have it."
            ]
        },
        "trade": {
            "description": "Begin trading with the player",
            "responses": [
                "Let's trade.",
                "What do you have to offer?",
                "I have some items to trade.",
                "Maybe we can make a deal?",
                "I'm interested in trading with you."
            ]
        },
        "show_info": {
            "description": "Share information with the player",
            "responses": [
                "Let me tell you something interesting.",
                "Did you know...",
                "I heard something you might want to know.",
                "Here's some information that might help you.",
                "I've learned something important."
            ]
        }
    }
    
    # Command recognition patterns
    COMMAND_PATTERNS = {
        "follow": [
            "follow me", "come with me", "follow", "come along", 
            "join me", "stay with me", "tag along"
        ],
        "stop_following": [
            "stop following", "stay here", "wait here", "leave me alone",
            "go away", "stop following me", "don't follow"
        ],
        "give": [
            "give me", "can i have", "do you have anything", 
            "share", "spare some"
        ],
        "trade": [
            "trade", "let's trade", "want to trade", "can we trade",
            "exchange", "buy", "sell"
        ],
        "info": [
            "tell me about", "what do you know", "any information",
            "heard anything", "what's new", "tell me something"
        ]
    }
    
    @staticmethod
    def detect_command(message: str) -> Optional[str]:
        """Detect if a player message contains a command"""
        message = message.lower()
    
        # First check for stop_following commands as they are more specific
        for pattern in NPCActionHandler.COMMAND_PATTERNS["stop_following"]:
            if pattern in message:
                return "stop_following"
    
    # Then check for other commands
        for command, patterns in NPCActionHandler.COMMAND_PATTERNS.items():
            if command == "stop_following":
                continue  # Already checked above
            for pattern in patterns:
                if pattern in message:
                    return command
    
        return None

    
    @staticmethod
    def generate_response(command: str, npc_id: str, player_id: str = None) -> ActionResponse:
        """Generate an appropriate response for a detected command"""
        if command == "follow":
            action = "follow_player"
            speech = random.choice(NPCActionHandler.ACTIONS["follow_player"]["responses"])
            return ActionResponse(
                action=action,
                speech=speech,
                target_id=player_id,
                mood_change=0.2  # Slight positive mood change
            )
            
        elif command == "stop_following":
            action = "stop_following"
            speech = random.choice(NPCActionHandler.ACTIONS["stop_following"]["responses"])
            return ActionResponse(
                action=action,
                speech=speech,
                mood_change=-0.1  # Slight negative mood change
            )
            
        elif command == "give":
            action = "give_item"
            speech = random.choice(NPCActionHandler.ACTIONS["give_item"]["responses"])
            return ActionResponse(
                action=action,
                speech=speech,
                target_id=player_id,
                mood_change=0.1
            )
            
        elif command == "trade":
            action = "trade"
            speech = random.choice(NPCActionHandler.ACTIONS["trade"]["responses"])
            return ActionResponse(
                action=action,
                speech=speech,
                target_id=player_id,
                mood_change=0.1
            )
            
        elif command == "info":
            action = "show_info"
            speech = random.choice(NPCActionHandler.ACTIONS["show_info"]["responses"])
            return ActionResponse(
                action=action,
                speech=speech,
                mood_change=0.0
            )
            
        # Default response if command doesn't match exactly
        return ActionResponse(
            action="idle",
            speech="I'm not sure what you want me to do.",
            mood_change=0.0
        )

    @staticmethod
    def process_player_message(message: str, npc_id: str, player_id: str = None) -> Tuple[bool, Optional[ActionResponse]]:
        """
        Process a player message to determine if it contains a command
        
        Returns:
            Tuple[bool, Optional[ActionResponse]]: 
                - Boolean indicating if a command was detected
                - ActionResponse object if a command was detected, None otherwise
        """
        command = NPCActionHandler.detect_command(message)
        
        if command:
            response = NPCActionHandler.generate_response(command, npc_id, player_id)
            return True, response
        
        return False, None

class NPCActionExecutor:
    """Executes NPC actions in the game world"""
    
    @staticmethod
    def execute_action(npc, action_response, game_engine=None):
        """
        Execute an action on an NPC entity
        
        Args:
            npc: The NPC entity
            action_response: The ActionResponse object
            game_engine: Reference to the game engine (optional)
        
        Returns:
            bool: True if action was executed successfully
        """
        action = action_response.action
        
        # Handle follow player action
        if action == "follow_player" and game_engine:
            # Find the player
            player = None
            for obj in game_engine.objects:
                if hasattr(obj, 'controllable') and obj.controllable:
                    player = obj
                    break
            
            if player:
                # Create or get a FollowPlayerAI controller for this NPC
                from engine.ai import FollowPlayerAI
                
                # Check if NPC already has an AI controller
                if hasattr(npc, 'ai_controller') and npc.ai_controller:
                    # If it's already a FollowPlayerAI, just ensure it's active
                    if isinstance(npc.ai_controller, FollowPlayerAI):
                        logger.info(f"NPC {id(npc)} is already following player")
                        return True
                    
                    # Otherwise, replace the controller
                    npc.ai_controller = FollowPlayerAI(npc, detection_range=10)
                    game_engine.add_ai_controller(npc.ai_controller)
                else:
                    # Create new controller
                    npc.ai_controller = FollowPlayerAI(npc, detection_range=10)
                    game_engine.add_ai_controller(npc.ai_controller)
                
                logger.info(f"NPC {id(npc)} now following player")
                return True
        
        # Handle stop following action
        elif action == "stop_following" and game_engine:
            # Remove any FollowPlayerAI controller
            if hasattr(npc, 'ai_controller') and npc.ai_controller:
                from engine.ai import FollowPlayerAI, RandomWanderAI
                
                if isinstance(npc.ai_controller, FollowPlayerAI):
                    # Replace with random wander AI
                    npc.ai_controller = RandomWanderAI(npc)
                    game_engine.add_ai_controller(npc.ai_controller)
                    logger.info(f"NPC {id(npc)} stopped following player")
                    return True
        
        # Handle give item action (placeholder)
        elif action == "give_item" and game_engine:
            # Placeholder for item giving logic
            logger.info(f"NPC {id(npc)} wants to give an item (not implemented)")
            return True
        
        # Handle trade action (placeholder)
        elif action == "trade" and game_engine:
            # Placeholder for trading logic
            logger.info(f"NPC {id(npc)} wants to trade (not implemented)")
            return True
        
        # Handle show info action (placeholder)
        elif action == "show_info":
            # Placeholder for showing information
            logger.info(f"NPC {id(npc)} wants to share information (not implemented)")
            return True
        
        return False
import logging
import random
import re
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
    """Response from an NPC action handler"""
    action: str
    speech: str = ""
    target_id: Optional[str] = None
    mood_change: float = 0.0
    # Add these new fields to support advice following
    following_advice: bool = False
    advice_direction: Optional[str] = None
    advice_distance: int = 0
    advice_remaining_distance: int = 0


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
        },
        # New exploration actions
        "explore": {
            "description": "Explore the surrounding area",
            "responses": [
                "I'll explore the area.",
                "Let me see what's around here.",
                "Time to do some exploring.",
                "I'll check out the surroundings.",
                "I wonder what I'll discover."
            ]
        },
        "return_home": {
            "description": "Return to home base",
            "responses": [
                "I'll head back home.",
                "Time to return to my base.",
                "I should go back to where I started.",
                "I'll make my way back home.",
                "Let me return to my starting point."
            ]
        },
        "share_memories": {
            "description": "Share discovered locations and memories",
            "responses": [
                "Let me tell you what I've discovered.",
                "I've found some interesting places.",
                "Here's what I remember from my explorations.",
                "I can share my knowledge of the area with you.",
                "Let me tell you about the places I've been."
            ]
        },
        "record_location": {
            "description": "Record current location in memory",
            "responses": [
                "I should remember this place.",
                "This location seems important.",
                "I'll make a note of this area.",
                "This is worth remembering.",
                "I'll add this to my mental map."
            ]
        }
    }
    
    @staticmethod
    def handle_follow_command(message, agent_id, player_id):
        """Handle a command to follow the player"""
        # Check for follow command patterns
        follow_patterns = [
            r"(?:follow|come with|accompany)\s+(?:me|us)",
            r"(?:come|tag)\s+along",
            r"(?:join|stick with)\s+(?:me|us)"
        ]
        
        for pattern in follow_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="follow_player",
                    speech=random.choice(NPCActionHandler.ACTIONS["follow_player"]["responses"]),
                    target_id=player_id,
                    mood_change=0.1
                )
        
        return None
    
    @staticmethod
    def handle_stop_command(message, agent_id, player_id):
        """Handle a command to stop following the player"""
        # Check for stop command patterns
        stop_patterns = [
            r"(?:stop|quit|cease)\s+(?:following|coming)",
            r"(?:stay|wait|remain)\s+(?:here|there)",
            r"(?:leave|go away)",
            r"(?:don't|do not)\s+(?:follow|come)"
        ]
        
        for pattern in stop_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="stop_following",
                    speech=random.choice(NPCActionHandler.ACTIONS["stop_following"]["responses"]),
                    mood_change=-0.05
                )
        
        return None
    
    @staticmethod
    def handle_give_command(message, agent_id, player_id):
        """Handle a command to give an item to the player"""
        # Check for give command patterns
        give_patterns = [
            r"(?:give|hand|pass)\s+(?:me|us)\s+(?:a|an|the|some|your)?\s*(.+)",
            r"(?:can|could|would)\s+(?:you)?\s+(?:give|hand|pass)\s+(?:me|us)\s+(?:a|an|the|some|your)?\s*(.+)",
            r"(?:i|we)\s+(?:want|need|would like)\s+(?:a|an|the|some|your)?\s*(.+)"
        ]
        
        for pattern in give_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                item = match.group(1).strip()
                return ActionResponse(
                    action="give_item",
                    speech=random.choice(NPCActionHandler.ACTIONS["give_item"]["responses"]).replace("this", item),
                    target_id=player_id,
                    mood_change=0.05
                )
        
        return None
    
    @staticmethod
    def handle_trade_command(message, agent_id, player_id):
        """Handle a command to trade with the player"""
        # Check for trade command patterns
        trade_patterns = [
            r"(?:trade|barter|exchange)\s+(?:with|me|us)",
            r"(?:let's|lets)\s+(?:trade|barter|exchange)",
            r"(?:can|could|would)\s+(?:you)?\s+(?:trade|barter|exchange)\s+(?:with|me|us)",
            r"(?:i|we)\s+(?:want|would like)\s+to\s+(?:trade|barter|exchange)"
        ]
        
        for pattern in trade_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="trade",
                    speech=random.choice(NPCActionHandler.ACTIONS["trade"]["responses"]),
                    target_id=player_id,
                    mood_change=0.1
                )
        
        return None
    
    @staticmethod
    def handle_info_command(message, agent_id, player_id):
        """Handle a command to share information"""
        # Check for info command patterns
        info_patterns = [
            r"(?:tell|share|give)\s+(?:me|us)\s+(?:some|any)?\s*(?:info|information|knowledge)",
            r"(?:what|anything)\s+(?:do you|can you)\s+(?:tell|share)\s+(?:me|us)",
            r"(?:do you|have you)\s+(?:know|heard|seen)\s+(?:anything|something)"
        ]
        
        for pattern in info_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="show_info",
                    speech=random.choice(NPCActionHandler.ACTIONS["show_info"]["responses"]),
                    target_id=player_id,
                    mood_change=0.05
                )
        
        return None
    
    @staticmethod
    def handle_explore_command(message, agent_id, player_id):
        """Handle a command to explore an area"""
        # Check for explore command patterns
        explore_patterns = [
            r"(?:explore|check out|investigate)\s+(?:the\s+)?(area|surroundings|region)",
            r"(?:go|look)\s+(?:explore|investigating|scouting)"
        ]
        
        for pattern in explore_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="explore",
                    speech=random.choice(NPCActionHandler.ACTIONS["explore"]["responses"]),
                    mood_change=0.1
                )
        
        return None
    
    @staticmethod
    def handle_return_command(message, agent_id, player_id):
        """Handle a command to return home"""
        # Check for return home command patterns
        return_patterns = [
            r"(?:return|go back|head back)\s+(?:to|to your)?\s*(?:home|base|starting point)",
            r"(?:go|come)\s+home"
        ]
        
        for pattern in return_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="return_home",
                    speech=random.choice(NPCActionHandler.ACTIONS["return_home"]["responses"]),
                    mood_change=0.1
                )
        
        return None
    
    @staticmethod
    def handle_memory_command(message, agent_id, player_id):
        """Handle a command to share memories"""
        # Check for memory sharing command patterns
        memory_patterns = [
            r"(?:tell me about|share|what are)\s+your\s+(?:memories|discoveries|findings)",
            r"what\s+(?:have you|did you)\s+(?:found|discovered|learned|seen)"
        ]
        
        for pattern in memory_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="share_memories",
                    speech=random.choice(NPCActionHandler.ACTIONS["share_memories"]["responses"]),
                    mood_change=0.1
                )
        
        return None
    
    @staticmethod
    def handle_record_command(message, agent_id, player_id):
        """Handle a command to record the current location"""
        # Check for record location command patterns
        record_patterns = [
            r"(?:remember|record|note)\s+(?:this|current|the)\s+(?:place|location|spot|area)",
            r"(?:mark|save)\s+(?:this|current|the)\s+(?:place|location|spot|area)"
        ]
        
        for pattern in record_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return ActionResponse(
                    action="record_location",
                    speech=random.choice(NPCActionHandler.ACTIONS["record_location"]["responses"]),
                    mood_change=0.05
                )
        
        return None

    @staticmethod
    def _parse_advice(message):
        """Parse advice from a player message
        
        Returns a dictionary with:
        - type: 'direction' or 'location'
        - what: what the advice is about (water, food, etc.)
        - direction: for direction advice
        - distance: for direction advice
        - landmark: for location advice
        - confidence: confidence in the parsing
        """
        message = message.lower()
        
        # Initialize result
        result = {
            'type': None,
            'what': 'resource',  # Default
            'confidence': 0.0
        }
        
        # Check for direction advice
        direction_patterns = {
            'right': ['right', 'east'],
            'left': ['left', 'west'],
            'up': ['up', 'north'],
            'down': ['down', 'south']
        }
        
        # Check for resource types
        resource_types = {
            'water': ['water', 'lake', 'river', 'pond', 'stream'],
            'food': ['food', 'berries', 'fruit', 'meat'],
            'shelter': ['shelter', 'house', 'building', 'cave'],
            'resource': ['resource', 'item', 'thing']
        }
        
        # Try to identify direction
        found_direction = None
        for direction, keywords in direction_patterns.items():
            for keyword in keywords:
                if keyword in message:
                    found_direction = direction
                    result['confidence'] += 0.3
                    break
            if found_direction:
                break
        
        # Try to identify resource type
        found_resource = None
        for resource, keywords in resource_types.items():
            for keyword in keywords:
                if keyword in message:
                    found_resource = resource
                    result['confidence'] += 0.2
                    break
            if found_resource:
                break
        
        # Try to identify distance
        distance_pattern = r'(\d+)\s+(?:blocks?|tiles?|steps?)'
        distance_match = re.search(distance_pattern, message)
        found_distance = None
        if distance_match:
            try:
                found_distance = int(distance_match.group(1))
                result['confidence'] += 0.3
            except ValueError:
                found_distance = 1
        
        # If we found a direction, it's direction advice
        if found_direction:
            result['type'] = 'direction'
            result['direction'] = found_direction
            result['distance'] = found_distance if found_distance is not None else 1
            
            # If we also found a resource, add it
            if found_resource:
                result['what'] = found_resource
            
            # If we have both direction and distance, high confidence
            if found_distance is not None:
                result['confidence'] = max(result['confidence'], 0.8)
        
        # If confidence is too low, return None
        if result['confidence'] < 0.5:
            return None
        
        return result

    @staticmethod
    def handle_advice_command(message, agent_id, player_id):
        """Handle player giving advice to an NPC"""
        # Parse the advice from the message
        advice = NPCActionHandler._parse_advice(message)
        
        if not advice:
            return None
        
        # Get the direction and distance
        direction = advice.get('direction')
        distance = advice.get('distance', 1)
        what = advice.get('what', 'resource')
        
        # Map direction to action
        action = None
        if direction == 'right':
            action = 'move_right'
        elif direction == 'left':
            action = 'move_left'
        elif direction == 'up':
            action = 'move_up'
        elif direction == 'down':
            action = 'move_down'
        
        if not action:
            return None
        
        # Create a response
        return ActionResponse(
            action=action,
            speech=f"I'll check for {what} {distance} tiles to the {direction}.",
            mood_change=0.1,
            following_advice=True,
            advice_direction=direction,
            advice_distance=distance,
            advice_remaining_distance=distance
        )

    
    @staticmethod
    def process_player_message(message, agent_id, player_id):
        """Process a player message to see if it contains a command"""
        # Check for various command types
        handlers = [
            NPCActionHandler.handle_follow_command,
            NPCActionHandler.handle_stop_command,
            NPCActionHandler.handle_give_command,
            NPCActionHandler.handle_trade_command,
            NPCActionHandler.handle_info_command,
            NPCActionHandler.handle_explore_command,
            NPCActionHandler.handle_return_command,
            NPCActionHandler.handle_memory_command,
            NPCActionHandler.handle_record_command,
            NPCActionHandler.handle_advice_command
        ]
        
        for handler in handlers:
            response = handler(message, agent_id, player_id)
            if response:
                return True, response
        
        return False, None

class NPCActionExecutor:
    """Executes NPC actions based on ActionResponse objects"""
    
    @staticmethod
    def execute_action(npc, action_response, game_engine=None):
        """Execute an action on an NPC entity"""
        if not action_response:
            return False
        
        action = action_response.action
        
        # Handle follow player action
        if action == "follow_player":
            if hasattr(npc, 'ai_controller'):
                # If NPC has an AI controller, set it to follow player
                from engine.ai import FollowPlayerAI
                if not isinstance(npc.ai_controller, FollowPlayerAI):
                    # Create a new follow player AI controller
                    npc.ai_controller = FollowPlayerAI(npc, detection_range=8)
                    print(f"DEBUG: NPC {id(npc)} now following player")
                return True
        
        # Handle stop following action
        elif action == "stop_following":
            if hasattr(npc, 'ai_controller'):
                # If NPC has an AI controller, reset it to default
                from engine.ai import RandomWanderAI
                npc.ai_controller = RandomWanderAI(npc, wander_range=5)
                print(f"DEBUG: NPC {id(npc)} stopped following player")
                return True
        
        # Handle give item action
        elif action == "give_item":
            # Placeholder for giving item to player
            print(f"DEBUG: NPC {id(npc)} would give an item to player")
            return True
        
        # Handle trade action
        elif action == "trade":
            # Placeholder for trading with player
            print(f"DEBUG: NPC {id(npc)} would trade with player")
            return True
        
        # Handle show info action
        elif action == "show_info":
            # Placeholder for showing information
            print(f"DEBUG: NPC {id(npc)} would show information to player")
            return True
        
        # Handle explore action
        elif action == "explore":
            # Set NPC to exploration mode
            if hasattr(npc, 'exploration_mode'):
                npc.exploration_mode = "exploring"
                
                # Choose a random direction to explore
                if game_engine and game_engine.world_map:
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    dx, dy = random.choice(directions)
                    
                    # Set exploration target a few tiles away
                    explore_distance = random.randint(3, 8)
                    npc.exploration_target_x = npc.grid_x + (dx * explore_distance)
                    npc.exploration_target_y = npc.grid_y + (dy * explore_distance)
                    
                    # Ensure target is within map bounds
                    map_width = game_engine.world_map.width
                    map_height = game_engine.world_map.height
                    npc.exploration_target_x = max(0, min(map_width - 1, npc.exploration_target_x))
                    npc.exploration_target_y = max(0, min(map_height - 1, npc.exploration_target_y))
                
                print(f"DEBUG: NPC {id(npc)} starting exploration")
                return True
        
        # Handle return home action
        elif action == "return_home":
            # Set NPC to return home mode
            if hasattr(npc, 'exploration_mode') and hasattr(npc, 'home_location'):
                npc.exploration_mode = "returning"
                npc.exploration_target_x = npc.home_location[0]
                npc.exploration_target_y = npc.home_location[1]
                print(f"DEBUG: NPC {id(npc)} returning home to ({npc.exploration_target_x}, {npc.exploration_target_y})")
                return True
        
        # Handle share memories action
        elif action == "share_memories":
            # Generate a summary of memories to share
            if hasattr(npc, 'interesting_locations') and game_engine and hasattr(game_engine, 'ui'):
                memory_summary = []
                
                # Count locations by type
                for location_type, locations in npc.interesting_locations.items():
                    if locations:
                        memory_summary.append(f"I've found {len(locations)} {location_type} locations.")
                
                # Add explored area size
                if hasattr(npc, 'explored_tiles'):
                    memory_summary.append(f"I've explored about {len(npc.explored_tiles)} different areas.")
                
                # Create speech from summary
                if memory_summary:
                    speech = action_response.speech + " " + " ".join(memory_summary)
                else:
                    speech = "I haven't discovered much yet. I need to explore more."
                
                # Show the speech in a text bubble
                game_engine.ui.add_text_bubble(speech, npc, duration=5.0)
                print(f"DEBUG: NPC {id(npc)} sharing memories: {speech}")
                return True
        
        # Handle record location action
        elif action == "record_location":
            if game_engine and game_engine.world_map and hasattr(npc, 'interesting_locations'):
                # Get current tile type
                current_tile = game_engine.world_map.get_tile(npc.grid_x, npc.grid_y)
                if current_tile:
                    tile_type = current_tile.type
                    
                    # Record in interesting locations
                    if tile_type not in npc.interesting_locations:
                        npc.interesting_locations[tile_type] = []
                    
                    # Check if already recorded
                    location_exists = False
                    for x, y in npc.interesting_locations[tile_type]:
                        if x == npc.grid_x and y == npc.grid_y:
                            location_exists = True
                            break
                    
                    if not location_exists:
                        npc.interesting_locations[tile_type].append((npc.grid_x, npc.grid_y))
                        
                        # Record in world cache if available
                        if hasattr(game_engine, 'world_cache'):
                            game_engine.world_cache.add_location_discovery(
                                str(id(npc)),
                                tile_type,
                                npc.grid_x,
                                npc.grid_y,
                                f"{tile_type.capitalize()} area"
                            )
                    
                    print(f"DEBUG: NPC {id(npc)} recorded location: {tile_type} at ({npc.grid_x}, {npc.grid_y})")
                    return True
        
        # Handle follow advice action
        elif action == "follow_advice":
            # Set NPC to follow player advice
            if hasattr(action_response, 'target_coordinates'):
                # Coordinate-based advice
                x, y = action_response.target_coordinates
                
                # Set as exploration target
                if hasattr(npc, 'exploration_mode'):
                    npc.exploration_mode = "exploring"
                    npc.exploration_target_x = x
                    npc.exploration_target_y = y
                    print(f"DEBUG: NPC {id(npc)} following advice to coordinates ({x}, {y})")
                    return True
            
            elif hasattr(action_response, 'advice_direction') and hasattr(action_response, 'advice_distance'):
                # Direction-based advice
                direction = action_response.advice_direction
                distance = action_response.advice_distance
                
                # Set advice attributes on NPC
                npc.advice_direction = direction
                npc.advice_remaining_distance = distance
                
                # Start following the advice immediately
                if direction == "left":
                    npc.target_grid_x = npc.grid_x - 1
                    npc.is_moving = True
                elif direction == "right":
                    npc.target_grid_x = npc.grid_x + 1
                    npc.is_moving = True
                elif direction == "up":
                    npc.target_grid_y = npc.grid_y - 1
                    npc.is_moving = True
                elif direction == "down":
                    npc.target_grid_y = npc.grid_y + 1
                    npc.is_moving = True
                
                npc.advice_remaining_distance -= 1
                print(f"DEBUG: NPC {id(npc)} received advice to move {distance} tiles {direction}")
                return True
        
        return False

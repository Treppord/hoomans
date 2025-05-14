import json
import re
import logging
import random
from typing import Dict, List, Optional, Any
import traceback
import time

from ai.interfaces.local_model_interface import LocalModelInterface
from ai.utils.prompt_utils import create_adaptive_system_prompt, generate_player_advice_section

logger = logging.getLogger("AIUniverseController")

class AIInterface:
    """Interface for communicating with the AI model"""
    
    # Define available actions as class constants
    ACTIONS = {
        # Basic movement
        "move_left": {"description": "Move one step left"},
        "move_right": {"description": "Move one step right"},
        "move_up": {"description": "Move one step up"},
        "move_down": {"description": "Move one step down"},
        
        # Multi-step movement (for urgent needs)
        "move_left_fast": {"description": "Move multiple steps left quickly (when urgent)"},
        "move_right_fast": {"description": "Move multiple steps right quickly (when urgent)"},
        "move_up_fast": {"description": "Move multiple steps up quickly (when urgent)"},
        "move_down_fast": {"description": "Move multiple steps down quickly (when urgent)"},
        
        # Need-based actions
        "drink": {"description": "Drink water (only when adjacent to water)"},
        "eat": {"description": "Eat food (only when adjacent to food)"},
        
        # Exploration actions
        "explore": {"description": "Start exploring in a random direction"},
        "return_home": {"description": "Return to home base location"},
        "record_location": {"description": "Record current location in memory"},
        
        # Other actions
        "idle": {"description": "Stand still and observe surroundings"},
        "search": {"description": "Look around for resources"}
    }

    
    def __init__(self, use_local_model=True, model_path="models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"):
        self.use_local_model = use_local_model
        self.api_url = "http://localhost:11434/api/generate"  # Fallback to Ollama
        self.model_name = "tinyllama"  # Fallback model name
        self.local_model_loaded = False
        
        # Updated system prompt with template for player advice
        self.system_prompt = """
You are the AI controller for a game called Hoomans. Your job is to determine the actions and speech of NPCs.
Respond with a JSON object containing:
- action: move_left, move_right, move_up, move_down, drink, eat, idle
- speech: What the NPC says (can be empty). IMPORTANT: The speech should be natural dialogue, NOT commands or descriptions of actions.
- reason: Brief explanation of your decision (helps with debugging)
- mood_change: How this decision affects the NPC's mood (-1.0 to 1.0)

IMPORTANT RULES:
1. NPCs should speak in first person (e.g., "I'm thirsty" is correct)
2. Speech should reflect the NPC's personality traits and current needs
3. The "drink" action can ONLY be performed when the NPC is adjacent to water
4. ONLY focus on thirst and drinking when thirst is at 0 (critical)
5. When thirst is normal (1-5), focus on personality and exploration instead
6. If the player gives advice, consider following it, especially if it helps with critical needs

Example response:
{"action": "move_left", "speech": "I'm so thirsty!", "reason": "Looking for water", "mood_change": -0.1}
{"action": "drink", "speech": "Ah, refreshing water!", "reason": "Found water when critically thirsty", "mood_change": 0.5}
{"action": "idle", "speech": "What a beautiful day!", "reason": "No urgent needs, enjoying surroundings", "mood_change": 0.1}

Keep your responses concise and focused on the action and speech.
"""

        
        # Initialize local model if enabled
        if use_local_model:
            self.local_model = LocalModelInterface(model_path=model_path)

    def _validate_response_for_needs(self, response_json, has_critical_thirst, has_critical_hunger, nearby_tiles, grid_x, grid_y, agent_id=None):
        """Validate and correct the AI response based on the agent's needs"""
        
        knows_water_sources = False
        water_locations = []
        
        if agent_id and hasattr(self, 'world_cache') and self.world_cache:
            # Get agent memories
            agent_memories = self.world_cache.get_entity_memories(agent_id)
            
            # Look for water discoveries in memories
            for memory in agent_memories:
                if memory.get('type') == 'location_discovery' and memory.get('data', {}).get('location_type') == 'water':
                    knows_water_sources = True
                    water_data = memory.get('data', {})
                    water_locations.append((water_data.get('x'), water_data.get('y')))
        
        # If agent knows water sources and is critically thirsty, override to move to water
        if knows_water_sources and has_critical_thirst and water_locations:
            # Find the closest water source
            closest_water = min(water_locations, key=lambda loc: abs(loc[0] - grid_x) + abs(loc[1] - grid_y))
            water_x, water_y = closest_water
            
            # Calculate direction to water
            dx = water_x - grid_x
            dy = water_y - grid_y
            
            # Determine which direction to move
            if abs(dx) > abs(dy):
                action = "move_right" if dx > 0 else "move_left"
            else:
                action = "move_down" if dy > 0 else "move_up"
            
            # Override the action and speech
            response_json["action"] = action
            response_json["speech"] = ""  # No speech about thirst when we know where water is
            response_json["reason"] = f"Moving to known water source at ({water_x}, {water_y})"
            response_json["is_heading_to_known_water"] = True
            
            print(f"DEBUG: Agent {agent_id} knows about water at {closest_water} and is moving there")
            
            return response_json
        
        # Ensure we're working with a dictionary
        if isinstance(response_json, str):
            try:
                response_json = json.loads(response_json)
            except:
                # If parsing fails, create a basic response
                return {"action": "idle", "speech": ""}
        
        action = response_json.get("action", "idle")
        speech = response_json.get("speech", "")
        reason = response_json.get("reason", "")
        
        # Handle fast movement actions (convert to regular movement but remember it's fast)
        is_fast_movement = False
        if action.endswith("_fast"):
            is_fast_movement = True
            action = action.replace("_fast", "")
        
        # Check if the agent is following player advice
        following_advice = False
        advice_direction = None
        advice_distance = 0
        
        # Look for advice-related keywords in the reason
        advice_keywords = ["advice", "player said", "player told", "player mentioned", "player suggested"]
        if any(keyword in reason.lower() for keyword in advice_keywords):
            following_advice = True
            
            # Try to extract direction from reason or action
            direction_keywords = {
                "left": "left",
                "right": "right", 
                "up": "up",
                "north": "up",
                "down": "down",
                "south": "down",
                "east": "right",
                "west": "left"
            }
            
            for keyword, direction in direction_keywords.items():
                if keyword in reason.lower() or (action.startswith("move_") and action.endswith(keyword)):
                    advice_direction = direction
                    break
            
            # Try to extract distance from reason
            distance_pattern = r"(\d+)\s+(?:blocks?|tiles?|steps?)"
            distance_match = re.search(distance_pattern, reason.lower())
            if distance_match:
                try:
                    advice_distance = int(distance_match.group(1))
                except ValueError:
                    advice_distance = 1
            else:
                advice_distance = 1
        
        # Check if the agent knows about water sources (from world cache)
        knows_water_sources = False
        water_locations = []
        
        if agent_id and hasattr(self, 'world_cache') and self.world_cache:
            # Get agent memories
            agent_memories = self.world_cache.get_entity_memories(agent_id)
            
            # Look for water discoveries in memories
            for memory in agent_memories:
                if memory.get('type') == 'location_discovery' and memory.get('data', {}).get('location_type') == 'water':
                    knows_water_sources = True
                    water_data = memory.get('data', {})
                    water_locations.append((water_data.get('x'), water_data.get('y')))
        
        # Validate drink action
        if action == "drink":
            # Check if agent has critical thirst
            if not has_critical_thirst:
                # If thirst is not critical but still low (1-3), allow drinking
                if has_critical_thirst == False and 1 <= 3:  # Fixed: removed reference to agent_state
                    # Check if agent is adjacent to water
                    is_adjacent_to_water = False
                    for tile in nearby_tiles:
                        if (tile.get("type") == "water" and 
                            abs(tile["x"] - grid_x) <= 1 and 
                            abs(tile["y"] - grid_y) <= 1):
                            is_adjacent_to_water = True
                            break
                    
                    if not is_adjacent_to_water:
                        # If not adjacent to water, look for water
                        action = "search"
                else:
                    # If thirst is good (4-10), don't drink, explore instead
                    action = "explore"
            else:
                # Critical thirst - check if agent is adjacent to water
                is_adjacent_to_water = False
                for tile in nearby_tiles:
                    if (tile.get("type") == "water" and 
                        abs(tile["x"] - grid_x) <= 1 and 
                        abs(tile["y"] - grid_y) <= 1):
                        is_adjacent_to_water = True
                        break
                
                if not is_adjacent_to_water:
                    # If not adjacent to water but critically thirsty, look for water
                    water_tiles = [tile for tile in nearby_tiles if tile.get("type") == "water"]
                    if water_tiles:
                        # Move towards the nearest water
                        nearest_water = min(water_tiles, key=lambda t: abs(t["x"] - grid_x) + abs(t["y"] - grid_y))
                        dx = nearest_water["x"] - grid_x
                        dy = nearest_water["y"] - grid_y
                        
                        if abs(dx) > abs(dy):
                            action = "move_right" if dx > 0 else "move_left"
                        else:
                            action = "move_down" if dy > 0 else "move_up"
                        
                        # Mark as fast movement since we're critically thirsty
                        is_fast_movement = True
                    else:
                        # No water in sight, search randomly
                        action = random.choice(["move_left", "move_right", "move_up", "move_down"])
                        is_fast_movement = True
        
        # Handle exploration when thirst is good (5-10)
        # Fixed: removed reference to agent_state.thirst
        if action == "idle" and not has_critical_thirst and not has_critical_hunger:
            # 50% chance to explore instead of idle when needs are satisfied
            if random.random() < 0.5:
                action = "explore"
                if not speech:
                    exploration_speeches = [
                        "I should explore more of this area.",
                        "Let me see what's around here.",
                        "Time to do some exploring.",
                        "I wonder what I'll find if I look around.",
                        "I feel like exploring today."
                    ]
                    speech = random.choice(exploration_speeches)
        
        # Handle return home action
        if action == "return_home":
            # Only allow returning home if not critically thirsty
            if has_critical_thirst:
                action = "search"  # Look for water instead
                speech = "I need to find water before I can go home."
            else:
                if not speech:
                    return_speeches = [
                        "I should head back home now.",
                        "Time to return to my base.",
                        "I've explored enough, let's go home.",
                        "I'll head back to my starting point."
                    ]
                    speech = random.choice(return_speeches)
        
        # Handle record location action
        if action == "record_location":
            # Convert to idle but add memory update
            action = "idle"
            if not speech:
                record_speeches = [
                    "I should remember this location.",
                    "This is an interesting spot to remember.",
                    "I'll make a note of this place.",
                    "This location seems important."
                ]
                speech = random.choice(record_speeches)
        
        # Generate appropriate speech based on needs and actions
        if has_critical_thirst:
            # If critically thirsty but knows water sources, don't speak about thirst
            # The NPC will handle moving to water in the apply_ai_decision method
            if knows_water_sources:
                water_knowledge_speeches = [
                    "I know where to find water.",
                    "I remember seeing water nearby.",
                    "I should head to that water source I found earlier.",
                    "Good thing I know where water is.",
                    "I'll go to the water I discovered before."
                ]
                speech = random.choice(water_knowledge_speeches)
            else:
                # If critically thirsty and doesn't know water sources, override speech with water-focused dialogue
                water_speeches = [
                    "I need water desperately!",
                    "So thirsty... must find water...",
                    "Water... I need water now!",
                    "I'm dying of thirst!",
                    "Need to find water immediately!",
                    "My throat is so dry... need water...",
                    "Water! Where is water?!",
                    "Can't... go on... without... water...",
                    "Must... find... water..."
                ]
                speech = random.choice(water_speeches)
        elif has_critical_hunger:
            # If critically hungry, override speech with food-focused dialogue
            food_speeches = [
                "I'm starving!",
                "Need food... so hungry...",
                "Must find something to eat!",
                "My stomach hurts from hunger!",
                "Food... need food now!",
                "I haven't eaten in so long...",
                "So hungry I can barely walk...",
                "Need to find food before I collapse!"
            ]
            speech = random.choice(food_speeches)
        elif following_advice:
            # If following advice, generate appropriate speech
            if not speech or random.random() < 0.7:  # 70% chance to override existing speech
                advice_speeches = [
                    "Let me check what the player mentioned...",
                    "I'll follow that advice and see where it leads.",
                    "That's helpful information, I'll check it out.",
                    "Thanks for the tip! I'll head that way.",
                    "I appreciate the advice. Let me go see.",
                    "That sounds promising, I'll investigate."
                ]
                speech = random.choice(advice_speeches)
        else:
            # Filter out problematic speech for non-critical states
            if speech:
                # Check if speech is just a number or very short
                if speech.strip().isdigit() or len(speech.strip()) < 3:
                    speech = ""
                
                # Check if speech contains action commands
                action_keywords = ["move left", "move right", "move up", "move down", "move_left", "move_right", "move_up", "move_down"]
                if any(keyword in speech.lower() for keyword in action_keywords):
                    speech = ""
                
                # Check if speech contains implementation details
                implementation_keywords = ["npc", "agent", "tinted", "mojang", "draft", "action", "speech"]
                if any(keyword in speech.lower() for keyword in implementation_keywords):
                    speech = ""
                
                # Check if speech is incomplete (ends with certain characters)
                if speech.endswith(("I", "and I", "I'm", "she", "he", "they", "we", "the", "a", "an", "this", "that")):
                    speech = ""
            
            # If speech was filtered out, provide a generic alternative
            if not speech:
                generic_speeches = [
                    "Hello there!",
                    "Nice weather today.",
                    "I'm enjoying my walk.",
                    "This place is interesting.",
                    "I wonder what I'll find today.",
                    "It's good to be out exploring.",
                    "I like this area.",
                    "The scenery here is lovely."
                ]
                speech = random.choice(generic_speeches)
            
            # Reduce speech frequency to make it more natural
            # Only 20% chance to actually speak when moving
            if action != "idle" and action != "drink" and action != "eat" and random.random() > 0.2:
                speech = ""
        
        # Add fast movement flag to the response
        return {
            "action": action,
            "speech": speech,
            "reason": reason,
            "is_fast_movement": is_fast_movement,
            "following_advice": following_advice,
            "advice_direction": advice_direction,
            "advice_distance": advice_distance
        }

    def generate_decision(self, agent_state):
        """Generate a decision for an agent based on its current state"""
        try:
            # Check if the agent is standing on water (emergency situation)
            is_on_water = False
            for tile in agent_state.nearby_tiles:
                if (tile.get("type") == "water" and 
                    tile["x"] == agent_state.grid_x and 
                    tile["y"] == agent_state.grid_y):
                    is_on_water = True
                    break
            
            # If standing on water, find the nearest land tile and move there
            if is_on_water:
                print(f"DEBUG: Agent {agent_state.agent_id} is standing on water! Finding nearest land...")
                
                # Find the nearest land tile
                land_tiles = [tile for tile in agent_state.nearby_tiles 
                             if tile.get("type") != "water" and tile.get("walkable", False)]
                
                if land_tiles:
                    # Find the closest land tile
                    nearest_land = min(land_tiles, 
                                      key=lambda t: abs(t["x"] - agent_state.grid_x) + abs(t["y"] - agent_state.grid_y))
                    
                    # Calculate direction to land
                    dx = nearest_land["x"] - agent_state.grid_x
                    dy = nearest_land["y"] - agent_state.grid_y
                    
                    # Determine which direction to move (prioritize the larger distance)
                    if abs(dx) > abs(dy):
                        action = "move_right" if dx > 0 else "move_left"
                    else:
                        action = "move_down" if dy > 0 else "move_up"
                    
                    # Create a decision to escape water
                    from ai.models.agent_models import AgentDecision
                    return AgentDecision(
                        agent_id=agent_state.agent_id,
                        action=action,
                        speech="I need to get out of this water!",
                        reason="Escaping from standing on water",
                        mood_change=-0.3,  # Negative mood impact
                        is_escaping_water=True
                    )
                else:
                    # No land tiles found in nearby area, move in a random direction
                    action = random.choice(["move_left", "move_right", "move_up", "move_down"])
                    from ai.models.agent_models import AgentDecision
                    return AgentDecision(
                        agent_id=agent_state.agent_id,
                        action=action,
                        speech="Help! I'm stuck in water!",
                        reason="Trying to escape water but no land in sight",
                        mood_change=-0.5,  # Larger negative mood impact
                        is_escaping_water=True
                    )
            
            # Determine if agent has critical needs
            has_critical_thirst = agent_state.thirst < 1
            has_critical_hunger = agent_state.hunger < 1
            
            # Create a minimal state representation
            prompt = f"Position: ({agent_state.grid_x}, {agent_state.grid_y})\n"
            
            
            # Check if agent knows about water sources
            knows_water_sources = False
            water_locations = []
            
            if hasattr(self, 'world_cache') and self.world_cache:
                # Get agent memories from cache
                agent_memories = self.world_cache.get_entity_memories(agent_state.agent_id)
                
                # Look for water discoveries in memories
                for memory in agent_memories:
                    if memory.get('type') == 'location_discovery' and memory.get('data', {}).get('location_type') == 'water':
                        knows_water_sources = True
                        water_data = memory.get('data', {})
                        if 'x' in water_data and 'y' in water_data:
                            water_locations.append((water_data.get('x'), water_data.get('y')))
            
            # If agent is thirsty and knows water locations, prioritize going there
            if agent_state.thirst <= 3 and knows_water_sources and water_locations:
                # Find the closest water source
                closest_water = min(water_locations, key=lambda loc: abs(loc[0] - agent_state.grid_x) + abs(loc[1] - agent_state.grid_y))
                water_x, water_y = closest_water
                
                # Calculate direction to water
                dx = water_x - agent_state.grid_x
                dy = water_y - agent_state.grid_y
                
                # If we're at the water source, drink
                if abs(dx) <= 1 and abs(dy) <= 1:
                    from ai.models.agent_models import AgentDecision
                    return AgentDecision(
                        agent_id=agent_state.agent_id,
                        action="drink",
                        speech="",  # No speech needed
                        reason=f"Drinking from known water source at ({water_x}, {water_y})",
                        mood_change=0.3
                    )
                
                # Determine which direction to move
                if abs(dx) > abs(dy):
                    action = "move_right" if dx > 0 else "move_left"
                else:
                    action = "move_down" if dy > 0 else "move_up"
                
                print(f"DEBUG: Agent {agent_state.agent_id} is thirsty and moving to known water at ({water_x}, {water_y})")
                
                from ai.models.agent_models import AgentDecision
                return AgentDecision(
                    agent_id=agent_state.agent_id,
                    action=action,
                    speech="",  # No speech about thirst when we know where water is
                    reason=f"Moving to known water source at ({water_x}, {water_y})",
                    target_x=water_x,
                    target_y=water_y,
                    mood_change=0.1,
                    is_heading_to_known_water=True
                )
            
            
            # Add information about water if critically thirsty
            if has_critical_thirst:
                prompt += "CRITICAL THIRST! "
                # Add water locations if any
                water_tiles = [tile for tile in agent_state.nearby_tiles if tile.get("type") == "water"]
                if water_tiles:
                    nearest = min(water_tiles, key=lambda t: abs(t["x"] - agent_state.grid_x) + abs(t["y"] - agent_state.grid_y))
                    prompt += f"Nearest water: ({nearest['x']}, {nearest['y']}). "
                else:
                    prompt += "No water visible. "
            
            if has_critical_hunger:
                prompt += "CRITICAL HUNGER! "
            
            # Add personality info (very brief)
            if agent_state.cna_data:
                prompt += f"Name: {agent_state.cna_data.first_name}, "
                prompt += f"Culture: {agent_state.cna_data.culture.name}"
            
            # Add player advice if available
            if hasattr(agent_state, 'player_advice') and agent_state.player_advice:
                advice = agent_state.player_advice
                if advice["type"] == "direction":
                    prompt += f"\nPLAYER ADVICE: {advice['what']} is {advice['distance']} tiles to the {advice['direction']}."
                elif advice["type"] == "location":
                    prompt += f"\nPLAYER ADVICE: {advice['what']} is near the {advice['landmark']}."
            
            # Create a concise system prompt
            system_prompt = create_adaptive_system_prompt(has_critical_thirst, has_critical_hunger, self.ACTIONS)
            
            # Use local model if enabled
            if self.use_local_model and hasattr(self, 'local_model'):
                response_json = self.local_model.generate_response(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=64  # Keep responses short
                )
                
                # Validate the response
                validated_response = self._validate_response_for_needs(
                    response_json, 
                    has_critical_thirst, 
                    has_critical_hunger,
                    agent_state.nearby_tiles,
                    agent_state.grid_x,
                    agent_state.grid_y,
                    agent_id=agent_state.agent_id  # Pass the agent_id
                )
                
                # Check if we should follow player advice
                if hasattr(agent_state, 'player_advice') and agent_state.player_advice:
                    advice = agent_state.player_advice
                    advice_age = time.time() - getattr(agent_state, 'player_advice_time', 0)
                    
                    # Only follow recent advice (within last 30 seconds)
                    if advice_age < 30:
                        # If we have critical thirst and advice is about water, follow it
                        if (has_critical_thirst and advice["type"] == "direction" and 
                            (advice["what"] == "water" or "water" in advice["what"])):
                            
                            direction = advice["direction"]
                            # Map direction to action
                            action_map = {
                                "left": "move_left",
                                "right": "move_right", 
                                "up": "move_up",
                                "down": "move_down",
                                "north": "move_up",
                                "south": "move_down",
                                "east": "move_right",
                                "west": "move_left"
                            }
                            
                            if direction in action_map:
                                validated_response["action"] = action_map[direction]
                                validated_response["speech"] = "I'll check for water where you suggested!"
                                validated_response["following_advice"] = True
                                validated_response["advice_direction"] = direction
                                validated_response["advice_distance"] = advice["distance"]
                                validated_response["reason"] = "Following player's advice about water location"
                
                from ai.models.agent_models import AgentDecision
                return AgentDecision.from_ai_response(agent_state.agent_id, validated_response)
                
        except Exception as e:
            logger.error(f"Error generating decision: {e}")
            logger.error(traceback.format_exc())
            from ai.models.agent_models import AgentDecision
            return AgentDecision(agent_id=agent_state.agent_id, action="idle")

    def generate_batch_decisions(self, agent_states):
        """Generate decisions for multiple agents (one by one)"""
        decisions = []
        for state in agent_states:
            decision = self.generate_decision(state)
            decisions.append(decision)
        return decisions

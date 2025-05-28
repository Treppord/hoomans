import threading
import queue
import time
import random
import json
import os
import sys
import logging
import traceback
from typing import Dict, List, Tuple, Optional, Any
import re

# Import refactored modules
from ai.models.agent_models import AgentState, AgentDecision
from ai.interfaces.ai_interface import AIInterface
from ai.controllers.fallback_ai import FallbackAI
from ai.interfaces.local_model_interface import LocalModelInterface
from ai.utils.world_utils import WorldStateCollector, parse_player_advice, is_memory_query, detect_attribute_query
from ai.utils.prompt_utils import create_attribute_aware_prompt, extract_npc_response, generate_fallback_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AIUniverseController")

# Import CNA utilities from the existing codebase
try:
    from cna_utils import CNAAttributes, CNACodec, Gender, Culture, Nation
except ImportError:
    # If running from a different directory, try to add the parent directory to path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    try:
        from cna_utils import CNAAttributes, CNACodec, Gender, Culture, Nation
    except ImportError:
        logger.error("Failed to import CNA utilities. Make sure cna_utils.py is accessible.")
        raise

class AIUniverseController:
    """Main controller for the AI universe simulation"""
    
    def __init__(self, use_llm: bool = True, use_local_model: bool = False, model_path: str = None, model_name: str = "llama3"):
        self.agents: Dict[str, AgentState] = {}
        self.running = False
        self.thread = None
        self.use_llm = use_llm
        self.use_local_model = use_local_model
        
        # Queues for communication with the game engine
        self.state_update_queue = queue.Queue()
        self.decision_queue = queue.Queue()
        
        # Initialize AI interface
        if self.use_llm:
            try:
                self.ai_interface = AIInterface(use_local_model=use_local_model, model_path=model_path)
                if use_local_model and model_path:
                    logger.info(f"Initialized AI interface with local model: {model_path}")
                else:
                    logger.info(f"Initialized AI interface with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize AI interface: {e}")
                logger.error("Falling back to rule-based AI")
                self.use_llm = False
        
        # Processing interval (seconds)
        self.processing_interval = 0.5
        
        # Last processing time for each agent
        self.last_processed = {}
        
        # Load CNA data cache
        self.cna_cache = {}

    def start(self):
        """Start the AI universe controller thread"""
        if self.running:
            logger.warning("AI Universe Controller is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("AI Universe Controller started")
    
    def stop(self):
        """Stop the AI universe controller thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            logger.info("AI Universe Controller stopped")
    
    def _run_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Process any state updates from the game engine
                self._process_state_updates()
                
                # Process agents that need decisions
                self._process_agents()
                
                # Sleep to avoid high CPU usage
                time.sleep(0.05)
            except Exception as e:
                logger.error(f"Error in AI Universe Controller loop: {e}")
                logger.error(traceback.format_exc())
    
    def _process_state_updates(self):
        """Process state updates from the game engine"""
        try:
            # Process all available updates without blocking
            while not self.state_update_queue.empty():
                update = self.state_update_queue.get_nowait()
                
                if isinstance(update, dict) and "agent_id" in update:
                    agent_id = update["agent_id"]
                    
                    # Check if this is a chat response request
                    if "player_message" in update and "should_respond" in update and update["should_respond"]:
                        # Generate a response immediately
                        self._generate_chat_response(agent_id, update["player_message"])
                        self.state_update_queue.task_done()
                        continue
                    
                    # Create or update agent state
                    if agent_id not in self.agents:
                        # New agent
                        self.agents[agent_id] = AgentState(
                            agent_id=agent_id,
                            grid_x=update.get("grid_x", 0),
                            grid_y=update.get("grid_y", 0)
                        )
                        self.last_processed[agent_id] = 0
                    
                    # Update existing agent
                    agent = self.agents[agent_id]
                    
                    # Update position
                    if "grid_x" in update and "grid_y" in update:
                        agent.grid_x = update["grid_x"]
                        agent.grid_y = update["grid_y"]
                    
                    # Update needs
                    if "thirst" in update:
                        agent.thirst = update["thirst"]
                    if "hunger" in update:
                        agent.hunger = update["hunger"]
                    if "health" in update:
                        agent.health = update["health"]
                    
                    # Update environment awareness
                    if "nearby_entities" in update:
                        agent.nearby_entities = update["nearby_entities"]
                    if "nearby_tiles" in update:
                        agent.nearby_tiles = update["nearby_tiles"]
                    
                    # Update CNA data if provided
                    if "cna_file" in update and update["cna_file"]:
                        cna_file = update["cna_file"]
                        if cna_file not in self.cna_cache:
                            try:
                                self.cna_cache[cna_file] = CNACodec.load_from_file(cna_file)
                                logger.info(f"Loaded CNA data from {cna_file}")
                            except Exception as e:
                                logger.error(f"Failed to load CNA data from {cna_file}: {e}")
                        
                        if cna_file in self.cna_cache:
                            agent.cna_data = self.cna_cache[cna_file]
                
                # Mark as processed
                self.state_update_queue.task_done()
        except Exception as e:
            logger.error(f"Error processing state updates: {e}")
            logger.error(traceback.format_exc())
    
    def _parse_agent_decision(self, agent_id: str, response_text: str) -> AgentDecision:
        """Parse the agent's decision from the response text"""
        # Default values
        action = "idle"
        speech = ""
        reason = ""
        
        # Try to extract action, speech, and reason from the response
        action_match = re.search(r'ACTION:\s*(\w+)', response_text)
        speech_match = re.search(r'SPEECH:\s*(.*?)(?:\n|$)', response_text)
        reason_match = re.search(r'REASON:\s*(.*?)(?:\n|$)', response_text)
        
        if action_match:
            action = action_match.group(1).strip().lower()
        if speech_match:
            speech = speech_match.group(1).strip()
        if reason_match:
            reason = reason_match.group(1).strip()
        # Check if the agent is following player advice
        following_advice = False
        advice_direction = None
        advice_distance = 0
        
        # Get the agent state
        agent_state = self.agents.get(agent_id)
        if agent_state and hasattr(agent_state, 'player_advice') and agent_state.player_advice:
            advice = agent_state.player_advice
            
            # Check if the reason mentions following advice
            advice_keywords = ["advice", "player said", "player told", "player mentioned"]
            if any(keyword in reason.lower() for keyword in advice_keywords):
                following_advice = True
                
                # For directional advice
                if advice["type"] == "direction":
                    advice_direction = advice["direction"]
                    advice_distance = advice["distance"]
                    
                    # Mark that the advice is being followed
                    agent_state.advice_followed = True
        
        return AgentDecision(
            agent_id=agent_id,
            action=action,
            speech=speech,
            reason=reason,
            mood_change=0.0,  # Default mood change
            following_advice=following_advice,
            advice_direction=advice_direction,
            advice_distance=advice_distance
        )
    
    def _get_agent_memory_for_location(self, agent_id: str, resource_type: str) -> Optional[Dict]:
        """
        Retrieve an agent's memory about a specific resource location
        Returns memory data or None if not found
        """
        # First check if agent exists
        if agent_id not in self.agents:
            print(f"DEBUG: Agent {agent_id} not found in agents dictionary")
            return None
            
        # Check if we have a world cache reference
        if not hasattr(self, 'world_cache'):
            # Try to get world cache from game engine
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'world_cache'):
                self.world_cache = SimpleGameEngine.instance.world_cache
                print(f"DEBUG: Got world cache reference from game engine")
            else:
                print(f"DEBUG: Could not get world cache reference")
                return None
        
        # Get agent memories from cache
        agent_memories = self.world_cache.get_entity_memories(agent_id) if hasattr(self.world_cache, 'get_entity_memories') else []
        print(f"DEBUG: Found {len(agent_memories)} memories for agent {agent_id}")
        
        # Look for location memories matching the resource type
        for memory in agent_memories:
            if memory.get("type") == "location_discovery":
                memory_data = memory.get("data", {})
                if memory_data.get("location_type") == resource_type:
                    print(f"DEBUG: Found memory for {resource_type} at ({memory_data.get('x')}, {memory_data.get('y')})")
                    return memory_data
        
        # If agent doesn't have direct memory, check discovered locations
        discovered_locations = self.world_cache.get_discovered_locations(resource_type) if hasattr(self.world_cache, 'get_discovered_locations') else []
        print(f"DEBUG: Found {len(discovered_locations)} discovered {resource_type} locations")
        
        # Check if any of these locations were discovered by this agent
        for location in discovered_locations:
            if "discovered_by" in location and agent_id in location["discovered_by"]:
                print(f"DEBUG: Found location discovered by agent at ({location.get('x')}, {location.get('y')})")
                return location
                
        # If still not found, check if the agent is near any discovered location of this type
        agent_state = self.agents[agent_id]
        for location in discovered_locations:
            # Calculate Manhattan distance
            distance = abs(location["x"] - agent_state.grid_x) + abs(location["y"] - agent_state.grid_y)
            # If agent is or has been near this location, they might know about it
            if distance <= 10:  # Within reasonable distance
                print(f"DEBUG: Found nearby location at ({location.get('x')}, {location.get('y')})")
                # Important: Don't return the location directly, create a copy with this agent as discoverer
                # This prevents accidentally attributing the discovery to this agent
                location_copy = location.copy()
                return {
                    "location_type": resource_type,
                    "x": location["x"],
                    "y": location["y"],
                    "name": location.get("name", f"{resource_type} source")
                }
                
        print(f"DEBUG: No memory found for {resource_type}")
        return None
    
    def _generate_chat_response(self, agent_id, player_message):
        """Generate a response to a player chat message"""
        try:
            # Get the agent state
            agent = self.agents.get(agent_id)
            if not agent:
                logger.error(f"DEBUG: Agent {agent_id} not found for chat response")
                return
            
            logger.info(f"DEBUG: Generating chat response for agent {agent_id} to message: '{player_message}'")
            
            # IMPORTANT: Set a flag to indicate this agent is responding to chat
            # This will be used to prioritize chat responses
            agent.is_responding_to_chat = True
            agent.chat_response_time = time.time()
            
            # Check if this is a memory query
            is_memory_query_result, resource_type = is_memory_query(player_message)
            
            # Special handling for water queries
            if "water" in player_message.lower() and any(word in player_message.lower() for word in ["where", "location", "know", "remember", "nearby"]):
                is_memory_query_result = True
                resource_type = "water"
                logger.info(f"DEBUG: Detected water query override")
            
            if is_memory_query_result:
                logger.info(f"DEBUG: Detected memory query for resource type: {resource_type}")
                
                # Handle general memory query
                if resource_type == "general":
                    # Get all agent memories
                    if not hasattr(self, 'world_cache'):
                        from engine.core import SimpleGameEngine
                        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'world_cache'):
                            self.world_cache = SimpleGameEngine.instance.world_cache
                    
                    if hasattr(self, 'world_cache'):
                        memories = self.world_cache.get_entity_memories(agent_id)
                        if memories:
                            # Summarize memories
                            memory_types = set(memory.get("type") for memory in memories)
                            
                            # Create a response based on memory types
                            if "location_discovery" in memory_types:
                                location_memories = [m for m in memories if m.get("type") == "location_discovery"]
                                locations = [m.get("data", {}).get("location_type") for m in location_memories]
                                locations = [loc for loc in locations if loc]  # Filter out None
                                
                                if locations:
                                    response = f"I remember finding {', '.join(locations)}. "
                                    
                                    # Add details about the most recent location
                                    recent_location = location_memories[-1].get("data", {})
                                    if "x" in recent_location and "y" in recent_location:
                                        response += f"The most recent was {recent_location.get('location_type')} at coordinates ({recent_location.get('x')}, {recent_location.get('y')})."
                                    
                                    # Create a decision with the response
                                    decision = AgentDecision(
                                        agent_id=agent_id,
                                        action="idle",
                                        speech=response,
                                        mood_change=0.1
                                    )
                                    self.decision_queue.put(decision)
                                    return
                    
                    # Fallback for general memory query
                    decision = AgentDecision(
                        agent_id=agent_id,
                        action="idle",
                        speech="I don't have any significant memories to share right now.",
                        mood_change=0
                    )
                    self.decision_queue.put(decision)
                    
                    return
                
                # Direct check for water sources in world cache
                if resource_type == "water" and hasattr(self, 'world_cache'):
                    # Try to get world cache from game engine if not already available
                    if not hasattr(self, 'world_cache'):
                        from engine.core import SimpleGameEngine
                        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'world_cache'):
                            self.world_cache = SimpleGameEngine.instance.world_cache
                    
                    # Check if we have water locations in the cache
                    water_locations = self.world_cache.get_discovered_locations("water")
                    print(f"DEBUG: Found {len(water_locations)} water locations in cache")
                    
                    if water_locations:
                        # Find locations discovered by this agent
                        agent_water_locations = [loc for loc in water_locations if "discovered_by" in loc and agent_id in loc["discovered_by"]]
                        
                        if agent_water_locations:
                            # Use the most recently discovered water location
                            location = max(agent_water_locations, key=lambda loc: loc.get("discovery_time", 0))
                            
                            x = location.get("x")
                            y = location.get("y")
                            name = location.get("name", "Water source")
                            
                            # Calculate direction from agent to location
                            direction = ""
                            if x is not None and y is not None:
                                dx = x - agent.grid_x
                                dy = y - agent.grid_y
                                
                                if abs(dx) > abs(dy):
                                    direction = "east" if dx > 0 else "west"
                                else:
                                    direction = "south" if dy > 0 else "north"
                                    
                                # Calculate distance
                                distance = abs(dx) + abs(dy)
                                
                                response = f"Yes, I found a {name} at coordinates ({x}, {y}). "
                                response += f"That's about {distance} tiles to the {direction} from here."
                            else:
                                response = f"Yes, I remember finding a {name}, but I'm not sure exactly where it was."
                            
                            # Create a decision with the response
                            decision = AgentDecision(
                                agent_id=agent_id,
                                action="idle",
                                speech=response,
                                mood_change=0.1
                            )
                            self.decision_queue.put(decision)
                            return
                        else:
                            # Check if there are any water locations nearby that the agent might know about
                            nearby_water = None
                            for location in water_locations:
                                # Calculate Manhattan distance
                                distance = abs(location["x"] - agent.grid_x) + abs(location["y"] - agent.grid_y)
                                # If agent is or has been near this location, they might know about it
                                if distance <= 10:  # Within reasonable distance
                                    nearby_water = location
                                    break
                            
                            if nearby_water:
                                x = nearby_water.get("x")
                                y = nearby_water.get("y")
                                name = nearby_water.get("name", "Water source")
                                
                                # Calculate direction from agent to location
                                direction = ""
                                if x is not None and y is not None:
                                    dx = x - agent.grid_x
                                    dy = y - agent.grid_y
                                    
                                    if abs(dx) > abs(dy):
                                        direction = "east" if dx > 0 else "west"
                                    else:
                                        direction = "south" if dy > 0 else "north"
                                        
                                    # Calculate distance
                                    distance = abs(dx) + abs(dy)
                                    
                                    response = f"I've seen a {name} at coordinates ({x}, {y}). "
                                    response += f"That's about {distance} tiles to the {direction} from here."
                                    
                                    # Create a decision with the response
                                    decision = AgentDecision(
                                        agent_id=agent_id,
                                        action="idle",
                                        speech=response,
                                        mood_change=0.1
                                    )
                                    self.decision_queue.put(decision)
                                    
                                    # IMPORTANT: Record this as a memory for this agent
                                    # This ensures the agent "knows" about this location for future queries
                                    if hasattr(self, 'world_cache'):
                                        print(f"DEBUG: Recording water location memory for agent {agent_id}")
                                        self.world_cache.add_location_discovery(
                                            agent_id,
                                            "water",
                                            x,
                                            y,
                                            name
                                        )
                                    
                                    return
                
                # Handle specific resource type query
                memory_data = self._get_agent_memory_for_location(agent_id, resource_type)
                
                if memory_data:
                    # Generate response with location information
                    x = memory_data.get("x")
                    y = memory_data.get("y")
                    name = memory_data.get("name", f"{resource_type} source")
                    
                    # Calculate direction from agent to location
                    direction = ""
                    if x is not None and y is not None:
                        dx = x - agent.grid_x
                        dy = y - agent.grid_y
                        
                        if abs(dx) > abs(dy):
                            direction = "east" if dx > 0 else "west"
                        else:
                            direction = "south" if dy > 0 else "north"
                            
                        # Calculate distance
                        distance = abs(dx) + abs(dy)
                        
                        response = f"I remember finding {name} at coordinates ({x}, {y}). "
                        response += f"That's about {distance} tiles to the {direction} from here."
                        
                        # IMPORTANT: Record this as a memory for this agent if it's not already recorded
                        # This ensures the agent "knows" about this location for future queries
                        if hasattr(self, 'world_cache'):
                            # Check if this agent already has this memory
                            agent_memories = self.world_cache.get_entity_memories(agent_id)
                            has_memory = False
                            for memory in agent_memories:
                                if (memory.get("type") == "location_discovery" and
                                    memory.get("data", {}).get("x") == x and
                                    memory.get("data", {}).get("y") == y):
                                    has_memory = True
                                    break
                            
                            if not has_memory:
                                print(f"DEBUG: Recording {resource_type} location memory for agent {agent_id}")
                                self.world_cache.add_location_discovery(
                                    agent_id,
                                    resource_type,
                                    x,
                                    y,
                                    name
                                )
                    else:
                        response = f"I remember finding {name}, but I'm not sure exactly where it was."
                    
                    # Create a decision with the response
                    decision = AgentDecision(
                        agent_id=agent_id,
                        action="idle",
                        speech=response,
                        mood_change=0.1
                    )
                    self.decision_queue.put(decision)
                    return
                else:
                    # No memory found
                    response = f"I don't remember seeing any {resource_type} around here."
                    decision = AgentDecision(
                        agent_id=agent_id,
                        action="idle",
                        speech=response,
                        mood_change=-0.1
                    )
                    self.decision_queue.put(decision)
                    return
            
            # Continue with existing command processing
            from entities.npc_actions import NPCActionHandler
            is_command, action_response = NPCActionHandler.process_player_message(
                player_message, 
                agent_id, 
                player_id="player"
            )
            
            if is_command and action_response:
                logger.info(f"DEBUG: Detected command in message: {action_response.action}")
                
                # Create a decision with the action and speech
                decision = AgentDecision(
                    agent_id=agent_id,
                    action=action_response.action,
                    speech=action_response.speech,
                    mood_change=action_response.mood_change
                )
                
                # Add target_id as an attribute after creation if needed
                if hasattr(action_response, 'target_id') and action_response.target_id:
                    decision.target_id = action_response.target_id
                
                if hasattr(action_response, 'following_advice') and action_response.following_advice:
                    decision.following_advice = action_response.following_advice
                
                if hasattr(action_response, 'advice_direction') and action_response.advice_direction:
                    decision.advice_direction = action_response.advice_direction
                
                if hasattr(action_response, 'advice_distance'):
                    decision.advice_distance = action_response.advice_distance
                
                if hasattr(action_response, 'advice_remaining_distance'):
                    decision.advice_remaining_distance = action_response.advice_remaining_distance
                
                logger.info(f"DEBUG: Queuing command response decision for agent {agent_id}")
                
                # Put the decision in the queue for the game engine
                self.decision_queue.put(decision)
                return
            
            # Check if this is advice about directions or resources
            advice = parse_player_advice(player_message)
            if advice:
                logger.info(f"DEBUG: Detected advice in message: {advice}")
                
                # Create a movement decision based on the advice
                direction = advice.get('direction', '').lower()
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
                
                if action:
                    logger.info(f"DEBUG: Created movement decision based on advice: {action}")
                    
                    # First, acknowledge the advice
                    decision = AgentDecision(
                        agent_id=agent_id,
                        action="idle",
                        speech=f"Thanks for the tip! I'll go check for {what} to the {direction}."
                    )
                    self.decision_queue.put(decision)
                    
                    # Then create a decision to follow the advice
                    decision = AgentDecision(
                        agent_id=agent_id,
                        action=action,
                        speech=f"I'll check for {what} {distance} tiles to the {direction}.",
                        following_advice=True,
                        advice_direction=direction,
                        advice_distance=distance,
                        advice_remaining_distance=distance  # Set the remaining distance
                    )
                    self.decision_queue.put(decision)
                    return
            
            attribute_query = detect_attribute_query(player_message)
            
            # Create a simpler, more direct prompt for the small model
            prompt = f"Player: {player_message}\n\nRespond as an NPC in a game. Keep it short and natural."
            
            if agent.cna_data:
                prompt = create_attribute_aware_prompt(agent, player_message, attribute_query)
            
            # Simplified system prompt
            system_prompt = "You are an NPC in a game. Respond to the player's message with a short, natural reply that reflects your character's attributes. DO NOT prefix your response with your name. DO NOT say you're here to help on a journey or adventure."
            
            # Generate response
            response_text = None
            
            # Create a simpler, more direct prompt for the small model
            prompt = f"Player: {player_message}\n\nRespond as an NPC in a game. Keep it short and natural."
            
            if agent.cna_data:
                prompt = create_attribute_aware_prompt(agent, player_message, attribute_query)
            
            # Simplified system prompt
            system_prompt = "You are an NPC in a game. Respond to the player's message with a short, natural reply that reflects your character's attributes. DO NOT prefix your response with your name. DO NOT say you're here to help on a journey or adventure."
            
            # Generate response
            response_text = None
            if self.use_llm and hasattr(self, 'ai_interface'):
                try:
                    if hasattr(self.ai_interface, 'local_model'):
                        logger.info(f"DEBUG: Using local model for chat response")
                        
                        # Try direct text generation instead of JSON format for small models
                        try:
                            # Direct text generation approach
                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ]
                            
                            output = self.ai_interface.local_model.llm.create_chat_completion(
                                messages=messages,
                                max_tokens=128,
                                temperature=0.8,
                                top_p=0.95,
                                stop=["</s>", "Player:", "player:", "User:", "user:"]
                            )
                            
                            # Extract the raw text response
                            response_text = output["choices"][0]["message"]["content"].strip()
                            logger.info(f"DEBUG: Raw model text response: '{response_text}'")
                            
                            # Clean up the response
                            # Remove any name prefix (e.g., "Dakota: ")
                            if ":" in response_text and response_text.split(":")[0].strip() == agent.cna_data.first_name:
                                response_text = response_text.split(":", 1)[1].strip()
                            
                            # Remove any JSON-like formatting that might have been generated
                            response_text = response_text.replace('{"speech": "', '').replace('"}', '')
                            response_text = response_text.replace('"', '')
                            
                                
                        except Exception as e:
                            logger.error(f"Error with direct text generation: {e}")
                            response_text = None
                            
                except Exception as e:
                    logger.error(f"Error generating chat response: {e}")
                    logger.error(traceback.format_exc())
            
            # If direct text generation failed or is empty, use fallback responses
            if not response_text:
                logger.info(f"DEBUG: Using fallback responses for chat")
                
                # Generate attribute-appropriate fallback responses
                if attribute_query == "mental_health" and agent.cna_data and hasattr(agent.cna_data, 'mental_health'):
                    mental_health = agent.cna_data.mental_health
                    if mental_health <= 1:
                        response_text = "I'm struggling mentally right now. Everything feels overwhelming."
                    elif mental_health <= 3:
                        response_text = "My mental state is okay, I suppose. I have good days and bad days."
                    else:
                        response_text = "I'm in a good place mentally. My thoughts are clear and I feel positive."
                elif attribute_query == "physical_health" and agent.cna_data and hasattr(agent.cna_data, 'physical_health'):
                    physical_health = agent.cna_data.physical_health
                    if physical_health <= 1:
                        response_text = "I'm not doing well physically. My body feels weak and I tire easily."
                    elif physical_health <= 3:
                        response_text = "I'm in average physical condition. Not great, but I manage."
                    else:
                        response_text = "I'm in excellent physical shape. I feel strong and energetic."
                elif attribute_query == "intelligence" and agent.cna_data and hasattr(agent.cna_data, 'intelligence_factor'):
                    intelligence = agent.cna_data.intelligence_factor
                    if intelligence < 0.8:
                        response_text = "I'm not the brightest, but I get by with what I know."
                    elif intelligence < 1.2:
                        response_text = "I'd say I'm of average intelligence. I understand most things."
                    else:
                        response_text = "I've always been quick to learn. I understand complex ideas easily."
                else:
                    # Simple fallback responses
                    fallback_responses = [
                        "Hello there!",
                        "Nice to meet you.",
                        "What an interesting thing to say.",
                        "I'm not sure I understand.",
                        "That's fascinating.",
                        "I was just thinking about that.",
                        "I see what you mean.",
                        "Is that so?",
                        "Tell me more about that."
                    ]
                    
                    # If we have CNA data, add some personalized responses
                    if agent.cna_data:
                        name = agent.cna_data.first_name
                        fallback_responses.extend([
                            f"I'm {name}, nice to meet you!",
                            f"That's interesting. By the way, I'm {name}.",
                            f"I'm from {agent.cna_data.nation.name}, we don't talk like that there.",
                            f"In {agent.cna_data.culture.name} culture, we have a saying about that."
                        ])
                    
                    # If thirsty, add thirst-related responses
                    if agent.thirst <= 1:
                        fallback_responses.extend([
                            "Sorry, I'm too thirsty to chat right now.",
                            "I need to find water soon...",
                            "Do you know where I can find some water?"
                        ])
                    
                    # Always use a fallback response for now to ensure we get a response
                    response_text = random.choice(fallback_responses)
                    logger.info(f"DEBUG: Selected fallback response: '{response_text}'")
            
            logger.info(f"DEBUG: Final NPC response speech: '{response_text}'")
            
            # Create a decision with just the speech
            decision = AgentDecision(
                agent_id=agent_id,
                action="respond_to_chat",  # Special action for chat responses
                speech=response_text,
                mood_change=0.1  # Slight mood boost from social interaction
            )
            
            logger.info(f"DEBUG: Queuing chat response decision for agent {agent_id}")
            
            # Put the decision in the queue for the game engine
            self.decision_queue.put(decision)
        
            # IMPORTANT: Clear the responding to chat flag since we've generated a response
            agent.is_responding_to_chat = False
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            logger.error(traceback.format_exc())
            
            # Fallback response
            fallback_response = "I'm sorry, I didn't quite understand that."
            decision = AgentDecision(
                agent_id=agent_id,
                action="respond_to_chat",
                speech=fallback_response,
                mood_change=0.0
            )
            self.decision_queue.put(decision)
            
            if 'agent' in locals() and agent:
                agent.is_responding_to_chat = False

    def _process_agents(self):
        """Process agents that need decisions"""
        current_time = time.time()
        agents_to_process = []
        
        # First, check for agents that are responding to chat
        chat_responders = []
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'is_responding_to_chat') and agent.is_responding_to_chat:
                # If the chat response has been pending for too long, clear the flag
                if current_time - agent.chat_response_time > 60.0:  # 60 second timeout
                    agent.is_responding_to_chat = False
                    logger.warning(f"Chat response for agent {agent_id} timed out")
                    
                    # Create a fallback response to ensure the NPC doesn't stay paused
                    decision = AgentDecision(
                        agent_id=agent_id,
                        action="respond_to_chat",
                        speech="Sorry, I got distracted. What were you saying?",
                        mood_change=-0.1  # Slight negative mood impact for getting distracted
                    )
                    self.decision_queue.put(decision)
                else:
                    chat_responders.append(agent)
        
        # Process chat responders first
        if chat_responders:
            logger.info(f"Processing {len(chat_responders)} agents responding to chat")
            agents_to_process.extend(chat_responders)
        
        # Then process regular agents that need decisions
        if not agents_to_process:  # Only if no chat responders
            for agent_id, agent in self.agents.items():
                last_time = self.last_processed.get(agent_id, 0)
                if current_time - last_time >= self.processing_interval:
                    # Skip agents that are waiting for chat responses
                    if hasattr(agent, 'is_responding_to_chat') and agent.is_responding_to_chat:
                        continue
                    
                    # Skip agents that are currently drinking water
                    if (hasattr(agent, 'thirst') and agent.thirst < 5 and 
                        hasattr(agent, 'is_adjacent_to_water') and agent.is_adjacent_to_water):
                        # Skip processing - let the NPC continue drinking
                        continue
                        
                    agents_to_process.append(agent)
                    self.last_processed[agent_id] = current_time
        
        if not agents_to_process:
            return
        
        # Generate decisions
        try:
            if self.use_llm:
                try:
                    decisions = self.ai_interface.generate_batch_decisions(agents_to_process)
                except Exception as e:
                    logger.error(f"Error using AI interface: {e}")
                    logger.error("Falling back to rule-based AI for this batch")
                    decisions = FallbackAI.generate_batch_decisions(agents_to_process)
            else:
                decisions = FallbackAI.generate_batch_decisions(agents_to_process)
            
            # Process decisions
            for decision in decisions:
                # Update agent state based on decision
                if decision.agent_id in self.agents:
                    agent = self.agents[decision.agent_id]
                    
                    # Update last action and speech
                    agent.last_action = decision.action
                    if decision.speech:
                        agent.last_speech = decision.speech
                    
                    # Update mood
                    agent.mood = max(0.0, min(1.0, agent.mood + decision.mood_change))
                    
                    # Update memory if there's a reason
                    if hasattr(decision, 'reason') and decision.reason:
                        agent.memory.append({
                            "timestamp": time.time(),
                            "content": decision.reason
                        })
                        # Keep memory limited to last 20 items
                        if len(agent.memory) > 20:
                            agent.memory = agent.memory[-20:]
                
                # Put decision in queue for game engine
                self.decision_queue.put(decision)
        
        except Exception as e:
            logger.error(f"Error processing agents: {e}")
            logger.error(traceback.format_exc())
    
    def update_agent_state(self, agent_id, **kwargs):
        """Update an agent's state from the game engine"""
        update = {"agent_id": agent_id, **kwargs}
        self.state_update_queue.put(update)
        
        # Check if this is a chat response request and notify the game engine
        if "player_message" in kwargs and "should_respond" in kwargs and kwargs["should_respond"]:
            # Find the NPC in the game engine and pause its activities
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance'):
                engine = SimpleGameEngine.instance
                for obj in engine.objects:
                    if hasattr(obj, 'get_entity_id') and obj.get_entity_id() == agent_id:
                        if hasattr(obj, '_pause_for_chat'):
                            obj._pause_for_chat()
                            print(f"DEBUG: AI Universe notified NPC {agent_id} to pause for chat")
                        break
        
        # Check if there's a player message to process
        if "player_message" in kwargs:
            # Parse the message for advice
            advice = parse_player_advice(kwargs["player_message"])
            if advice and agent_id in self.agents:
                # Get the agent state from the agents dictionary
                agent_state = self.agents[agent_id]
                # Store the advice in the agent state
                agent_state.player_advice = advice
                agent_state.player_advice_time = time.time()
                agent_state.advice_followed = False  # Reset this flag
                logger.info(f"DEBUG: Stored player advice for agent {agent_id}: {advice}")
    
    def get_pending_decisions(self) -> List[AgentDecision]:
        """Get all pending decisions for the game engine"""
        decisions = []
        try:
            while not self.decision_queue.empty():
                decisions.append(self.decision_queue.get_nowait())
                self.decision_queue.task_done()
        except Exception as e:
            logger.error(f"Error getting pending decisions: {e}")
        
        return decisions
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get the current state of an agent"""
        return self.agents.get(agent_id)
    
    def get_all_agent_states(self) -> Dict[str, AgentState]:
        """Get all agent states"""
        return self.agents.copy()
        
    def apply_decision_to_npc(self, npc, decision):
        """Apply an AI decision to an NPC entity"""
        # Handle fast movement (multiple steps)
        if decision.is_fast_movement and hasattr(npc, 'grid_x') and hasattr(npc, 'grid_y'):
            # Determine how many steps to take (2-3 when critically thirsty/hungry)
            steps = random.randint(2, 3)
            
            # Calculate target position based on action and steps
            if decision.action == "move_left":
                npc.target_grid_x = max(0, npc.grid_x - steps)
                npc.target_grid_y = npc.grid_y
            elif decision.action == "move_right":
                npc.target_grid_x = npc.grid_x + steps
                npc.target_grid_y = npc.grid_y
            elif decision.action == "move_up":
                npc.target_grid_x = npc.grid_x
                npc.target_grid_y = max(0, npc.grid_y - steps)
            elif decision.action == "move_down":
                npc.target_grid_x = npc.grid_x
                npc.target_grid_y = npc.grid_y + steps
            
            # Set the NPC to moving state
            npc.is_moving = True
            
            return True
        
        return False  # Indicate that we didn't handle the decision specially

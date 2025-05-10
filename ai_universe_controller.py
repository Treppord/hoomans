import threading
import queue
import time
import random
import json
import os
import sys
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import requests
import traceback
from dataclasses import dataclass, asdict, field
from llama_cpp import Llama
import re

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

# ================ Data Structures ================

@dataclass
class AgentState:
    """Represents the current state of an agent in the simulation"""
    agent_id: str
    grid_x: int
    grid_y: int
    thirst: int = 5  # 0-5 scale
    hunger: int = 5  # 0-5 scale
    health: int = 5  # 0-5 scale
    mood: float = 0.5  # 0-1 scale
    last_action: str = "idle"
    last_speech: str = ""
    speech_cooldown: int = 0
    action_cooldown: int = 0
    nearby_entities: List[Dict] = field(default_factory=list)
    nearby_tiles: List[Dict] = field(default_factory=list)
    cna_data: Optional[CNAAttributes] = None
    memory: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for AI prompt"""
        result = {
            "agent_id": self.agent_id,
            "position": {"x": self.grid_x, "y": self.grid_y},
            "needs": {
                "thirst": self.thirst,
                "hunger": self.hunger,
                "health": self.health
            },
            "mood": self.mood,
            "last_action": self.last_action,
            "last_speech": self.last_speech,
            "nearby_entities": self.nearby_entities,
            "nearby_tiles": self.nearby_tiles,
            "memory": self.memory[-5:] if self.memory else []  # Last 5 memories
        }
        
        # Add CNA attributes if available
        if self.cna_data:
            result["personality"] = {
                "name": f"{self.cna_data.first_name} {self.cna_data.last_name}",
                "gender": self.cna_data.gender.name,
                "culture": self.cna_data.culture.name,
                "nation": self.cna_data.nation.name,
                "physical_health": self.cna_data.physical_health,
                "mental_health": self.cna_data.mental_health,
                "generational_health": self.cna_data.generational_health,
                "intelligence": self.cna_data.intelligence_factor,
                "adaptability": self.cna_data.adaptability,
                "immunity": self.cna_data.immunity_strength
            }
            
            if hasattr(self.cna_data, "personality_traits") and self.cna_data.personality_traits:
                traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
                for i, trait_name in enumerate(traits):
                    if i < len(self.cna_data.personality_traits):
                        result["personality"][trait_name] = self.cna_data.personality_traits[i]
        
        return result

@dataclass
class AgentDecision:
    """Represents an AI decision for an agent"""
    agent_id: str
    action: str  # move_left, move_right, move_up, move_down, drink, eat, idle, etc.
    speech: str = ""  # What the agent might say
    target_x: Optional[int] = None  # Target x position if moving
    target_y: Optional[int] = None  # Target y position if moving
    mood_change: float = 0.0  # How this decision affects mood (-1 to 1)
    memory_update: Optional[str] = None  # New memory to add
    is_fast_movement: bool = False  # Whether this is a fast movement (multiple steps)
    
    @classmethod
    def from_ai_response(cls, agent_id: str, response_json: Dict) -> 'AgentDecision':
        """Create an AgentDecision from AI response JSON"""
        try:
            action = response_json.get("action", "idle")
            speech = response_json.get("speech", "")
            
            # Extract target position if provided
            target_x = None
            target_y = None
            if "target" in response_json and isinstance(response_json["target"], dict):
                target_x = response_json["target"].get("x")
                target_y = response_json["target"].get("y")
            
            # Extract mood change
            mood_change = float(response_json.get("mood_change", 0.0))
            
            # Extract memory update
            memory_update = response_json.get("memory_update")
            
            # Extract fast movement flag
            is_fast_movement = response_json.get("is_fast_movement", False)
            
            return cls(
                agent_id=agent_id,
                action=action,
                speech=speech,
                target_x=target_x,
                target_y=target_y,
                mood_change=mood_change,
                memory_update=memory_update,
                is_fast_movement=is_fast_movement
            )
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.error(f"Response JSON: {response_json}")
            # Return a default idle decision
            return cls(agent_id=agent_id, action="idle")





# ================ AI Interface ================

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
        
        # Other actions
        "idle": {"description": "Stand still and observe surroundings"},
        "search": {"description": "Look around for resources"}
    }
    
    def __init__(self, use_local_model=True, model_path="models/tinyllama-1.1b-chat-v1.0.Q2_K.gguf"):
        self.use_local_model = use_local_model
        self.api_url = "http://localhost:11434/api/generate"  # Fallback to Ollama
        self.model_name = "tinyllama"  # Fallback model name
        self.local_model_loaded = False
        
        self.system_prompt = """
You are the AI controller for a game called Hoomans. Your job is to determine the actions and speech of NPCs.
Respond with a JSON object containing:
- action: move_left, move_right, move_up, move_down, drink, eat, idle
- speech: What the NPC says (can be empty). IMPORTANT: The speech should be natural dialogue, NOT commands or descriptions of actions.

IMPORTANT RULES:
1. NPCs should speak in first person (e.g., "I'm thirsty" is correct)
2. Speech should reflect the NPC's personality traits and current needs
3. The "drink" action can ONLY be performed when the NPC is adjacent to water
4. ONLY focus on thirst and drinking when thirst is at 0 (critical)
5. When thirst is normal (1-5), focus on personality and exploration instead

Example response:
{"action": "move_left", "speech": "I'm so thirsty!"}
{"action": "drink", "speech": "Ah, refreshing water!"}
{"action": "idle", "speech": "What a beautiful day!"}

Keep your responses concise and focused on the action and speech.
"""
        
        # Initialize local model if enabled
        if use_local_model:
            self.local_model = LocalModelInterface(model_path=model_path)


    def _create_adaptive_system_prompt(self, has_critical_thirst, has_critical_hunger):
        """Create a concise system prompt based on agent's needs"""
        
        # Start with available actions
        action_list = ", ".join(self.ACTIONS.keys())
        base_prompt = f"You control an NPC in a game. Respond with JSON: {{\"action\": \"[action]\", \"speech\": \"[optional speech]\"}}. Available actions: {action_list}."
        
        # Add specific guidance based on critical needs
        if has_critical_thirst and has_critical_hunger:
            base_prompt += " NPC is CRITICALLY THIRSTY AND HUNGRY. Prioritize finding water first. Use fast movement actions. Speech should express URGENT need for water."
        elif has_critical_thirst:
            base_prompt += " NPC is CRITICALLY THIRSTY. Prioritize finding water. Use fast movement actions. Speech should express URGENT need for water."
        elif has_critical_hunger:
            base_prompt += " NPC is CRITICALLY HUNGRY. Prioritize finding food. Use fast movement actions. Speech should express URGENT need for food."
        else:
            base_prompt += " NPC is fine. Focus on exploration and personality. Use regular movement actions. Never mention thirst/hunger/water/food."
        
        return base_prompt

    def _validate_response_for_needs(self, response_json, has_critical_thirst, has_critical_hunger, nearby_tiles, grid_x, grid_y):
        """Validate and correct the AI response based on the agent's needs"""
        
        # Ensure we're working with a dictionary
        if isinstance(response_json, str):
            try:
                response_json = json.loads(response_json)
            except:
                # If parsing fails, create a basic response
                return {"action": "idle", "speech": ""}
        
        action = response_json.get("action", "idle")
        speech = response_json.get("speech", "")
        
        # Handle fast movement actions (convert to regular movement but remember it's fast)
        is_fast_movement = False
        if action.endswith("_fast"):
            is_fast_movement = True
            action = action.replace("_fast", "")
        
        # Validate drink action
        if action == "drink":
            # Check if agent has critical thirst
            if not has_critical_thirst:
                action = "idle"
            else:
                # Check if agent is adjacent to water
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
        
        # Validate eat action (similar to drink)
        if action == "eat":
            # Check if agent has critical hunger
            if not has_critical_hunger:
                action = "idle"
            else:
                # For now, just convert to movement since we don't have food tiles
                action = random.choice(["move_left", "move_right", "move_up", "move_down"])
                is_fast_movement = True
        
        # Handle search action
        if action == "search":
            if has_critical_thirst or has_critical_hunger:
                # If searching with critical needs, convert to movement
                action = random.choice(["move_left", "move_right", "move_up", "move_down"])
                is_fast_movement = True
            else:
                # Regular search just becomes idle with looking around speech
                action = "idle"
                if not speech:
                    speech = random.choice([
                        "I should look around for interesting things.",
                        "Let me see what's nearby.",
                        "I wonder what I can find here."
                    ])
        
        # Encourage more movement when no critical needs
        if action == "idle" and not has_critical_thirst and not has_critical_hunger:
            # 70% chance to convert idle to movement when no critical needs
            if random.random() < 0.7:
                # Choose a random direction, but avoid walls
                possible_directions = []
                
                # Check each direction for walls
                directions = [
                    ("move_left", grid_x - 1, grid_y),
                    ("move_right", grid_x + 1, grid_y),
                    ("move_up", grid_x, grid_y - 1),
                    ("move_down", grid_x, grid_y + 1)
                ]
                
                for dir_action, x, y in directions:
                    # Check if there's a wall in this direction
                    has_wall = False
                    for tile in nearby_tiles:
                        if tile.get("type") == "wall" and tile["x"] == x and tile["y"] == y:
                            has_wall = True
                            break
                    
                    if not has_wall:
                        possible_directions.append(dir_action)
                
                # If we have valid directions, choose one randomly
                if possible_directions:
                    action = random.choice(possible_directions)
        
        # Generate appropriate speech based on needs and actions
        if has_critical_thirst:
            # If critically thirsty, override speech with water-focused dialogue
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
            "is_fast_movement": is_fast_movement
        }

    def generate_decision(self, agent_state: AgentState) -> AgentDecision:
        """Generate a decision for an agent based on its current state"""
        try:
            # Determine if agent has critical needs
            has_critical_thirst = agent_state.thirst < 1
            has_critical_hunger = agent_state.hunger < 1
            
            # Create a minimal state representation
            prompt = f"Position: ({agent_state.grid_x}, {agent_state.grid_y})\n"
            
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
            
            # Create a concise system prompt
            system_prompt = self._create_adaptive_system_prompt(has_critical_thirst, has_critical_hunger)
            
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
                    agent_state.grid_y
                )
                
                return AgentDecision.from_ai_response(agent_state.agent_id, validated_response)
                
        except Exception as e:
            logger.error(f"Error generating decision: {e}")
            logger.error(traceback.format_exc())
            return AgentDecision(agent_id=agent_state.agent_id, action="idle")
        
    def generate_batch_decisions(self, agent_states: List[AgentState]) -> List[AgentDecision]:
        """Generate decisions for multiple agents (one by one)"""
        decisions = []
        for state in agent_states:
            decision = self.generate_decision(state)
            decisions.append(decision)
        return decisions


# ================ Fallback AI ================

class FallbackAI:
    """Simple rule-based AI that can be used when the LLM is not available"""
    
    @staticmethod
    def generate_decision(agent_state: AgentState) -> AgentDecision:
        """Generate a decision based on simple rules"""
        action = "idle"
        speech = ""
        target_x = None
        target_y = None
        mood_change = 0.0
        memory_update = None
        
        # Check for critical thirst (only when thirst is 0)
        if agent_state.thirst == 0:
            # Look for water in nearby tiles
            water_tiles = [tile for tile in agent_state.nearby_tiles if tile.get("type") == "water"]
            if water_tiles:
                # Check if already adjacent to water
                is_adjacent_to_water = False
                for tile in water_tiles:
                    if abs(tile["x"] - agent_state.grid_x) <= 1 and abs(tile["y"] - agent_state.grid_y) <= 1:
                        is_adjacent_to_water = True
                        break
                
                if is_adjacent_to_water:
                    # If adjacent to water, drink
                    action = "drink"
                    speech = "I need water desperately..."
                    mood_change = 0.3
                    memory_update = "I found water when I was extremely thirsty."
                else:
                    # Move towards the nearest water
                    nearest_water = min(water_tiles, key=lambda t: abs(t["x"] - agent_state.grid_x) + abs(t["y"] - agent_state.grid_y))
                    dx = nearest_water["x"] - agent_state.grid_x
                    dy = nearest_water["y"] - agent_state.grid_y
                    
                    if abs(dx) > abs(dy):
                        action = "move_right" if dx > 0 else "move_left"
                    else:
                        action = "move_down" if dy > 0 else "move_up"
                    
                    target_x = nearest_water["x"]
                    target_y = nearest_water["y"]
                    speech = "I'm dying of thirst... Need water..."
                    mood_change = -0.2
            else:
                # Wander randomly looking for water
                action = random.choice(["move_left", "move_right", "move_up", "move_down"])
                speech = "So thirsty... must find water..."
                mood_change = -0.3
        # Random movement if no critical needs
        elif random.random() < 0.3:  # 30% chance to move
            action = random.choice(["move_left", "move_right", "move_up", "move_down"])
            
            # Avoid walls
            wall_tiles = [tile for tile in agent_state.nearby_tiles if tile.get("type") == "wall"]
            for wall in wall_tiles:
                if action == "move_left" and wall["x"] == agent_state.grid_x - 1 and wall["y"] == agent_state.grid_y:
                    action = random.choice(["move_right", "move_up", "move_down"])
                elif action == "move_right" and wall["x"] == agent_state.grid_x + 1 and wall["y"] == agent_state.grid_y:
                    action = random.choice(["move_left", "move_up", "move_down"])
                elif action == "move_up" and wall["x"] == agent_state.grid_x and wall["y"] == agent_state.grid_y - 1:
                    action = random.choice(["move_left", "move_right", "move_down"])
                elif action == "move_down" and wall["x"] == agent_state.grid_x and wall["y"] == agent_state.grid_y + 1:
                    action = random.choice(["move_left", "move_right", "move_up"])
        
        # Random speech
        if random.random() < 0.1 and not speech:  # 10% chance to say something if not already speaking
            if agent_state.cna_data:
                name = agent_state.cna_data.first_name
                culture = agent_state.cna_data.culture.name
                nation = agent_state.cna_data.nation.name
                
                # Add some thirst-related speech if thirst is low but not critical
                if agent_state.thirst <= 2:
                    speech_options = [
                        "I'm getting thirsty.",
                        "I could use some water soon.",
                        "My throat feels a bit dry.",
                        "I should find some water before I get too thirsty."
                    ]
                else:
                    speech_options = [
                        f"I'm from {nation}.",
                        "Nice weather today.",
                        "I wonder what's over there.",
                        f"The {culture} culture has such interesting traditions.",
                        "I should explore more of this area.",
                        "I hope I find something interesting soon."
                    ]
                speech = random.choice(speech_options)
        
        return AgentDecision(
            agent_id=agent_state.agent_id,
            action=action,
            speech=speech,
            target_x=target_x,
            target_y=target_y,
            mood_change=mood_change,
            memory_update=memory_update
        )

    
    @staticmethod
    def generate_batch_decisions(agent_states: List[AgentState]) -> List[AgentDecision]:
        """Generate decisions for multiple agents"""
        return [FallbackAI.generate_decision(state) for state in agent_states]

# ================ Universe Controller ================

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
    
    def _generate_chat_response(self, agent_id, player_message):
        """Generate a response to a player chat message"""
        try:
            # Get the agent state
            agent = self.agents.get(agent_id)
            if not agent:
                logger.error(f"DEBUG: Agent {agent_id} not found for chat response")
                return
            
            logger.info(f"DEBUG: Generating chat response for agent {agent_id} to message: '{player_message}'")
            
            # Create a simpler, more direct prompt for the small model
            prompt = f"Player: {player_message}\n\nRespond as an NPC in a game. Keep it short and natural."
            
            if agent.cna_data:
                prompt = f"You are {agent.cna_data.first_name}, a character in a game.\n\nPlayer: {player_message}\n\nRespond in a short, natural way."
            
            # Simplified system prompt
            system_prompt = "You are an NPC in a game. Respond to the player's message with a short, natural reply."
            
            # Generate response
            response_text = None
            if self.use_llm and hasattr(self, 'ai_interface'):
                try:
                    if hasattr(self.ai_interface, 'local_model'):
                        logger.info(f"DEBUG: Using local model for chat response")
                        
                        # Try direct text generation instead of JSON format for small models
                        # This bypasses the JSON parsing which might be challenging for TinyLlama
                        try:
                            # Direct text generation approach
                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ]
                            
                            output = self.ai_interface.local_model.llm.create_chat_completion(
                                messages=messages,
                                max_tokens=128,  # Increase token limit
                                temperature=0.8,  # Slightly higher temperature for more varied responses
                                top_p=0.95,
                                stop=["</s>", "Player:", "player:", "User:", "user:"]
                            )
                            
                            # Extract the raw text response
                            response_text = output["choices"][0]["message"]["content"].strip()
                            logger.info(f"DEBUG: Raw model text response: '{response_text}'")
                            
                            # Clean up the response
                            # Remove any JSON-like formatting that might have been generated
                            response_text = response_text.replace('{"speech": "', '').replace('"}', '')
                            response_text = response_text.replace('"', '')
                            
                            # If response is too long, truncate it
                            if len(response_text) > 100:
                                response_text = response_text[:97] + "..."
                                
                        except Exception as e:
                            logger.error(f"Error with direct text generation: {e}")
                            response_text = None
                            
                except Exception as e:
                    logger.error(f"Error generating chat response: {e}")
                    logger.error(traceback.format_exc())
            
            # If direct text generation failed or is empty, use fallback responses
            if not response_text:
                logger.info(f"DEBUG: Using fallback responses for chat")
                # Simple fallback responses
                fallback_responses = [
                    f"Hello there!",
                    f"Nice to meet you.",
                    f"What an interesting thing to say.",
                    f"I'm not sure I understand.",
                    f"That's fascinating.",
                    f"I was just thinking about that.",
                    f"I see what you mean.",
                    f"Is that so?",
                    f"Tell me more about that."
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
                action="idle",  # Just stand still while talking
                speech=response_text,
                mood_change=0.1  # Slight mood boost from social interaction
            )
            
            logger.info(f"DEBUG: Queuing chat response decision for agent {agent_id}")
            
            # Put the decision in the queue for the game engine
            self.decision_queue.put(decision)
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            logger.error(traceback.format_exc())



    
    def _process_agents(self):
        """Process agents that need decisions"""
        current_time = time.time()
        agents_to_process = []
        
        # Identify agents that need processing
        for agent_id, agent in self.agents.items():
            last_time = self.last_processed.get(agent_id, 0)
            if current_time - last_time >= self.processing_interval:
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
                    
                    # Update memory
                    if decision.memory_update:
                        agent.memory.append({
                            "timestamp": time.time(),
                            "content": decision.memory_update
                        })
                        # Keep memory limited to last 20 items
                        if len(agent.memory) > 20:
                            agent.memory = agent.memory[-20:]
                
                # Put decision in queue for game engine
                self.decision_queue.put(decision)
        
        except Exception as e:
            logger.error(f"Error processing agents: {e}")
            logger.error(traceback.format_exc())
    
    def update_agent_state(self, agent_id: str, **kwargs):
        """Update an agent's state from the game engine"""
        update = {"agent_id": agent_id, **kwargs}
        self.state_update_queue.put(update)
    
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


# ================ Integration Helpers ================

class WorldStateCollector:
    """Helper class to collect world state information for the AI controller"""
    
    @staticmethod
    def collect_nearby_tiles(world_map, grid_x: int, grid_y: int, radius: int = 5) -> List[Dict]:
        """Collect information about nearby tiles"""
        nearby_tiles = []
        
        for y in range(grid_y - radius, grid_y + radius + 1):
            for x in range(grid_x - radius, grid_x + radius + 1):
                tile = world_map.get_tile(x, y)
                if tile:
                    nearby_tiles.append({
                        "x": x,
                        "y": y,
                        "type": tile.type,
                        "walkable": tile.is_walkable(),
                        "is_water": tile.is_water()
                    })
        
        return nearby_tiles
    
    @staticmethod
    def collect_nearby_entities(entities, grid_x: int, grid_y: int, radius: int = 5) -> List[Dict]:
        """Collect information about nearby entities"""
        nearby_entities = []
        
        for entity in entities:
            if hasattr(entity, 'grid_x') and hasattr(entity, 'grid_y'):
                dx = abs(entity.grid_x - grid_x)
                dy = abs(entity.grid_y - grid_y)
                
                if dx <= radius and dy <= radius:
                    entity_info = {
                        "x": entity.grid_x,
                        "y": entity.grid_y,
                        "type": entity.__class__.__name__
                    }
                    
                    # Add name if entity has CNA data
                    if hasattr(entity, 'cna_data') and entity.cna_data:
                        entity_info["name"] = f"{entity.cna_data.first_name} {entity.cna_data.last_name}"
                    
                    # Add controllable flag if present
                    if hasattr(entity, 'controllable'):
                        entity_info["is_player"] = entity.controllable
                    
                    nearby_entities.append(entity_info)
        
        return nearby_entities
    
class LocalModelInterface:
    """Interface for local LLM inference using llama-cpp-python"""
    
    def __init__(self, model_path="models/tinyllama-1.1b-chat-v1.0.Q2_K.gguf"):
        try:
            from llama_cpp import Llama
            
            # Load the model
            self.llm = Llama(
                model_path=model_path,
                n_ctx=512,  # Smaller context window to save memory
                n_batch=8,  # Smaller batch size
                n_threads=4,  # Adjust based on your CPU
                verbose=False
            )
            
            logger.info(f"Successfully loaded local model from {model_path}")
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            logger.error(traceback.format_exc())
            self.model_loaded = False
    
    def generate_response(self, prompt, system_prompt="", max_tokens=64):
        """Generate a response using the local model"""
        if not self.model_loaded:
            return {"action": "idle", "speech": ""}
        
        try:
            # Format the prompt for chat completion
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Generate completion
            output = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                stop=["</s>", "user:", "User:", "system:", "System:"],
            )
            
            # Extract the response text
            response_text = output["choices"][0]["message"]["content"].strip()
            
            # Try to parse as JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract action and speech
                action_match = re.search(r'"action"\s*:\s*"([^"]+)"', response_text)
                speech_match = re.search(r'"speech"\s*:\s*"([^"]*)"', response_text)
                
                action = action_match.group(1) if action_match else "idle"
                speech = speech_match.group(1) if speech_match else ""
                
                return {"action": action, "speech": speech}
                
        except Exception as e:
            logger.error(f"Error generating response with local model: {e}")
            logger.error(traceback.format_exc())
            return {"action": "idle", "speech": ""}





# ================ Example Usage ================

def example_usage():
    """Example of how to use the AI Universe Controller"""
    # Create the controller
    controller = AIUniverseController(use_llm=True, model_name="llama3")
    
    # Start the controller
    controller.start()
    
    try:
        # Example: Update an agent's state
        controller.update_agent_state(
            agent_id="agent1",
            grid_x=10,
            grid_y=15,
            thirst=3,
            hunger=4,
            nearby_tiles=[
                {"x": 10, "y": 14, "type": "grass", "walkable": True, "is_water": False},
                {"x": 11, "y": 15, "type": "water", "walkable": False, "is_water": True}
            ],
            nearby_entities=[
                {"x": 12, "y": 15, "type": "NPC", "name": "Alex Brown", "is_player": False}
            ],
            cna_file="cna/data/Dakota_Brown.cna"
        )
        
        # Wait for processing
        time.sleep(1.0)
        
        # Get pending decisions
        decisions = controller.get_pending_decisions()
        for decision in decisions:
            print(f"Agent {decision.agent_id}: Action={decision.action}, Speech={decision.speech}")
        
        # Run for a while
        time.sleep(5.0)
    
    finally:
        # Stop the controller
        controller.stop()

if __name__ == "__main__":
    example_usage()
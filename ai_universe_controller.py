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
    
    @classmethod
    def from_ai_response(cls, agent_id: str, response_json: Dict) -> 'AgentDecision':
        """Create an AgentDecision from AI response JSON"""
        try:
            # Make sure we're working with a dictionary
            if isinstance(response_json, str):
                try:
                    # Try to parse as JSON
                    response_json = json.loads(response_json)
                except:
                    # If parsing fails, try to extract action and speech
                    action = "idle"
                    speech = ""
                    
                    # Check for action keywords
                    action_keywords = {
                        "move left": "move_left",
                        "move right": "move_right", 
                        "move up": "move_up",
                        "move down": "move_down",
                        "drink": "drink",
                        "eat": "eat"
                    }
                    
                    text_lower = response_json.lower()
                    for keyword, act in action_keywords.items():
                        if keyword in text_lower:
                            action = act
                            break
                    
                    # Try to extract speech - look for quotes or speech indicators
                    speech_match = re.search(r'["\'](.*?)["\']', response_json)
                    if speech_match:
                        speech = speech_match.group(1)
                    elif "says" in text_lower:
                        speech_parts = text_lower.split("says")
                        if len(speech_parts) > 1:
                            speech = speech_parts[1].strip().strip('"\'')
                    
                    response_json = {"action": action, "speech": speech}
            
            # Extract action, defaulting to idle
            action = response_json.get("action", "idle")
            
            # Clean up action string if needed
            action = action.strip().lower()
            if "move_" not in action and "move " in action:
                # Convert "move left" to "move_left" etc.
                action = action.replace("move ", "move_")
            
            # Extract speech
            speech = response_json.get("speech", "")
            
            # Clean up speech - remove JSON formatting if present
            if isinstance(speech, str):
                # Remove quotes at beginning and end if present
                speech = speech.strip('"\'')
                
                # If speech looks like JSON, try to extract the actual speech
                if speech.startswith("{") and "speech" in speech:
                    try:
                        speech_json = json.loads(speech)
                        if isinstance(speech_json, dict) and "speech" in speech_json:
                            speech = speech_json["speech"]
                    except:
                        pass
                
                # Filter out speech that contains the word "action" or is just "action"
                if speech.lower() == "action" or speech.lower() == "\"action\"":
                    speech = ""
                
                # Filter out speech that looks like a command or JSON
                if (speech.startswith("{") or 
                    speech.startswith("[") or 
                    "action:" in speech.lower() or 
                    "speech:" in speech.lower() or
                    "move_" in speech.lower() or
                    "action" in speech.lower()):
                    speech = ""
            
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
            
            return cls(
                agent_id=agent_id,
                action=action,
                speech=speech,
                target_x=target_x,
                target_y=target_y,
                mood_change=mood_change,
                memory_update=memory_update
            )
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.error(f"Response JSON: {response_json}")
            # Return a default idle decision
            return cls(agent_id=agent_id, action="idle")




# ================ AI Interface ================

class AIInterface:
    """Interface for communicating with the AI model"""
    
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

Example response:
{"action": "move_left", "speech": "I'm so thirsty!"}
{"action": "drink", "speech": "Ah, refreshing water!"}
{"action": "idle", "speech": "What a beautiful day!"}

BAD examples (don't do these):
{"action": "move_left", "speech": "action"}
{"action": "drink", "speech": "I will drink now"}

Keep your responses concise and focused on the action and speech.
"""


        
        # Initialize local model if enabled
        if use_local_model:
            self.local_model = LocalModelInterface(model_path=model_path)


    # Add the _extract_json_from_text function here
    def _extract_json_from_text(self, text):
        """Extract JSON from potentially malformed text response"""
        try:
            # First try direct parsing
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON-like structure
            try:
                # Look for opening and closing braces
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = text[start:end]
                    return json.loads(json_str)
            except:
                pass
                
            # If all else fails, create a basic response
            return {
                "action": "idle",
                "speech": text[:50] if text else "",
                "mood_change": 0.0
            }

    def generate_decision(self, agent_state: AgentState) -> AgentDecision:
        """Generate a decision for an agent based on its current state"""
        try:
            # Convert agent state to a simplified dictionary for the prompt
            simplified_state = {
                "position": {"x": agent_state.grid_x, "y": agent_state.grid_y},
                "thirst": agent_state.thirst,
                "hunger": agent_state.hunger,
                "last_action": agent_state.last_action
            }
            
            # Add personality if available
            if agent_state.cna_data:
                simplified_state["name"] = f"{agent_state.cna_data.first_name} {agent_state.cna_data.last_name}"
                simplified_state["gender"] = agent_state.cna_data.gender.name
            
            # Add nearby water tiles only (to keep prompt small)
            water_tiles = [tile for tile in agent_state.nearby_tiles if tile.get("type") == "water"]
            if water_tiles:
                simplified_state["water_tiles"] = [{"x": t["x"], "y": t["y"]} for t in water_tiles[:3]]  # Limit to 3
            
            # Create a simple prompt
            prompt = f"Agent state: {json.dumps(simplified_state)}\nChoose an action and optional speech for this agent."
            
            # Use local model if enabled
            if self.use_local_model and hasattr(self, 'local_model'):
                response_json = self.local_model.generate_response(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=64  # Keep responses short
                )
                return AgentDecision.from_ai_response(agent_state.agent_id, response_json)
                
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
        
        # Check for basic needs
        if agent_state.thirst <= 1:
            # Look for water in nearby tiles
            water_tiles = [tile for tile in agent_state.nearby_tiles if tile.get("type") == "water"]
            if water_tiles:
                # If already adjacent to water, drink
                for tile in water_tiles:
                    if abs(tile["x"] - agent_state.grid_x) <= 1 and abs(tile["y"] - agent_state.grid_y) <= 1:
                        action = "drink"
                        speech = "I need water..."
                        mood_change = 0.2
                        memory_update = "I found water when I was thirsty."
                        break
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
                    speech = "Need to find water..."
                    mood_change = -0.1
            else:
                # Wander randomly looking for water
                action = random.choice(["move_left", "move_right", "move_up", "move_down"])
                speech = "So thirsty..."
                mood_change = -0.2
        
        # Random movement if no specific need
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
                
                speech_options = [
                    f"I'm from {nation}.",
                    f"My name is {name}.",
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
    
    def __init__(self, use_llm=True, use_local_model=True, model_path="models/tinyllama-1.1b-chat-v1.0.Q2_K.gguf"):
        self.agents: Dict[str, AgentState] = {}
        self.running = False
        self.thread = None
        self.use_llm = use_llm
        self.use_local_model = use_local_model
        self.model_path = model_path
        
        # Queues for communication with the game engine
        self.state_update_queue = queue.Queue()
        self.decision_queue = queue.Queue()
        
        # Initialize AI interface
        if self.use_llm:
            try:
                self.ai_interface = AIInterface(use_local_model=use_local_model, model_path=model_path)
                logger.info(f"Initialized AI interface with {'local model' if use_local_model else 'Ollama API'}")
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
                        logger.info(f"Agent {decision.agent_id} speech: '{decision.speech}'")
                    
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
    """Interface for using a local LLM model directly from the project folder"""
    
    def __init__(self, model_path="models/tinyllama-1.1b-chat-v1.0.Q2_K.gguf", n_ctx=512, n_threads=4):
        """Initialize the local model interface"""
        self.model_path = model_path
        
        # Load the model
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,          # Context window size
                n_threads=n_threads,  # Number of CPU threads to use
                n_batch=8,            # Batch size for prompt processing
                verbose=False         # Disable verbose output
            )
            logger.info(f"Successfully loaded local model from {model_path}")
            self.model_loaded = True
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            logger.error(traceback.format_exc())
            self.model_loaded = False
    
    def generate_response(self, prompt, system_prompt, max_tokens=128):
        """Generate a response from the local model"""
        if not self.model_loaded:
            return {"action": "idle", "speech": ""}
        
        try:
            # Format the prompt for the model
            full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>"
            
            # Generate response
            response = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                stop=["<|user|>", "<|system|>"],
                temperature=0.7,
                echo=False
            )
            
            # Extract the generated text
            generated_text = response["choices"][0]["text"].strip()
            
            # Try to parse as JSON
            try:
                import json
                import re
                
                # Look for JSON-like structure
                json_match = re.search(r'(\{.*\})', generated_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    parsed_json = json.loads(json_str)
                    
                    # Make sure we have action and speech fields
                    if "action" not in parsed_json:
                        parsed_json["action"] = self._extract_action(generated_text)
                    
                    # Filter speech
                    if "speech" in parsed_json:
                        speech = parsed_json["speech"]
                        # Filter out speech that contains the word "action" or is just "action"
                        if speech.lower() == "action" or speech.lower() == "\"action\"":
                            parsed_json["speech"] = ""
                        # Filter out speech that looks like a command or JSON
                        elif (speech.startswith("{") or 
                              speech.startswith("[") or 
                              "action:" in speech.lower() or 
                              "speech:" in speech.lower() or
                              "move_" in speech.lower() or
                              "action" in speech.lower()):
                            parsed_json["speech"] = ""
                    else:
                        parsed_json["speech"] = ""
                        
                    return parsed_json
                else:
                    # If no JSON found, extract action and speech
                    action = self._extract_action(generated_text)
                    
                    # Try to extract speech - look for quotes or speech indicators
                    speech = ""
                    speech_match = re.search(r'["\'](.*?)["\']', generated_text)
                    if speech_match:
                        speech = speech_match.group(1)
                    elif "says" in generated_text.lower():
                        speech_parts = generated_text.lower().split("says")
                        if len(speech_parts) > 1:
                            speech = speech_parts[1].strip().strip('"\'')
                    
                    # Filter speech
                    if speech.lower() == "action" or speech.lower() == "\"action\"":
                        speech = ""
                    elif (speech.startswith("{") or 
                          speech.startswith("[") or 
                          "action:" in speech.lower() or 
                          "speech:" in speech.lower() or
                          "move_" in speech.lower() or
                          "action" in speech.lower()):
                        speech = ""
                    
                    return {
                        "action": action,
                        "speech": speech if speech else ""
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, extract action and speech
                action = self._extract_action(generated_text)
                
                # Try to extract speech - look for quotes or speech indicators
                speech = ""
                speech_match = re.search(r'["\'](.*?)["\']', generated_text)
                if speech_match:
                    speech = speech_match.group(1)
                elif "says" in generated_text.lower():
                    speech_parts = generated_text.lower().split("says")
                    if len(speech_parts) > 1:
                        speech = speech_parts[1].strip().strip('"\'')
                
                # Filter speech
                if speech.lower() == "action" or speech.lower() == "\"action\"":
                    speech = ""
                elif (speech.startswith("{") or 
                      speech.startswith("[") or 
                      "action:" in speech.lower() or 
                      "speech:" in speech.lower() or
                      "move_" in speech.lower() or
                      "action" in speech.lower()):
                    speech = ""
                
                return {
                    "action": action,
                    "speech": speech if speech else ""
                }
                
        except Exception as e:
            logger.error(f"Error generating response from local model: {e}")
            return {"action": "idle", "speech": ""}



    def _extract_action(self, text):
        """Extract an action from text if possible"""
        action_keywords = {
            "move left": "move_left",
            "move right": "move_right", 
            "move up": "move_up",
            "move down": "move_down",
            "drink": "drink",
            "eat": "eat",
            "idle": "idle"
        }
        
        text_lower = text.lower()
        for keyword, action in action_keywords.items():
            if keyword in text_lower:
                return action
        
        return "idle"  # Default action


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

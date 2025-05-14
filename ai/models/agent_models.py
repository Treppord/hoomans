from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import time

@dataclass
class AgentState:
    """Represents the current state of an agent in the simulation"""
    agent_id: str
    grid_x: int
    grid_y: int
    thirst: int = 10  # 0-10 scale
    hunger: int = 10  # 0-10 scale
    health: int = 5  # 0-5 scale
    mood: float = 0.5  # 0-1 scale
    last_action: str = "idle"
    last_speech: str = ""
    speech_cooldown: int = 0
    action_cooldown: int = 0
    nearby_entities: List[Dict] = field(default_factory=list)
    nearby_tiles: List[Dict] = field(default_factory=list)
    cna_data: Optional[Any] = None
    memory: List[Dict] = field(default_factory=list)
    player_advice: Optional[Dict] = None
    player_advice_time: float = 0
    advice_followed: bool = False
    
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
        
        # Add player advice if available and recent
        if self.player_advice and (time.time() - self.player_advice_time < 300):  # Advice valid for 5 minutes
            result["player_advice"] = self.player_advice
            result["advice_followed"] = self.advice_followed
        
        return result

@dataclass
class AgentDecision:
    """Represents an AI decision for an agent"""
    agent_id: str
    action: str  # move_left, move_right, move_up, move_down, drink, eat, idle, etc.
    speech: str = ""  # What the agent might say
    reason: str = ""  # Reason for the decision (for memory)
    target_x: Optional[int] = None  # Target x position if moving
    target_y: Optional[int] = None  # Target y position if moving
    mood_change: float = 0.0  # How this decision affects mood (-1 to 1)
    memory_update: Optional[str] = None  # New memory to add
    is_fast_movement: bool = False  # Whether this is a fast movement (multiple steps)
    following_advice: bool = False  # Whether this decision is following player advice
    advice_direction: Optional[str] = None  # Direction from player advice
    advice_distance: int = 0  # Distance from player advice
    advice_remaining_distance: int = 0  # Remaining distance to travel
    is_heading_to_known_water: bool = False  # Whether heading to a known water source
    is_escaping_water: bool = False  # Whether escaping from standing on water
    
    @classmethod
    def from_ai_response(cls, agent_id: str, response_json: Dict) -> 'AgentDecision':
        """Create an AgentDecision from AI response JSON"""
        try:
            action = response_json.get("action", "idle")
            speech = response_json.get("speech", "")
            reason = response_json.get("reason", "")
            
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
            
            # Extract advice following flags
            following_advice = response_json.get("following_advice", False)
            advice_direction = response_json.get("advice_direction")
            advice_distance = response_json.get("advice_distance", 0)
            
            return cls(
                agent_id=agent_id,
                action=action,
                speech=speech,
                reason=reason,
                target_x=target_x,
                target_y=target_y,
                mood_change=mood_change,
                memory_update=memory_update,
                is_fast_movement=is_fast_movement,
                following_advice=following_advice,
                advice_direction=advice_direction,
                advice_distance=advice_distance
            )
        except Exception as e:
            import logging
            logger = logging.getLogger("AgentDecision")
            logger.error(f"Error parsing AI response: {e}")
            logger.error(f"Response JSON: {response_json}")
            # Return a default idle decision
            return cls(agent_id=agent_id, action="idle")

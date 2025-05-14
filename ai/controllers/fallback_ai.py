import random
import re
from typing import List

from ai.models.agent_models import AgentState, AgentDecision

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
        
        # Check for critical thirst (when thirst is 0 or 1)
        if agent_state.thirst <= 1:
            # First check if the agent knows about any water sources
            known_water_location = None
            
            # Check agent's memory for water locations
            if hasattr(agent_state, 'memory'):
                for memory in agent_state.memory:
                    if isinstance(memory, dict) and 'content' in memory:
                        content = memory['content']
                        # Look for water location memories
                        if 'water' in content.lower() and 'coordinates' in content.lower():
                            # Try to extract coordinates
                            coords_match = re.search(r'coordinates\s*\((\d+),\s*(\d+)\)', content)
                            if coords_match:
                                try:
                                    water_x = int(coords_match.group(1))
                                    water_y = int(coords_match.group(2))
                                    known_water_location = (water_x, water_y)
                                    break
                                except ValueError:
                                    pass
            
            # If no water in memory, check if we have access to world cache
            if not known_water_location and hasattr(agent_state, 'agent_id'):
                # Try to access world cache through AIUniverseController
                from ai_universe_controller import AIUniverseController
                controller = None
                
                # Try to get controller instance
                for obj in globals().values():
                    if isinstance(obj, AIUniverseController) and hasattr(obj, 'world_cache'):
                        controller = obj
                        break
                
                if controller and controller.world_cache:
                    # Get agent memories from cache
                    agent_memories = controller.world_cache.get_entity_memories(agent_state.agent_id)
                    
                    # Look for water discoveries in memories
                    for memory in agent_memories:
                        if memory.get('type') == 'location_discovery' and memory.get('data', {}).get('location_type') == 'water':
                            water_data = memory.get('data', {})
                            if 'x' in water_data and 'y' in water_data:
                                known_water_location = (water_data.get('x'), water_data.get('y'))
                                break
            
            # If we know a water location, move towards it
            if known_water_location:
                water_x, water_y = known_water_location
                dx = water_x - agent_state.grid_x
                dy = water_y - agent_state.grid_y
                
                # Determine which direction to move
                if abs(dx) > abs(dy):
                    action = "move_right" if dx > 0 else "move_left"
                else:
                    action = "move_down" if dy > 0 else "move_up"
                
                # Set target coordinates
                target_x = water_x
                target_y = water_y
                
                # No speech about thirst when we know where water is
                speech = ""
                mood_change = 0.1  # Slight mood boost for knowing where to find water
                memory_update = f"I'm heading to the water source I remember at coordinates ({water_x}, {water_y})."
                
                return AgentDecision(
                    agent_id=agent_state.agent_id,
                    action=action,
                    speech=speech,
                    target_x=target_x,
                    target_y=target_y,
                    mood_change=mood_change,
                    memory_update=memory_update,
                    is_heading_to_known_water=True  # Add a flag to indicate we're heading to known water
                )

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

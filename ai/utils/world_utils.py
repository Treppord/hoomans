from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger("AIUniverseController")

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

def parse_player_advice(message: str) -> Optional[Dict]:
    """
    Parse player messages for actionable advice
    Returns a dictionary with parsed advice or None if no advice detected
    """
    advice = None
    message = message.lower()
    
    # Pattern for directional advice (e.g., "water 5 blocks to the left")
    direction_patterns = [
        r"(?:there is|there's|is|are)\s+(\w+)\s+(\d+)\s+(?:blocks?|tiles?)\s+(?:to\s+)?(?:the\s+)?(\w+)",
        r"(?:move|go|head)\s+(\d+)\s+(?:blocks?|tiles?)\s+(?:to\s+)?(?:the\s+)?(\w+)",
        r"(?:move|go|head)\s+(?:to\s+)?(?:the\s+)?(\w+)\s+(\d+)\s+(?:blocks?|tiles?)",
        r"if you are (?:thirsty|hungry) (?:move|go|head)\s+(\d+)\s+(?:blocks?|tiles?)\s+(?:to\s+)?(?:the\s+)?(\w+)"
    ]
    
    # Try each pattern
    for pattern in direction_patterns:
        match = re.search(pattern, message)
        if match:
            groups = match.groups()
            
            # Handle different pattern formats
            if len(groups) == 3:  # "there is water 5 tiles to the right"
                what, distance, direction = groups
                try:
                    distance = int(distance)
                    advice = {
                        "type": "direction",
                        "what": what,
                        "distance": distance,
                        "direction": direction,
                        "confidence": 0.9  # High confidence for explicit directions
                    }
                    logger.info(f"DEBUG: Parsed player advice: {advice}")
                    return advice
                except ValueError:
                    pass
            elif len(groups) == 2:
                # Check if first group is a number ("move 5 tiles right")
                try:
                    distance = int(groups[0])
                    direction = groups[1]
                    advice = {
                        "type": "direction",
                        "what": "resource",  # Generic resource
                        "distance": distance,
                        "direction": direction,
                        "confidence": 0.8
                    }
                    logger.info(f"DEBUG: Parsed player advice: {advice}")
                    return advice
                except ValueError:
                    # First group might be direction ("move right 5 tiles")
                    try:
                        direction = groups[0]
                        distance = int(groups[1])
                        advice = {
                            "type": "direction",
                            "what": "resource",
                            "distance": distance,
                            "direction": direction,
                            "confidence": 0.8
                        }
                        logger.info(f"DEBUG: Parsed player advice: {advice}")
                        return advice
                    except ValueError:
                        pass
    
    # Check for water-specific advice
    if "water" in message and any(word in message for word in ["thirsty", "drink", "find"]):
        # Look for direction words
        directions = {
            "right": ["right", "east"],
            "left": ["left", "west"],
            "up": ["up", "north", "above"],
            "down": ["down", "south", "below"]
        }
        
        for direction_key, direction_words in directions.items():
            if any(word in message for word in direction_words):
                # Try to find a number for distance
                distance_match = re.search(r"(\d+)", message)
                distance = int(distance_match.group(1)) if distance_match else 5  # Default to 5 if no number
                
                advice = {
                    "type": "direction",
                    "what": "water",
                    "distance": distance,
                    "direction": direction_key,
                    "confidence": 0.7  # Medium confidence for less explicit directions
                }
                logger.info(f"DEBUG: Parsed water-specific advice: {advice}")
                return advice
    
    # Pattern for location advice (e.g., "there's water near the mountain")
    location_pattern = r"(?:there is|there's|is|are)\s+(\w+)\s+(?:near|by|at|close to)\s+(?:the\s+)?(\w+)"
    location_match = re.search(location_pattern, message)
    
    if location_match:
        what, landmark = location_match.groups()
        advice = {
            "type": "location",
            "what": what,
            "landmark": landmark,
            "confidence": 0.7  # Medium confidence for less precise directions
        }
        logger.info(f"DEBUG: Parsed location advice: {advice}")
        return advice
        
    return None

def is_memory_query(message: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a message is asking about remembered locations or past events
    Returns (is_memory_query, query_type)
    """
    message = message.lower()
    
    # Check for water-specific queries first
    if ("water" in message or "drink" in message) and any(word in message for word in ["where", "location", "know", "remember", "nearby"]):
        logger.info(f"DEBUG: Detected water-specific memory query")
        return True, "water"
    
    # Check for location memory queries
    location_patterns = [
        r"(?:where|location of|where is|where can i find|where to find|find)\s+(?:a|the)?\s*(\w+)",
        r"(?:do you know|remember|recall).+?(?:where|location).+?(\w+)",
        r"(?:do you know|remember|recall).+?(\w+).+?(?:location|where)"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message)
        if match:
            resource_type = match.group(1)
            # Clean up resource type (remove trailing "s" if plural)
            if resource_type.endswith('s'):
                resource_type = resource_type[:-1]
            
            # Skip common words that aren't resources
            if resource_type.lower() in ["of", "any", "some", "the", "a", "an", "is", "are", "do", "you", "know"]:
                continue
            
            # Map common terms to resource types
            resource_mapping = {
                "water": "water",
                "drink": "water",
                "river": "water",
                "lake": "water",
                "pond": "water",
                "food": "food",
                "eat": "food",
                "fruit": "food",
                "shelter": "shelter",
                "house": "shelter",
                "building": "shelter"
            }
            
            # Get standardized resource type
            resource_type = resource_mapping.get(resource_type, resource_type)
            
            logger.info(f"DEBUG: Detected memory query for resource: {resource_type}")
            return True, resource_type
    
    # Special case for "water sources" or similar phrases
    if "water" in message and any(word in message for word in ["source", "sources", "location", "locations", "nearby"]):
        logger.info(f"DEBUG: Detected special case water source query")
        return True, "water"
    
    # Check for general memory queries
    if any(phrase in message for phrase in [
        "what do you remember", 
        "what have you seen", 
        "tell me about your memory", 
        "what do you know about",
        "according to your memory",
        "do you know of any"
    ]):
        return True, "general"
        
    return False, None

def detect_attribute_query(message):
    """Detect if the message is asking about a specific attribute"""
    message = message.lower()
    
    # Mental health queries
    if any(term in message for term in ["mental health", "mentally", "feeling mentally", "mind", "psychological", "psychologically", "psychology"]):
        return "mental_health"
    
    # Physical health queries
    if any(term in message for term in ["physical health", "physically", "feeling physically", "body", "health", "strength"]):
        return "physical_health"
    
    # Personality queries
    if any(term in message for term in ["personality", "character", "nature", "temperament", "what are you like"]):
        return "personality"
    
    # Intelligence queries
    if any(term in message for term in ["intelligence", "smart", "clever", "intellect", "how smart", "how intelligent"]):
        return "intelligence"
    
    # General feeling queries
    if any(term in message for term in ["how are you", "how do you feel", "feeling", "mood", "how's it going"]):
        return "general_feeling"
    
    return None

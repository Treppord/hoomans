"""
World Cache System - Stores entity memories for each world seed
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class WorldCache:
    """Manages caching of world data and entity memories for specific world seeds"""
    
    def __init__(self, cache_dir="cache"):
        """Initialize the world cache system"""
        self.cache_dir = cache_dir
        self.current_seed = None
        self.entity_memories = {}  # agent_id -> memories
        self.discovered_locations = {}  # location_type -> list of coordinates
        self.entity_relationships = {}  # agent_id -> {other_agent_id: relationship_data}
        self.last_save_time = 0
        self.save_interval = 60  # Save every 60 seconds
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def set_world_seed(self, seed):
        """Set the current world seed and load cached data if available"""
        self.current_seed = seed
        self.entity_memories = {}
        self.discovered_locations = {}
        self.entity_relationships = {}
        
        # Try to load cached data for this seed
        self._load_cache()
    
    def add_entity_memory(self, entity_id, memory_type, data):
        """Add a memory for an entity"""
        if not self.current_seed:
            return False
            
        # Initialize entity memory if needed
        if entity_id not in self.entity_memories:
            self.entity_memories[entity_id] = []
        
        # Create memory entry
        memory = {
            "type": memory_type,
            "data": data,
            "timestamp": time.time()
        }
        
        # Add to memories
        self.entity_memories[entity_id].append(memory)
        
        # Limit memory size (keep last 100 memories)
        if len(self.entity_memories[entity_id]) > 100:
            self.entity_memories[entity_id] = self.entity_memories[entity_id][-100:]
        
        # Save cache if it's been a while
        self._auto_save()
        
        return True
    
    def add_discovered_location(self, entity_id, location_type, x, y, name=None):
        """Add a discovered location"""
        if not self.current_seed:
            return False
        
        # Initialize location type if needed
        if location_type not in self.discovered_locations:
            self.discovered_locations[location_type] = []
        
        # Check if location already exists
        for loc in self.discovered_locations[location_type]:
            if loc["x"] == x and loc["y"] == y:
                # Update discovery info
                if entity_id not in loc["discovered_by"]:
                    loc["discovered_by"].append(entity_id)
                return True
        
        # Create new location entry
        location = {
            "x": x,
            "y": y,
            "name": name or f"{location_type.capitalize()} at {x},{y}",
            "discovered_by": [entity_id],
            "discovery_time": time.time()
        }
        
        # Add to locations
        self.discovered_locations[location_type].append(location)
        
        # Add memory for the entity
        self.add_entity_memory(
            entity_id, 
            "location_discovery",
            {
                "location_type": location_type,
                "x": x,
                "y": y,
                "name": location["name"]
            }
        )
        
        # Save cache
        self._auto_save()
        
        return True
    
    def update_entity_relationship(self, entity_id, other_entity_id, relationship_type, data=None):
        """Update relationship between entities"""
        if not self.current_seed:
            return False
        
        # Initialize entity relationships if needed
        if entity_id not in self.entity_relationships:
            self.entity_relationships[entity_id] = {}
        
        # Get current relationship or create new one
        if other_entity_id in self.entity_relationships[entity_id]:
            relationship = self.entity_relationships[entity_id][other_entity_id]
        else:
            relationship = {
                "type": relationship_type,
                "first_met": time.time(),
                "last_interaction": time.time(),
                "interaction_count": 0,
                "data": {}
            }
        
        # Update relationship
        relationship["type"] = relationship_type
        relationship["last_interaction"] = time.time()
        relationship["interaction_count"] += 1
        
        # Update additional data if provided
        if data:
            relationship["data"].update(data)
        
        # Store updated relationship
        self.entity_relationships[entity_id][other_entity_id] = relationship
        
        # Save cache
        self._auto_save()
        
        return True
    
    
    def add_location_discovery(self, entity_id, location_type, x, y, name=None):
        """
        Record a location discovery by an entity
        
        Args:
            entity_id: Unique identifier for the entity
            location_type: Type of location (e.g., "water", "food", "shelter")
            x: X coordinate
            y: Y coordinate
            name: Optional name for the location
        """
        if not self.current_seed:
            logger.warning("Cannot add location discovery: No current seed set")
            return False
            
        # Create default name if none provided
        if not name:
            name = f"{location_type.capitalize()} source"
            
        # Add to entity memories
        if entity_id not in self.entity_memories:
            self.entity_memories[entity_id] = []
            
        # Check if this entity already has this location in memory
        for memory in self.entity_memories[entity_id]:
            if (memory.get("type") == "location_discovery" and
                memory.get("data", {}).get("location_type") == location_type and
                memory.get("data", {}).get("x") == x and
                memory.get("data", {}).get("y") == y):
                # Already discovered, no need to add again
                return True
                
        # Add new memory
        memory = {
            "type": "location_discovery",
            "data": {
                "location_type": location_type,
                "x": x,
                "y": y,
                "name": name
            },
            "timestamp": time.time()
        }
        self.entity_memories[entity_id].append(memory)
        
        # Add to discovered locations
        if location_type not in self.discovered_locations:
            self.discovered_locations[location_type] = []
            
        # Check if this location is already in the list
        for location in self.discovered_locations[location_type]:
            if location.get("x") == x and location.get("y") == y:
                # Location already discovered, just add this entity to discoverers
                if "discovered_by" not in location:
                    location["discovered_by"] = []
                if entity_id not in location["discovered_by"]:
                    location["discovered_by"].append(entity_id)
                return True
                
        # Add new location
        location = {
            "x": x,
            "y": y,
            "name": name,
            "discovered_by": [entity_id],
            "discovery_time": time.time()
        }
        self.discovered_locations[location_type].append(location)
        
        # Save cache after adding new data
        self._save_cache()
        return True
        
    def get_entity_memories(self, entity_id):
        """Get all memories for a specific entity"""
        return self.entity_memories.get(entity_id, [])
        
    def get_discovered_locations(self, location_type=None):
        """
        Get discovered locations
        
        Args:
            location_type: Optional type to filter by (e.g., "water")
            
        Returns:
            List of location dictionaries
        """
        if location_type:
            return self.discovered_locations.get(location_type, [])
        else:
            # Return all locations
            all_locations = []
            for locations in self.discovered_locations.values():
                all_locations.extend(locations)
            return all_locations

    
    
    def get_entity_relationships(self, entity_id):
        """Get all relationships for an entity"""
        if not self.current_seed or entity_id not in self.entity_relationships:
            return {}
        
        return self.entity_relationships[entity_id]
    
    def _load_cache(self):
        """Load cache data for the current seed"""
        if not self.current_seed:
            logger.info("Cannot load cache: No current seed set")
            return False
        
        cache_file = os.path.join(self.cache_dir, f"world_{self.current_seed}.json")
        
        if not os.path.exists(cache_file):
            logger.info(f"No cache file found for seed {self.current_seed}")
            return False
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Load data from cache
            self.entity_memories = cache_data.get("entity_memories", {})
            self.discovered_locations = cache_data.get("discovered_locations", {})
            self.entity_relationships = cache_data.get("entity_relationships", {})
            
            logger.info(f"Loaded cache for seed {self.current_seed}")
            print(f"DEBUG: Loaded world cache from {cache_file}")
            print(f"DEBUG: Cache contains {len(self.entity_memories)} entity memories and {len(self.discovered_locations)} location types")
            return True
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            print(f"ERROR loading cache: {e}")
            return False
    
    def _save_cache(self):
        """Save cache data for the current seed"""
        if not self.current_seed:
            logger.info("Cannot save cache: No current seed set")
            return False
        
        cache_file = os.path.join(self.cache_dir, f"world_{self.current_seed}.json")
        
        try:
            cache_data = {
                "seed": self.current_seed,
                "entity_memories": self.entity_memories,
                "discovered_locations": self.discovered_locations,
                "entity_relationships": self.entity_relationships,
                "last_updated": time.time()
            }
            
            # Create cache directory if it doesn't exist
            os.makedirs(self.cache_dir, exist_ok=True)
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.last_save_time = time.time()
            logger.info(f"Saved cache for seed {self.current_seed}")
            print(f"DEBUG: Saved world cache to {cache_file}")
            print(f"DEBUG: Cache contains {len(self.entity_memories)} entity memories and {len(self.discovered_locations)} location types")
            return True
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            print(f"ERROR saving cache: {e}")
            return False

    
    def _auto_save(self):
        """Automatically save cache if it's been a while"""
        if time.time() - self.last_save_time > self.save_interval:
            return self._save_cache()
        return False
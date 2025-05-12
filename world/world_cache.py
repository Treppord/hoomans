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
    
    def get_entity_memories(self, entity_id, memory_type=None, limit=10):
        """Get memories for an entity, optionally filtered by type"""
        if not self.current_seed or entity_id not in self.entity_memories:
            return []
        
        memories = self.entity_memories[entity_id]
        
        # Filter by type if specified
        if memory_type:
            memories = [m for m in memories if m["type"] == memory_type]
        
        # Sort by timestamp (newest first) and limit
        return sorted(memories, key=lambda m: m["timestamp"], reverse=True)[:limit]
    
    def get_discovered_locations(self, entity_id, location_type=None):
        """Get locations discovered by an entity"""
        if not self.current_seed:
            return []
        
        locations = []
        
        # Get all location types or just the specified one
        location_types = [location_type] if location_type else self.discovered_locations.keys()
        
        for lt in location_types:
            if lt in self.discovered_locations:
                # Filter locations discovered by this entity
                for loc in self.discovered_locations[lt]:
                    if entity_id in loc["discovered_by"]:
                        locations.append({
                            "type": lt,
                            "x": loc["x"],
                            "y": loc["y"],
                            "name": loc["name"]
                        })
        
        return locations
    
    def get_entity_relationships(self, entity_id):
        """Get all relationships for an entity"""
        if not self.current_seed or entity_id not in self.entity_relationships:
            return {}
        
        return self.entity_relationships[entity_id]
    
    def _load_cache(self):
        """Load cache data for the current seed"""
        if not self.current_seed:
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
            return True
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return False
    
    def _save_cache(self):
        """Save cache data for the current seed"""
        if not self.current_seed:
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
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.last_save_time = time.time()
            logger.info(f"Saved cache for seed {self.current_seed}")
            return True
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            return False
    
    def _auto_save(self):
        """Automatically save cache if it's been a while"""
        if time.time() - self.last_save_time > self.save_interval:
            return self._save_cache()
        return False
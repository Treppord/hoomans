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
        
        # Clean up any duplicate location discoveries
        self.cleanup_duplicates()
    
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
        location_exists = False
        for loc in self.discovered_locations[location_type]:
            if loc["x"] == x and loc["y"] == y:
                # Update discovery info
                if entity_id not in loc["discovered_by"]:
                    loc["discovered_by"].append(entity_id)
                location_exists = True
                
                # Use this location's name for the memory to ensure consistency
                name = loc["name"]
                break
        
        # Create new location entry if it doesn't exist
        if not location_exists:
            location = {
                "x": x,
                "y": y,
                "name": name or f"{location_type.capitalize()} at {x},{y}",
                "discovered_by": [entity_id],
                "discovery_time": time.time()
            }
            
            # Add to locations
            self.discovered_locations[location_type].append(location)
        
        # Add memory for the entity - check for duplicates first
        has_duplicate = False
        for memory in self.entity_memories.get(entity_id, []):
            if (memory["type"] == "location_discovery" and
                memory["data"]["location_type"] == location_type and
                memory["data"]["x"] == x and
                memory["data"]["y"] == y):
                has_duplicate = True
                break
        
        if not has_duplicate:
            self.add_entity_memory(
                entity_id, 
                "location_discovery",
                {
                    "location_type": location_type,
                    "x": x,
                    "y": y,
                    "name": name or f"{location_type.capitalize()} at {x},{y}"
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
        # Convert entity_id to string if it's not already
        entity_id = str(entity_id)
        
        # Ensure entity_id is in the memories dictionary
        if entity_id not in self.entity_memories:
            self.entity_memories[entity_id] = []
        
        # Check if this entity already has this exact location discovery
        has_duplicate = False
        for memory in self.entity_memories[entity_id]:
            if (memory["type"] == "location_discovery" and 
                memory["data"]["location_type"] == location_type and
                memory["data"]["x"] == x and 
                memory["data"]["y"] == y):
                has_duplicate = True
                break
        
        # Only add to entity memories if it's not a duplicate
        if not has_duplicate:
            # Create the memory entry
            memory = {
                "type": "location_discovery",
                "data": {
                    "location_type": location_type,
                    "x": x,
                    "y": y,
                    "name": name or f"{location_type.capitalize()} source"
                },
                "timestamp": time.time()
            }
            
            # Add to entity memories
            self.entity_memories[entity_id].append(memory)
        
        # Also record in discovered locations
        if location_type not in self.discovered_locations:
            self.discovered_locations[location_type] = []
        
        # Check if this location already exists
        location_exists = False
        for loc in self.discovered_locations[location_type]:
            if loc["x"] == x and loc["y"] == y:
                # Location exists, add this entity to discoverers if not already there
                if "discovered_by" not in loc:
                    loc["discovered_by"] = []
                if entity_id not in loc["discovered_by"]:
                    loc["discovered_by"].append(entity_id)
                location_exists = True
                break
        
        # If location doesn't exist, add it
        if not location_exists:
            self.discovered_locations[location_type].append({
                "x": x,
                "y": y,
                "name": name or f"{location_type.capitalize()} source",
                "discovered_by": [entity_id],
                "discovery_time": time.time()
            })
        
        # Save the cache
        self._save_cache()
        
        # Get the cache file path for the current seed
        cache_file = os.path.join(self.cache_dir, f"world_{self.current_seed}.json") if self.current_seed else "No cache file (no seed set)"
        
        print(f"DEBUG: Saved world cache to {cache_file}")
        print(f"DEBUG: Cache contains {len(self.entity_memories)} entity memories and {len(self.discovered_locations)} location types")

    def cleanup_duplicates(self):
        """Clean up duplicate location discoveries in entity memories and consolidate across entities"""
        if not self.current_seed:
            return
        
        print(f"DEBUG: Starting aggressive duplicate cleanup for seed {self.current_seed}")
        
        # STEP 1: First consolidate all discovered locations by coordinates
        consolidated_locations = {}
        for location_type, locations in self.discovered_locations.items():
            if location_type not in consolidated_locations:
                consolidated_locations[location_type] = {}
                
            for loc in locations:
                # Use coordinates as key
                coord_key = (loc["x"], loc["y"])
                
                if coord_key not in consolidated_locations[location_type]:
                    # First time seeing this location
                    consolidated_locations[location_type][coord_key] = {
                        "x": loc["x"],
                        "y": loc["y"],
                        "name": loc["name"],
                        "discovered_by": loc.get("discovered_by", []),
                        "discovery_time": loc.get("discovery_time", time.time())
                    }
                else:
                    # Merge with existing location
                    existing = consolidated_locations[location_type][coord_key]
                    
                    # Merge discoverers
                    for entity_id in loc.get("discovered_by", []):
                        if entity_id not in existing["discovered_by"]:
                            existing["discovered_by"].append(entity_id)
                    
                    # Keep earliest discovery time
                    if "discovery_time" in loc:
                        existing["discovery_time"] = min(
                            existing["discovery_time"],
                            loc["discovery_time"]
                        )
        
        # STEP 2: Rebuild the discovered_locations structure
        self.discovered_locations = {}
        for location_type, locations in consolidated_locations.items():
            self.discovered_locations[location_type] = list(locations.values())
            print(f"DEBUG: Consolidated {len(locations)} unique {location_type} locations")
        
        # STEP 3: Create a canonical mapping of locations to their names
        canonical_names = {}
        for location_type, locations in self.discovered_locations.items():
            for loc in locations:
                canonical_names[(location_type, loc["x"], loc["y"])] = loc["name"]
        
        # STEP 4: Rebuild entity memories to eliminate duplicates
        for entity_id in list(self.entity_memories.keys()):
            memories = self.entity_memories[entity_id]
            new_memories = []
            seen_locations = set()
            
            # First, keep all non-location memories
            for memory in memories:
                if memory["type"] != "location_discovery":
                    new_memories.append(memory)
            
            # Then add exactly one memory per discovered location
            for location_type, locations in self.discovered_locations.items():
                for loc in locations:
                    if entity_id in loc["discovered_by"]:
                        loc_key = (location_type, loc["x"], loc["y"])
                        
                        # Skip if we've already added this location
                        if loc_key in seen_locations:
                            continue
                        
                        seen_locations.add(loc_key)
                        
                        # Find the original memory for this location if it exists
                        original_memory = None
                        original_timestamp = None
                        
                        for memory in memories:
                            if (memory["type"] == "location_discovery" and
                                memory["data"]["location_type"] == location_type and
                                memory["data"]["x"] == loc["x"] and
                                memory["data"]["y"] == loc["y"]):
                                if original_timestamp is None or memory["timestamp"] < original_timestamp:
                                    original_memory = memory
                                    original_timestamp = memory["timestamp"]
                        
                        # Create a new memory or use the original
                        if original_memory:
                            # Use original but update the name to be consistent
                            memory_copy = dict(original_memory)
                            memory_copy["data"]["name"] = canonical_names[loc_key]
                            new_memories.append(memory_copy)
                        else:
                            # Create a new memory
                            new_memories.append({
                                "type": "location_discovery",
                                "data": {
                                    "location_type": location_type,
                                    "x": loc["x"],
                                    "y": loc["y"],
                                    "name": canonical_names[loc_key]
                                },
                                "timestamp": loc["discovery_time"]
                            })
            
            # Replace with cleaned memories
            self.entity_memories[entity_id] = new_memories
            print(f"DEBUG: Cleaned entity {entity_id}: {len(new_memories)} memories ({len(seen_locations)} locations)")
        
        # STEP 5: Save the completely rebuilt cache
        self._save_cache()
        print(f"DEBUG: Completed aggressive duplicate cleanup for seed {self.current_seed}")




        
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
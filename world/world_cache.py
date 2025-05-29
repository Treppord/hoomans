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
        
        # World state tracking
        self.entity_tiles = {}  # (x, y) -> entity_tile_data
        self.entity_positions = {}  # entity_id -> {x, y, type, data}
        self.removed_entity_tiles = set()  # Set of (x, y) coordinates where entity tiles were removed
        self.world_modifications = {}  # Track any world modifications
        self.world_items = []  # Track items in the world


        # NEW: Custom map support
        self.custom_map_path = None  # Path to custom map file if loaded
        self.is_custom_map = False   # Flag to indicate if using custom map


        # Save interval tracking
        self.last_save_time = 0
        self.save_interval = 60  # Save every 60 seconds
        
        # Optimization settings - increased limits to reduce cleanup frequency
        self.max_memories_per_entity = 100  # Increased from 50
        self.max_world_modifications = 500  # Increased from 100
        self.max_entity_tiles = 5000  # Increased from 2000
        self.cleanup_interval = 600  # Clean up every 10 minutes instead of 5
        self.last_cleanup_time = 0
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def set_custom_map(self, map_path):
        """Set a custom map to be loaded
        
        Args:
            map_path: Full path to the custom map file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(map_path):
                print(f"Custom map file not found: {map_path}")
                return False
            
            # Store the custom map path for later use
            self.custom_map_path = map_path
            print(f"Custom map set: {map_path}")
            return True
            
        except Exception as e:
            print(f"Error setting custom map: {e}")
            return False
    
    def get_custom_map_path(self) -> Optional[str]:
        """Get the path to the custom map if one is set"""
        return self.custom_map_path if self.is_custom_map else None
    
    def clear_custom_map(self):
        """Clear custom map and return to procedural generation"""
        self.custom_map_path = None
        self.is_custom_map = False
        print("Cleared custom map, returning to procedural generation")
    
    def get_available_maps(self) -> List[Dict[str, Any]]:
        """Get list of available custom maps"""
        maps_dir = "maps"
        available_maps = []
        
        if not os.path.exists(maps_dir):
            return available_maps
        
        try:
            from tools.map_editor.map_serializer import MapSerializer
            serializer = MapSerializer()
            
            for filename in os.listdir(maps_dir):
                if filename.endswith('.json'):
                    map_path = os.path.join(maps_dir, filename)
                    map_info = serializer.get_map_info(map_path)
                    
                    if map_info:
                        # Add modification time
                        stat = os.stat(map_path)
                        map_info['modified_time'] = stat.st_mtime
                        map_info['modified_str'] = time.strftime(
                            '%Y-%m-%d %H:%M:%S', 
                            time.localtime(stat.st_mtime)
                        )
                        available_maps.append(map_info)
            
            # Sort by modification time (newest first)
            available_maps.sort(key=lambda x: x['modified_time'], reverse=True)
            
        except ImportError:
            print("Map serializer not available for map info")
        except Exception as e:
            print(f"Error scanning for maps: {e}")
        
        return available_maps
    
    def load_custom_map(self, world_map):
        """Load the set custom map into a world map
        
        Args:
            world_map: The WorldMap instance to load into
            
        Returns:
            True if successful, False otherwise
        """
        if not hasattr(self, 'custom_map_path') or not self.custom_map_path:
            print("No custom map path set")
            return False
        
        try:
            from tools.map_editor.map_serializer import MapSerializer
            
            serializer = MapSerializer()
            
            # Load the custom map
            custom_world_map = serializer.load_map(os.path.basename(self.custom_map_path))
            
            if not custom_world_map:
                print(f"Failed to load custom map: {self.custom_map_path}")
                return False
            
            # Copy the custom map data to the target world map
            if custom_world_map.width != world_map.width or custom_world_map.height != world_map.height:
                print(f"Warning: Map size mismatch. Custom: {custom_world_map.width}x{custom_world_map.height}, Target: {world_map.width}x{world_map.height}")
                # You might want to resize or crop here
            
            # Copy tiles
            for y in range(min(custom_world_map.height, world_map.height)):
                for x in range(min(custom_world_map.width, world_map.width)):
                    tile = custom_world_map.get_tile(x, y)
                    if tile:
                        world_map.set_tile(x, y, tile.type)
            
            # Copy entity tiles
            if hasattr(custom_world_map, 'entity_tile_manager') and custom_world_map.entity_tile_manager:
                if not hasattr(world_map, 'entity_tile_manager'):
                    world_map.initialize_entity_tiles()
                
                for entity_tile in custom_world_map.entity_tile_manager.entity_tiles:
                    # Recreate entity tiles in the target map
                    if entity_tile.tile_type == "tree":
                        world_map.add_tree(entity_tile.base_x, entity_tile.base_y)
                    elif entity_tile.tile_type == "house":
                        world_map.add_house(entity_tile.base_x, entity_tile.base_y)
            
            print(f"Custom map loaded successfully: {self.custom_map_path}")
            
            # Mark this world as using a custom map
            self.is_custom_map = True
            self.custom_map_name = os.path.basename(self.custom_map_path)
            
            return True
            
        except Exception as e:
            print(f"Error loading custom map: {e}")
            import traceback
            traceback.print_exc()
            return False
        s
    # Keep all existing methods unchanged...
    def save_entity_tile(self, x, y, entity_tile_type, entity_tile_data=None):
        """Save an entity tile to the cache with optimization"""
        if not self.current_seed:
            return False
        
        # Check if we're at the limit
        if len(self.entity_tiles) >= self.max_entity_tiles:
            self._cleanup_old_entity_tiles()
        
        tile_key = f"{x},{y}"
        
        # Optimize entity tile data - only save essential information
        optimized_data = self._optimize_entity_tile_data(entity_tile_data or {})
        
        self.entity_tiles[tile_key] = {
            "x": x,
            "y": y,
            "type": entity_tile_type,
            "data": optimized_data,
            "created_time": time.time()
        }
        
        # Remove from removed set if it was there
        if (x, y) in self.removed_entity_tiles:
            self.removed_entity_tiles.remove((x, y))
        
        self._auto_save()
        return True
    
    def _optimize_entity_tile_data(self, data):
        """Optimize entity tile data to reduce size"""
        if not isinstance(data, dict):
            return {}
        
        optimized = {}
        
        # Only save essential data, skip redundant or large data
        essential_keys = [
            'opacity', 'is_active', 'is_door_open', 'max_occupants',
            'entities_inside_count', 'entities_in_trunk_count'
        ]
        
        for key in essential_keys:
            if key in data:
                value = data[key]
                # Skip default values to save space
                if key == 'opacity' and value == 1.0:
                    continue
                if key == 'is_active' and value == True:
                    continue
                if key == 'is_door_open' and value == False:
                    continue
                if key == 'max_occupants' and value == 4:
                    continue
                if key in ['entities_inside_count', 'entities_in_trunk_count'] and value == 0:
                    continue
                
                optimized[key] = value
        
        return optimized
    
    def save_entity_position(self, entity_id, x, y, entity_type, entity_data=None):
        """Save an entity's position and data with optimization"""
        if not self.current_seed:
            return False
        
        # Optimize entity data
        optimized_data = self._optimize_entity_data(entity_data or {})
        
        self.entity_positions[entity_id] = {
            "x": x,
            "y": y,
            "type": entity_type,
            "data": optimized_data,
            "last_updated": time.time()
        }
        
        self._auto_save()
        return True
    
    def _optimize_entity_data(self, data):
        """Optimize entity data to reduce size"""
        if not isinstance(data, dict):
            return {}
        
        optimized = {}
        
        # Essential data only
        essential_keys = [
            'thirst', 'hunger', 'comfort', 'exploration_mode', 'curiosity',
            'color', 'cna_file', 'heading_to_known_water', 'heading_to_food', 
            'heading_to_comfort'
        ]
        
        for key in essential_keys:
            if key in data:
                value = data[key]
                # Skip default values
                if key == 'exploration_mode' and value == 'idle':
                    continue
                if key in ['heading_to_known_water', 'heading_to_food', 'heading_to_comfort'] and value == False:
                    continue
                
                optimized[key] = value
        
        # Handle complex data structures with limits
        if 'interesting_locations' in data and isinstance(data['interesting_locations'], dict):
            locations = {}
            for loc_type, loc_list in data['interesting_locations'].items():
                if isinstance(loc_list, list) and len(loc_list) > 0:
                    # Limit to 10 most recent locations per type
                    locations[loc_type] = loc_list[-10:]
            if locations:
                optimized['interesting_locations'] = locations
        
        if 'explored_tiles' in data and isinstance(data['explored_tiles'], list):
            # Limit explored tiles to 100 most recent
            if len(data['explored_tiles']) > 100:
                optimized['explored_tiles'] = data['explored_tiles'][-100:]
            elif len(data['explored_tiles']) > 0:
                optimized['explored_tiles'] = data['explored_tiles']
        
        # Only save home_location if it's different from current position
        if 'home_location' in data:
            home = data['home_location']
            current_pos = (data.get('x', 0), data.get('y', 0))
            if isinstance(home, (list, tuple)) and len(home) >= 2:
                if (home[0], home[1]) != current_pos:
                    optimized['home_location'] = list(home)
        
        return optimized
    
    def add_entity_memory(self, entity_id, memory_type, data):
        """Add a memory for an entity with size limits"""
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
        
        # Limit memory size (keep last N memories)
        if len(self.entity_memories[entity_id]) > self.max_memories_per_entity:
            self.entity_memories[entity_id] = self.entity_memories[entity_id][-self.max_memories_per_entity:]
        
        # Save cache if it's been a while
        self._auto_save()
        
        return True
    
    def save_world_modification(self, modification_type, x, y, old_data, new_data):
        """Save a world modification with limits"""
        if not self.current_seed:
            return False
        
        # Check if we're at the limit
        if len(self.world_modifications) >= self.max_world_modifications:
            self._cleanup_old_world_modifications()
        
        mod_key = f"{modification_type}_{x}_{y}_{int(time.time())}"
        self.world_modifications[mod_key] = {
            "type": modification_type,
            "x": x,
            "y": y,
            "old_data": self._compress_tile_data(old_data),
            "new_data": self._compress_tile_data(new_data),
            "timestamp": time.time()
        }
        
        self._auto_save()
        return True
    
    def _compress_tile_data(self, data):
        """Compress tile data to essential information only"""
        if isinstance(data, dict) and 'type' in data:
            return {"type": data['type']}
        return data
    
    def _cleanup_old_data(self):
        """Clean up old data to keep cache size manageable"""
        current_time = time.time()
        
        # Only run cleanup periodically - increase the interval to reduce spam
        if current_time - self.last_cleanup_time < self.cleanup_interval:
            return
        
        self.last_cleanup_time = current_time
        
        # Only print debug message occasionally
        cleanup_count = 0
        
        # Clean up old world modifications (keep only last 30 days)
        cutoff_time = current_time - (30 * 24 * 3600)  # 30 days
        old_modifications = []
        for key, mod in self.world_modifications.items():
            if mod.get('timestamp', 0) < cutoff_time:
                old_modifications.append(key)
        
        for key in old_modifications:
            del self.world_modifications[key]
            cleanup_count += 1
        
        # Clean up old entity memories (keep only recent ones)
        for entity_id in list(self.entity_memories.keys()):
            memories = self.entity_memories[entity_id]
            if len(memories) > self.max_memories_per_entity:
                old_count = len(memories)
                self.entity_memories[entity_id] = memories[-self.max_memories_per_entity:]
                cleanup_count += old_count - len(self.entity_memories[entity_id])
        
        # Clean up old entity tiles (remove very old ones)
        old_tiles = []
        for key, tile_data in self.entity_tiles.items():
            if tile_data.get('created_time', 0) < cutoff_time:
                old_tiles.append(key)
        
        for key in old_tiles:
            del self.entity_tiles[key]
            cleanup_count += 1
        
        # Only print debug message if we actually cleaned up a significant amount
        if cleanup_count > 10:
            print(f"DEBUG: Cache cleanup completed - removed {cleanup_count} old entries")
    
    def _cleanup_old_entity_tiles(self):
        """Remove oldest entity tiles when at limit"""
        if len(self.entity_tiles) <= self.max_entity_tiles:
            return
        
        # Sort by creation time and remove oldest 20%
        sorted_tiles = sorted(
            self.entity_tiles.items(),
            key=lambda x: x[1].get('created_time', 0)
        )
        
        remove_count = len(sorted_tiles) // 5  # Remove 20%
        for i in range(remove_count):
            key = sorted_tiles[i][0]
            del self.entity_tiles[key]
        
        print(f"DEBUG: Removed {remove_count} oldest entity tiles")
    
    def _cleanup_old_world_modifications(self):
        """Remove oldest world modifications when at limit"""
        if len(self.world_modifications) <= self.max_world_modifications:
            return
        
        # Sort by timestamp and remove oldest entries (not newest!)
        sorted_mods = sorted(
            self.world_modifications.items(),
            key=lambda x: x[1].get('timestamp', 0)
        )
        
        # Calculate how many to remove (remove oldest 20%)
        remove_count = len(sorted_mods) // 5  # Remove 20%
        if remove_count == 0:
            remove_count = 1  # Remove at least 1 if we're at the limit
        
        # Remove the OLDEST entries (first in sorted list)
        removed_keys = []
        for i in range(remove_count):
            key = sorted_mods[i][0]
            removed_keys.append(key)
            del self.world_modifications[key]
        
        # Only print debug message if we actually removed something significant
        if remove_count > 5:  # Only log if we removed more than 5 items
            print(f"DEBUG: Removed {remove_count} oldest world modifications (keeping {len(self.world_modifications)} recent ones)")
    
    def _save_cache(self):
        """Save cache data for the current seed with compression"""
        if not self.current_seed:
            logger.info("Cannot save cache: No current seed set")
            return False
        
        cache_file = os.path.join(self.cache_dir, f"world_{self.current_seed}.json")
        
        try:
            # Run cleanup before saving
            self._cleanup_old_data()
            
            # Convert removed_entity_tiles set to list for JSON serialization
            removed_tiles_list = list(self.removed_entity_tiles) if hasattr(self, 'removed_entity_tiles') else []
            
            cache_data = {
                "seed": self.current_seed,
                "entity_memories": self.entity_memories,
                "discovered_locations": self.discovered_locations,
                "entity_relationships": self.entity_relationships,
                "entity_tiles": self.entity_tiles,
                "entity_positions": self.entity_positions,
                "removed_entity_tiles": removed_tiles_list,
                "world_modifications": self.world_modifications,
                "world_items": getattr(self, 'world_items', []),
                "last_updated": time.time(),
                "cache_version": "1.2",  # Increment version for custom map support
                # Enhanced custom map support
                "custom_map_path": self.custom_map_path,
                "is_custom_map": self.is_custom_map,
                # NEW: Save constructed entity tiles separately for custom maps
                "constructed_entity_tiles": self._get_constructed_entity_tiles() if self.is_custom_map else {}
            }
            
            # Create cache directory if it doesn't exist
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Save with minimal indentation to reduce file size
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, separators=(',', ':'))  # Compact JSON
            
            self.last_save_time = time.time()
            
            # Calculate and log file size
            file_size = os.path.getsize(cache_file)
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Saved cache for seed {self.current_seed} ({file_size_mb:.2f} MB)")
            
            # Special handling for custom maps - also update the original map file if desired
            if self.is_custom_map and self.custom_map_path:
                self._save_constructed_tiles_to_custom_map()
            
            return True
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            print(f"ERROR saving cache: {e}")
            return False
    
    def get_available_maps(self):
        """Get available custom maps from the map creator"""
        try:
            # Import here to avoid circular imports
            from tools.map_editor.map_serializer import MapSerializer
            
            serializer = MapSerializer()
            map_files = serializer.list_maps()
            
            available_maps = []
            for filename in map_files:
                map_info = serializer.get_map_info(filename)
                if map_info:
                    # Convert to the format expected by the main menu
                    map_data = {
                        'filename': filename,
                        'width': map_info['width'],
                        'height': map_info['height'],
                        'entity_count': map_info['entity_count'],
                        'item_count': 0,  # Maps don't store items yet
                        'file_size_kb': map_info['file_size'] / 1024,
                        'compressed': map_info.get('compressed', False),
                        'full_path': os.path.join(serializer.get_maps_directory(), filename),
                        'modified_str': self._get_file_modified_time(os.path.join(serializer.get_maps_directory(), filename))
                    }
                    available_maps.append(map_data)
            
            return available_maps
            
        except Exception as e:
            print(f"Error getting available maps: {e}")
            return []
        
    def _get_file_modified_time(self, file_path):
        """Get formatted modification time for a file"""
        try:
            import time
            import os
            mtime = os.path.getmtime(file_path)
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        except:
            return "Unknown"
    
    def _get_constructed_entity_tiles(self):
        """Get all entity tiles that were constructed by players (not from original map)"""
        constructed_tiles = {}
        
        # Get the game engine to access the world map
        from engine.core.simple_game_engine import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance') or not SimpleGameEngine.instance:
            return constructed_tiles
        
        engine = SimpleGameEngine.instance
        if not hasattr(engine, 'world_map') or not engine.world_map:
            return constructed_tiles
        
        world_map = engine.world_map
        if not hasattr(world_map, 'entity_tile_manager'):
            return constructed_tiles
        
        # Get all current entity tiles
        for entity_tile in world_map.entity_tile_manager.entity_tiles:
            tile_key = f"{entity_tile.base_x},{entity_tile.base_y}"
            
            # Check if this tile was constructed (not from original map)
            if self._is_constructed_tile(entity_tile):
                constructed_tiles[tile_key] = {
                    "x": entity_tile.base_x,
                    "y": entity_tile.base_y,
                    "type": entity_tile.tile_type,
                    "width": entity_tile.width,
                    "height": entity_tile.height,
                    "data": entity_tile.get_save_data(),
                    "constructed_time": time.time()
                }
        
        return constructed_tiles
    
    def _is_constructed_tile(self, entity_tile):
        """Check if an entity tile was constructed by a player (not from original map)"""
        # For now, we'll assume any entity tile that's not in the original map data is constructed
        # This could be enhanced with a flag on entity tiles to track their origin
        
        if not self.is_custom_map or not self.custom_map_path:
            return True  # For procedural maps, all entity tiles are "constructed"
        
        # Check if this entity tile was in the original custom map
        try:
            import json
            with open(self.custom_map_path, 'r') as f:
                map_data = json.load(f)
            
            original_entity_tiles = map_data.get('entity_tiles', [])
            
            # Check if this tile matches any original tile
            for original_tile in original_entity_tiles:
                if (original_tile.get('x') == entity_tile.base_x and 
                    original_tile.get('y') == entity_tile.base_y and
                    original_tile.get('type') == entity_tile.tile_type):
                    return False  # This tile was in the original map
            
            return True  # This tile was not in the original map, so it's constructed
            
        except Exception as e:
            print(f"Error checking if tile is constructed: {e}")
            return True  # Assume constructed if we can't check
    
    def _save_constructed_tiles_to_custom_map(self):
        """Optionally save constructed tiles back to the custom map file"""
        # This is optional - we could create a separate "modified" version of the map
        # For now, we'll just log that we could do this
        constructed_count = len(self._get_constructed_entity_tiles())
        if constructed_count > 0:
            print(f"DEBUG: {constructed_count} constructed entity tiles could be saved to custom map")
    
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
            
            # Load world state data
            self.entity_tiles = cache_data.get("entity_tiles", {})
            self.entity_positions = cache_data.get("entity_positions", {})
            
            # Convert removed_entity_tiles list back to set
            removed_tiles_list = cache_data.get("removed_entity_tiles", [])
            self.removed_entity_tiles = set(tuple(coord) for coord in removed_tiles_list)
            
            self.world_modifications = cache_data.get("world_modifications", {})
            self.world_items = cache_data.get("world_items", [])
            
            # Load custom map info
            self.custom_map_path = cache_data.get("custom_map_path")
            self.is_custom_map = cache_data.get("is_custom_map", False)
            
            # NEW: Load constructed entity tiles for custom maps
            self.constructed_entity_tiles = cache_data.get("constructed_entity_tiles", {})
            
            # Calculate and log file size
            file_size = os.path.getsize(cache_file)
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Loaded cache for seed {self.current_seed} ({file_size_mb:.2f} MB)")
            
            if self.is_custom_map:
                constructed_count = len(self.constructed_entity_tiles)
                print(f"DEBUG: Loaded {constructed_count} constructed entity tiles for custom map")
            
            return True
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            print(f"ERROR loading cache: {e}")
            return False
    
    def load_constructed_entity_tiles(self, world_map):
        """Load constructed entity tiles into the world map"""
        if not hasattr(self, 'constructed_entity_tiles') or not self.constructed_entity_tiles:
            return
        
        if not hasattr(world_map, 'entity_tile_manager'):
            world_map.initialize_entity_tiles()
        
        print(f"DEBUG: Loading {len(self.constructed_entity_tiles)} constructed entity tiles")
        
        for tile_key, tile_data in self.constructed_entity_tiles.items():
            try:
                x = tile_data["x"]
                y = tile_data["y"]
                tile_type = tile_data["type"]
                
                # Check if this position is already occupied
                existing_tile = world_map.entity_tile_manager.get_entity_tile_at(x, y)
                if existing_tile:
                    print(f"DEBUG: Skipping constructed tile at ({x}, {y}) - position occupied")
                    continue
                
                # Create the appropriate entity tile
                entity_tile = None
                if tile_type == "tree":
                    entity_tile = world_map.add_tree(x, y)
                elif tile_type == "house":
                    entity_tile = world_map.add_house(x, y)
                # Add more entity tile types as needed
                
                if entity_tile:
                    # Restore saved data
                    if "data" in tile_data:
                        entity_tile.load_save_data(tile_data["data"])
                    print(f"DEBUG: Loaded constructed {tile_type} at ({x}, {y})")
                else:
                    print(f"DEBUG: Failed to create constructed {tile_type} at ({x}, {y})")
                    
            except Exception as e:
                print(f"Error loading constructed entity tile {tile_key}: {e}")

    
    def get_cache_stats(self):
        """Get statistics about the current cache"""
        stats = {
            "entity_memories": len(self.entity_memories),
            "total_memories": sum(len(memories) for memories in self.entity_memories.values()),
            "discovered_locations": len(self.discovered_locations),
            "total_locations": sum(len(locs) for locs in self.discovered_locations.values()),
            "entity_relationships": len(self.entity_relationships),
            "entity_tiles": len(self.entity_tiles),
            "entity_positions": len(self.entity_positions),
            "world_modifications": len(self.world_modifications),
            "removed_entity_tiles": len(self.removed_entity_tiles)
        }
        return stats
    
    # Keep all other existing methods unchanged...
    def remove_entity_tile(self, x, y):
        """Mark an entity tile as removed"""
        if not self.current_seed:
            return False
        
        tile_key = f"{x},{y}"
        
        # Remove from entity tiles if it exists
        if tile_key in self.entity_tiles:
            del self.entity_tiles[tile_key]
        
        # Add to removed set
        self.removed_entity_tiles.add((x, y))
        
        self._auto_save()
        return True
    
    def get_entity_tile(self, x, y):
        """Get entity tile data at specific coordinates"""
        if not self.current_seed:
            return None
        
        tile_key = f"{x},{y}"
        return self.entity_tiles.get(tile_key)
    
    def is_entity_tile_removed(self, x, y):
        """Check if an entity tile was removed at these coordinates"""
        return (x, y) in self.removed_entity_tiles
    
    def get_all_entity_tiles(self):
        """Get all saved entity tiles"""
        return list(self.entity_tiles.values())
    
    def get_entity_position(self, entity_id):
        """Get an entity's saved position and data"""
        return self.entity_positions.get(entity_id)
    
    def remove_entity_position(self, entity_id):
        """Remove an entity's position data"""
        if entity_id in self.entity_positions:
            del self.entity_positions[entity_id]
            self._auto_save()
            return True
        return False
    
    def get_all_entity_positions(self):
        """Get all saved entity positions"""
        # Return as a list of dictionaries with entity_id included
        result = []
        for entity_id, position_data in self.entity_positions.items():
            entity_dict = dict(position_data)
            entity_dict["entity_id"] = entity_id
            result.append(entity_dict)
        return result
    
    def get_world_modifications(self, modification_type=None):
        """Get world modifications, optionally filtered by type"""
        if modification_type:
            return {k: v for k, v in self.world_modifications.items() 
                   if v["type"] == modification_type}
        return dict(self.world_modifications)

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
        """Record a location discovery by an entity"""
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

    def cleanup_duplicates(self):
        """Clean up duplicate location discoveries in entity memories and consolidate across entities"""
        if not self.current_seed:
            return
        
        print(f"DEBUG: Starting optimized duplicate cleanup for seed {self.current_seed}")
        
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
                    
                    # Merge discoverers (limit to 10 most recent)
                    for entity_id in loc.get("discovered_by", []):
                        if entity_id not in existing["discovered_by"]:
                            existing["discovered_by"].append(entity_id)
                    
                    # Limit discoverers to prevent bloat
                    if len(existing["discovered_by"]) > 10:
                        existing["discovered_by"] = existing["discovered_by"][-10:]
                    
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
            
            # First, keep all non-location memories (limit to recent ones)
            non_location_memories = []
            for memory in memories:
                if memory["type"] != "location_discovery":
                    non_location_memories.append(memory)
            
            # Keep only the most recent non-location memories
            if len(non_location_memories) > 20:
                non_location_memories = sorted(non_location_memories, key=lambda x: x.get("timestamp", 0))[-20:]
            
            new_memories.extend(non_location_memories)
            
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
        print(f"DEBUG: Completed optimized duplicate cleanup for seed {self.current_seed}")



    def get_entity_memories(self, entity_id):
        """Get all memories for a specific entity"""
        return self.entity_memories.get(entity_id, [])
        
    def get_discovered_locations(self, location_type=None):
        """Get discovered locations"""
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
    

    
    def _auto_save(self):
        """Automatically save cache if it's been a while"""
        current_time = time.time()
        if current_time - self.last_save_time > self.save_interval:
            return self._save_cache()
        return False


    def save_world_items(self, items_data):
        """Save world items data"""
        if not self.current_seed:
            return False
        
        self.world_items = items_data
        self._auto_save()
        return True

    def get_world_items(self):
        """Get world items data"""
        return getattr(self, 'world_items', [])

    def create_fresh_world(self, seed):
        """Create a completely fresh world cache, clearing any existing data"""
        print(f"DEBUG: Creating fresh world for seed {seed}")
        
        # Clear all existing data
        self.entity_memories = {}
        self.discovered_locations = {}
        self.entity_relationships = {}
        self.entity_tiles = {}
        self.entity_positions = {}
        self.removed_entity_tiles = set()
        self.world_modifications = {}
        
        # Set the new seed
        self.current_seed = seed
        
        # Create empty cache file
        self.create_empty_cache(seed)
        
        # Reset timing
        self.last_save_time = 0
        self.last_cleanup_time = 0
        
        print(f"DEBUG: Fresh world cache created for seed {seed}")
    
    def set_world_seed(self, seed):
        """Set the current world seed and load cached data if available"""
        print(f"DEBUG: Setting world seed to {seed}")
        
        # Only clear data if we're switching to a different seed
        if self.current_seed != seed:
            self.current_seed = seed
            self.entity_memories = {}
            self.discovered_locations = {}
            self.entity_relationships = {}
            
            # Reset world state tracking
            self.entity_tiles = {}
            self.entity_positions = {}
            self.removed_entity_tiles = set()
            self.world_modifications = {}
            
            # Try to load cached data for this seed
            cache_loaded = self._load_cache()
            
            if cache_loaded:
                # Clean up any duplicate location discoveries
                self.cleanup_duplicates()
                
                # Perform initial cleanup
                self._cleanup_old_data()
                print(f"DEBUG: Loaded existing cache for seed {seed}")
            else:
                print(f"DEBUG: No existing cache found for seed {seed}")
        else:
            print(f"DEBUG: Already using seed {seed}, no need to reload")
    
    def create_empty_cache(self, seed):
        """Create an empty cache file for a new world if it doesn't exist"""
        cache_file = os.path.join(self.cache_dir, f"world_{seed}.json")
        
        # Always create a fresh empty cache (overwrite if exists for new worlds)
        cache_data = {
            "seed": seed,
            "entity_memories": {},
            "discovered_locations": {},
            "entity_relationships": {},
            "entity_tiles": {},
            "entity_positions": {},
            "removed_entity_tiles": [],
            "world_modifications": {},
            "world_items": [],  # Add empty world items
            "last_updated": time.time(),
            "cache_version": "1.1"
        }
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Save the empty cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, separators=(',', ':'))  # Compact JSON
            
            print(f"Created fresh empty cache file for seed {seed}: {cache_file}")
            return True
        except Exception as e:
            logger.error(f"Error creating empty cache: {e}")
            print(f"ERROR creating empty cache: {e}")
            return False

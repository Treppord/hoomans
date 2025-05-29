"""
Map serialization system for the map editor
Handles saving and loading maps to/from JSON files with compression
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple
from world.map import WorldMap
from world.entity_tile import TreeEntityTile, HouseEntityTile

class MapSerializer:
    """Handles map serialization and deserialization with compression"""
    
    def __init__(self):
        """Initialize the map serializer"""
        # Get the project root directory (3 levels up from this file)
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.maps_directory = os.path.join(self.project_root, "maps")
        self._ensure_maps_directory()
        print(f"Map serializer initialized - maps directory: {self.maps_directory}")
    
    def _ensure_maps_directory(self):
        """Ensure the maps directory exists"""
        if not os.path.exists(self.maps_directory):
            os.makedirs(self.maps_directory)
            print(f"Created maps directory: {self.maps_directory}")
    
    def _compress_tiles(self, tiles: List[List[str]]) -> List[Dict[str, Any]]:
        """Compress tile data using run-length encoding
        
        Args:
            tiles: 2D array of tile types
            
        Returns:
            Compressed tile data as list of segments
        """
        compressed = []
        
        for y, row in enumerate(tiles):
            x = 0
            while x < len(row):
                tile_type = row[x]
                count = 1
                
                # Count consecutive tiles of the same type
                while x + count < len(row) and row[x + count] == tile_type:
                    count += 1
                
                # Store the segment
                segment = {
                    "type": tile_type,
                    "x": x,
                    "y": y,
                    "count": count
                }
                compressed.append(segment)
                
                x += count
        
        return compressed
    
    def _decompress_tiles(self, compressed_data: List[Dict[str, Any]], width: int, height: int) -> List[List[str]]:
        """Decompress tile data from run-length encoding
        
        Args:
            compressed_data: Compressed tile segments
            width: Map width
            height: Map height
            
        Returns:
            2D array of tile types
        """
        # Initialize with empty tiles
        tiles = [["empty" for _ in range(width)] for _ in range(height)]
        
        # Fill in the compressed segments
        for segment in compressed_data:
            tile_type = segment["type"]
            x = segment["x"]
            y = segment["y"]
            count = segment["count"]
            
            # Validate coordinates
            if 0 <= y < height:
                for i in range(count):
                    if x + i < width:
                        tiles[y][x + i] = tile_type
        
        return tiles
    
    def _analyze_compression_efficiency(self, original_tiles: List[List[str]], compressed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compression efficiency
        
        Args:
            original_tiles: Original tile data
            compressed_data: Compressed tile data
            
        Returns:
            Compression statistics
        """
        original_size = len(original_tiles) * len(original_tiles[0]) if original_tiles else 0
        compressed_size = len(compressed_data)
        
        compression_ratio = compressed_size / original_size if original_size > 0 else 0
        space_saved = original_size - compressed_size
        
        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "space_saved": space_saved,
            "efficiency_percent": (1 - compression_ratio) * 100 if compression_ratio <= 1 else 0
        }
    
    def save_map(self, world_map: WorldMap, filename: str) -> bool:
        """Save a world map to a JSON file with compression
        
        Args:
            world_map: The WorldMap instance to save
            filename: The filename to save to (can include subdirectory)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare raw tile data for compression
            raw_tiles = []
            for y in range(world_map.height):
                row = []
                for x in range(world_map.width):
                    tile = world_map.get_tile(x, y)
                    row.append(tile.type if tile else "empty")
                raw_tiles.append(row)
            
            # Compress the tile data
            compressed_tiles = self._compress_tiles(raw_tiles)
            
            # Analyze compression efficiency
            compression_stats = self._analyze_compression_efficiency(raw_tiles, compressed_tiles)
            
            # Prepare map data with compression
            map_data = {
                "version": "1.1",  # Updated version for compression support
                "width": world_map.width,
                "height": world_map.height,
                "compressed": True,
                "tiles": compressed_tiles,  # Now compressed
                "entity_tiles": [],
                "compression_stats": compression_stats
            }
            
            # Save entity tiles (these are typically few, so no compression needed)
            if hasattr(world_map, 'entity_tile_manager') and world_map.entity_tile_manager:
                for entity_tile in world_map.entity_tile_manager.entity_tiles:
                    entity_data = {
                        "type": entity_tile.tile_type,
                        "x": entity_tile.base_x,
                        "y": entity_tile.base_y,
                        "width": entity_tile.width,
                        "height": entity_tile.height,
                        "properties": self._serialize_entity_properties(entity_tile)
                    }
                    map_data["entity_tiles"].append(entity_data)
            
            # Handle filename - remove any path separators and ensure .json extension
            clean_filename = os.path.basename(filename)
            if not clean_filename.endswith('.json'):
                clean_filename += '.json'
            
            # Create full path
            full_path = os.path.join(self.maps_directory, clean_filename)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Save to file with minimal formatting to save space
            with open(full_path, 'w') as f:
                json.dump(map_data, f, separators=(',', ':'))  # Compact JSON
            
            # Print compression statistics
            print(f"Map saved successfully: {full_path}")
            print(f"Compression: {compression_stats['original_size']} -> {compression_stats['compressed_size']} tiles")
            print(f"Space saved: {compression_stats['space_saved']} tiles ({compression_stats['efficiency_percent']:.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"Error saving map: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_map(self, filename: str) -> Optional[WorldMap]:
        """Load a world map from a JSON file with decompression support
        
        Args:
            filename: The filename to load from
            
        Returns:
            WorldMap instance if successful, None otherwise
        """
        try:
            # Handle filename - remove any path separators and ensure .json extension
            clean_filename = os.path.basename(filename)
            if not clean_filename.endswith('.json'):
                clean_filename += '.json'
            
            # Create full path
            full_path = os.path.join(self.maps_directory, clean_filename)
            
            if not os.path.exists(full_path):
                print(f"Map file not found: {full_path}")
                return None
            
            # Load from file
            with open(full_path, 'r') as f:
                map_data = json.load(f)
            
            # Validate map data
            if not self._validate_map_data(map_data):
                print(f"Invalid map data in file: {full_path}")
                return None
            
            # Create world map
            world_map = WorldMap(map_data["width"], map_data["height"])
            world_map.initialize_entity_tiles()
            world_map.initialize_world_items()
            
            # Handle both compressed and uncompressed formats
            if map_data.get("compressed", False):
                print("Loading compressed map data...")
                # Decompress tile data
                tiles = self._decompress_tiles(map_data["tiles"], map_data["width"], map_data["height"])
                
                # Load decompressed tiles
                for y, row in enumerate(tiles):
                    for x, tile_type in enumerate(row):
                        if 0 <= x < world_map.width and 0 <= y < world_map.height:
                            world_map.set_tile(x, y, tile_type)
                
                # Print decompression info
                if "compression_stats" in map_data:
                    stats = map_data["compression_stats"]
                    print(f"Decompressed: {stats['compressed_size']} -> {stats['original_size']} tiles")
            else:
                print("Loading uncompressed map data...")
                # Legacy format - direct tile array
                for y, row in enumerate(map_data["tiles"]):
                    for x, tile_type in enumerate(row):
                        if 0 <= x < world_map.width and 0 <= y < world_map.height:
                            world_map.set_tile(x, y, tile_type)
            
            # Load entity tiles
            if "entity_tiles" in map_data:
                for entity_data in map_data["entity_tiles"]:
                    self._create_entity_tile(world_map, entity_data)
            
            print(f"Map loaded successfully: {full_path}")
            print(f"Loaded {len(map_data.get('entity_tiles', []))} entity tiles")
            return world_map
            
        except Exception as e:
            print(f"Error loading map: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _validate_map_data(self, map_data: Dict[str, Any]) -> bool:
        """Validate map data structure (supports both compressed and uncompressed)
        
        Args:
            map_data: The map data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["width", "height", "tiles"]
        
        for field in required_fields:
            if field not in map_data:
                print(f"Missing required field: {field}")
                return False
        
        # Check dimensions
        width = map_data["width"]
        height = map_data["height"]
        
        if not isinstance(width, int) or not isinstance(height, int):
            print("Width and height must be integers")
            return False
        
        if width <= 0 or height <= 0:
            print("Width and height must be positive")
            return False
        
        # Check tiles data format
        tiles = map_data["tiles"]
        if not isinstance(tiles, list):
            print("Tiles must be a list")
            return False
        
        # Validate based on compression format
        if map_data.get("compressed", False):
            # Compressed format - validate segments
            for i, segment in enumerate(tiles):
                if not isinstance(segment, dict):
                    print(f"Compressed tile segment {i} must be a dictionary")
                    return False
                
                required_segment_fields = ["type", "x", "y", "count"]
                for field in required_segment_fields:
                    if field not in segment:
                        print(f"Missing field '{field}' in compressed segment {i}")
                        return False
        else:
            # Uncompressed format - validate 2D array
            if len(tiles) != height:
                print(f"Tiles array height mismatch: expected {height}, got {len(tiles)}")
                return False
            
            for y, row in enumerate(tiles):
                if not isinstance(row, list):
                    print(f"Tiles row {y} must be a list")
                    return False
                
                if len(row) != width:
                    print(f"Tiles row {y} width mismatch: expected {width}, got {len(row)}")
                    return False
        
        return True
    
    def _serialize_entity_properties(self, entity_tile) -> Dict[str, Any]:
        """Serialize entity-specific properties
        
        Args:
            entity_tile: The entity tile to serialize
            
        Returns:
            Dictionary of properties
        """
        properties = {}
        
        # Common properties
        if hasattr(entity_tile, 'opacity'):
            properties["opacity"] = entity_tile.opacity
        
        if hasattr(entity_tile, 'is_active'):
            properties["is_active"] = entity_tile.is_active
        
        # Tree-specific properties
        if isinstance(entity_tile, TreeEntityTile):
            if hasattr(entity_tile, 'entities_in_trunk'):
                properties["entities_in_trunk_count"] = len(entity_tile.entities_in_trunk)
        
        # House-specific properties
        elif isinstance(entity_tile, HouseEntityTile):
            if hasattr(entity_tile, 'is_door_open'):
                properties["is_door_open"] = entity_tile.is_door_open
            
            if hasattr(entity_tile, 'max_occupants'):
                properties["max_occupants"] = entity_tile.max_occupants
        
        return properties
    
    def _create_entity_tile(self, world_map: WorldMap, entity_data: Dict[str, Any]):
        """Create an entity tile from serialized data
        
        Args:
            world_map: The world map to add the entity to
            entity_data: The serialized entity data
        """
        entity_type = entity_data["type"]
        x = entity_data["x"]
        y = entity_data["y"]
        properties = entity_data.get("properties", {})
        
        try:
            # Create the appropriate entity tile
            entity_tile = None
            
            if entity_type == "tree":
                entity_tile = world_map.add_tree(x, y)
            elif entity_type == "house":
                entity_tile = world_map.add_house(x, y)
            else:
                print(f"Unknown entity type: {entity_type}")
                return
            
            if entity_tile:
                # Apply properties
                self._apply_entity_properties(entity_tile, properties)
                print(f"Created {entity_type} at ({x}, {y})")
            else:
                print(f"Failed to create {entity_type} at ({x}, {y})")
                
        except Exception as e:
            print(f"Error creating entity tile {entity_type} at ({x}, {y}): {e}")
    
    def _apply_entity_properties(self, entity_tile, properties: Dict[str, Any]):
        """Apply properties to an entity tile
        
        Args:
            entity_tile: The entity tile to modify
            properties: The properties to apply
        """
        for key, value in properties.items():
            if hasattr(entity_tile, key):
                try:
                    setattr(entity_tile, key, value)
                except Exception as e:
                    print(f"Warning: Could not set property {key} to {value}: {e}")
    
    def list_maps(self) -> list:
        """List all available map files
        
        Returns:
            List of map filenames (without full path)
        """
        try:
            files = []
            if os.path.exists(self.maps_directory):
                for filename in os.listdir(self.maps_directory):
                    if filename.endswith('.json'):
                        files.append(filename)
            return sorted(files)
        except Exception as e:
            print(f"Error listing maps: {e}")
            return []
    
    def delete_map(self, filename: str) -> bool:
        """Delete a map file
        
        Args:
            filename: The filename to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle filename - remove any path separators and ensure .json extension
            clean_filename = os.path.basename(filename)
            if not clean_filename.endswith('.json'):
                clean_filename += '.json'
            
            # Create full path
            full_path = os.path.join(self.maps_directory, clean_filename)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"Map deleted: {full_path}")
                return True
            else:
                print(f"Map file not found: {full_path}")
                return False
                
        except Exception as e:
            print(f"Error deleting map: {e}")
            return False
    
    def get_maps_directory(self) -> str:
        """Get the full path to the maps directory
        
        Returns:
            Full path to the maps directory
        """
        return self.maps_directory
    
    def get_map_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get information about a map file without fully loading it
        
        Args:
            filename: The map filename
            
        Returns:
            Map information dictionary or None if error
        """
        try:
            clean_filename = os.path.basename(filename)
            if not clean_filename.endswith('.json'):
                clean_filename += '.json'
            
            full_path = os.path.join(self.maps_directory, clean_filename)
            
            if not os.path.exists(full_path):
                return None
            
            with open(full_path, 'r') as f:
                map_data = json.load(f)
            
            info = {
                "filename": clean_filename,
                "version": map_data.get("version", "1.0"),
                "width": map_data.get("width", 0),
                "height": map_data.get("height", 0),
                "compressed": map_data.get("compressed", False),
                "entity_count": len(map_data.get("entity_tiles", [])),
                "file_size": os.path.getsize(full_path)
            }
            
            if "compression_stats" in map_data:
                info["compression_stats"] = map_data["compression_stats"]
            
            return info
            
        except Exception as e:
            print(f"Error getting map info: {e}")
            return None

"""
Map serialization system for saving and loading maps
Compatible with the game engine's map format with compression support
"""

import json
import os
import sys
import gzip
import base64
from typing import Dict, List, Any, Optional

# Import game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from world.map import WorldMap
from world.tile import Tile
from world.entity_tile import TreeEntityTile, HouseEntityTile

class MapSerializer:
    """Handles saving and loading of map data with compression"""
    
    def __init__(self):
        """Initialize the map serializer"""
        self.version = "1.1"  # Updated version for compression support
        print("Map serializer initialized with compression support")
    
    def save_map(self, world_map: WorldMap, filename: str, compress: bool = True):
        """Save a world map to a compressed JSON file"""
        # Ensure maps directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else "maps", exist_ok=True)
        
        # Serialize map data with compression
        if compress:
            map_data = self._create_compressed_map_data(world_map)
        else:
            map_data = self._create_uncompressed_map_data(world_map)
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(map_data, f, separators=(',', ':'))  # Compact JSON
        
        # Calculate file size
        file_size = os.path.getsize(filename)
        file_size_kb = file_size / 1024
        
        print(f"Map saved to {filename} ({file_size_kb:.1f} KB)")
    
    def _create_compressed_map_data(self, world_map: WorldMap) -> Dict[str, Any]:
        """Create compressed map data"""
        # Compress tiles using run-length encoding
        compressed_tiles = self._compress_tiles(world_map)
        
        # Serialize entity tiles normally (usually not many)
        entity_tiles = self._serialize_entity_tiles(world_map)
        
        # Serialize world items normally
        world_items = self._serialize_world_items(world_map)
        
        return {
            "version": self.version,
            "compressed": True,
            "metadata": {
                "width": world_map.width,
                "height": world_map.height,
                "tile_size": Tile.SIZE,
                "compression_method": "rle_gzip"
            },
            "tiles": compressed_tiles,
            "entity_tiles": entity_tiles,
            "world_items": world_items
        }
    
    def _create_uncompressed_map_data(self, world_map: WorldMap) -> Dict[str, Any]:
        """Create uncompressed map data (legacy format)"""
        return {
            "version": self.version,
            "compressed": False,
            "metadata": {
                "width": world_map.width,
                "height": world_map.height,
                "tile_size": Tile.SIZE
            },
            "tiles": self._serialize_tiles(world_map),
            "entity_tiles": self._serialize_entity_tiles(world_map),
            "world_items": self._serialize_world_items(world_map)
        }
    
    def _compress_tiles(self, world_map: WorldMap) -> str:
        """Compress tile data using run-length encoding + gzip"""
        # First, create a flat list of tile types
        tile_data = []
        for y in range(world_map.height):
            for x in range(world_map.width):
                tile = world_map.get_tile(x, y)
                tile_data.append(tile.type if tile else "empty")
        
        # Apply run-length encoding
        rle_data = self._run_length_encode(tile_data)
        
        # Convert to JSON string
        rle_json = json.dumps(rle_data, separators=(',', ':'))
        
        # Compress with gzip
        compressed_bytes = gzip.compress(rle_json.encode('utf-8'))
        
        # Encode as base64 for JSON storage
        compressed_b64 = base64.b64encode(compressed_bytes).decode('ascii')
        
        return compressed_b64
    
    def _run_length_encode(self, data: List[str]) -> List[List]:
        """Apply run-length encoding to tile data"""
        if not data:
            return []
        
        encoded = []
        current_tile = data[0]
        count = 1
        
        for i in range(1, len(data)):
            if data[i] == current_tile:
                count += 1
            else:
                # Add the run
                if count == 1:
                    encoded.append([current_tile])
                else:
                    encoded.append([current_tile, count])
                
                # Start new run
                current_tile = data[i]
                count = 1
        
        # Add the last run
        if count == 1:
            encoded.append([current_tile])
        else:
            encoded.append([current_tile, count])
        
        return encoded
    
    def _decompress_tiles(self, compressed_data: str, width: int, height: int) -> List[List[str]]:
        """Decompress tile data"""
        try:
            # Decode from base64
            compressed_bytes = base64.b64decode(compressed_data.encode('ascii'))
            
            # Decompress with gzip
            rle_json = gzip.decompress(compressed_bytes).decode('utf-8')
            
            # Parse JSON
            rle_data = json.loads(rle_json)
            
            # Decode run-length encoding
            flat_data = self._run_length_decode(rle_data)
            
            # Convert back to 2D array
            tiles = []
            for y in range(height):
                row = []
                for x in range(width):
                    index = y * width + x
                    if index < len(flat_data):
                        row.append(flat_data[index])
                    else:
                        row.append("empty")
                tiles.append(row)
            
            return tiles
            
        except Exception as e:
            print(f"Error decompressing tiles: {e}")
            # Return empty map as fallback
            return [["grass" for _ in range(width)] for _ in range(height)]
    
    def _run_length_decode(self, encoded_data: List[List]) -> List[str]:
        """Decode run-length encoded data"""
        decoded = []
        
        for run in encoded_data:
            if len(run) == 1:
                # Single tile
                decoded.append(run[0])
            elif len(run) == 2:
                # Run of tiles
                tile_type, count = run
                decoded.extend([tile_type] * count)
        
        return decoded
    
    def load_map(self, filename: str) -> Optional[WorldMap]:
        """Load a world map from a JSON file (supports both compressed and uncompressed)"""
        if not os.path.exists(filename):
            print(f"Map file not found: {filename}")
            return None
        
        try:
            with open(filename, 'r') as f:
                map_data = json.load(f)
            
            # Validate version
            version = map_data.get("version", "1.0")
            if version != self.version and version != "1.0":
                print(f"Warning: Map version mismatch. Expected {self.version}, got {version}")
            
            # Create world map
            metadata = map_data["metadata"]
            world_map = WorldMap(metadata["width"], metadata["height"])
            world_map.initialize_entity_tiles()
            world_map.initialize_world_items()
            
            # Load tiles (compressed or uncompressed)
            if map_data.get("compressed", False):
                print("Loading compressed map...")
                tiles_data = self._decompress_tiles(
                    map_data["tiles"], 
                    metadata["width"], 
                    metadata["height"]
                )
                self._deserialize_tiles(world_map, tiles_data)
            else:
                print("Loading uncompressed map...")
                self._deserialize_tiles(world_map, map_data["tiles"])
            
            # Load entity tiles
            if "entity_tiles" in map_data:
                self._deserialize_entity_tiles(world_map, map_data["entity_tiles"])
            
            # Load world items
            if "world_items" in map_data:
                self._deserialize_world_items(world_map, map_data["world_items"])
            
            # Calculate compression ratio if applicable
            if map_data.get("compressed", False):
                file_size = os.path.getsize(filename)
                print(f"Map loaded from {filename} ({file_size/1024:.1f} KB, compressed)")
            else:
                file_size = os.path.getsize(filename)
                print(f"Map loaded from {filename} ({file_size/1024:.1f} KB, uncompressed)")
            
            return world_map
            
        except Exception as e:
            print(f"Error loading map from {filename}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _serialize_tiles(self, world_map: WorldMap) -> List[List[str]]:
        """Serialize the tile grid (uncompressed)"""
        tiles = []
        for y in range(world_map.height):
            row = []
            for x in range(world_map.width):
                tile = world_map.get_tile(x, y)
                row.append(tile.type if tile else "empty")
            tiles.append(row)
        return tiles
    
    def _deserialize_tiles(self, world_map: WorldMap, tiles_data: List[List[str]]):
        """Deserialize the tile grid"""
        for y, row in enumerate(tiles_data):
            for x, tile_type in enumerate(row):
                if x < world_map.width and y < world_map.height:
                    world_map.set_tile(x, y, tile_type)
    
    def _serialize_entity_tiles(self, world_map: WorldMap) -> List[Dict[str, Any]]:
        """Serialize entity tiles"""
        entity_tiles = []
        
        if hasattr(world_map, 'entity_tile_manager'):
            for entity_tile in world_map.entity_tile_manager.entity_tiles:
                entity_data = {
                    "type": entity_tile.tile_type,
                    "x": entity_tile.base_x,
                    "y": entity_tile.base_y,
                    "width": entity_tile.width,
                    "height": entity_tile.height,
                    "data": entity_tile.get_save_data()
                }
                entity_tiles.append(entity_data)
        
        return entity_tiles
    
    def _deserialize_entity_tiles(self, world_map: WorldMap, entity_tiles_data: List[Dict[str, Any]]):
        """Deserialize entity tiles"""
        for entity_data in entity_tiles_data:
            entity_type = entity_data["type"]
            x = entity_data["x"]
            y = entity_data["y"]
            
            # Create the appropriate entity tile
            if entity_type == "tree":
                entity_tile = world_map.add_tree(x, y)
            elif entity_type == "house":
                entity_tile = world_map.add_house(x, y)
            else:
                print(f"Unknown entity tile type: {entity_type}")
                continue
            
            # Load additional data
            if entity_tile and "data" in entity_data:
                entity_tile.load_save_data(entity_data["data"])
    
    def _serialize_world_items(self, world_map: WorldMap) -> List[Dict[str, Any]]:
        """Serialize world items"""
        world_items = []
        
        if hasattr(world_map, 'world_item_manager'):
            for item in world_map.world_item_manager.items:
                item_data = {
                    "item_id": item.item_id,
                    "x": item.world_x,
                    "y": item.world_y,
                    "quantity": item.quantity
                }
                world_items.append(item_data)
        
        return world_items
    
    def _deserialize_world_items(self, world_map: WorldMap, world_items_data: List[Dict[str, Any]]):
        """Deserialize world items"""
        for item_data in world_items_data:
            world_map.spawn_item_at_position(
                item_data["item_id"],
                item_data["x"],
                item_data["y"],
                item_data["quantity"]
            )
    
    def get_map_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get basic information about a map file without fully loading it"""
        if not os.path.exists(filename):
            return None
        
        try:
            with open(filename, 'r') as f:
                map_data = json.load(f)
            
            metadata = map_data.get("metadata", {})
            file_size = os.path.getsize(filename)
            
            return {
                "filename": os.path.basename(filename),
                "full_path": filename,
                "width": metadata.get("width", 0),
                "height": metadata.get("height", 0),
                "tile_size": metadata.get("tile_size", 16),
                "version": map_data.get("version", "1.0"),
                "compressed": map_data.get("compressed", False),
                "file_size_kb": file_size / 1024,
                "entity_count": len(map_data.get("entity_tiles", [])),
                "item_count": len(map_data.get("world_items", []))
            }
            
        except Exception as e:
            print(f"Error reading map info from {filename}: {e}")
            return None

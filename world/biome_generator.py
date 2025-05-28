"""
Professional 2D Procedural Map Generator using Wave Function Collapse principles
"""
import random
import math
import numpy as np
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from enum import Enum

class BiomeType(Enum):
    OCEAN = "ocean"
    LAKE = "lake"
    RIVER = "river"
    BEACH = "beach"
    PLAINS = "plains"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    SNOW = "snow"
    SWAMP = "swamp"

@dataclass
class BiomeRule:
    """Defines adjacency rules and tile mappings for biomes"""
    primary_tile: str
    secondary_tiles: List[str]
    allowed_neighbors: Set[BiomeType]
    elevation_range: Tuple[float, float]  # min, max elevation
    moisture_range: Tuple[float, float]   # min, max moisture
    temperature_range: Tuple[float, float] # min, max temperature
    min_region_size: int = 4
    
class ProceduralMapGenerator:
    """High-quality 2D procedural map generator"""
    
    def __init__(self, width: int, height: int, seed: int = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 999999)
        
        # Initialize noise parameters
        self.elevation_scale = 0.02
        self.moisture_scale = 0.03
        self.temperature_scale = 0.025
        
        # Biome definitions with realistic adjacency rules
        self.biome_rules = {
            BiomeType.OCEAN: BiomeRule(
                "deep_water", ["shallow_water"],
                {BiomeType.OCEAN, BiomeType.BEACH, BiomeType.LAKE},
                (-1.0, 0.2), (0.8, 1.0), (0.3, 0.8), 20
            ),
            BiomeType.LAKE: BiomeRule(
                "shallow_water", ["deep_water"],
                {BiomeType.LAKE, BiomeType.BEACH, BiomeType.PLAINS, BiomeType.FOREST, BiomeType.SWAMP},
                (0.1, 0.4), (0.7, 1.0), (0.2, 0.9), 6
            ),
            BiomeType.BEACH: BiomeRule(
                "sand", [],
                {BiomeType.OCEAN, BiomeType.LAKE, BiomeType.PLAINS, BiomeType.DESERT},
                (0.15, 0.35), (0.4, 0.8), (0.4, 0.9), 3
            ),
            BiomeType.PLAINS: BiomeRule(
                "grass", ["path"],
                {BiomeType.PLAINS, BiomeType.FOREST, BiomeType.BEACH, BiomeType.DESERT, BiomeType.MOUNTAIN},
                (0.2, 0.6), (0.3, 0.7), (0.3, 0.8), 8
            ),
            BiomeType.FOREST: BiomeRule(
                "forest", ["grass"],
                {BiomeType.FOREST, BiomeType.PLAINS, BiomeType.MOUNTAIN, BiomeType.SWAMP, BiomeType.LAKE},
                (0.3, 0.7), (0.5, 0.9), (0.2, 0.7), 12
            ),
            BiomeType.MOUNTAIN: BiomeRule(
                "mountain", ["rock"],
                {BiomeType.MOUNTAIN, BiomeType.FOREST, BiomeType.PLAINS, BiomeType.SNOW},
                (0.6, 1.0), (0.2, 0.6), (0.0, 0.6), 8
            ),
            BiomeType.DESERT: BiomeRule(
                "sand", ["rock"],
                {BiomeType.DESERT, BiomeType.PLAINS, BiomeType.BEACH},
                (0.2, 0.5), (0.0, 0.3), (0.6, 1.0), 10
            ),
            BiomeType.SNOW: BiomeRule(
                "snow", ["mountain"],
                {BiomeType.SNOW, BiomeType.MOUNTAIN},
                (0.7, 1.0), (0.3, 0.8), (0.0, 0.3), 6
            ),
            BiomeType.SWAMP: BiomeRule(
                "shallow_water", ["grass"],
                {BiomeType.SWAMP, BiomeType.FOREST, BiomeType.LAKE},
                (0.1, 0.3), (0.8, 1.0), (0.4, 0.8), 5
            )
        }
        
    def generate_map(self) -> Tuple[List[List[str]], Dict]:
        """Generate a complete map with biomes and return tile grid + metadata"""
        print(f"Generating map with seed {self.seed}")
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        # Step 1: Generate base noise maps
        elevation_map = self._generate_noise_map(self.elevation_scale, octaves=6)
        moisture_map = self._generate_noise_map(self.moisture_scale, octaves=4, offset=1000)
        temperature_map = self._generate_noise_map(self.temperature_scale, octaves=3, offset=2000)
        
        # Step 2: Create biome map based on environmental factors
        biome_map = self._generate_biome_map(elevation_map, moisture_map, temperature_map)
        
        # Step 3: Apply WFC-style constraints to ensure coherent regions
        biome_map = self._apply_coherence_constraints(biome_map)
        
        # Step 4: Convert biomes to actual tiles
        tile_map = self._biomes_to_tiles(biome_map, elevation_map, moisture_map)
        
        # Step 5: Add natural features (rivers, paths, etc.)
        tile_map = self._add_natural_features(tile_map, elevation_map, biome_map)
        
        # Generate metadata for debugging
        metadata = {
            'seed': self.seed,
            'biome_distribution': self._calculate_biome_distribution(biome_map),
            'elevation_map': elevation_map,
            'moisture_map': moisture_map,
            'temperature_map': temperature_map,
            'biome_map': biome_map
        }
        
        return tile_map, metadata
    
    def _generate_noise_map(self, scale: float, octaves: int = 4, offset: int = 0) -> np.ndarray:
        """Generate Perlin-like noise using multiple octaves"""
        noise_map = np.zeros((self.height, self.width))
        
        for octave in range(octaves):
            frequency = scale * (2 ** octave)
            amplitude = 1.0 / (2 ** octave)
            
            for y in range(self.height):
                for x in range(self.width):
                    # Simple noise function - replace with proper Perlin if available
                    sample_x = (x + offset) * frequency
                    sample_y = (y + offset) * frequency
                    
                    # Pseudo-random noise based on coordinates and seed
                    noise_value = self._pseudo_noise(sample_x, sample_y, self.seed + octave)
                    noise_map[y, x] += noise_value * amplitude
        
        # Normalize to [0, 1]
        noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
        return noise_map
    
    def _pseudo_noise(self, x: float, y: float, seed: int) -> float:
        """Simple pseudo-random noise function"""
        # Hash the coordinates with the seed
        n = int(x * 374761393 + y * 668265263 + seed * 1013904223)
        n = (n << 13) ^ n
        return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)
    
    def _generate_biome_map(self, elevation: np.ndarray, moisture: np.ndarray, temperature: np.ndarray) -> np.ndarray:
        """Generate biome assignments based on environmental factors"""
        biome_map = np.full((self.height, self.width), BiomeType.PLAINS, dtype=object)
        
        for y in range(self.height):
            for x in range(self.width):
                e, m, t = elevation[y, x], moisture[y, x], temperature[y, x]
                
                # Determine biome based on environmental factors
                if e < 0.2:  # Low elevation
                    if m > 0.7:
                        biome_map[y, x] = BiomeType.OCEAN if e < 0.1 else BiomeType.LAKE
                    else:
                        biome_map[y, x] = BiomeType.BEACH
                elif e > 0.8:  # High elevation
                    if t < 0.3:
                        biome_map[y, x] = BiomeType.SNOW
                    else:
                        biome_map[y, x] = BiomeType.MOUNTAIN
                else:  # Medium elevation
                    if m < 0.2 and t > 0.6:
                        biome_map[y, x] = BiomeType.DESERT
                    elif m > 0.8 and t > 0.4:
                        biome_map[y, x] = BiomeType.SWAMP
                    elif m > 0.5 and t < 0.7:
                        biome_map[y, x] = BiomeType.FOREST
                    else:
                        biome_map[y, x] = BiomeType.PLAINS
        
        return biome_map
    
    def _apply_coherence_constraints(self, biome_map: np.ndarray) -> np.ndarray:
        """Apply WFC-style constraints to ensure coherent biome regions"""
        # Multiple passes to smooth and enforce constraints
        for iteration in range(3):
            new_biome_map = biome_map.copy()
            
            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    current_biome = biome_map[y, x]
                    neighbors = self._get_neighbors(biome_map, x, y)
                    
                    # Check if current biome violates adjacency rules
                    allowed_neighbors = self.biome_rules[current_biome].allowed_neighbors
                    invalid_neighbors = [n for n in neighbors if n not in allowed_neighbors]
                    
                    # If too many invalid neighbors, change to most common valid neighbor
                    if len(invalid_neighbors) > len(neighbors) // 2:
                        valid_neighbors = [n for n in neighbors if n in allowed_neighbors]
                        if valid_neighbors:
                            new_biome_map[y, x] = max(set(valid_neighbors), key=valid_neighbors.count)
            
            biome_map = new_biome_map
        
        # Enforce minimum region sizes
        biome_map = self._enforce_minimum_regions(biome_map)
        
        return biome_map
    
    def _get_neighbors(self, biome_map: np.ndarray, x: int, y: int) -> List[BiomeType]:
        """Get neighboring biomes (8-directional)"""
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append(biome_map[ny, nx])
        return neighbors
    
    def _enforce_minimum_regions(self, biome_map: np.ndarray) -> np.ndarray:
        """Remove small isolated regions that are below minimum size"""
        visited = np.zeros((self.height, self.width), dtype=bool)
        
        for y in range(self.height):
            for x in range(self.width):
                if not visited[y, x]:
                    biome = biome_map[y, x]
                    region = self._flood_fill_region(biome_map, x, y, biome, visited)
                    
                    min_size = self.biome_rules[biome].min_region_size
                    if len(region) < min_size:
                        # Replace small region with most common neighboring biome
                        replacement_biome = self._find_replacement_biome(biome_map, region, biome)
                        for rx, ry in region:
                            biome_map[ry, rx] = replacement_biome
        
        return biome_map
    
    def _flood_fill_region(self, biome_map: np.ndarray, start_x: int, start_y: int, 
                          target_biome: BiomeType, visited: np.ndarray) -> List[Tuple[int, int]]:
        """Flood fill to find connected region of same biome"""
        stack = [(start_x, start_y)]
        region = []
        
        while stack:
            x, y = stack.pop()
            if (x < 0 or x >= self.width or y < 0 or y >= self.height or 
                visited[y, x] or biome_map[y, x] != target_biome):
                continue
            
            visited[y, x] = True
            region.append((x, y))
            
            # Add 4-directional neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                stack.append((x + dx, y + dy))
        
        return region
    
    def _find_replacement_biome(self, biome_map: np.ndarray, region: List[Tuple[int, int]], 
                               current_biome: BiomeType) -> BiomeType:
        """Find the most appropriate replacement biome for a small region"""
        neighbor_biomes = []
        
        for x, y in region:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    biome_map[ny, nx] != current_biome):
                    neighbor_biomes.append(biome_map[ny, nx])
        
        if neighbor_biomes:
            return max(set(neighbor_biomes), key=neighbor_biomes.count)
        return BiomeType.PLAINS  # Fallback
    
    def _biomes_to_tiles(self, biome_map: np.ndarray, elevation: np.ndarray, 
                        moisture: np.ndarray) -> List[List[str]]:
        """Convert biome map to actual tile types"""
        tile_map = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        
        for y in range(self.height):
            for x in range(self.width):
                biome = biome_map[y, x]
                rule = self.biome_rules[biome]
                
                # Choose primary or secondary tile based on local variation
                if rule.secondary_tiles and random.random() < 0.2:
                    tile_type = random.choice(rule.secondary_tiles)
                else:
                    tile_type = rule.primary_tile
                
                tile_map[y][x] = tile_type
        
        return tile_map
    
    def _add_natural_features(self, tile_map: List[List[str]], elevation: np.ndarray, 
                             biome_map: np.ndarray) -> List[List[str]]:
        """Add rivers, paths, and other natural features"""
        # Add rivers from mountains to water
        self._add_rivers(tile_map, elevation, biome_map)
        
        # Add border walls
        self._add_border_walls(tile_map)
        
        return tile_map
    
    def _add_rivers(self, tile_map: List[List[str]], elevation: np.ndarray, 
                   biome_map: np.ndarray):
        """Add realistic rivers flowing from high to low elevation"""
        num_rivers = max(2, min(8, self.width * self.height // 10000))
        
        for _ in range(num_rivers):
            # Find a mountain start point
            start_points = []
            for y in range(self.height):
                for x in range(self.width):
                    if (biome_map[y, x] == BiomeType.MOUNTAIN and 
                        elevation[y, x] > 0.7):
                        start_points.append((x, y))
            
            if not start_points:
                continue
                
            start_x, start_y = random.choice(start_points)
            river_path = self._trace_river_path(start_x, start_y, elevation, biome_map)
            
            # Apply river to tile map
            for x, y in river_path:
                if (0 <= x < self.width and 0 <= y < self.height and
                    biome_map[y, x] not in [BiomeType.OCEAN, BiomeType.LAKE]):
                    tile_map[y][x] = "shallow_water"
    
    def _trace_river_path(self, start_x: int, start_y: int, elevation: np.ndarray,
                         biome_map: np.ndarray) -> List[Tuple[int, int]]:
        """Trace a river path from start point to water or edge"""
        path = [(start_x, start_y)]
        x, y = start_x, start_y
        
        for _ in range(min(self.width, self.height)):
            # Find lowest neighboring point
            best_neighbor = None
            lowest_elevation = elevation[y, x]
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    (nx, ny) not in path):
                    neighbor_elevation = elevation[ny, nx]
                    if neighbor_elevation < lowest_elevation:
                        lowest_elevation = neighbor_elevation
                        best_neighbor = (nx, ny)
            
            if best_neighbor is None:
                break
                
            x, y = best_neighbor
            path.append((x, y))
            
            # Stop if we reach water
            if biome_map[y, x] in [BiomeType.OCEAN, BiomeType.LAKE]:
                break
        
        return path
    
    def _add_border_walls(self, tile_map: List[List[str]]):
        """Add walls around the map border"""
        for x in range(self.width):
            tile_map[0][x] = "wall"
            tile_map[self.height - 1][x] = "wall"
        
        for y in range(self.height):
            tile_map[y][0] = "wall"
            tile_map[y][self.width - 1] = "wall"
    
    def _calculate_biome_distribution(self, biome_map: np.ndarray) -> Dict[str, float]:
        """Calculate percentage distribution of biomes for debugging"""
        total_tiles = self.width * self.height
        distribution = {}
        
        for biome_type in BiomeType:
            count = np.sum(biome_map == biome_type)
            distribution[biome_type.value] = (count / total_tiles) * 100
        
        return distribution

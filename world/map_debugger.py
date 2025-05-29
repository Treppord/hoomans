"""
Map Generation Debugger and Visualizer
"""
import pygame
import numpy as np
from typing import Dict, List, Tuple, Any
from world.biome_generator import BiomeType

class MapDebugger:
    """Visualize and debug procedural map generation"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tile_size = 4  # Small tiles for overview
        
        # Color schemes for different visualizations
        self.biome_colors = {
            BiomeType.OCEAN: (0, 50, 100),
            BiomeType.LAKE: (50, 100, 150),
            BiomeType.RIVER: (100, 150, 200),
            BiomeType.BEACH: (194, 178, 128),
            BiomeType.PLAINS: (100, 150, 50),
            BiomeType.FOREST: (50, 100, 50),
            BiomeType.MOUNTAIN: (120, 100, 80),
            BiomeType.DESERT: (200, 180, 100),
            BiomeType.SNOW: (240, 240, 240),
            BiomeType.SWAMP: (80, 120, 80)
        }
        
        self.elevation_colors = {
            'low': (0, 0, 100),
            'medium': (100, 100, 0),
            'high': (200, 200, 200)
        }
    
    def create_debug_surface(self, metadata: Dict[str, Any]) -> pygame.Surface:
        """Create a debug visualization surface"""
        debug_width = self.width * self.tile_size * 3  # Three panels side by side
        debug_height = self.height * self.tile_size
        
        surface = pygame.Surface((debug_width, debug_height))
        surface.fill((20, 20, 20))
        
        # Panel 1: Biome map
        biome_surface = self._create_biome_visualization(metadata['biome_map'])
        surface.blit(biome_surface, (0, 0))
        
        # Panel 2: Elevation map
        elevation_surface = self._create_elevation_visualization(metadata['elevation_map'])
        surface.blit(elevation_surface, (self.width * self.tile_size, 0))
        
        # Panel 3: Moisture map
        moisture_surface = self._create_moisture_visualization(metadata['moisture_map'])
        surface.blit(moisture_surface, (self.width * self.tile_size * 2, 0))
        
        return surface
    
    def _create_biome_visualization(self, biome_map: np.ndarray) -> pygame.Surface:
        """Create biome map visualization"""
        surface = pygame.Surface((self.width * self.tile_size, self.height * self.tile_size))
        
        for y in range(self.height):
            for x in range(self.width):
                biome = biome_map[y, x]
                color = self.biome_colors.get(biome, (255, 0, 255))  # Magenta for unknown
                
                rect = pygame.Rect(
                    x * self.tile_size, 
                    y * self.tile_size, 
                    self.tile_size, 
                    self.tile_size
                )
                pygame.draw.rect(surface, color, rect)
        
        return surface
    
    def _create_elevation_visualization(self, elevation_map: np.ndarray) -> pygame.Surface:
        """Create elevation map visualization"""
        surface = pygame.Surface((self.width * self.tile_size, self.height * self.tile_size))
        
        for y in range(self.height):
            for x in range(self.width):
                elevation = elevation_map[y, x]
                # Convert elevation to grayscale
                gray_value = int(elevation * 255)
                color = (gray_value, gray_value, gray_value)
                
                rect = pygame.Rect(
                    x * self.tile_size, 
                    y * self.tile_size, 
                    self.tile_size, 
                    self.tile_size
                )
                pygame.draw.rect(surface, color, rect)
        
        return surface
    
    def _create_moisture_visualization(self, moisture_map: np.ndarray) -> pygame.Surface:
        """Create moisture map visualization"""
        surface = pygame.Surface((self.width * self.tile_size, self.height * self.tile_size))
        
        for y in range(self.height):
            for x in range(self.width):
                moisture = moisture_map[y, x]
                # Blue gradient for moisture
                blue_value = int(moisture * 255)
                color = (0, 0, blue_value)
                
                rect = pygame.Rect(
                    x * self.tile_size, 
                    y * self.tile_size, 
                    self.tile_size, 
                    self.tile_size
                )
                pygame.draw.rect(surface, color, rect)
        
        return surface
    
    
        
            
    def print_generation_stats(self, metadata: Dict[str, Any]):
        """Print detailed generation statistics"""
        print(f"\n=== Map Generation Stats (Seed: {metadata['seed']}) ===")
        print(f"Map Size: {self.width}x{self.height}")
        
        print("\nBiome Distribution:")
        for biome, percentage in metadata['biome_distribution'].items():
            print(f"  {biome.capitalize()}: {percentage:.1f}%")
        
        # NEW: Add patch analysis
        patch_stats = self._analyze_patches(metadata['biome_map'])
        print(f"\nPatch Analysis:")
        print(f"  Average patch size: {patch_stats['avg_patch_size']:.1f} tiles")
        print(f"  Largest patch: {patch_stats['largest_patch']} tiles")
        print(f"  Total patches: {patch_stats['total_patches']}")
        
        print(f"\nGeneration completed successfully!")

    def _analyze_patches(self, biome_map):
        """Analyze patch sizes and distribution"""
        visited = np.zeros((self.height, self.width), dtype=bool)
        patch_sizes = []
        
        for y in range(self.height):
            for x in range(self.width):
                if not visited[y, x]:
                    biome = biome_map[y, x]
                    patch_size = self._measure_patch_size(biome_map, x, y, biome, visited)
                    patch_sizes.append(patch_size)
        
        return {
            'avg_patch_size': np.mean(patch_sizes) if patch_sizes else 0,
            'largest_patch': max(patch_sizes) if patch_sizes else 0,
            'total_patches': len(patch_sizes)
        }

    def _measure_patch_size(self, biome_map, start_x, start_y, target_biome, visited):
        """Measure the size of a connected patch"""
        stack = [(start_x, start_y)]
        size = 0
        
        while stack:
            x, y = stack.pop()
            if (x < 0 or x >= self.width or y < 0 or y >= self.height or 
                visited[y, x] or biome_map[y, x] != target_biome):
                continue
            
            visited[y, x] = True
            size += 1
            
            # Add 4-directional neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                stack.append((x + dx, y + dy))
        
        return size

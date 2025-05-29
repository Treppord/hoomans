"""
Aseprite integration for the map editor
Provides API access to Aseprite for advanced tile editing
"""

import subprocess
import json
import os
import tempfile
import pygame
from typing import Dict, List, Optional, Tuple

class AsepriteIntegration:
    """Handles integration with Aseprite for tile editing"""
    
    def __init__(self, aseprite_path: str):
        """Initialize Aseprite integration"""
        self.aseprite_path = aseprite_path
        self.is_available = self._check_aseprite_availability()
        
        # Temporary directory for Aseprite files
        self.temp_dir = tempfile.mkdtemp(prefix="hoomans_map_editor_")
        
        # Tile cache
        self.tile_cache = {}
        
        if self.is_available:
            print(f"Aseprite integration initialized: {aseprite_path}")
        else:
            print(f"Aseprite not available at: {aseprite_path}")
    
    def _check_aseprite_availability(self) -> bool:
        """Check if Aseprite is available and working"""
        try:
            result = subprocess.run([self.aseprite_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"Aseprite check failed: {e}")
            return False
    
    def create_tile_template(self, tile_size: int = 16) -> str:
        """Create a new tile template in Aseprite"""
        if not self.is_available:
            return None
        
        template_file = os.path.join(self.temp_dir, f"tile_template_{tile_size}x{tile_size}.aseprite")
        
        try:
            # Create a new Aseprite file with the specified tile size
            cmd = [
                self.aseprite_path,
                "--batch",
                "--new",
                f"--width={tile_size}",
                f"--height={tile_size}",
                "--save-as", template_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(template_file):
                print(f"Created tile template: {template_file}")
                return template_file
            else:
                print(f"Failed to create tile template: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error creating tile template: {e}")
            return None
    
    def edit_tile(self, tile_type: str, existing_image: Optional[pygame.Surface] = None) -> Optional[pygame.Surface]:
        """Open Aseprite to edit a tile"""
        if not self.is_available:
            return existing_image
        
        # Create temporary file for the tile
        tile_file = os.path.join(self.temp_dir, f"edit_tile_{tile_type}.png")
        
        try:
            # Save existing image if provided
            if existing_image:
                pygame.image.save(existing_image, tile_file)
            else:
                # Create a blank tile
                blank_tile = pygame.Surface((16, 16), pygame.SRCALPHA)
                blank_tile.fill((0, 0, 0, 0))
                pygame.image.save(blank_tile, tile_file)
            
            # Open Aseprite with the tile
            cmd = [self.aseprite_path, tile_file]
            
            print(f"Opening Aseprite for tile editing: {tile_type}")
            print("Close Aseprite when finished editing...")
            
            # Launch Aseprite and wait for it to close
            process = subprocess.Popen(cmd)
            process.wait()
            
            # Load the edited tile
            if os.path.exists(tile_file):
                try:
                    edited_tile = pygame.image.load(tile_file).convert_alpha()
                    print(f"Tile edited successfully: {tile_type}")
                    return edited_tile
                except Exception as e:
                    print(f"Error loading edited tile: {e}")
                    return existing_image
            else:
                print("Tile file not found after editing")
                return existing_image
                
        except Exception as e:
            print(f"Error editing tile in Aseprite: {e}")
            return existing_image
    
    def create_tileset(self, tile_types: List[str], tile_size: int = 16) -> Optional[str]:
        """Create a tileset in Aseprite with multiple tiles"""
        if not self.is_available:
            return None
        
        # Calculate tileset dimensions
        tiles_per_row = 8
        rows = (len(tile_types) + tiles_per_row - 1) // tiles_per_row
        
        tileset_width = tiles_per_row * tile_size
        tileset_height = rows * tile_size
        
        tileset_file = os.path.join(self.temp_dir, "custom_tileset.aseprite")
        
        try:
            # Create new tileset file
            cmd = [
                self.aseprite_path,
                "--batch",
                "--new",
                f"--width={tileset_width}",
                f"--height={tileset_height}",
                "--save-as", tileset_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"Created tileset template: {tileset_file}")
                
                # Open for editing
                subprocess.Popen([self.aseprite_path, tileset_file])
                
                return tileset_file
            else:
                print(f"Failed to create tileset: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error creating tileset: {e}")
            return None
    
    def export_tileset(self, aseprite_file: str, output_dir: str) -> List[str]:
        """Export individual tiles from an Aseprite tileset"""
        if not self.is_available or not os.path.exists(aseprite_file):
            return []
        
        exported_files = []
        
        try:
            # Export as sprite sheet
            sprite_sheet = os.path.join(output_dir, "tileset_export.png")
            
            cmd = [
                self.aseprite_path,
                "--batch",
                aseprite_file,
                "--save-as", sprite_sheet
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(sprite_sheet):
                print(f"Exported tileset: {sprite_sheet}")
                exported_files.append(sprite_sheet)
            
            return exported_files
            
        except Exception as e:
            print(f"Error exporting tileset: {e}")
            return []
    
    def get_tile_from_aseprite(self, aseprite_file: str, tile_index: int, tile_size: int = 16) -> Optional[pygame.Surface]:
        """Extract a specific tile from an Aseprite file"""
        if not self.is_available:
            return None
        
        # Export the file as PNG first
        temp_png = os.path.join(self.temp_dir, f"temp_export_{tile_index}.png")
        
        try:
            cmd = [
                self.aseprite_path,
                "--batch",
                aseprite_file,
                "--save-as", temp_png
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_png):
                # Load the exported image
                full_image = pygame.image.load(temp_png).convert_alpha()
                
                # Calculate tile position
                tiles_per_row = full_image.get_width() // tile_size
                tile_x = (tile_index % tiles_per_row) * tile_size
                tile_y = (tile_index // tiles_per_row) * tile_size
                
                # Extract the tile
                tile_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                tile_surface.blit(full_image, (0, 0), (tile_x, tile_y, tile_size, tile_size))
                
                # Clean up temp file
                os.remove(temp_png)
                
                return tile_surface
            
        except Exception as e:
            print(f"Error extracting tile from Aseprite: {e}")
        
        return None
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("Aseprite integration cleanup complete")
        except Exception as e:
            print(f"Error during Aseprite cleanup: {e}")

"""
Aseprite integration for the map editor
Provides interface to Aseprite for advanced tile editing
"""

import os
import subprocess
from typing import Optional, List, Dict, Any

class AsepriteIntegration:
    """Integration with Aseprite for advanced tile editing"""
    
    def __init__(self, aseprite_path: str):
        """Initialize Aseprite integration
        
        Args:
            aseprite_path: Path to the Aseprite executable
        """
        self.aseprite_path = aseprite_path
        self.is_available = self._check_aseprite_availability()
        
        if self.is_available:
            print(f"Aseprite integration initialized: {aseprite_path}")
        else:
            print(f"Aseprite not available at: {aseprite_path}")
    
    def _check_aseprite_availability(self) -> bool:
        """Check if Aseprite is available at the specified path"""
        try:
            if not os.path.exists(self.aseprite_path):
                return False
            
            # Try to run Aseprite with --version flag
            result = subprocess.run([self.aseprite_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"Error checking Aseprite availability: {e}")
            return False
    
    def open_tileset(self, tileset_path: str) -> bool:
        """Open a tileset in Aseprite for editing
        
        Args:
            tileset_path: Path to the tileset file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            print("Aseprite is not available")
            return False
        
        try:
            subprocess.Popen([self.aseprite_path, tileset_path])
            print(f"Opened tileset in Aseprite: {tileset_path}")
            return True
        except Exception as e:
            print(f"Error opening tileset in Aseprite: {e}")
            return False
    
    def export_tileset(self, source_path: str, output_path: str, 
                      tile_width: int = 16, tile_height: int = 16) -> bool:
        """Export a tileset from Aseprite
        
        Args:
            source_path: Path to the source Aseprite file
            output_path: Path to export the tileset to
            tile_width: Width of each tile
            tile_height: Height of each tile
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            print("Aseprite is not available")
            return False
        
        try:
            cmd = [
                self.aseprite_path,
                "--batch",
                source_path,
                "--save-as", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"Exported tileset: {output_path}")
                return True
            else:
                print(f"Error exporting tileset: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error exporting tileset: {e}")
            return False
    
    def get_available_tilesets(self, tilesets_dir: str) -> List[str]:
        """Get list of available Aseprite tileset files
        
        Args:
            tilesets_dir: Directory to search for tilesets
            
        Returns:
            List of tileset file paths
        """
        tilesets = []
        
        if not os.path.exists(tilesets_dir):
            return tilesets
        
        try:
            for filename in os.listdir(tilesets_dir):
                if filename.endswith(('.ase', '.aseprite')):
                    tilesets.append(os.path.join(tilesets_dir, filename))
        except Exception as e:
            print(f"Error listing tilesets: {e}")
        
        return sorted(tilesets)
    
    def cleanup(self):
        """Clean up Aseprite integration resources"""
        # Nothing to clean up for now
        pass

"""
Map Creator Tool for Hoomans Game Engine
A visual map editor using Aseprite API integration

This tool allows developers to:
- Visually design maps using tiles
- Place entity tiles (trees, houses, etc.)
- Design terrain and biomes
- Save maps compatible with the game engine
"""

import sys
import os
import pygame
import json
from typing import Dict, List, Tuple, Optional, Any

# Add the parent directory to the path so we can import game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.map_editor.editor_core import MapEditor
from tools.map_editor.aseprite_integration import AsepriteIntegration
from tools.map_editor.tile_palette import TilePalette
from tools.map_editor.map_serializer import MapSerializer
from config.game_args import GameArgumentParser

class MapCreatorTool:
    """Main map creator application"""
    
    def __init__(self):
        """Initialize the map creator tool"""
        self.running = False
        self.editor = None
        self.aseprite = None
        
        # Parse command line arguments
        self.args = self._parse_arguments()
        
        # Initialize pygame
        pygame.init()
        
        # Set up display
        self.screen = pygame.display.set_mode((self.args.width, self.args.height))
        pygame.display.set_caption("Hoomans Map Creator")
        self.clock = pygame.time.Clock()
        
        print("Map Creator Tool initialized")
        print(f"Display: {self.args.width}x{self.args.height}")
    
    def _parse_arguments(self):
        """Parse command line arguments specific to the map creator"""
        parser = GameArgumentParser()
        
        # Add map creator specific arguments
        creator_group = parser.parser.add_argument_group('Map Creator Options')
        creator_group.add_argument(
            '--map-width',
            type=int,
            default=64,
            help='Width of the map in tiles (default: 64)'
        )
        creator_group.add_argument(
            '--map-height',
            type=int,
            default=64,
            help='Height of the map in tiles (default: 64)'
        )
        creator_group.add_argument(
            '--tile-size',
            type=int,
            default=16,
            help='Size of each tile in pixels (default: 16)'
        )
        creator_group.add_argument(
            '--load-map',
            type=str,
            help='Load an existing map file'
        )
        creator_group.add_argument(
            '--aseprite-path',
            type=str,
            help='Path to Aseprite executable for integration'
        )
        
        return parser.parse_args()
    
    def initialize(self):
        """Initialize all components of the map creator"""
        try:
            # Initialize Aseprite integration
            if self.args.aseprite_path:
                print(f"Initializing Aseprite integration: {self.args.aseprite_path}")
                self.aseprite = AsepriteIntegration(self.args.aseprite_path)
            else:
                print("No Aseprite path provided, using built-in tile system")
                self.aseprite = None
            
            # Initialize the map editor core
            print("Initializing map editor...")
            self.editor = MapEditor(
                map_width=self.args.map_width,
                map_height=self.args.map_height,
                tile_size=self.args.tile_size,
                screen_width=self.args.width,
                screen_height=self.args.height,
                aseprite_integration=self.aseprite
            )
            
            # Load existing map if specified
            if self.args.load_map:
                print(f"Loading map: {self.args.load_map}")
                self.editor.load_map(self.args.load_map)
            
            print("Map Creator initialization complete")
            return True
            
        except Exception as e:
            print(f"Error initializing Map Creator: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """Main application loop"""
        if not self.initialize():
            print("Failed to initialize Map Creator")
            return
        
        self.running = True
        print("Starting Map Creator...")
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                        # Ctrl+S to save
                        self.editor.save_map()
                    elif event.key == pygame.K_o and pygame.key.get_pressed()[pygame.K_LCTRL]:
                        # Ctrl+O to open
                        self.editor.open_map_dialog()
                    elif event.key == pygame.K_n and pygame.key.get_pressed()[pygame.K_LCTRL]:
                        # Ctrl+N for new map
                        self.editor.new_map()
                
                # Pass event to editor
                if self.editor:
                    self.editor.handle_event(event)
            
            # Update
            if self.editor:
                self.editor.update()
            
            # Render
            self.screen.fill((40, 40, 40))  # Dark gray background
            
            if self.editor:
                self.editor.render(self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up Map Creator...")
        
        if self.aseprite:
            self.aseprite.cleanup()
        
        pygame.quit()
        print("Map Creator shutdown complete")

def main():
    """Main entry point for the map creator tool"""
    print("=== Hoomans Map Creator Tool ===")
    
    try:
        tool = MapCreatorTool()
        tool.run()
    except KeyboardInterrupt:
        print("\nMap Creator interrupted by user")
    except Exception as e:
        print(f"Fatal error in Map Creator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
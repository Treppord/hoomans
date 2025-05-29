"""
Core map editor functionality
Handles the main editing logic, tool management, and map manipulation
"""

import pygame
import os
import sys
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

# Import game engine modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from world.tile import Tile
from world.map import WorldMap
from world.entity_tile import EntityTileManager, TreeEntityTile, HouseEntityTile
from world.world_item import WorldItemManager
from tools.map_editor.tile_palette import TilePalette
from tools.map_editor.entity_palette import EntityPalette
from tools.map_editor.map_serializer import MapSerializer
from tools.map_editor.editor_camera import EditorCamera

class EditorTool(Enum):
    """Available editing tools"""
    TILE_BRUSH = "tile_brush"
    ENTITY_PLACER = "entity_placer"
    ERASER = "eraser"
    SELECTOR = "selector"
    FILL = "fill"

class MapEditor:
    """Core map editor class"""
    
    def __init__(self, map_width: int, map_height: int, tile_size: int, 
                 screen_width: int, screen_height: int, aseprite_integration=None):
        """Initialize the map editor"""
        self.map_width = map_width
        self.map_height = map_height
        self.tile_size = tile_size
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Initialize the world map
        self.world_map = WorldMap(map_width, map_height)
        self.world_map.initialize_entity_tiles()
        self.world_map.initialize_world_items()
        
        # Initialize camera
        self.camera = EditorCamera(screen_width, screen_height)
        
        # Initialize palettes
        self.tile_palette = TilePalette(aseprite_integration)
        self.entity_palette = EntityPalette()
        
        # Initialize serializer
        self.serializer = MapSerializer()
        
        # Editor state
        self.current_tool = EditorTool.TILE_BRUSH
        self.selected_tile_type = "grass"
        self.selected_entity_type = "tree"
        self.is_painting = False
        self.last_painted_pos = None
        
        # UI state
        self.show_grid = True
        self.show_palette = True
        self.palette_width = 200
        
        # Initialize with a basic grass map
        self._initialize_default_map()
        
        print(f"Map Editor initialized: {map_width}x{map_height} tiles")
    
    def _initialize_default_map(self):
        """Initialize the map with default grass tiles"""
        for y in range(self.map_height):
            for x in range(self.map_width):
                self.world_map.set_tile(x, y, "grass")
    
    def handle_event(self, event):
        """Handle input events"""
        # Handle camera events first
        if self.camera.handle_event(event):
            return True
        
        # Handle tool selection
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.current_tool = EditorTool.TILE_BRUSH
                print("Selected: Tile Brush")
            elif event.key == pygame.K_2:
                self.current_tool = EditorTool.ENTITY_PLACER
                print("Selected: Entity Placer")
            elif event.key == pygame.K_3:
                self.current_tool = EditorTool.ERASER
                print("Selected: Eraser")
            elif event.key == pygame.K_4:
                self.current_tool = EditorTool.SELECTOR
                print("Selected: Selector")
            elif event.key == pygame.K_5:
                self.current_tool = EditorTool.FILL
                print("Selected: Fill Tool")
            elif event.key == pygame.K_g:
                self.show_grid = not self.show_grid
                print(f"Grid: {'ON' if self.show_grid else 'OFF'}")
            elif event.key == pygame.K_p:
                self.show_palette = not self.show_palette
                print(f"Palette: {'ON' if self.show_palette else 'OFF'}")
        
        # Handle mouse events
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.is_painting = True
                self._handle_paint_action(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_painting = False
                self.last_painted_pos = None
        elif event.type == pygame.MOUSEMOTION:
            if self.is_painting:
                self._handle_paint_action(event.pos)
        
        # Handle palette events
        if self.show_palette:
            palette_rect = pygame.Rect(self.screen_width - self.palette_width, 0, 
                                     self.palette_width, self.screen_height)
            if palette_rect.collidepoint(pygame.mouse.get_pos()):
                if self.current_tool == EditorTool.TILE_BRUSH:
                    selected_tile = self.tile_palette.handle_event(event, palette_rect)
                    if selected_tile:
                        self.selected_tile_type = selected_tile
                        print(f"Selected tile: {selected_tile}")
                elif self.current_tool == EditorTool.ENTITY_PLACER:
                    selected_entity = self.entity_palette.handle_event(event, palette_rect)
                    if selected_entity:
                        self.selected_entity_type = selected_entity
                        print(f"Selected entity: {selected_entity}")
                return True
        
        return False
    
    def _handle_paint_action(self, screen_pos):
        """Handle painting action at screen position"""
        # Convert screen position to world coordinates
        world_x, world_y = self.camera.screen_to_world(screen_pos[0], screen_pos[1])
        
        # Convert to tile coordinates
        tile_x = int(world_x // self.tile_size)
        tile_y = int(world_y // self.tile_size)
        
        # Check bounds
        if not (0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height):
            return
        
        # Avoid painting the same tile repeatedly
        if self.last_painted_pos == (tile_x, tile_y):
            return
        self.last_painted_pos = (tile_x, tile_y)
        
        # Apply the current tool
        if self.current_tool == EditorTool.TILE_BRUSH:
            self.world_map.set_tile(tile_x, tile_y, self.selected_tile_type)
        
        elif self.current_tool == EditorTool.ENTITY_PLACER:
            self._place_entity(tile_x, tile_y)
        
        elif self.current_tool == EditorTool.ERASER:
            # Remove entity tile if present
            if hasattr(self.world_map, 'entity_tile_manager'):
                self.world_map.remove_entity_tile(tile_x, tile_y)
            # Reset to grass
            self.world_map.set_tile(tile_x, tile_y, "grass")
        
        elif self.current_tool == EditorTool.FILL:
            self._flood_fill(tile_x, tile_y)
    
    def _place_entity(self, tile_x, tile_y):
        """Place an entity at the specified tile position"""
        if not hasattr(self.world_map, 'entity_tile_manager'):
            return
        
        # Remove existing entity tile first
        self.world_map.remove_entity_tile(tile_x, tile_y)
        
        # Place new entity
        if self.selected_entity_type == "tree":
            self.world_map.add_tree(tile_x, tile_y)
        elif self.selected_entity_type == "house":
            self.world_map.add_house(tile_x, tile_y)
        # Add more entity types as needed
    
    def _flood_fill(self, start_x, start_y):
        """Flood fill algorithm for the fill tool"""
        if not (0 <= start_x < self.map_width and 0 <= start_y < self.map_height):
            return
        
        original_tile = self.world_map.get_tile(start_x, start_y)
        if not original_tile:
            return
        
        original_type = original_tile.type
        if original_type == self.selected_tile_type:
            return  # Already the target type
        
        # Simple flood fill using a stack
        stack = [(start_x, start_y)]
        visited = set()
        
        while stack and len(visited) < 1000:  # Limit to prevent infinite loops
            x, y = stack.pop()
            
            if (x, y) in visited:
                continue
            if not (0 <= x < self.map_width and 0 <= y < self.map_height):
                continue
            
            tile = self.world_map.get_tile(x, y)
            if not tile or tile.type != original_type:
                continue
            
            visited.add((x, y))
            self.world_map.set_tile(x, y, self.selected_tile_type)
            
            # Add neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                stack.append((x + dx, y + dy))
    
    def update(self):
        """Update the editor state"""
        self.camera.update()
    
    def render(self, screen):
        """Render the map editor"""
        # Clear screen
        screen.fill((40, 40, 40))
        
        # Calculate the main editing area
        edit_area_width = self.screen_width - (self.palette_width if self.show_palette else 0)
        edit_area = pygame.Rect(0, 0, edit_area_width, self.screen_height)
        
        # Set camera viewport
        self.camera.set_viewport(edit_area)
        
        # Render the world map
        if self.world_map:
            self.world_map.render(screen, self.camera)
        
        # Render grid if enabled
        if self.show_grid:
            self._render_grid(screen, edit_area)
        
        # Render tool cursor
        self._render_cursor(screen)
        
        # Render palette
        if self.show_palette:
            self._render_palette(screen)
        
        # Render UI
        self._render_ui(screen)
    
    def _render_grid(self, screen, edit_area):
        """Render the tile grid"""
        grid_color = (80, 80, 80)
        
        # Calculate visible tile range
        start_x = max(0, int(self.camera.x // self.tile_size))
        start_y = max(0, int(self.camera.y // self.tile_size))
        end_x = min(self.map_width, int((self.camera.x + edit_area.width / self.camera.zoom) // self.tile_size) + 1)
        end_y = min(self.map_height, int((self.camera.y + edit_area.height / self.camera.zoom) // self.tile_size) + 1)
        
        # Draw vertical lines
        for x in range(start_x, end_x + 1):
            world_x = x * self.tile_size
            screen_x = int((world_x - self.camera.x) * self.camera.zoom)
            if 0 <= screen_x <= edit_area.width:
                pygame.draw.line(screen, grid_color, 
                               (screen_x, 0), (screen_x, edit_area.height))
        
        # Draw horizontal lines
        for y in range(start_y, end_y + 1):
            world_y = y * self.tile_size
            screen_y = int((world_y - self.camera.y) * self.camera.zoom)
            if 0 <= screen_y <= edit_area.height:
                pygame.draw.line(screen, grid_color, 
                               (0, screen_y), (edit_area.width, screen_y))
    
    def _render_cursor(self, screen):
        """Render the tool cursor"""
        mouse_pos = pygame.mouse.get_pos()
        
        # Don't render cursor over palette
        if self.show_palette and mouse_pos[0] >= self.screen_width - self.palette_width:
            return
        
        # Convert to tile position
        world_x, world_y = self.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        tile_x = int(world_x // self.tile_size)
        tile_y = int(world_y // self.tile_size)
        
        if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
            # Calculate screen position of tile
            screen_x = int((tile_x * self.tile_size - self.camera.x) * self.camera.zoom)
            screen_y = int((tile_y * self.tile_size - self.camera.y) * self.camera.zoom)
            tile_screen_size = int(self.tile_size * self.camera.zoom)
            
            # Choose cursor color based on tool
            cursor_colors = {
                EditorTool.TILE_BRUSH: (255, 255, 255),
                EditorTool.ENTITY_PLACER: (255, 255, 0),
                EditorTool.ERASER: (255, 0, 0),
                EditorTool.SELECTOR: (0, 255, 255),
                EditorTool.FILL: (0, 255, 0)
            }
            
            color = cursor_colors.get(self.current_tool, (255, 255, 255))
            
            # Draw cursor rectangle
            pygame.draw.rect(screen, color, 
                           (screen_x, screen_y, tile_screen_size, tile_screen_size), 2)
    
    def _render_palette(self, screen):
        """Render the tool palette"""
        palette_rect = pygame.Rect(self.screen_width - self.palette_width, 0, 
                                 self.palette_width, self.screen_height)
        
        # Draw palette background
        pygame.draw.rect(screen, (60, 60, 60), palette_rect)
        pygame.draw.line(screen, (100, 100, 100), 
                        (palette_rect.left, 0), (palette_rect.left, self.screen_height), 2)
        
        # Render appropriate palette based on current tool
        if self.current_tool == EditorTool.TILE_BRUSH:
            self.tile_palette.render(screen, palette_rect, self.selected_tile_type)
        elif self.current_tool == EditorTool.ENTITY_PLACER:
            self.entity_palette.render(screen, palette_rect, self.selected_entity_type)
    
    def _render_ui(self, screen):
        """Render UI elements"""
        font = pygame.font.Font(None, 24)
        
        # Tool info
        tool_text = f"Tool: {self.current_tool.value}"
        text_surface = font.render(tool_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        # Selected item info
        if self.current_tool == EditorTool.TILE_BRUSH:
            item_text = f"Tile: {self.selected_tile_type}"
        elif self.current_tool == EditorTool.ENTITY_PLACER:
            item_text = f"Entity: {self.selected_entity_type}"
        else:
            item_text = ""
        
        if item_text:
            text_surface = font.render(item_text, True, (255, 255, 255))
            screen.blit(text_surface, (10, 35))
        
        # Controls help
        help_lines = [
            "Controls:",
            "1-5: Select Tools",
            "G: Toggle Grid",
            "P: Toggle Palette",
            "WASD: Pan Camera",
            "Mouse Wheel: Zoom",
            "Ctrl+S: Save Map",
            "Ctrl+O: Open Map",
            "Ctrl+N: New Map"
        ]
        
        small_font = pygame.font.Font(None, 18)
        for i, line in enumerate(help_lines):
            text_surface = small_font.render(line, True, (200, 200, 200))
            screen.blit(text_surface, (10, self.screen_height - 160 + i * 18))
    
    def save_map(self, filename=None):
        """Save the current map"""
        if not filename:
            # Generate default filename
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"maps/map_{timestamp}.json"
        
        try:
            self.serializer.save_map(self.world_map, filename)
            print(f"Map saved: {filename}")
        except Exception as e:
            print(f"Error saving map: {e}")
    
    def load_map(self, filename):
        """Load a map from file"""
        try:
            self.world_map = self.serializer.load_map(filename)
            if self.world_map:
                self.map_width = self.world_map.width
                self.map_height = self.world_map.height
                print(f"Map loaded: {filename}")
            else:
                print(f"Failed to load map: {filename}")
        except Exception as e:
            print(f"Error loading map: {e}")
    
    def new_map(self):
        """Create a new map"""
        self.world_map = WorldMap(self.map_width, self.map_height)
        self.world_map.initialize_entity_tiles()
        self.world_map.initialize_world_items()
        self._initialize_default_map()
        print("New map created")
    
    def open_map_dialog(self):
        """Open a file dialog to select a map to load"""
        # For now, just print available maps
        maps_dir = "maps"
        if os.path.exists(maps_dir):
            maps = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
            print("Available maps:")
            for i, map_file in enumerate(maps):
                print(f"  {i}: {map_file}")
            print("Use load_map(filename) to load a specific map")
        else:
            print("No maps directory found")

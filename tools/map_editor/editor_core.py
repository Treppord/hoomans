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
from tools.map_editor.entity_renderer import MapEditorEntityRenderer

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
        
        # Initialize custom entity renderer for map editor
        self.entity_renderer = MapEditorEntityRenderer()
        
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
    
    def render(self, screen):
        """Render the map editor"""
        # Clear screen
        screen.fill((40, 40, 40))
        
        # Calculate the main editing area
        edit_area_width = self.screen_width - (self.palette_width if self.show_palette else 0)
        edit_area = pygame.Rect(0, 0, edit_area_width, self.screen_height)
        
        # Set camera viewport
        self.camera.set_viewport(edit_area)
        
        # Render the world map tiles (but not entity tiles)
        if self.world_map:
            self._render_world_tiles(screen, edit_area)
        
        # Render entity tiles using custom renderer
        if self.world_map and hasattr(self.world_map, 'entity_tile_manager'):
            self._render_entity_tiles(screen)
        
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
    
    def _render_world_tiles(self, screen, edit_area):
        """Render only the terrain tiles (not entity tiles)"""
        # Calculate visible tile range based on camera position and zoom
        world_left, world_top = self.camera.reverse_apply(0, 0)
        world_right, world_bottom = self.camera.reverse_apply(edit_area.width, edit_area.height)
        
        # Calculate tile range to render
        start_x = max(0, int(world_left / Tile.SIZE))
        start_y = max(0, int(world_top / Tile.SIZE))
        end_x = min(self.map_width, int(world_right / Tile.SIZE) + 2)
        end_y = min(self.map_height, int(world_bottom / Tile.SIZE) + 2)
        
        # Render visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Apply camera transformation
                tile_x, tile_y, tile_width, tile_height = self.camera.apply(
                    x * Tile.SIZE, y * Tile.SIZE, Tile.SIZE, Tile.SIZE
                )
                
                # Only render if the tile is on screen
                if (tile_x + tile_width > 0 and tile_x < edit_area.width and
                    tile_y + tile_height > 0 and tile_y < edit_area.height):
                    self.world_map.tiles[y][x].render(screen, int(tile_x), int(tile_y), 
                                                    int(tile_width), int(tile_height))
    
    def _render_entity_tiles(self, screen):
        """Render entity tiles using the custom entity renderer"""
        if not hasattr(self.world_map, 'entity_tile_manager'):
            return
        
        # Get screen dimensions for culling
        screen_width, screen_height = screen.get_size()
        
        # Render each entity tile
        for entity_tile in self.world_map.entity_tile_manager.entity_tiles:
            # Calculate screen bounds for this entity
            world_x = entity_tile.base_x * Tile.SIZE
            world_y = entity_tile.base_y * Tile.SIZE
            world_width = entity_tile.width * Tile.SIZE
            world_height = entity_tile.height * Tile.SIZE
            
            screen_x, screen_y, screen_width, screen_height = self.camera.apply(
                world_x, world_y, world_width, world_height
            )
            
            # Only render if on screen
            if (screen_x + screen_width > 0 and screen_x < self.screen_width and
                screen_y + screen_height > 0 and screen_y < self.screen_height):
                self.entity_renderer.render_entity_tile(screen, entity_tile, self.camera)
    
    def _render_grid(self, screen, edit_area):
        """Render the grid overlay"""
        if not self.camera.should_draw_grid():
            return
        
        grid_color = (80, 80, 80)
        
        # Calculate visible tile range
        world_left, world_top = self.camera.reverse_apply(0, 0)
        world_right, world_bottom = self.camera.reverse_apply(edit_area.width, edit_area.height)
        
        start_x = max(0, int(world_left / Tile.SIZE))
        start_y = max(0, int(world_top / Tile.SIZE))
        end_x = min(self.map_width, int(world_right / Tile.SIZE) + 2)
        end_y = min(self.map_height, int(world_bottom / Tile.SIZE) + 2)
        
        # Draw vertical grid lines
        for x in range(start_x, end_x + 1):
            grid_x, grid_y, _, _ = self.camera.apply(x * Tile.SIZE, start_y * Tile.SIZE, 0, 0)
            _, grid_bottom, _, _ = self.camera.apply(x * Tile.SIZE, end_y * Tile.SIZE, 0, 0)
            if 0 <= grid_x <= edit_area.width:
                pygame.draw.line(screen, grid_color, (int(grid_x), int(grid_y)), 
                               (int(grid_x), int(grid_bottom)), 1)
        
        # Draw horizontal grid lines
        for y in range(start_y, end_y + 1):
            grid_x, grid_y, _, _ = self.camera.apply(start_x * Tile.SIZE, y * Tile.SIZE, 0, 0)
            grid_right, _, _, _ = self.camera.apply(end_x * Tile.SIZE, y * Tile.SIZE, 0, 0)
            if 0 <= grid_y <= edit_area.height:
                pygame.draw.line(screen, grid_color, (int(grid_x), int(grid_y)), 
                               (int(grid_right), int(grid_y)), 1)
    
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
            # Choose cursor color and size based on tool and entity type
            cursor_colors = {
                EditorTool.TILE_BRUSH: (255, 255, 255),
                EditorTool.ENTITY_PLACER: (255, 255, 0),
                EditorTool.ERASER: (255, 0, 0),
                EditorTool.SELECTOR: (0, 255, 255),
                EditorTool.FILL: (0, 255, 0)
            }
            
            color = cursor_colors.get(self.current_tool, (255, 255, 255))
            
            # Calculate cursor size based on entity type
            cursor_width = 1
            cursor_height = 1
            
            if self.current_tool == EditorTool.ENTITY_PLACER:
                cursor_width, cursor_height = self.entity_renderer.get_entity_size(self.selected_entity_type)
            
            # Calculate screen position and size
            for dy in range(cursor_height):
                for dx in range(cursor_width):
                    cursor_tile_x = tile_x + dx
                    cursor_tile_y = tile_y + dy
                    
                    if (0 <= cursor_tile_x < self.map_width and 
                        0 <= cursor_tile_y < self.map_height):
                        
                        screen_x, screen_y, tile_screen_width, tile_screen_height = self.camera.apply(
                            cursor_tile_x * self.tile_size, cursor_tile_y * self.tile_size,
                            self.tile_size, self.tile_size
                        )
                        
                        # Draw cursor rectangle
                        pygame.draw.rect(screen, color, 
                                       (int(screen_x), int(screen_y), 
                                        int(tile_screen_width), int(tile_screen_height)), 2)
    
    def _render_palette(self, screen):
        """Render the tool and tile palette"""
        palette_rect = pygame.Rect(self.screen_width - self.palette_width, 0, 
                                 self.palette_width, self.screen_height)
        
        # Background
        pygame.draw.rect(screen, (60, 60, 60), palette_rect)
        pygame.draw.rect(screen, (100, 100, 100), palette_rect, 2)
        
        # Render appropriate palette based on current tool
        if self.current_tool == EditorTool.TILE_BRUSH:
            self.tile_palette.render(screen, palette_rect)
        elif self.current_tool == EditorTool.ENTITY_PLACER:
            self.entity_palette.render(screen, palette_rect)
    
    def _render_ui(self, screen):
        """Render UI elements"""
        # Tool indicator
        font = pygame.font.Font(None, 24)
        tool_text = f"Tool: {self.current_tool.value.replace('_', ' ').title()}"
        
        if self.current_tool == EditorTool.TILE_BRUSH:
            tool_text += f" ({self.selected_tile_type})"
        elif self.current_tool == EditorTool.ENTITY_PLACER:
            tool_text += f" ({self.selected_entity_type})"
        
        text_surface = font.render(tool_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        # Instructions
        instructions = [
            "Left Click: Paint/Place",
            "Right Click: Erase",
            "Middle Click: Pan",
            "Mouse Wheel: Zoom",
            "Arrow Keys: Move Camera",
            "G: Toggle Grid",
            "P: Toggle Palette",
            "1-5: Select Tool",
            "Ctrl+S: Save",
            "Ctrl+O: Open"
        ]
        
        small_font = pygame.font.Font(None, 16)
        for i, instruction in enumerate(instructions):
            text_surface = small_font.render(instruction, True, (200, 200, 200))
            screen.blit(text_surface, (10, 40 + i * 18))
    
    def _place_entity(self, tile_x, tile_y):
        """Place an entity at the specified tile position"""
        if not hasattr(self.world_map, 'entity_tile_manager'):
            print("DEBUG: Initializing entity tile manager")
            self.world_map.initialize_entity_tiles()
        
        # Check if position is valid and not occupied
        if self.selected_entity_type == "tree":
            # Trees are 1x2, check both positions
            if not (0 <= tile_x < self.world_map.width and 0 <= tile_y < self.world_map.height - 1):
                print(f"DEBUG: Tree position ({tile_x}, {tile_y}) out of bounds")
                return False
            
            # Check if positions are walkable
            tile1 = self.world_map.get_tile(tile_x, tile_y)
            tile2 = self.world_map.get_tile(tile_x, tile_y + 1)
            if not tile1 or not tile2 or not tile1.is_walkable() or not tile2.is_walkable():
                print(f"DEBUG: Tree position ({tile_x}, {tile_y}) not walkable")
                return False
            
            # Check if already occupied by entity tiles
            if (self.world_map.entity_tile_manager.get_entity_tile_at(tile_x, tile_y) or
                self.world_map.entity_tile_manager.get_entity_tile_at(tile_x, tile_y + 1)):
                print(f"DEBUG: Tree position ({tile_x}, {tile_y}) already occupied")
                return False
            
            # Place the tree
            tree = self.world_map.add_tree(tile_x, tile_y)
            if tree:
                print(f"DEBUG: Successfully placed tree at ({tile_x}, {tile_y})")
                return True
            else:
                print(f"DEBUG: Failed to place tree at ({tile_x}, {tile_y})")
                return False
                
        elif self.selected_entity_type == "house":
            # Houses are 2x2, check all positions
            if not (0 <= tile_x < self.world_map.width - 1 and 0 <= tile_y < self.world_map.height - 1):
                print(f"DEBUG: House position ({tile_x}, {tile_y}) out of bounds")
                return False
            
            # Check if all positions are walkable
            for dx in range(2):
                for dy in range(2):
                    tile = self.world_map.get_tile(tile_x + dx, tile_y + dy)
                    if not tile or not tile.is_walkable():
                        print(f"DEBUG: House position ({tile_x + dx}, {tile_y + dy}) not walkable")
                        return False
            
            # Check if already occupied by entity tiles
            for dx in range(2):
                for dy in range(2):
                    if self.world_map.entity_tile_manager.get_entity_tile_at(tile_x + dx, tile_y + dy):
                        print(f"DEBUG: House position ({tile_x + dx}, {tile_y + dy}) already occupied")
                        return False
            
            # Place the house
            house = self.world_map.add_house(tile_x, tile_y)
            if house:
                print(f"DEBUG: Successfully placed house at ({tile_x}, {tile_y})")
                return True
            else:
                print(f"DEBUG: Failed to place house at ({tile_x}, {tile_y})")
                return False
        
        print(f"DEBUG: Unknown entity type: {self.selected_entity_type}")
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
            print(f"DEBUG: Placed tile {self.selected_tile_type} at ({tile_x}, {tile_y})")
        
        elif self.current_tool == EditorTool.ENTITY_PLACER:
            success = self._place_entity(tile_x, tile_y)
            if success:
                print(f"DEBUG: Successfully placed {self.selected_entity_type} at ({tile_x}, {tile_y})")
            else:
                print(f"DEBUG: Failed to place {self.selected_entity_type} at ({tile_x}, {tile_y})")
        
        elif self.current_tool == EditorTool.ERASER:
            # Remove entity tile if present
            if hasattr(self.world_map, 'entity_tile_manager'):
                entity_tile = self.world_map.entity_tile_manager.get_entity_tile_at(tile_x, tile_y)
                if entity_tile:
                    self.world_map.entity_tile_manager.remove_entity_tile(entity_tile)
                    print(f"DEBUG: Removed entity tile at ({tile_x}, {tile_y})")
            # Reset to grass
            self.world_map.set_tile(tile_x, tile_y, "grass")
        
        elif self.current_tool == EditorTool.FILL:
            self._flood_fill(tile_x, tile_y)
    
    def _flood_fill(self, start_x, start_y):
        """Flood fill starting from the specified position"""
        if self.current_tool != EditorTool.FILL:
            return
        
        original_tile = self.world_map.get_tile(start_x, start_y)
        if not original_tile or original_tile.type == self.selected_tile_type:
            return
        
        original_type = original_tile.type
        stack = [(start_x, start_y)]
        filled_tiles = set()
        
        while stack and len(filled_tiles) < 1000:  # Limit to prevent infinite loops
            x, y = stack.pop()
            
            if (x, y) in filled_tiles:
                continue
            
            if not (0 <= x < self.map_width and 0 <= y < self.map_height):
                continue
            
            tile = self.world_map.get_tile(x, y)
            if not tile or tile.type != original_type:
                continue
            
            # Fill this tile
            self.world_map.set_tile(x, y, self.selected_tile_type)
            filled_tiles.add((x, y))
            
            # Add neighbors to stack
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                stack.append((x + dx, y + dy))
        
        print(f"DEBUG: Flood filled {len(filled_tiles)} tiles")
    
    def _initialize_default_map(self):
        """Initialize the map with default grass tiles"""
        for y in range(self.map_height):
            for x in range(self.map_width):
                self.world_map.set_tile(x, y, "grass")
    
    def handle_event(self, event):
        """Handle input events"""
        # Camera events first
        if self.camera.handle_event(event):
            return True
        
        # Palette events
        if self.show_palette:
            palette_rect = pygame.Rect(self.screen_width - self.palette_width, 0, 
                                     self.palette_width, self.screen_height)
            if palette_rect.collidepoint(pygame.mouse.get_pos()):
                # Handle palette clicks
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.current_tool == EditorTool.TILE_BRUSH:
                        selected_tile = self.tile_palette.get_tile_at_pos(event.pos, palette_rect)
                        if selected_tile:
                            self.selected_tile_type = selected_tile
                            self.tile_palette.selected_tile = selected_tile
                            return True
                    elif self.current_tool == EditorTool.ENTITY_PLACER:
                        selected_entity = self.entity_palette.get_entity_at_pos(event.pos, palette_rect)
                        if selected_entity:
                            self.selected_entity_type = selected_entity
                            self.entity_palette.selected_entity = selected_entity
                            return True
                
                # Handle palette scrolling
                if self.current_tool == EditorTool.TILE_BRUSH:
                    if self.tile_palette.handle_event(event):
                        return True
                elif self.current_tool == EditorTool.ENTITY_PLACER:
                    if self.entity_palette.handle_event(event):
                        return True
        
        # Mouse events
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.is_painting = True
                self.last_painted_pos = None
                self._handle_paint_action(event.pos)
                return True
            elif event.button == 3:  # Right click
                # Switch to eraser temporarily
                old_tool = self.current_tool
                self.current_tool = EditorTool.ERASER
                self._handle_paint_action(event.pos)
                self.current_tool = old_tool
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_painting = False
                self.last_painted_pos = None
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_painting:
                self._handle_paint_action(event.pos)
                return True
        
        # Keyboard events
        elif event.type == pygame.KEYDOWN:
            # Tool selection
            if event.key == pygame.K_1:
                self.current_tool = EditorTool.TILE_BRUSH
                return True
            elif event.key == pygame.K_2:
                self.current_tool = EditorTool.ENTITY_PLACER
                return True
            elif event.key == pygame.K_3:
                self.current_tool = EditorTool.ERASER
                return True
            elif event.key == pygame.K_4:
                self.current_tool = EditorTool.SELECTOR
                return True
            elif event.key == pygame.K_5:
                self.current_tool = EditorTool.FILL
                return True
            
            # UI toggles
            elif event.key == pygame.K_g:
                self.show_grid = not self.show_grid
                return True
            elif event.key == pygame.K_p:
                self.show_palette = not self.show_palette
                return True
        
        return False
    
    def update(self):
        """Update the editor state"""
        # Update world items if they exist
        if hasattr(self.world_map, 'world_item_manager'):
            self.world_map.update_world_items()
    
    def load_map(self, filename):
        """Load a map from file"""
        try:
            loaded_map = self.serializer.load_map(filename)
            if loaded_map:
                self.world_map = loaded_map
                self.map_width = self.world_map.width
                self.map_height = self.world_map.height
                print(f"Map loaded: {filename}")
                print(f"DEBUG: Loaded map has {len(self.world_map.entity_tile_manager.entity_tiles) if hasattr(self.world_map, 'entity_tile_manager') else 0} entity tiles")
                return loaded_map
            else:
                print(f"Failed to load map: {filename}")
                return None
        except Exception as e:
            print(f"Error loading map: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_map(self, filename=None):
        """Save the current map"""
        if not filename:
            # Generate default filename with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"map_editor_{timestamp}"
        
        try:
            print(f"DEBUG: Saving map with {len(self.world_map.entity_tile_manager.entity_tiles) if hasattr(self.world_map, 'entity_tile_manager') else 0} entity tiles")
            success = self.serializer.save_map(self.world_map, filename)
            if success:
                print(f"Map saved: {filename}")
            else:
                print(f"Failed to save map: {filename}")
        except Exception as e:
            print(f"Error saving map: {e}")
            import traceback
            traceback.print_exc()
    
    def open_map_dialog(self):
        """Open a file dialog to load a map"""
        # List available maps
        available_maps = self.serializer.list_maps()
        
        if not available_maps:
            print("No maps found in maps directory")
            print(f"Maps directory: {self.serializer.get_maps_directory()}")
            return
        
        print("Available maps:")
        for i, map_file in enumerate(available_maps):
            print(f"  {i + 1}: {map_file}")
        
        # For now, just load the first map as an example
        # In a full implementation, you'd show a proper file dialog
        if available_maps:
            first_map = available_maps[0]
            print(f"Loading first available map: {first_map}")
            self.load_map(first_map)

    def new_map(self):
        """Create a new map"""
        self.world_map = WorldMap(self.map_width, self.map_height)
        self.world_map.initialize_entity_tiles()
        self.world_map.initialize_world_items()
        self._initialize_default_map()
        print("New map created")
    
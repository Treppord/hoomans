"""
Map Editor Tool - Embedded tool for editing game maps
"""
import pygame
import pygame_gui
import os
import sys
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from typing import Dict, Any, Optional, List, Tuple
from engine.studio.studio_tools import EmbeddedTool

class MapEditor(EmbeddedTool):
    """Embedded map editor for the studio"""
    
    def __init__(self, studio_instance, ui_manager=None):
        super().__init__(studio_instance, "map_editor", ui_manager)
        self.map_width = 256
        self.map_height = 256
        self.current_tool = "terrain"
        self.current_terrain = "grass"
        self.zoom_level = 1.0
        self.map_offset_x = 0
        self.map_offset_y = 0
        
        # Map data
        self.terrain_map = {}
        self.entity_map = {}
        self.item_map = {}
        
        # UI elements
        self.main_panel = None
        self.tool_panel = None
        self.map_canvas = None
        self.properties_panel = None
        
        # Available tools and terrain types
        self.tools = ["terrain", "entities", "items", "structures"]
        self.terrain_types = ["grass", "water", "stone", "dirt", "sand"]
        self.entity_types = ["player_spawn", "npc_spawn", "food_spawn"]
        self.item_types = ["apple", "berries", "water_bottle", "stone_axe"]
    
    def _create_ui(self):
        """Create the map editor UI"""
        if not self.ui_manager:
            return
        
        # Main panel - positioned to be clearly on top
        panel_width = 1200
        panel_height = 800
        panel_x = (self.studio.screen_size[0] - panel_width) // 2
        panel_y = 80  # Start below the studio menu bar
        
        self.main_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.ui_manager
        )
        self.ui_elements.append(self.main_panel)
        
        # Title and close button
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, panel_width - 120, 30),
            text="Map Editor",
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(title_label)
        
        close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_width - 100, 10, 80, 30),
            text="Close",
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(close_button)
        
        # Tool panel (left side)
        self.tool_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(10, 50, 200, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.tool_panel)
        
        # Tool selection
        tool_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 180, 25),
            text="Tool:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(tool_label)
        
        self.tool_dropdown = pygame_gui.elements.UIDropDownMenu(
            relative_rect=pygame.Rect(10, 40, 180, 30),
            options_list=self.tools,
            starting_option="terrain",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(self.tool_dropdown)
        
        # Terrain selection
        terrain_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 80, 180, 25),
            text="Terrain:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(terrain_label)
        
        self.terrain_dropdown = pygame_gui.elements.UIDropDownMenu(
            relative_rect=pygame.Rect(10, 110, 180, 30),
            options_list=self.terrain_types,
            starting_option="grass",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(self.terrain_dropdown)
        
        # Map size controls
        size_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 150, 180, 25),
            text="Map Size:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(size_label)
        
        width_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 180, 50, 25),
            text="Width:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(width_label)
        
        self.width_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(70, 180, 80, 25),
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.width_input.set_text(str(self.map_width))
        self.ui_elements.append(self.width_input)
        
        height_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 210, 50, 25),
            text="Height:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(height_label)
        
        self.height_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(70, 210, 80, 25),
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.height_input.set_text(str(self.map_height))
        self.ui_elements.append(self.height_input)
        
        # Action buttons
        new_map_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 250, 80, 30),
            text="New Map",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(new_map_button)
        
        save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 250, 80, 30),
            text="Save",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(save_button)
        
        load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 290, 80, 30),
            text="Load",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(load_button)
        
        clear_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 290, 80, 30),
            text="Clear",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(clear_button)
        
        # Map canvas (center) - This is the key addition for visual editing
        canvas_width = 700
        canvas_height = panel_height - 100
        
        self.map_canvas = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(220, 50, canvas_width, canvas_height),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.map_canvas)
        
        canvas_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, canvas_width - 20, 25),
            text="Map Canvas - Click to edit",
            manager=self.ui_manager,
            container=self.map_canvas
        )
        self.ui_elements.append(canvas_label)
        
        # Create the actual map surface for drawing
        self.map_surface = pygame.Surface((canvas_width - 20, canvas_height - 40))
        self.tile_size = 8  # Size of each tile in pixels
        self.visible_width = (canvas_width - 20) // self.tile_size
        self.visible_height = (canvas_height - 40) // self.tile_size
        
        # Properties panel (right side)
        self.properties_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(930, 50, 260, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.properties_panel)
        
        props_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 240, 25),
            text="Properties:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(props_label)
        
        self.properties_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, 40, 240, 200),
            html_text="Select a tile to view properties",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.properties_text)
        
        # Initialize with empty map
        self._create_new_map()
        self._render_map()

    def _render_map(self):
        """Render the map to the canvas surface"""
        if not hasattr(self, 'map_surface'):
            return
        
        # Clear the surface
        self.map_surface.fill((50, 50, 50))  # Dark gray background
        
        # Define terrain colors
        terrain_colors = {
            "grass": (34, 139, 34),      # Forest green
            "water": (30, 144, 255),     # Dodger blue
            "stone": (128, 128, 128),    # Gray
            "dirt": (139, 69, 19),       # Saddle brown
            "sand": (238, 203, 173)      # Navajo white
        }
        
        # Calculate visible area
        start_x = max(0, self.map_offset_x)
        start_y = max(0, self.map_offset_y)
        end_x = min(self.map_width, start_x + self.visible_width)
        end_y = min(self.map_height, start_y + self.visible_height)
        
        # Draw terrain tiles
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                terrain = self.terrain_map.get((x, y), "grass")
                color = terrain_colors.get(terrain, (100, 100, 100))
                
                screen_x = (x - start_x) * self.tile_size
                screen_y = (y - start_y) * self.tile_size
                
                pygame.draw.rect(self.map_surface, color, 
                            (screen_x, screen_y, self.tile_size, self.tile_size))
                
                # Draw grid lines
                pygame.draw.rect(self.map_surface, (80, 80, 80), 
                            (screen_x, screen_y, self.tile_size, self.tile_size), 1)
        
        # Draw entities
        entity_colors = {
            "player_spawn": (255, 255, 0),    # Yellow
            "npc_spawn": (255, 0, 255),       # Magenta
            "food_spawn": (0, 255, 0)         # Green
        }
        
        for (x, y), entity in self.entity_map.items():
            if start_x <= x < end_x and start_y <= y < end_y:
                color = entity_colors.get(entity, (255, 255, 255))
                screen_x = (x - start_x) * self.tile_size
                screen_y = (y - start_y) * self.tile_size
                
                # Draw entity as a circle
                center_x = screen_x + self.tile_size // 2
                center_y = screen_y + self.tile_size // 2
                pygame.draw.circle(self.map_surface, color, (center_x, center_y), self.tile_size // 3)
        
        # Draw items
        for (x, y), item in self.item_map.items():
            if start_x <= x < end_x and start_y <= y < end_y:
                screen_x = (x - start_x) * self.tile_size
                screen_y = (y - start_y) * self.tile_size
                
                # Draw item as a small square
                item_size = self.tile_size // 2
                offset = self.tile_size // 4
                pygame.draw.rect(self.map_surface, (255, 255, 255), 
                            (screen_x + offset, screen_y + offset, item_size, item_size))

    def _handle_canvas_click(self, pos):
        """Handle clicks on the map canvas"""
        if not self.map_canvas:
            return
        
        # Get canvas position relative to main panel
        canvas_rect = self.map_canvas.relative_rect
        main_panel_rect = self.main_panel.relative_rect
        
        # Calculate absolute canvas position
        canvas_abs_x = main_panel_rect.x + canvas_rect.x + 10  # +10 for canvas padding
        canvas_abs_y = main_panel_rect.y + canvas_rect.y + 40  # +40 for label
        
        # Check if click is within canvas bounds
        canvas_x = pos[0] - canvas_abs_x
        canvas_y = pos[1] - canvas_abs_y
        
        if (0 <= canvas_x <= self.map_surface.get_width() and 
            0 <= canvas_y <= self.map_surface.get_height()):
            
            # Convert to grid coordinates
            grid_x = (canvas_x // self.tile_size) + self.map_offset_x
            grid_y = (canvas_y // self.tile_size) + self.map_offset_y
            
            if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                self._edit_tile(grid_x, grid_y)
                self._render_map()  # Re-render after editing

    def _edit_tile(self, x, y):
        """Edit a tile at the given coordinates"""
        if self.current_tool == "terrain":
            self.terrain_map[(x, y)] = self.current_terrain
        elif self.current_tool == "entities":
            # Toggle entity placement
            if (x, y) in self.entity_map:
                del self.entity_map[(x, y)]
            else:
                self.entity_map[(x, y)] = "npc_spawn"
        elif self.current_tool == "items":
            # Toggle item placement
            if (x, y) in self.item_map:
                del self.item_map[(x, y)]
            else:
                self.item_map[(x, y)] = "apple"
        
        # Update properties display
        self._update_properties_display(x, y)

    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, 'text'):
                if event.ui_element.text == "Close":
                    self.close()
                elif event.ui_element.text == "New Map":
                    self._create_new_map()
                    self._render_map()
                elif event.ui_element.text == "Save":
                    self._save_map()
                elif event.ui_element.text == "Load":
                    self._load_map()
                    self._render_map()
                elif event.ui_element.text == "Clear":
                    self._clear_map()
                    self._render_map()
        
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.tool_dropdown:
                self.current_tool = event.text
            elif event.ui_element == self.terrain_dropdown:
                self.current_terrain = event.text
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_canvas_click(event.pos)
    
    def _update_properties_display(self, x, y):
        """Update the properties display for the selected tile"""
        terrain = self.terrain_map.get((x, y), "grass")
        entity = self.entity_map.get((x, y), None)
        item = self.item_map.get((x, y), None)
        
        html_text = f"""
        <b>Tile ({x}, {y})</b><br>
        <b>Terrain:</b> {terrain}<br>
        """
        
        if entity:
            html_text += f"<b>Entity:</b> {entity}<br>"
        
        if item:
            html_text += f"<b>Item:</b> {item}<br>"
        
        self.properties_text.html_text = html_text
        self.properties_text.rebuild()
    
    def _create_new_map(self):
        """Create a new empty map"""
        try:
            self.map_width = int(self.width_input.get_text())
            self.map_height = int(self.height_input.get_text())
        except ValueError:
            self.map_width = 256
            self.map_height = 256
        
        self.terrain_map.clear()
        self.entity_map.clear()
        self.item_map.clear()
        
        # Fill with default terrain
        for x in range(self.map_width):
            for y in range(self.map_height):
                self.terrain_map[(x, y)] = "grass"
    
    def _save_map(self):
        """Save the current map"""
        map_data = {
            "width": self.map_width,
            "height": self.map_height,
            "terrain": {f"{x},{y}": terrain for (x, y), terrain in self.terrain_map.items()},
            "entities": {f"{x},{y}": entity for (x, y), entity in self.entity_map.items()},
            "items": {f"{x},{y}": item for (x, y), item in self.item_map.items()}
        }
        
        # Save to maps directory
        maps_dir = os.path.join(project_root, "maps")
        os.makedirs(maps_dir, exist_ok=True)
        
        map_file = os.path.join(maps_dir, "custom_map.json")
        with open(map_file, 'w') as f:
            json.dump(map_data, f, indent=2)
        
        print(f"Map saved to: {map_file}")
        
        # Update studio status
        if hasattr(self.studio, 'status_label'):
            self.studio.status_label.set_text("Map saved successfully")
    
    def _load_map(self):
        """Load a map from file"""
        maps_dir = os.path.join(project_root, "maps")
        map_file = os.path.join(maps_dir, "custom_map.json")
        
        if not os.path.exists(map_file):
            print("No map file found to load")
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text("No map file found")
            return
        
        try:
            with open(map_file, 'r') as f:
                map_data = json.load(f)
            
            self.map_width = map_data.get("width", 256)
            self.map_height = map_data.get("height", 256)
            
            # Load terrain
            self.terrain_map.clear()
            for pos_str, terrain in map_data.get("terrain", {}).items():
                x, y = map(int, pos_str.split(','))
                self.terrain_map[(x, y)] = terrain
            
            # Load entities
            self.entity_map.clear()
            for pos_str, entity in map_data.get("entities", {}).items():
                x, y = map(int, pos_str.split(','))
                self.entity_map[(x, y)] = entity
            
            # Load items
            self.item_map.clear()
            for pos_str, item in map_data.get("items", {}).items():
                x, y = map(int, pos_str.split(','))
                self.item_map[(x, y)] = item
            
            # Update UI
            self.width_input.set_text(str(self.map_width))
            self.height_input.set_text(str(self.map_height))
            
            print("Map loaded successfully")
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text("Map loaded successfully")
                
        except Exception as e:
            print(f"Error loading map: {e}")
            if hasattr(self.studio, 'status_label'):
                self.studio.status_label.set_text(f"Error loading map: {e}")
    
    def _clear_map(self):
        """Clear the current map"""
        self.terrain_map.clear()
        self.entity_map.clear()
        self.item_map.clear()
        
        # Fill with default terrain
        for x in range(self.map_width):
            for y in range(self.map_height):
                self.terrain_map[(x, y)] = "grass"
        
        if hasattr(self.studio, 'status_label'):
            self.studio.status_label.set_text("Map cleared")

    def update(self, time_delta):
        """Update the map editor"""
        # Handle keyboard input for map navigation
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] and self.map_offset_x > 0:
            self.map_offset_x -= 1
            self._render_map()
        elif keys[pygame.K_RIGHT] and self.map_offset_x < self.map_width - self.visible_width:
            self.map_offset_x += 1
            self._render_map()
        elif keys[pygame.K_UP] and self.map_offset_y > 0:
            self.map_offset_y -= 1
            self._render_map()
        elif keys[pygame.K_DOWN] and self.map_offset_y < self.map_height - self.visible_height:
            self.map_offset_y += 1
            self._render_map()

    def render(self, surface):
        """Render the map editor"""
        if self.visible and hasattr(self, 'map_surface') and self.map_surface:
            # Get the canvas position
            if self.map_canvas and self.main_panel:
                canvas_rect = self.map_canvas.relative_rect
                main_panel_rect = self.main_panel.relative_rect
                
                # Calculate where to blit the map surface
                blit_x = main_panel_rect.x + canvas_rect.x + 10
                blit_y = main_panel_rect.y + canvas_rect.y + 40
                
                # Blit the map surface to the screen
                surface.blit(self.map_surface, (blit_x, blit_y))
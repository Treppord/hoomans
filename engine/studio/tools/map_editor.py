"""
Map Editor Tool - Embedded tool for editing game maps
Enhanced with full map editor capabilities
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
from enum import Enum
from engine.studio.studio_tools import EmbeddedTool

# Import the advanced map editor components
from tools.map_editor.editor_core import MapEditor as CoreMapEditor, EditorTool
from tools.map_editor.aseprite_integration import AsepriteIntegration
from tools.map_editor.tile_palette import TilePalette
from tools.map_editor.entity_palette import EntityPalette
from tools.map_editor.map_serializer import MapSerializer
from tools.map_editor.editor_camera import EditorCamera
from tools.map_editor.entity_renderer import MapEditorEntityRenderer
from world.map import WorldMap
from world.tile import Tile

class MapEditor(EmbeddedTool):
    """Enhanced embedded map editor for the studio with full capabilities"""
    
    def __init__(self, studio_instance, ui_manager=None):
        super().__init__(studio_instance, "map_editor", ui_manager)
        
        # Map editor core settings
        self.map_width = 256
        self.map_height = 256
        self.tile_size = 16
        
        # UI elements
        self.main_panel = None
        self.tool_panel = None
        self.map_canvas = None
        self.properties_panel = None
        self.status_label = None
        
        # Core map editor instance
        self.core_editor = None
        
        # Canvas settings for embedded mode
        self.canvas_width = 700
        self.canvas_height = 600
        self.canvas_surface = None
        
        # Integration components
        self.aseprite_integration = None
        
        # UI state
        self.show_advanced_tools = False
        
        print("Enhanced Map Editor initialized")
    
    def _create_ui(self):
        """Create the enhanced map editor UI"""
        if not self.ui_manager:
            return
        
        # Main panel - larger to accommodate advanced features
        panel_width = 1400
        panel_height = 900
        panel_x = (self.studio.screen_size[0] - panel_width) // 2
        panel_y = 50
        
        self.main_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.ui_manager
        )
        self.ui_elements.append(self.main_panel)
        
        # Title bar with close button
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, panel_width - 120, 30),
            text="Enhanced Map Editor",
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
        
        # Tool panel (left side) - enhanced
        self.tool_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(10, 50, 250, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.tool_panel)
        
        self._create_tool_panel_ui()
        
        # Map canvas (center) - larger for better editing
        self.canvas_width = 800
        self.canvas_height = panel_height - 100
        
        self.map_canvas = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(270, 50, self.canvas_width, self.canvas_height),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.map_canvas)
        
        canvas_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, self.canvas_width - 20, 25),
            text="Map Canvas - Use mouse and keyboard controls",
            manager=self.ui_manager,
            container=self.map_canvas
        )
        self.ui_elements.append(canvas_label)
        
        # Properties panel (right side) - enhanced
        self.properties_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(1080, 50, 310, panel_height - 100),
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.properties_panel)
        
        self._create_properties_panel_ui()
        
        # Status bar
        self.status_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, panel_height - 40, panel_width - 20, 25),
            text="Ready - Use tools to edit the map",
            manager=self.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.status_label)
        
        # Initialize the core map editor
        self._initialize_core_editor()
        
    def _create_tool_panel_ui(self):
        """Create the enhanced tool panel UI"""
        y_offset = 10
        
        # Tool selection
        tool_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="Editing Tools:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(tool_label)
        y_offset += 30
        
        # Tool buttons
        tools = [
            ("Tile Brush", "tile_brush"),
            ("Entity Placer", "entity_placer"),
            ("Eraser", "eraser"),
            ("Selector", "selector"),
            ("Fill Tool", "fill")
        ]
        
        for i, (tool_name, tool_id) in enumerate(tools):
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_offset, 110, 30),
                text=f"{i+1}. {tool_name}",
                manager=self.ui_manager,
                container=self.tool_panel
            )
            button.tool_id = tool_id
            self.ui_elements.append(button)
            y_offset += 35
        
        y_offset += 10
        
        # Map settings
        settings_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="Map Settings:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(settings_label)
        y_offset += 30
        
        # Map size controls
        width_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 60, 25),
            text="Width:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(width_label)
        
        self.width_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(80, y_offset, 80, 25),
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.width_input.set_text(str(self.map_width))
        self.ui_elements.append(self.width_input)
        y_offset += 30
        
        height_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 60, 25),
            text="Height:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(height_label)
        
        self.height_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(80, y_offset, 80, 25),
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.height_input.set_text(str(self.map_height))
        self.ui_elements.append(self.height_input)
        y_offset += 40
        
        # View controls
        view_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="View Controls:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(view_label)
        y_offset += 30
        
        grid_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset, 110, 30),
            text="Toggle Grid (G)",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(grid_button)
        
        palette_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(130, y_offset, 110, 30),
            text="Toggle Palette (P)",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(palette_button)
        y_offset += 40
        
        # File operations
        file_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="File Operations:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(file_label)
        y_offset += 30
        
        new_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset, 70, 30),
            text="New",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(new_button)
        
        save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(90, y_offset, 70, 30),
            text="Save",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(save_button)
        
        load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(170, y_offset, 70, 30),
            text="Load",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(load_button)
        y_offset += 40
        
        # Advanced features toggle
        advanced_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset, 230, 30),
            text="Show Advanced Tools",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(advanced_button)

    
    def _create_tool_panel_UI(self):
        """Create the enhanced tool panel UI"""
        y_offset = 10
        
        # Tool selection
        tool_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="Editing Tools:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(tool_label)
        y_offset += 30
        
        # Tool buttons
        tools = [
            ("Tile Brush", "tile_brush"),
            ("Entity Placer", "entity_placer"),
            ("Eraser", "eraser"),
            ("Selector", "selector"),
            ("Fill Tool", "fill")
        ]
        
        for i, (tool_name, tool_id) in enumerate(tools):
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_offset, 110, 30),
                text=f"{i+1}. {tool_name}",
                manager=self.ui_manager,
                container=self.tool_panel
            )
            button.tool_id = tool_id
            self.ui_elements.append(button)
            y_offset += 35
        
        y_offset += 10
        
        # Map settings
        settings_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="Map Settings:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(settings_label)
        y_offset += 30
        
        # Map size controls
        width_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 60, 25),
            text="Width:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(width_label)
        
        self.width_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(80, y_offset, 80, 25),
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.width_input.set_text(str(self.map_width))
        self.ui_elements.append(self.width_input)
        y_offset += 30
        
        height_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 60, 25),
            text="Height:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(height_label)
        
        self.height_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(80, y_offset, 80, 25),
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.height_input.set_text(str(self.map_height))
        self.ui_elements.append(self.height_input)
        y_offset += 40
        
        # View controls
        view_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="View Controls:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(view_label)
        y_offset += 30
        
        grid_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset, 110, 30),
            text="Toggle Grid (G)",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(grid_button)
        
        palette_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(130, y_offset, 110, 30),
            text="Toggle Palette (P)",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(palette_button)
        y_offset += 40
        
        # File operations
        file_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 230, 25),
            text="File Operations:",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(file_label)
        y_offset += 30
        
        new_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset, 70, 30),
            text="New",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(new_button)
        
        save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(90, y_offset, 70, 30),
            text="Save",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(save_button)
        
        load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(170, y_offset, 70, 30),
            text="Load",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(load_button)
        y_offset += 40
        
        # Advanced features toggle
        advanced_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_offset, 230, 30),
            text="Show Advanced Tools",
            manager=self.ui_manager,
            container=self.tool_panel
        )
        self.ui_elements.append(advanced_button)
    
    def _create_properties_panel_ui(self):
        """Create the properties panel UI"""
        y_offset = 10
        
        # Current tool display
        tool_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 290, 25),
            text="Current Tool: Tile Brush",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(tool_label)
        y_offset += 35
        
        # Selection info
        self.selection_info = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, y_offset, 290, 150),
            html_text="<b>Selection Info:</b><br>Click on the map to see tile information",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.selection_info)
        y_offset += 160
        
        # Map statistics
        stats_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 290, 25),
            text="Map Statistics:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(stats_label)
        y_offset += 30
        
        self.map_stats = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, y_offset, 290, 120),
            html_text="<b>Map Stats:</b><br>Size: 256x256<br>Entities: 0<br>Zoom: 100%",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.map_stats)
        y_offset += 130
        
        # Controls help
        help_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_offset, 290, 25),
            text="Controls:",
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(help_label)
        y_offset += 30
        
        controls_text = """
        <b>Mouse:</b><br>
        • Left Click: Paint/Place<br>
        • Right Click: Erase<br>
        • Middle Click: Pan<br>
        • Wheel: Zoom<br><br>
        <b>Keyboard:</b><br>
        • 1-5: Select Tools<br>
        • G: Toggle Grid<br>
        • P: Toggle Palette<br>
        • Arrows: Move Camera<br>
        • Ctrl+S: Save<br>
        • Ctrl+O: Open
        """
        
        self.controls_help = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(10, y_offset, 290, 200),
            html_text=controls_text,
            manager=self.ui_manager,
            container=self.properties_panel
        )
        self.ui_elements.append(self.controls_help)
        
    def _initialize_core_editor(self):
        """Initialize the core map editor with embedded canvas"""
        try:
            # Calculate canvas area (excluding UI padding)
            canvas_area_width = self.canvas_width - 20
            canvas_area_height = self.canvas_height - 40
            
            # Initialize core editor
            self.core_editor = CoreMapEditor(
                map_width=self.map_width,
                map_height=self.map_height,
                tile_size=self.tile_size,
                screen_width=canvas_area_width,
                screen_height=canvas_area_height,
                aseprite_integration=self.aseprite_integration
            )
            
            # Override the core editor's camera viewport to match our canvas
            self.core_editor.camera.set_viewport(pygame.Rect(0, 0, canvas_area_width, canvas_area_height))
            
            # COMPLETELY DISABLE the core editor's highlighting
            self._disable_core_editor_highlighting()
            
            # Create canvas surface for rendering
            self.canvas_surface = pygame.Surface((canvas_area_width, canvas_area_height))
            
            # Force initial render to populate the canvas
            self.core_editor.render(self.canvas_surface)
            
            print("Core map editor initialized successfully")
            self._update_status("Map editor ready")
            
        except Exception as e:
            print(f"Error initializing core editor: {e}")
            import traceback
            traceback.print_exc()
            self._update_status(f"Error: {e}")



    
    def _update_status(self, message):
        """Update the status label"""
        if self.status_label:
            self.status_label.set_text(message)
    
    def _update_tool_display(self):
        """Update the tool display in properties panel"""
        if not self.core_editor:
            return
        
        tool_name = self.core_editor.current_tool.value.replace('_', ' ').title()
        
        if self.core_editor.current_tool == EditorTool.TILE_BRUSH:
            tool_name += f" ({self.core_editor.selected_tile_type})"
        elif self.core_editor.current_tool == EditorTool.ENTITY_PLACER:
            tool_name += f" ({self.core_editor.selected_entity_type})"
        
        # Update tool label (find it in UI elements)
        for element in self.ui_elements:
            if hasattr(element, 'text') and element.text.startswith("Current Tool:"):
                element.set_text(f"Current Tool: {tool_name}")
                break
    
    def _update_map_stats(self):
        """Update map statistics display"""
        if not self.core_editor or not self.map_stats:
            return
        
        entity_count = 0
        if hasattr(self.core_editor.world_map, 'entity_tile_manager'):
            entity_count = len(self.core_editor.world_map.entity_tile_manager.entity_tiles)
        
        zoom_percent = int(self.core_editor.camera.zoom * 100)
        
        stats_html = f"""
        <b>Map Statistics:</b><br>
        Size: {self.core_editor.map_width}x{self.core_editor.map_height}<br>
        Entities: {entity_count}<br>
        Zoom: {zoom_percent}%<br>
        Tool: {self.core_editor.current_tool.value}
        """
        
        self.map_stats.html_text = stats_html
        self.map_stats.rebuild()
    
    def _update_selection_info(self, tile_x=None, tile_y=None):
        """Update selection information display"""
        if not self.selection_info:
            return
        
        if tile_x is None or tile_y is None:
            html_text = "<b>Selection Info:</b><br>Click on the map to see tile information"
        else:
            if self.core_editor and self.core_editor.world_map:
                tile = self.core_editor.world_map.get_tile(tile_x, tile_y)
                terrain = tile.type if tile else "empty"
                
                entity = None
                if hasattr(self.core_editor.world_map, 'entity_tile_manager'):
                    entity_tile = self.core_editor.world_map.entity_tile_manager.get_entity_tile_at(tile_x, tile_y)
                    if entity_tile:
                        entity = entity_tile.tile_type
                
                html_text = f"""
                <b>Tile ({tile_x}, {tile_y})</b><br>
                <b>Terrain:</b> {terrain}<br>
                """
                
                if entity:
                    html_text += f"<b>Entity:</b> {entity}<br>"
                
                html_text += f"<b>Walkable:</b> {tile.is_walkable() if tile else 'No'}<br>"
            else:
                html_text = f"<b>Tile ({tile_x}, {tile_y})</b><br>No map data"
        
        self.selection_info.html_text = html_text
        self.selection_info.rebuild()
    
    def _handle_canvas_interaction(self, event):
        """Handle mouse interactions with the canvas"""
        if not self.core_editor or not self.map_canvas or not self.main_panel:
            return False
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Calculate canvas absolute position
        canvas_rect = self.map_canvas.relative_rect
        main_panel_rect = self.main_panel.relative_rect
        canvas_abs_x = main_panel_rect.x + canvas_rect.x + 10  # +10 for canvas padding
        canvas_abs_y = main_panel_rect.y + canvas_rect.y + 40  # +40 for label
        
        # Calculate the actual editing area (excluding palette if visible)
        edit_area_width = self.canvas_width - (self.core_editor.palette_width if self.core_editor.show_palette else 0)
        
        # Check if event is within canvas bounds
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
            canvas_x = event.pos[0] - canvas_abs_x
            canvas_y = event.pos[1] - canvas_abs_y
            
            # Check if mouse is within the EDITING area (not the palette area)
            mouse_in_edit_area = (0 <= canvas_x <= edit_area_width and 
                                0 <= canvas_y <= self.canvas_surface.get_height())
            
            if mouse_in_edit_area:
                # Store current mouse position for highlighting
                self._current_mouse_pos = (canvas_x, canvas_y)
                
                # Create a modified event with canvas-relative coordinates
                canvas_event = type('Event', (), {})()
                canvas_event.type = event.type
                canvas_event.pos = (canvas_x, canvas_y)
                
                if hasattr(event, 'button'):
                    canvas_event.button = event.button
                if hasattr(event, 'rel'):
                    canvas_event.rel = event.rel
                
                # Pass to core editor
                handled = self.core_editor.handle_event(canvas_event)
                
                # Update selection info for clicks
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    world_x, world_y = self.core_editor.camera.screen_to_world(canvas_x, canvas_y)
                    tile_x = int(world_x // self.tile_size)
                    tile_y = int(world_y // self.tile_size)
                    self._update_selection_info(tile_x, tile_y)
                
                return handled
            else:
                # Mouse is outside edit area - clear highlight and let core editor handle palette
                if event.type == pygame.MOUSEMOTION:
                    self._current_mouse_pos = None
                
                # If mouse is in palette area, pass the event with proper coordinates
                if (canvas_x > edit_area_width and canvas_x <= self.canvas_width and
                    0 <= canvas_y <= self.canvas_surface.get_height()):
                    
                    # Create event with canvas-relative coordinates for palette
                    canvas_event = type('Event', (), {})()
                    canvas_event.type = event.type
                    canvas_event.pos = (canvas_x, canvas_y)
                    
                    if hasattr(event, 'button'):
                        canvas_event.button = event.button
                    if hasattr(event, 'rel'):
                        canvas_event.rel = event.rel
                    
                    return self.core_editor.handle_event(canvas_event)
                
                return False
        
        elif event.type == pygame.MOUSEWHEEL:
            # Handle zoom for edit area only
            canvas_x = mouse_pos[0] - canvas_abs_x
            canvas_y = mouse_pos[1] - canvas_abs_y
            
            if (0 <= canvas_x <= edit_area_width and 
                0 <= canvas_y <= self.canvas_surface.get_height()):
                
                canvas_event = type('Event', (), {})()
                canvas_event.type = event.type
                canvas_event.y = event.y
                
                return self.core_editor.handle_event(canvas_event)
        
        return False


    def _render_mouse_highlight(self, surface):
        """Render mouse highlight directly on the canvas surface"""
        # Only render highlight if mouse is actually over the canvas
        if not self.core_editor or not hasattr(self, '_current_mouse_pos') or self._current_mouse_pos is None:
            return
        
        canvas_x, canvas_y = self._current_mouse_pos
        
        # Convert canvas coordinates to world coordinates
        world_x, world_y = self.core_editor.camera.screen_to_world(canvas_x, canvas_y)
        
        # Convert world coordinates to tile coordinates
        tile_x = int(world_x // self.tile_size)
        tile_y = int(world_y // self.tile_size)
        
        # Convert tile coordinates back to screen coordinates for rendering
        screen_x, screen_y = self.core_editor.camera.world_to_screen(
            tile_x * self.tile_size, 
            tile_y * self.tile_size
        )
        
        # Calculate tile size on screen (accounting for zoom)
        tile_screen_size = int(self.tile_size * self.core_editor.camera.zoom)
        
        # Create highlight rect
        highlight_rect = pygame.Rect(
            int(screen_x), 
            int(screen_y), 
            tile_screen_size, 
            tile_screen_size
        )
        
        # Only draw if the highlight is within the canvas bounds
        if (highlight_rect.right > 0 and highlight_rect.left < surface.get_width() and
            highlight_rect.bottom > 0 and highlight_rect.top < surface.get_height()):
            
            # Draw yellow highlight for current tool
            if self.core_editor.current_tool == EditorTool.TILE_BRUSH:
                pygame.draw.rect(surface, (255, 255, 0), highlight_rect, 2)  # Yellow border
            elif self.core_editor.current_tool == EditorTool.ENTITY_PLACER:
                pygame.draw.rect(surface, (0, 255, 255), highlight_rect, 2)  # Cyan border
            elif self.core_editor.current_tool == EditorTool.ERASER:
                pygame.draw.rect(surface, (255, 0, 0), highlight_rect, 2)  # Red border
            else:
                pygame.draw.rect(surface, (255, 255, 255), highlight_rect, 1)  # White border for other tools



    def handle_event(self, event):
        """Handle UI events"""
        # Handle keyboard shortcuts globally first
        if event.type == pygame.KEYDOWN and self.core_editor:
            handled = self.core_editor.handle_event(event)
            if handled:
                self._update_tool_display()
                self._update_map_stats()
                return True
        
        # Handle mouse events - check palette area FIRST before canvas
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL]:
            if self.core_editor and self.core_editor.show_palette and self.map_canvas and self.main_panel:
                mouse_pos = pygame.mouse.get_pos()
                
                # Calculate canvas area first
                canvas_rect = self.map_canvas.relative_rect
                main_panel_rect = self.main_panel.relative_rect
                canvas_abs_x = main_panel_rect.x + canvas_rect.x + 10
                canvas_abs_y = main_panel_rect.y + canvas_rect.y + 40
                
                # Calculate palette area - this MUST match exactly where core_editor renders it
                # The core editor renders palette at: canvas_x + (canvas_width - palette_width)
                canvas_area_width = self.canvas_width - 20  # Subtract padding
                palette_x = canvas_abs_x + (canvas_area_width - self.core_editor.palette_width)
                palette_y = canvas_abs_y
                palette_rect = pygame.Rect(palette_x, palette_y, self.core_editor.palette_width, self.canvas_height - 40)
                
                # If mouse is over palette, handle palette interaction directly
                if palette_rect.collidepoint(mouse_pos):
                    # Clear map highlight
                    self._current_mouse_pos = None
                    
                    # Convert to palette-relative coordinates (relative to palette top-left)
                    palette_relative_x = mouse_pos[0] - palette_x
                    palette_relative_y = mouse_pos[1] - palette_y
                    
                    # Handle palette click directly
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.core_editor.current_tool.value == "tile_brush":
                            # Check tile palette with correct coordinates
                            selected_tile = self.core_editor.tile_palette.get_tile_at_pos(
                                (palette_relative_x, palette_relative_y), 
                                pygame.Rect(0, 0, self.core_editor.palette_width, self.canvas_height - 40)
                            )
                            if selected_tile:
                                self.core_editor.selected_tile_type = selected_tile
                                self.core_editor.tile_palette.selected_tile = selected_tile
                                self._update_tool_display()
                                self._update_status(f"Selected tile: {selected_tile}")
                                return True
                        
                        elif self.core_editor.current_tool.value == "entity_placer":
                            # Check entity palette with correct coordinates
                            selected_entity = self.core_editor.entity_palette.get_entity_at_pos(
                                (palette_relative_x, palette_relative_y),
                                pygame.Rect(0, 0, self.core_editor.palette_width, self.canvas_height - 40)
                            )
                            if selected_entity:
                                self.core_editor.selected_entity_type = selected_entity
                                self.core_editor.entity_palette.selected_entity = selected_entity
                                self._update_tool_display()
                                self._update_status(f"Selected entity: {selected_entity}")
                                return True
                    
                    # Handle palette scrolling
                    elif event.type == pygame.MOUSEWHEEL:
                        palette_event = type('Event', (), {})()
                        palette_event.type = event.type
                        palette_event.pos = (palette_relative_x, palette_relative_y)
                        palette_event.y = event.y
                        
                        if self.core_editor.current_tool.value == "tile_brush":
                            self.core_editor.tile_palette.handle_event(palette_event)
                        elif self.core_editor.current_tool.value == "entity_placer":
                            self.core_editor.entity_palette.handle_event(palette_event)
                        return True
                    
                    return True  # Consume the event
        
        # Now try canvas interaction (only if not handled by palette)
        canvas_handled = self._handle_canvas_interaction(event)
        if canvas_handled:
            self._update_tool_display()
            self._update_map_stats()
            return True
        
        # Handle UI button events (side panels, etc.)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, 'text'):
                button_text = event.ui_element.text
                
                if button_text == "Close":
                    self.close()
                    return True
                
                elif button_text == "New":
                    self._create_new_map()
                    return True
                
                elif button_text == "Save":
                    self._save_map()
                    return True
                
                elif button_text == "Load":
                    self._load_map_dialog()
                    return True
                
                elif button_text.startswith("Toggle Grid"):
                    if self.core_editor:
                        self.core_editor.show_grid = not self.core_editor.show_grid
                        self._update_status(f"Grid {'enabled' if self.core_editor.show_grid else 'disabled'}")
                    return True
                
                elif button_text.startswith("Toggle Palette"):
                    if self.core_editor:
                        self.core_editor.show_palette = not self.core_editor.show_palette
                        self._update_status(f"Palette {'shown' if self.core_editor.show_palette else 'hidden'}")
                    return True
                
                elif button_text == "Show Advanced Tools":
                    self._toggle_advanced_tools()
                    return True
                
                # Tool selection buttons
                elif hasattr(event.ui_element, 'tool_id'):
                    tool_id = event.ui_element.tool_id
                    if self.core_editor:
                        self.core_editor.current_tool = EditorTool(tool_id)
                        self._update_tool_display()
                        self._update_status(f"Selected tool: {tool_id.replace('_', ' ').title()}")
                    return True
        
        # If we get here, the event wasn't handled by the map editor
        return False

    def _create_new_map(self):
        """Create a new map"""
        try:
            # Get dimensions from input fields
            try:
                new_width = int(self.width_input.get_text())
                new_height = int(self.height_input.get_text())
            except ValueError:
                new_width = 256
                new_height = 256
                self.width_input.set_text("256")
                self.height_input.set_text("256")
            
            self.map_width = new_width
            self.map_height = new_height
            
            if self.core_editor:
                self.core_editor.map_width = new_width
                self.core_editor.map_height = new_height
                self.core_editor.new_map()
                
            self._update_status(f"Created new map: {new_width}x{new_height}")
            self._update_map_stats()
            
        except Exception as e:
            print(f"Error creating new map: {e}")
            self._update_status(f"Error creating map: {e}")
    
    def _save_map(self):
        """Save the current map"""
        if not self.core_editor:
            self._update_status("No map to save")
            return
        
        try:
            # Generate filename with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"studio_map_{timestamp}"
            
            self.core_editor.save_map(filename)
            self._update_status(f"Map saved: {filename}")
            
        except Exception as e:
            print(f"Error saving map: {e}")
            self._update_status(f"Error saving map: {e}")
    
    def _load_map_dialog(self):
        """Show load map dialog"""
        if not self.core_editor:
            return
        
        try:
            # Get available maps
            available_maps = self.core_editor.serializer.list_maps()
            
            if not available_maps:
                self._update_status("No maps found to load")
                return
            
            # For now, load the first available map
            # In a full implementation, you'd show a proper selection dialog
            first_map = available_maps[0]
            loaded_map = self.core_editor.load_map(first_map)
            
            if loaded_map:
                self.map_width = loaded_map.width
                self.map_height = loaded_map.height
                self.width_input.set_text(str(self.map_width))
                self.height_input.set_text(str(self.map_height))
                self._update_status(f"Loaded map: {first_map}")
                self._update_map_stats()
            else:
                self._update_status("Failed to load map")
                
        except Exception as e:
            print(f"Error loading map: {e}")
            self._update_status(f"Error loading map: {e}")
    
    def _toggle_advanced_tools(self):
        """Toggle advanced tools visibility"""
        self.show_advanced_tools = not self.show_advanced_tools
        
        # Update button text
        for element in self.ui_elements:
            if (hasattr(element, 'text') and 
                element.text in ["Show Advanced Tools", "Hide Advanced Tools"]):
                element.set_text("Hide Advanced Tools" if self.show_advanced_tools else "Show Advanced Tools")
                break
        
        # Initialize Aseprite integration if showing advanced tools
        if self.show_advanced_tools and not self.aseprite_integration:
            self._initialize_aseprite_integration()
        
        self._update_status(f"Advanced tools {'shown' if self.show_advanced_tools else 'hidden'}")
    
    def _initialize_aseprite_integration(self):
        """Initialize Aseprite integration if available"""
        try:
            # Try common Aseprite installation paths
            aseprite_paths = [
                "C:/Program Files/Aseprite/Aseprite.exe",
                "C:/Program Files (x86)/Aseprite/Aseprite.exe",
                "/usr/bin/aseprite",
                "/Applications/Aseprite.app/Contents/MacOS/aseprite"
            ]
            
            for path in aseprite_paths:
                if os.path.exists(path):
                    self.aseprite_integration = AsepriteIntegration(path)
                    if self.aseprite_integration.is_available:
                        self._update_status("Aseprite integration enabled")
                        return
            
            self._update_status("Aseprite not found - using built-in tools")
            
        except Exception as e:
            print(f"Error initializing Aseprite: {e}")
            self._update_status("Aseprite integration failed")
    
    def update(self, time_delta):
        """Update the map editor"""
        if self.core_editor:
            self.core_editor.update()
    
    def render(self, surface):
        """Render the map editor"""
        if not self.visible or not self.core_editor or not self.canvas_surface:
            return
        
        try:
            # Clear canvas surface
            self.canvas_surface.fill((40, 40, 40))
            
            # ALWAYS render the core editor to our canvas surface (map stays visible)
            self.core_editor.render(self.canvas_surface)
            
            # Add our custom mouse highlight on top (only if mouse is over canvas)
            self._render_mouse_highlight(self.canvas_surface)
            
            # Get canvas position on screen
            if self.map_canvas and self.main_panel:
                canvas_rect = self.map_canvas.relative_rect
                main_panel_rect = self.main_panel.relative_rect
                
                # Calculate where to blit the canvas surface
                blit_x = main_panel_rect.x + canvas_rect.x + 10
                blit_y = main_panel_rect.y + canvas_rect.y + 40
                
                # Blit the canvas surface to the screen
                surface.blit(self.canvas_surface, (blit_x, blit_y))
                
        except Exception as e:
            print(f"Error rendering map editor: {e}")
    
    def close(self):
        """Close the map editor and clean up resources"""
        try:
            # Clean up Aseprite integration
            if self.aseprite_integration:
                self.aseprite_integration.cleanup()
            
            # Clean up core editor
            if self.core_editor:
                # Save any unsaved changes prompt could go here
                pass
            
            print("Map editor closed")
            
        except Exception as e:
            print(f"Error closing map editor: {e}")
        
        # Call parent close
        super().close()
    
    def get_map_data(self):
        """Get the current map data for integration with other studio tools"""
        if not self.core_editor or not self.core_editor.world_map:
            return None
        
        try:
            # Return map data that other studio tools can use
            map_data = {
                "width": self.core_editor.world_map.width,
                "height": self.core_editor.world_map.height,
                "world_map": self.core_editor.world_map,
                "entity_count": len(self.core_editor.world_map.entity_tile_manager.entity_tiles) 
                              if hasattr(self.core_editor.world_map, 'entity_tile_manager') else 0,
                "serializer": self.core_editor.serializer
            }
            return map_data
            
        except Exception as e:
            print(f"Error getting map data: {e}")
            return None
    
    def load_map_from_data(self, map_data):
        """Load a map from external data (for studio integration)"""
        if not self.core_editor:
            return False
        
        try:
            if "world_map" in map_data:
                self.core_editor.world_map = map_data["world_map"]
                self.map_width = map_data.get("width", 256)
                self.map_height = map_data.get("height", 256)
                
                # Update UI
                self.width_input.set_text(str(self.map_width))
                self.height_input.set_text(str(self.map_height))
                
                self._update_status("Map loaded from studio")
                self._update_map_stats()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error loading map from data: {e}")
            return False
    
    def export_map_for_game(self, export_path=None):
        """Export the current map in game-ready format"""
        if not self.core_editor:
            self._update_status("No map to export")
            return False
        
        try:
            if not export_path:
                # Use default export location
                export_path = os.path.join(project_root, "maps", "exported")
                os.makedirs(export_path, exist_ok=True)
            
            # Generate export filename
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"game_map_{timestamp}"
            
            # Save using the serializer
            success = self.core_editor.serializer.save_map(
                self.core_editor.world_map, 
                os.path.join(export_path, export_filename)
            )
            
            if success:
                self._update_status(f"Map exported: {export_filename}")
                return True
            else:
                self._update_status("Export failed")
                return False
                
        except Exception as e:
            print(f"Error exporting map: {e}")
            self._update_status(f"Export error: {e}")
            return False
    
    def get_editor_statistics(self):
        """Get detailed statistics about the current editing session"""
        if not self.core_editor:
            return {}
        
        try:
            stats = {
                "map_size": f"{self.core_editor.map_width}x{self.core_editor.map_height}",
                "current_tool": self.core_editor.current_tool.value,
                "zoom_level": f"{int(self.core_editor.camera.zoom * 100)}%",
                "grid_enabled": self.core_editor.show_grid,
                "palette_visible": self.core_editor.show_palette,
                "entity_count": 0,
                "tile_types_used": set()
            }
            
            # Count entities and tile types
            if self.core_editor.world_map:
                if hasattr(self.core_editor.world_map, 'entity_tile_manager'):
                    stats["entity_count"] = len(self.core_editor.world_map.entity_tile_manager.entity_tiles)
                
                # Sample tile types (checking a subset for performance)
                for y in range(0, min(self.core_editor.map_height, 100), 10):
                    for x in range(0, min(self.core_editor.map_width, 100), 10):
                        tile = self.core_editor.world_map.get_tile(x, y)
                        if tile:
                            stats["tile_types_used"].add(tile.type)
                
                stats["tile_types_used"] = list(stats["tile_types_used"])
            
            return stats
            
        except Exception as e:
            print(f"Error getting editor statistics: {e}")
            return {}
    
    def set_tool(self, tool_name):
        """Set the current editing tool programmatically"""
        if not self.core_editor:
            return False
        
        try:
            # Map tool names to EditorTool enum
            tool_mapping = {
                "tile_brush": EditorTool.TILE_BRUSH,
                "entity_placer": EditorTool.ENTITY_PLACER,
                "eraser": EditorTool.ERASER,
                "selector": EditorTool.SELECTOR,
                "fill": EditorTool.FILL
            }
            
            if tool_name in tool_mapping:
                self.core_editor.current_tool = tool_mapping[tool_name]
                self._update_tool_display()
                self._update_status(f"Tool changed to: {tool_name.replace('_', ' ').title()}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error setting tool: {e}")
            return False
    
    def set_selected_tile(self, tile_type):
        """Set the selected tile type for painting"""
        if not self.core_editor:
            return False
        
        try:
            if tile_type in self.core_editor.tile_palette.available_tiles:
                self.core_editor.selected_tile_type = tile_type
                self.core_editor.tile_palette.selected_tile = tile_type
                self._update_tool_display()
                self._update_status(f"Selected tile: {tile_type}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error setting tile type: {e}")
            return False
    
    def set_selected_entity(self, entity_type):
        """Set the selected entity type for placement"""
        if not self.core_editor:
            return False
        
        try:
            if entity_type in self.core_editor.entity_palette.available_entities:
                self.core_editor.selected_entity_type = entity_type
                self.core_editor.entity_palette.selected_entity = entity_type
                self._update_tool_display()
                self._update_status(f"Selected entity: {entity_type}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error setting entity type: {e}")
            return False
    
    def center_camera_on(self, x, y):
        """Center the camera on specific world coordinates"""
        if not self.core_editor:
            return False
        
        try:
            world_x = x * self.tile_size
            world_y = y * self.tile_size
            self.core_editor.camera.center_on(world_x, world_y)
            self._update_status(f"Camera centered on ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"Error centering camera: {e}")
            return False
    
    def set_zoom(self, zoom_level):
        """Set the camera zoom level"""
        if not self.core_editor:
            return False
        
        try:
            # Clamp zoom level to valid range
            zoom_level = max(self.core_editor.camera.min_zoom, 
                           min(self.core_editor.camera.max_zoom, zoom_level))
            
            self.core_editor.camera.zoom = zoom_level
            self._update_map_stats()
            self._update_status(f"Zoom set to {int(zoom_level * 100)}%")
            return True
            
        except Exception as e:
            print(f"Error setting zoom: {e}")
            return False
    
    def get_tile_at_position(self, x, y):
        """Get tile information at specific coordinates"""
        if not self.core_editor or not self.core_editor.world_map:
            return None
        
        try:
            if 0 <= x < self.core_editor.map_width and 0 <= y < self.core_editor.map_height:
                tile = self.core_editor.world_map.get_tile(x, y)
                
                tile_info = {
                    "x": x,
                    "y": y,
                    "type": tile.type if tile else "empty",
                    "walkable": tile.is_walkable() if tile else False,
                    "entity": None
                }
                
                # Check for entity at this position
                if hasattr(self.core_editor.world_map, 'entity_tile_manager'):
                    entity_tile = self.core_editor.world_map.entity_tile_manager.get_entity_tile_at(x, y)
                    if entity_tile:
                        tile_info["entity"] = {
                            "type": entity_tile.tile_type,
                            "base_x": entity_tile.base_x,
                            "base_y": entity_tile.base_y,
                            "width": entity_tile.width,
                            "height": entity_tile.height
                        }
                
                return tile_info
            
            return None
            
        except Exception as e:
            print(f"Error getting tile at position: {e}")
            return None

    def _disable_core_editor_highlighting(self):
        """Completely disable the core editor's built-in highlighting system"""
        if not self.core_editor:
            return
        
        # Store the original render method
        original_render = self.core_editor.render
        
        def render_without_highlight(surface):
            """Custom render method that skips highlighting"""
            # Temporarily disable any highlight rendering
            original_highlight_methods = {}
            
            # List of possible highlight rendering methods to disable
            highlight_methods = [
                '_render_cursor',  # THIS IS THE KEY ONE - it draws the white highlight
                '_render_mouse_highlight',
                'render_mouse_highlight', 
                'draw_highlight',
                'draw_mouse_highlight',
                '_draw_highlight',
                'render_highlight'
            ]
            
            # Replace all highlight methods with no-op functions
            for method_name in highlight_methods:
                if hasattr(self.core_editor, method_name):
                    original_highlight_methods[method_name] = getattr(self.core_editor, method_name)
                    setattr(self.core_editor, method_name, lambda *args, **kwargs: None)
            
            # Call the original render
            try:
                original_render(surface)
            finally:
                # Restore original methods
                for method_name, original_method in original_highlight_methods.items():
                    setattr(self.core_editor, method_name, original_method)
        
        # Replace the core editor's render method
        self.core_editor.render = render_without_highlight

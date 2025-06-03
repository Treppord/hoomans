import sys
import os
import json
import gzip
import base64
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                               QScrollArea, QFrame, QSplitter, QStackedWidget,
                               QGraphicsDropShadowEffect, QSpinBox, QComboBox,
                               QCheckBox, QGroupBox, QFormLayout, QLineEdit,
                               QDoubleSpinBox, QTreeWidget, QTreeWidgetItem, QMenu)
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon, QPainter, QLinearGradient
import pygame
from PySide6.QtWidgets import QSlider
import random
from studio.ui import ModernButton, CanvasWidget

# Import the map creator components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import map system components
from engine.systems.map_system import (
    MapSystem, MapGenerationConfig, MapGenerationType, TileType, BiomeType,
    create_default_map_config, create_island_map_config, create_dungeon_map_config
)

from world.tile import Tile
from world.map import WorldMap
from world.entity_tile import EntityTileManager, TreeEntityTile, HouseEntityTile
from world.biome_generator import ProceduralMapGenerator, BiomeType
from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import QPoint

class MapEditorWidget(QWidget):
    """Enhanced map editor widget with full tile and entity placement capabilities"""
    
    def __init__(self, project_name=None):
        super().__init__()
        self.current_project_name = project_name or "default"  # Store project name
        self.world_map = None
        self.current_tool = "tile_brush"
        self.selected_tile_type = "grass"
        self.selected_entity_type = "tree"
        self.grid_visible = True
        self.zoom_level = 1.0
        self.camera_x = 0
        self.camera_y = 0
        self.mouse_pressed = False
        self.last_paint_pos = None
        
        # Available tiles and entities
        self.available_tiles = [
            "empty", "wall", "grass", "water", "sand", "forest", 
            "mountain", "deep_water", "shallow_water", "rock", "path", "snow"
        ]
        self.available_entities = ["tree", "house"]
        
        self.setup_ui()
        self.setup_pygame()
        
    def setup_pygame(self):
        """Initialize pygame for map rendering"""
        pygame.init()
        # Initialize display properly for entity image loading
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
        # Create a surface for rendering
        self.pygame_screen = pygame.Surface((800, 600))
        
        # Fix entity textures for multi-tile entities
        self.fix_entity_textures()

    def fix_entity_textures(self):
        """Fix entity textures to proper multi-tile sizes"""
        from world.entity_tile import IMAGES
        
        # Fix tree texture (should be 16x32 for 1x2 tiles)
        if "tree" in IMAGES:
            tree_img = IMAGES["tree"]
            if tree_img.get_width() == 16 and tree_img.get_height() == 16:
                # Scale to proper tree size (16x32)
                new_tree = pygame.Surface((16, 32), pygame.SRCALPHA)
                new_tree.fill((0, 0, 0, 0))  # Transparent
                # Put the tree image in the bottom half (trunk area)
                new_tree.blit(tree_img, (0, 16))
                # Create leaves in the top half
                leaves_surface = pygame.Surface((16, 16), pygame.SRCALPHA)
                leaves_surface.fill((0, 120, 0, 180))  # Semi-transparent green
                new_tree.blit(leaves_surface, (0, 0))
                IMAGES["tree"] = new_tree
                print("Fixed tree texture to 16x32")
        
        # Fix house texture (should be 32x32 for 2x2 tiles)
        if "house" in IMAGES:
            house_img = IMAGES["house"]
            if house_img.get_width() == 16 and house_img.get_height() == 16:
                # Scale to proper house size (32x32)
                new_house = pygame.Surface((32, 32), pygame.SRCALPHA)
                new_house.fill((0, 0, 0, 0))  # Transparent
                
                # Create a simple house pattern
                # Roof (top half)
                roof_color = (139, 69, 19)  # Brown
                pygame.draw.rect(new_house, roof_color, (0, 0, 32, 16))
                
                # Walls (bottom half)
                wall_color = (160, 82, 45)  # Saddle brown
                pygame.draw.rect(new_house, wall_color, (0, 16, 32, 16))
                
                # Door (bottom right)
                door_color = (101, 67, 33)  # Dark brown
                pygame.draw.rect(new_house, door_color, (20, 20, 8, 12))
                
                IMAGES["house"] = new_house
                print("Fixed house texture to 32x32")
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left panel - Enhanced controls
        controls_panel = self.create_enhanced_controls_panel()
        controls_panel.setFixedWidth(320)
        
        # Right panel - Map canvas
        canvas_panel = self.create_canvas_panel()
        
        layout.addWidget(controls_panel)
        layout.addWidget(canvas_panel)
        
    def handle_zoom(self, direction, mouse_pos):
        """Handle mouse wheel zooming - zoom towards mouse cursor"""
        if not self.world_map:
            return
            
        # Calculate zoom factor based on direction
        zoom_factor = 1.1 if direction > 0 else 0.9
        old_zoom = self.zoom_level
        
        # Apply zoom with limits
        self.zoom_level = max(0.25, min(4.0, self.zoom_level * zoom_factor))
        
        if old_zoom != self.zoom_level:
            # Update display without changing camera position
            self.update_canvas()
            self.update_zoom_info()


    def start_pan(self, pos):
        """Start panning with middle mouse button"""
        self.panning = True
        self.pan_start_pos = pos
        self.pan_start_camera = (self.camera_x, self.camera_y)

    def update_pan(self, pos):
        """Update camera position during panning"""
        if hasattr(self, 'panning') and self.panning:
            # Simple delta movement
            delta_x = pos.x() - self.pan_start_pos.x()
            delta_y = pos.y() - self.pan_start_pos.y()
            
            self.camera_x = self.pan_start_camera[0] + delta_x
            self.camera_y = self.pan_start_camera[1] + delta_y
            
            self.update_canvas()

    def stop_pan(self):
        """Stop panning"""
        self.panning = False

    def update_zoom_info(self):
        """Update the zoom information display"""
        if hasattr(self, 'zoom_info'):
            zoom_percent = int(self.zoom_level * 100)
            self.zoom_info.setText(f"Zoom: {zoom_percent}% (Mouse wheel to zoom)")

    def toggle_grid(self, enabled):
        """Toggle grid visibility"""
        self.grid_visible = enabled
        self.update_canvas()
        
    def create_enhanced_controls_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-right: 1px solid rgba(0, 0, 0, 0.08);
            }
            QGroupBox {
                color: #000000;
                font-weight: bold;
                margin-top: 10px;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: transparent;
                color: #000000;
            }
            QLabel {
                color: #000000;
                background: transparent;
            }
            QSpinBox, QComboBox {
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: white;
                border: 1px solid #ddd;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                color: #000000;
            }
            QSpinBox QLineEdit {
                color: #000000;
                background: white;
            }
            QComboBox::drop-down {
                background: white;
                border: 1px solid #ddd;
            }
            QComboBox::down-arrow {
                color: #000000;
            }
            QCheckBox {
                color: #000000;
                background: transparent;
            }
            QCheckBox::indicator {
                background: white;
                border: 1px solid #ddd;
            }
            QPushButton {
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: rgba(74, 144, 226, 0.1);
                border: 1px solid #4A90E2;
                color: #000000;
            }
            QPushButton:checked {
                background: #4A90E2;
                color: white;
                border: 1px solid #4A90E2;
            }
            QPushButton:pressed {
                background: #357ABD;
                color: white;
            }
        """)
        
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(74, 144, 226, 0.7);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(74, 144, 226, 1.0);
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Map Editor")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("""
            QLabel {
                color: #000000; 
                padding: 10px 0px;
                background: transparent;
            }
        """)
        layout.addWidget(title)
        
        # Tools section
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout(tools_group)
        
        self.tool_buttons = {}
        tools = [
            ("tile_brush", "🖌️ Tile Brush"),
            ("entity_placer", "🏠 Entity Placer"),
            ("eraser", "🗑️ Eraser"),
            ("selector", "👆 Selector"),
            ("fill", "🪣 Fill Tool")
        ]
        
        for tool_id, tool_name in tools:
            btn = QPushButton(tool_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tool_id: self.select_tool(t))
            self.tool_buttons[tool_id] = btn
            tools_layout.addWidget(btn)
            
        # Set default tool
        self.tool_buttons["tile_brush"].setChecked(True)
        layout.addWidget(tools_group)
        
        # Tile palette
        tiles_group = QGroupBox("Tile Palette")
        tiles_layout = QGridLayout(tiles_group)
        
        self.tile_buttons = {}
        for i, tile_type in enumerate(self.available_tiles):
            btn = QPushButton(tile_type.replace("_", " ").title())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tile_type: self.select_tile(t))
            self.tile_buttons[tile_type] = btn
            tiles_layout.addWidget(btn, i // 3, i % 3)
            
        # Set default tile
        self.tile_buttons["grass"].setChecked(True)
        layout.addWidget(tiles_group)
        
        # Entity palette
        entities_group = QGroupBox("Entity Palette")
        entities_layout = QVBoxLayout(entities_group)
        
        self.entity_buttons = {}
        for entity_type in self.available_entities:
            btn = QPushButton(entity_type.replace("_", " ").title())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, e=entity_type: self.select_entity(e))
            self.entity_buttons[entity_type] = btn
            entities_layout.addWidget(btn)
            
        # Set default entity
        self.entity_buttons["tree"].setChecked(True)
        layout.addWidget(entities_group)
        
        # Map generation section
        generation_group = QGroupBox("Map Generation")
        gen_layout = QFormLayout(generation_group)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(32, 512)
        self.width_spin.setValue(128)
        self.width_spin.setStyleSheet("color: #000000; background: white;")

        width_label = QLabel("Width:")
        width_label.setStyleSheet("color: #000000; background: transparent;")
        gen_layout.addRow(width_label, self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(32, 512)
        self.height_spin.setValue(128)
        self.height_spin.setStyleSheet("color: #000000; background: white;")

        height_label = QLabel("Height:")
        height_label.setStyleSheet("color: #000000; background: transparent;")
        gen_layout.addRow(height_label, self.height_spin)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setValue(random.randint(0, 999999))
        self.seed_spin.setStyleSheet("color: #000000; background: white;")

        seed_label = QLabel("Seed:")
        seed_label.setStyleSheet("color: #000000; background: transparent;")
        gen_layout.addRow(seed_label, self.seed_spin)

        self.generate_btn = ModernButton("Generate Map", primary=True)
        self.generate_btn.clicked.connect(self.generate_new_map)
        gen_layout.addWidget(self.generate_btn)

        layout.addWidget(generation_group)
        
        # View controls
        view_group = QGroupBox("View Controls")
        view_layout = QVBoxLayout(view_group)
        
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.toggle_grid)
        view_layout.addWidget(self.grid_checkbox)
        
        # Add zoom info label
        self.zoom_info = QLabel("Zoom: 100% (Mouse wheel to zoom)")
        self.zoom_info.setStyleSheet("""
            QLabel {
                color: #000000; 
                font-size: 11px; 
                padding: 5px;
                background: transparent;
            }
        """)
        view_layout.addWidget(self.zoom_info)
        
        layout.addWidget(view_group)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        self.new_btn = ModernButton("New Map")
        self.new_btn.clicked.connect(self.new_map)
        file_layout.addWidget(self.new_btn)
        
        self.save_btn = ModernButton("Save Map")
        self.save_btn.clicked.connect(self.save_map)
        self.save_btn.setEnabled(False)
        file_layout.addWidget(self.save_btn)
        
        self.load_btn = ModernButton("Load Map")
        self.load_btn.clicked.connect(self.load_map)
        file_layout.addWidget(self.load_btn)
        
        self.export_btn = ModernButton("Export Image")
        self.export_btn.clicked.connect(self.export_image)
        self.export_btn.setEnabled(False)
        file_layout.addWidget(self.export_btn)
        
        layout.addWidget(file_group)
        
        layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        return scroll_area


    def create_canvas_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: none;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Canvas info
        self.canvas_info = QLabel("Create or generate a map to start editing")
        self.canvas_info.setStyleSheet("color: #2c3e50; padding: 5px 0px;")
        layout.addWidget(self.canvas_info)
        
        # Create a custom widget for the canvas that properly handles mouse events
        self.canvas_widget = CanvasWidget(self)
        self.canvas_widget.setMinimumSize(600, 400)
        self.canvas_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px dashed rgba(149, 165, 166, 0.5);
                border-radius: 8px;
            }
        """)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(74, 144, 226, 0.7);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(74, 144, 226, 1.0);
            }
            QScrollBar:horizontal {
                background: rgba(0, 0, 0, 0.1);
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(74, 144, 226, 0.7);
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(74, 144, 226, 1.0);
            }
        """)
        layout.addWidget(scroll_area)
        
        return panel

        
    def select_tool(self, tool_id):
        """Select a tool and update UI"""
        self.current_tool = tool_id
        for tool, btn in self.tool_buttons.items():
            btn.setChecked(tool == tool_id)
            
    def select_tile(self, tile_type):
        """Select a tile type"""
        self.selected_tile_type = tile_type
        for tile, btn in self.tile_buttons.items():
            btn.setChecked(tile == tile_type)
            
    def select_entity(self, entity_type):
        """Select an entity type"""
        self.selected_entity_type = entity_type
        for entity, btn in self.entity_buttons.items():
            btn.setChecked(entity == entity_type)

        
    def update_zoom(self, value):
        """Update zoom level"""
        self.zoom_level = value / 100.0
        self.update_canvas()
        
    def generate_new_map(self):
        """Generate a new map using the biome generator"""
        try:
            width = self.width_spin.value()
            height = self.height_spin.value()
            seed = self.seed_spin.value()
            
            self.generate_btn.setText("Generating...")
            self.generate_btn.setEnabled(False)
            
            # Create new world map
            self.world_map = WorldMap(width, height)
            
            # Generate realistic map
            self.world_map.generate_realistic_map(seed=seed)
            
            # Initialize entity system after map generation
            if hasattr(self.world_map, 'initialize_entity_tiles'):
                self.world_map.initialize_entity_tiles()
            
            self.update_canvas()
            self.update_canvas_info()
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            
            print(f"Generated {width}x{height} map with seed {seed}")

            
        except Exception as e:
            print(f"Error generating map: {e}")
        finally:
            self.generate_btn.setText("Generate Map")
            self.generate_btn.setEnabled(True)

    def new_map(self):
        """Create a new empty map"""
        try:
            width = self.width_spin.value()
            height = self.height_spin.value()
            
            # Create new world map with grass tiles
            self.world_map = WorldMap(width, height)
            self.world_map.initialize_entity_tiles()
            
            # Fill with grass
            for y in range(height):
                for x in range(width):
                    self.world_map.set_tile(x, y, "grass")
                    
            self.update_canvas()
            self.update_canvas_info()
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            
            print(f"Created new {width}x{height} map")
            
        except Exception as e:
            print(f"Error creating new map: {e}")

    def paint_at_position(self, pos):
        """Paint at the given position based on current tool"""
        if not self.world_map:
            return
            
        # Convert screen coordinates to world coordinates properly
        # Account for camera offset and zoom level
        tile_size = int(Tile.SIZE * self.zoom_level)

        # Apply same clamping as update_canvas
        if tile_size < 1:
            tile_size = 1
        elif tile_size > 1000:
            tile_size = 1000

        # Convert screen coordinates to tile coordinates using the clamped tile_size
        tile_x = int((pos.x() - self.camera_x) / tile_size)
        tile_y = int((pos.y() - self.camera_y) / tile_size)
        
        # Ensure we're within bounds
        if not (0 <= tile_x < self.world_map.width and 0 <= tile_y < self.world_map.height):
            return
            
        # Avoid painting same position repeatedly
        current_pos = (tile_x, tile_y)
        if self.last_paint_pos == current_pos:
            return
        self.last_paint_pos = current_pos
        
        try:
            if self.current_tool == "tile_brush":
                self.world_map.set_tile(tile_x, tile_y, self.selected_tile_type)
                
            elif self.current_tool == "entity_placer":
                # Check and initialize entity manager if needed
                if not hasattr(self.world_map, 'entity_manager') or self.world_map.entity_manager is None:
                    from world.entity_tile import EntityTileManager
                    self.world_map.entity_manager = EntityTileManager(self.world_map)
                
                if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager is not None:
                    # Remove existing entity at this position first
                    existing_entity = self.world_map.entity_manager.get_entity_tile_at(tile_x, tile_y)
                    if existing_entity:
                        self.world_map.entity_manager.remove_entity_tile(existing_entity)
                    
                    # Create and place new entity
                    entity = None
                    can_place = False
                    
                    if self.selected_entity_type == "tree":
                        from world.entity_tile import TreeEntityTile
                        # Tree is 1x2 (width x height)
                        if (tile_x >= 0 and tile_x < self.world_map.width and 
                            tile_y >= 0 and tile_y + 1 < self.world_map.height):
                            
                            entity = TreeEntityTile(tile_x, tile_y)
                            
                            # Check if both positions are clear
                            can_place = True
                            for pos in entity.get_all_positions():
                                existing = self.world_map.entity_manager.get_entity_tile_at(pos[0], pos[1])
                                if existing:
                                    can_place = False
                                    break
                            
                    elif self.selected_entity_type == "house":
                        from world.entity_tile import HouseEntityTile
                        # House is 2x2 (width x height)
                        if (tile_x >= 0 and tile_x + 1 < self.world_map.width and 
                            tile_y >= 0 and tile_y + 1 < self.world_map.height):
                            
                            entity = HouseEntityTile(tile_x, tile_y)
                            
                            # Check if all 4 positions are clear
                            can_place = True
                            for pos in entity.get_all_positions():
                                existing = self.world_map.entity_manager.get_entity_tile_at(pos[0], pos[1])
                                if existing:
                                    can_place = False
                                    break
                    
                    # Place the entity if we can
                    if entity and can_place:
                        self.world_map.entity_manager.add_entity_tile(entity)
                            
            elif self.current_tool == "eraser":
                # Remove entity if present
                if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager:
                    existing_entity = self.world_map.entity_manager.get_entity_tile_at(tile_x, tile_y)
                    if existing_entity:
                        self.world_map.entity_manager.remove_entity_tile(existing_entity)
                # Set to empty tile
                self.world_map.set_tile(tile_x, tile_y, "empty")
                
            elif self.current_tool == "selector":
                # Get tile and entity info
                tile = self.world_map.get_tile(tile_x, tile_y)
                print(f"Selected tile at ({tile_x}, {tile_y}): {tile.type if tile else 'None'}")
                
                if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager:
                    entity = self.world_map.entity_manager.get_entity_tile_at(tile_x, tile_y)
                    if entity:
                        print(f"Entity: {entity.__class__.__name__} at base ({entity.base_x}, {entity.base_y})")
                
            elif self.current_tool == "fill":
                self.flood_fill(tile_x, tile_y, self.selected_tile_type)
                
            self.update_canvas()
            
        except Exception as e:
            print(f"Error painting at position: {e}")
            import traceback
            traceback.print_exc()


            
    def flood_fill(self, start_x, start_y, new_tile_type):
        """Flood fill algorithm for fill tool"""
        if not self.world_map:
            return
            
        original_tile = self.world_map.get_tile(start_x, start_y)
        if not original_tile or original_tile.type == new_tile_type:
            return
            
        original_type = original_tile.type
        stack = [(start_x, start_y)]
        filled = set()
        
        while stack and len(filled) < 1000:  # Limit to prevent infinite loops
            x, y = stack.pop()
            
            if (x, y) in filled:
                continue
                
            if not (0 <= x < self.world_map.width and 0 <= y < self.world_map.height):
                continue
                
            tile = self.world_map.get_tile(x, y)
            if not tile or tile.type != original_type:
                continue
                
            # Fill this tile
            self.world_map.set_tile(x, y, new_tile_type)
            filled.add((x, y))
            
            # Add neighbors to stack
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                stack.append((x + dx, y + dy))
                    
    def update_canvas(self):
        """Update the canvas display with proper coordinate transformation"""
        if not self.world_map:
            return
            
        try:
            # Calculate tile size at current zoom
            tile_size = int(Tile.SIZE * self.zoom_level)
            
            # Prevent tile_size from being too small or too large
            if tile_size < 1:
                tile_size = 1
            elif tile_size > 1000:
                tile_size = 1000
            
            # Calculate canvas size
            canvas_width = self.world_map.width * tile_size
            canvas_height = self.world_map.height * tile_size
            
            # Limit canvas size to prevent memory issues
            max_canvas_size = 8192
            if canvas_width > max_canvas_size or canvas_height > max_canvas_size:
                scale_factor = min(max_canvas_size / canvas_width, max_canvas_size / canvas_height)
                canvas_width = int(canvas_width * scale_factor)
                canvas_height = int(canvas_height * scale_factor)
                tile_size = int(tile_size * scale_factor)
            
            # Create pygame surface
            surface = pygame.Surface((max(canvas_width, 1), max(canvas_height, 1)))
            surface.fill((255, 255, 255))  # White background
            
            # Render all tiles with consistent coordinate system
            for y in range(self.world_map.height):
                for x in range(self.world_map.width):
                    tile = self.world_map.get_tile(x, y)
                    if tile:
                        # Use exact same coordinate calculation as paint_at_position
                        screen_x = x * tile_size
                        screen_y = y * tile_size
                        
                        # Make sure we don't render outside the surface
                        if 0 <= screen_x < canvas_width and 0 <= screen_y < canvas_height:
                            tile.render(surface, screen_x, screen_y, tile_size, tile_size)
            
            # Render entities using consistent coordinate system
            if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager:
                # Create a camera that matches our coordinate system
                class EditorCamera:
                    def __init__(self, tile_size):
                        self.tile_size = tile_size
                        
                    def apply(self, world_x, world_y, width, height):
                        # Convert world coordinates (in pixels) to screen coordinates
                        # Use exact same calculation as paint_at_position
                        screen_x = int((world_x / Tile.SIZE) * self.tile_size)
                        screen_y = int((world_y / Tile.SIZE) * self.tile_size)
                        screen_width = int((width / Tile.SIZE) * self.tile_size)
                        screen_height = int((height / Tile.SIZE) * self.tile_size)
                        return (screen_x, screen_y, screen_width, screen_height)
                
                camera = EditorCamera(tile_size)
                
                # Render all entity tiles
                for entity in self.world_map.entity_manager.entity_tiles:
                    entity.render(surface, camera)
            
            # Render grid if enabled
            if self.grid_visible and tile_size >= 4:
                self.render_grid(surface, tile_size)
            
            # Convert to QPixmap
            w, h = surface.get_size()
            if w > 0 and h > 0:
                raw = pygame.image.tobytes(surface, 'RGB')
                
                from PySide6.QtGui import QImage
                qimg = QImage(raw, w, h, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                
                # Update canvas widget
                self.canvas_widget.set_pixmap(pixmap)
            
        except Exception as e:
            print(f"Error updating canvas: {e}")
            import traceback
            traceback.print_exc()

    def render_grid(self, surface, tile_size):
        """Render grid lines on the surface"""
        grid_color = (200, 200, 200)  # Light gray
        
        # Vertical lines
        for x in range(0, self.world_map.width + 1):
            start_pos = (x * tile_size, 0)
            end_pos = (x * tile_size, self.world_map.height * tile_size)
            pygame.draw.line(surface, grid_color, start_pos, end_pos, 1)
            
        # Horizontal lines
        for y in range(0, self.world_map.height + 1):
            start_pos = (0, y * tile_size)
            end_pos = (self.world_map.width * tile_size, y * tile_size)
            pygame.draw.line(surface, grid_color, start_pos, end_pos, 1)
            
    def update_canvas_info(self):
        """Update canvas information display"""
        if self.world_map:
            # Get entity count from entity manager
            entity_count = 0
            if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager:
                entity_count = len(self.world_map.entity_manager.entity_tiles)
                
            info_text = (f"Map: {self.world_map.width}x{self.world_map.height} "
                        f"| Entities: {entity_count} "
                        f"| Zoom: {int(self.zoom_level * 100)}%")
            self.canvas_info.setText(info_text)
            self.canvas_info.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    background: transparent;
                    padding: 5px 0px;
                    font-weight: medium;
                }
            """)
        else:
            self.canvas_info.setText("No map loaded")
            self.canvas_info.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    background: transparent;
                    padding: 5px 0px;
                    font-style: italic;
                }
            """)


    
    def compress_map_data(self, map_data):
        """Compress map data using gzip and base64 encoding"""
        try:
            # Convert to JSON string
            json_str = json.dumps(map_data, separators=(',', ':'))  # Compact JSON
            
            # Compress with gzip
            compressed_data = gzip.compress(json_str.encode('utf-8'))
            
            # Encode with base64 for safe storage
            encoded_data = base64.b64encode(compressed_data).decode('utf-8')
            
            return encoded_data
        except Exception as e:
            print(f"Error compressing map data: {e}")
            return None
    
    def decompress_map_data(self, compressed_data):
        """Decompress map data from base64 and gzip"""
        try:
            # Decode from base64
            compressed_bytes = base64.b64decode(compressed_data.encode('utf-8'))
            
            # Decompress with gzip
            json_str = gzip.decompress(compressed_bytes).decode('utf-8')
            
            # Parse JSON
            map_data = json.loads(json_str)
            
            return map_data
        except Exception as e:
            print(f"Error decompressing map data: {e}")
            return None
    
    def serialize_world_map(self):
        """Convert WorldMap to serializable dictionary"""
        if not self.world_map:
            return None
            
        try:
            # Create base map data
            map_data = {
                "version": "1.0",
                "width": self.world_map.width,
                "height": self.world_map.height,
                "tiles": [],
                "entities": []
            }
            
            # Serialize tiles efficiently
            for y in range(self.world_map.height):
                row = []
                for x in range(self.world_map.width):
                    tile = self.world_map.get_tile(x, y)
                    if tile:
                        # Store tile type and variation for patch-aware rendering
                        tile_data = {
                            "type": tile.type,
                            "variation": getattr(tile, 'variation', 0)
                        }
                        row.append(tile_data)
                    else:
                        row.append({"type": "empty", "variation": 0})
                map_data["tiles"].append(row)
            
            # Serialize entities if they exist
            if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager:
                for entity in self.world_map.entity_manager.entity_tiles:
                    entity_data = {
                        "type": entity.__class__.__name__.lower().replace("entitytile", ""),
                        "x": entity.base_x,
                        "y": entity.base_y,
                        "width": entity.width,
                        "height": entity.height
                    }
                    
                    # Add any additional entity-specific data
                    if hasattr(entity, 'get_save_data'):
                        additional_data = entity.get_save_data()
                        if additional_data:
                            entity_data.update(additional_data)
                    
                    map_data["entities"].append(entity_data)
            
            return map_data
            
        except Exception as e:
            print(f"Error serializing world map: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def deserialize_world_map(self, map_data):
        """Convert serialized dictionary back to WorldMap"""
        try:
            if not map_data or "width" not in map_data or "height" not in map_data:
                print("Invalid map data structure")
                return None
            
            # Create new world map
            width = map_data["width"]
            height = map_data["height"]
            world_map = WorldMap(width, height)
            
            # Load tiles
            if "tiles" in map_data and len(map_data["tiles"]) == height:
                for y in range(height):
                    if y < len(map_data["tiles"]) and len(map_data["tiles"][y]) == width:
                        for x in range(width):
                            if x < len(map_data["tiles"][y]):
                                tile_data = map_data["tiles"][y][x]
                                tile_type = tile_data.get("type", "empty")
                                variation = tile_data.get("variation", 0)
                                
                                # Create tile with variation
                                tile = Tile(tile_type)
                                tile.variation = variation
                                world_map.tiles[y][x] = tile
            
            # Initialize entity system
            world_map.initialize_entity_tiles()
            
            # Load entities
            if "entities" in map_data:
                for entity_data in map_data["entities"]:
                    entity_type = entity_data.get("type", "")
                    x = entity_data.get("x", 0)
                    y = entity_data.get("y", 0)
                    
                    # Create appropriate entity
                    entity = None
                    if entity_type == "tree":
                        from world.entity_tile import TreeEntityTile
                        entity = TreeEntityTile(x, y)
                    elif entity_type == "house":
                        from world.entity_tile import HouseEntityTile
                        entity = HouseEntityTile(x, y)
                    
                    # Add entity to manager
                    if entity and world_map.entity_manager:
                        world_map.entity_manager.add_entity_tile(entity)
            
            return world_map
            
        except Exception as e:
            print(f"Error deserializing world map: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_map(self):
        """Save the current map using compression"""
        if not self.world_map:
            return
            
        try:
            # Create project-specific maps directory
            project_maps_dir = Path.home() / "hoomans" / "project" / self.current_project_name / "maps"
            project_maps_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"map_{self.world_map.width}x{self.world_map.height}_{random.randint(1000, 9999)}.json"
            filepath = project_maps_dir / filename
            
            # Serialize the world map
            print("Serializing world map...")
            map_data = self.serialize_world_map()
            if not map_data:
                print("Failed to serialize world map")
                return
            
            # Compress the data
            print("Compressing map data...")
            compressed_data = self.compress_map_data(map_data)
            if not compressed_data:
                print("Failed to compress map data")
                return
            
            # Create final save structure
            save_data = {
                "compressed": True,
                "data": compressed_data,
                "metadata": {
                    "created_by": "Hoomans Studio Map Editor",
                    "version": "1.0",
                    "width": self.world_map.width,
                    "height": self.world_map.height,
                    "entity_count": len(self.world_map.entity_manager.entity_tiles) if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager else 0
                }
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(save_data, f, separators=(',', ':'))  # Compact JSON
            
            # Calculate compression ratio
            original_size = len(json.dumps(map_data, separators=(',', ':')))
            compressed_size = len(json.dumps(save_data, separators=(',', ':')))
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            print(f"Map saved to {filepath}")
            print(f"Compression: {original_size} -> {compressed_size} bytes ({compression_ratio:.1f}% reduction)")
            
        except Exception as e:
            print(f"Error saving map: {e}")
            import traceback
            traceback.print_exc()
    
    def load_map(self):
        """Load a map using decompression"""
        try:
            # Look in project-specific maps directory first
            project_maps_dir = Path.home() / "hoomans" / "project" / self.current_project_name / "maps"
            
            # Fallback to main maps directory if project maps don't exist
            maps_dir = project_maps_dir if project_maps_dir.exists() else Path.home() / "hoomans" / "maps"
            
            if not maps_dir.exists():
                print("No maps directory found")
                return
                
            # Get first available map (simplified)
            map_files = list(maps_dir.glob("*.json"))
            if not map_files:
                print("No map files found")
                return
                
            filepath = map_files[0]  # Load first map found
            
            # Load file
            print(f"Loading map from {filepath}")
            with open(filepath, 'r') as f:
                save_data = json.load(f)
            
            # Check if it's a compressed file
            if isinstance(save_data, dict) and save_data.get("compressed", False):
                print("Decompressing map data...")
                compressed_data = save_data.get("data", "")
                map_data = self.decompress_map_data(compressed_data)
                if not map_data:
                    print("Failed to decompress map data")
                    return
            else:
                # Handle legacy uncompressed files
                print("Loading uncompressed map data...")
                map_data = save_data
            
            # Deserialize the world map
            print("Deserializing world map...")
            world_map = self.deserialize_world_map(map_data)
            if not world_map:
                print("Failed to deserialize world map")
                return
            
            # Set the loaded map
            self.world_map = world_map
            
            # Update UI
            self.update_canvas()
            self.update_canvas_info()
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            
            print(f"Map loaded successfully: {self.world_map.width}x{self.world_map.height}")
            
        except Exception as e:
            print(f"Error loading map: {e}")
            import traceback
            traceback.print_exc()
    
    def export_image(self):
        """Export map as PNG image"""
        if not self.world_map:
            return
            
        try:
            # Create project-specific maps directory
            project_maps_dir = Path.home() / "hoomans" / "project" / self.current_project_name / "maps"
            project_maps_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"map_{self.world_map.width}x{self.world_map.height}_{random.randint(1000, 9999)}.png"
            filepath = project_maps_dir / filename
            
            # Create high-resolution surface for export
            export_tile_size = 16  # Fixed size for export
            surface = pygame.Surface((
                self.world_map.width * export_tile_size,
                self.world_map.height * export_tile_size
            ))
            
            # Render tiles
            for y in range(self.world_map.height):
                for x in range(self.world_map.width):
                    tile = self.world_map.get_tile(x, y)
                    if tile:
                        screen_x = x * export_tile_size
                        screen_y = y * export_tile_size
                        tile.render(surface, screen_x, screen_y, export_tile_size, export_tile_size)
            
            # Render entities
            if hasattr(self.world_map, 'entity_manager') and self.world_map.entity_manager:
                class ExportCamera:
                    def __init__(self, tile_size):
                        self.tile_size = tile_size
                        
                    def apply(self, world_x, world_y, width, height):
                        screen_x = int((world_x / Tile.SIZE) * self.tile_size)
                        screen_y = int((world_y / Tile.SIZE) * self.tile_size)
                        screen_width = int((width / Tile.SIZE) * self.tile_size)
                        screen_height = int((height / Tile.SIZE) * self.tile_size)
                        return (screen_x, screen_y, screen_width, screen_height)
                
                camera = ExportCamera(export_tile_size)
                for entity in self.world_map.entity_manager.entity_tiles:
                    entity.render(surface, camera)
            
            # Save image
            pygame.image.save(surface, str(filepath))
            print(f"Map exported to {filepath}")
            
        except Exception as e:
            print(f"Error exporting map: {e}")

import sys
import os
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

# Import the map creator components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from world.tile import Tile
from world.map import WorldMap
from world.entity_tile import EntityTileManager, TreeEntityTile, HouseEntityTile
from world.biome_generator import ProceduralMapGenerator, BiomeType
from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import QPoint


# Import map system components
from engine.systems.map_system import (
    MapSystem, MapGenerationConfig, MapGenerationType, TileType, BiomeType,
    create_default_map_config, create_island_map_config, create_dungeon_map_config
)

class CanvasWidget(QWidget):
    def __init__(self, map_editor):
        super().__init__()
        self.map_editor = map_editor
        self.pixmap = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)  # Allow wheel events
        
    def paintEvent(self, event):
        if self.pixmap:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.pixmap)
        else:
            # Draw placeholder text with studio styling
            painter = QPainter(self)
            painter.setPen(QColor("#95a5a6"))  # Match the studio's placeholder color
            painter.setFont(QFont("Arial", 18, QFont.Weight.Light))  # Match studio font weight
            painter.drawText(self.rect(), Qt.AlignCenter, 
                           "Map Canvas\nGenerate or create a new map to begin\nMouse wheel to zoom")
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.map_editor.mouse_pressed = True
            self.map_editor.paint_at_position(event.position().toPoint())
        elif event.button() == Qt.MiddleButton:
            self.map_editor.start_pan(event.position().toPoint())
            
    def mouseMoveEvent(self, event):
        if self.map_editor.mouse_pressed:
            self.map_editor.paint_at_position(event.position().toPoint())
        elif hasattr(self.map_editor, 'panning') and self.map_editor.panning:
            self.map_editor.update_pan(event.position().toPoint())
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.map_editor.mouse_pressed = False
            self.map_editor.last_paint_pos = None
        elif event.button() == Qt.MiddleButton:
            self.map_editor.stop_pan()
        
    def wheelEvent(self, event):
        # Simple wheel event - just check if scrolling up or down
        if event.angleDelta().y() > 0:
            # Scroll up = zoom in
            self.map_editor.handle_zoom(1, event.position().toPoint())
        elif event.angleDelta().y() < 0:
            # Scroll down = zoom out
            self.map_editor.handle_zoom(-1, event.position().toPoint())
        
    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.setMinimumSize(pixmap.size())
        self.update()

        
class MapEditorWidget(QWidget):
    """Enhanced map editor widget with full tile and entity placement capabilities"""
    
    def __init__(self):
        super().__init__()
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
            # Calculate the world position under the mouse cursor BEFORE zoom
            world_x = (mouse_pos.x() - self.camera_x) / (Tile.SIZE * old_zoom)
            world_y = (mouse_pos.y() - self.camera_y) / (Tile.SIZE * old_zoom)
            
            # Calculate new camera position to keep the world position under the cursor AFTER zoom
            new_screen_x = world_x * Tile.SIZE * self.zoom_level
            new_screen_y = world_y * Tile.SIZE * self.zoom_level
            
            self.camera_x = mouse_pos.x() - new_screen_x
            self.camera_y = mouse_pos.y() - new_screen_y
            
            # Update display
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
        world_x = (pos.x() - self.camera_x) / (Tile.SIZE * self.zoom_level)
        world_y = (pos.y() - self.camera_y) / (Tile.SIZE * self.zoom_level)
        
        # Convert to tile coordinates
        tile_x = int(world_x)
        tile_y = int(world_y)
        
        # Check bounds
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
            
            # Render all tiles
            for y in range(self.world_map.height):
                for x in range(self.world_map.width):
                    tile = self.world_map.get_tile(x, y)
                    if tile:
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


            
    def save_map(self):
        """Save the current map using existing compression system"""
        if not self.world_map:
            return
            
        try:
            # Create maps directory
            maps_dir = Path.home() / "hoomans" / "maps"
            maps_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"map_{self.world_map.width}x{self.world_map.height}_{random.randint(1000, 9999)}.json"
            filepath = maps_dir / filename
            
            # Use the existing save_to_file method which handles compression
            self.world_map.save_to_file(str(filepath))
            
            print(f"Map saved to {filepath}")
            
        except Exception as e:
            print(f"Error saving map: {e}")
            
    def load_map(self):
        """Load a map using existing decompression system"""
        try:
            maps_dir = Path.home() / "hoomans" / "maps"
            if not maps_dir.exists():
                print("No maps directory found")
                return
                
            # Get first available map (simplified)
            map_files = list(maps_dir.glob("*.json"))
            if not map_files:
                print("No map files found")
                return
                
            filepath = map_files[0]  # Load first map found
            
            # Create new world map and use existing load_from_file method
            self.world_map = WorldMap(1, 1)  # Temporary size, will be updated by load
            success = self.world_map.load_from_file(str(filepath))
            
            if success:
                self.world_map.initialize_entity_tiles()  # Initialize entity system
                self.update_canvas()
                self.update_canvas_info()
                self.save_btn.setEnabled(True)
                self.export_btn.setEnabled(True)
                print(f"Map loaded from {filepath}")
            else:
                print("Failed to load map")
                
        except Exception as e:
            print(f"Error loading map: {e}")
            
    def export_image(self):
        """Export map as PNG image"""
        if not self.world_map:
            return
            
        try:
            maps_dir = Path.home() / "hoomans" / "maps"
            maps_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"map_{self.world_map.width}x{self.world_map.height}_{random.randint(1000, 9999)}.png"
            filepath = maps_dir / filename
            
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
            for entity in self.world_map.entity_tiles:
                screen_x = entity.x * export_tile_size
                screen_y = entity.y * export_tile_size
                entity.render(surface, screen_x, screen_y, export_tile_size, export_tile_size)
            
            # Save image
            pygame.image.save(surface, str(filepath))
            print(f"Map exported to {filepath}")
            
        except Exception as e:
            print(f"Error exporting map: {e}")


class ItemEditorWidget(QWidget):
    """Item editor widget for creating and managing game items"""
    
    def __init__(self):
        super().__init__()
        self.item_system = None
        self.current_item = None
        self.setup_ui()
        self.setup_item_system()
        
    def setup_item_system(self):
        """Initialize the item system"""
        try:
            # Get project root (navigate up from current file location)
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(current_file)
            
            # Add engine path to sys.path if not already there
            engine_path = os.path.join(project_root, 'engine')
            if engine_path not in sys.path:
                sys.path.insert(0, engine_path)
            
            # Import and create item system
            from engine.systems.item_system import ItemSystem
            
            self.item_system = ItemSystem(project_root)
            self.refresh_item_list()
            
        except ImportError as e:
            print(f"Could not import item system: {e}")
            self.item_system = None
        except Exception as e:
            print(f"Error initializing item system: {e}")
            self.item_system = None
            
    def setup_item_form(self):
        """Setup the item editing form with proper styling"""
        # Apply consistent styling to all form elements
        form_style = """
            QWidget {
                background: #ffffff;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 2px solid #4A90E2;
            }
            QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background: white;
                border: 1px solid #ddd;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow, QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                color: #000000;
            }
            QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {
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
            QComboBox QAbstractItemView {
                color: #000000;
                background: white;
                selection-background-color: rgba(74, 144, 226, 0.2);
            }
            QGroupBox {
                color: #000000;
                font-weight: bold;
                margin-top: 10px;
                background: transparent;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: white;
                color: #000000;
            }
            QLabel {
                color: #000000;
                background: transparent;
            }
            QPushButton {
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(74, 144, 226, 0.1);
                border: 1px solid #4A90E2;
                color: #000000;
            }
            QPushButton:pressed {
                background: rgba(74, 144, 226, 0.2);
            }
            
        """
        
        black_text_style = """
            QWidget[blackText="true"] {
                color: #000000 !important;
            }
            QSpinBox[blackText="true"] {
                color: #000000 !important;
            }
            QSpinBox[blackText="true"] QLineEdit {
                color: #000000 !important;
            }
            QLineEdit[blackText="true"] {
                color: #000000 !important;
            }
        """
        
        self.form_widget.setStyleSheet(form_style)
        
        # Basic properties with explicit labels
        self.item_id_edit = QLineEdit()
        self.item_id_edit.setPlaceholderText("unique_item_id")
        self.item_id_edit.textChanged.connect(self.on_form_changed)
        
        id_label = QLabel("Item ID:")
        id_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(id_label, self.item_id_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Display Name")
        self.name_edit.textChanged.connect(self.on_form_changed)
        
        name_label = QLabel("Name:")
        name_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(name_label, self.name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Item description")
        self.description_edit.textChanged.connect(self.on_form_changed)
        
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(desc_label, self.description_edit)
        
        # Category
        self.category_edit = QComboBox()
        from engine.systems.item_system import ItemCategory
        for category in ItemCategory:
            self.category_edit.addItem(category.value.title(), category.value)
        self.category_edit.currentTextChanged.connect(self.on_category_changed)
        
        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(category_label, self.category_edit)
        
        # Common properties
        self.max_stack_spin = QSpinBox()
        self.max_stack_spin.setRange(1, 999)
        self.max_stack_spin.setValue(64)
        self.max_stack_spin.valueChanged.connect(self.on_form_changed)
        
        stack_label = QLabel("Max Stack:")
        stack_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(stack_label, self.max_stack_spin)
        
        self.value_spin = QSpinBox()
        self.value_spin.setRange(0, 99999)
        self.value_spin.valueChanged.connect(self.on_form_changed)
        
        value_label = QLabel("Value:")
        value_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(value_label, self.value_spin)
        
        # Category-specific properties container
        self.specific_props_widget = QWidget()
        self.specific_props_layout = QFormLayout(self.specific_props_widget)
        self.form_layout.addRow(self.specific_props_widget)
        
        # Icon management
        icon_group = QGroupBox("Icon")
        icon_layout = QHBoxLayout(icon_group)
        
        self.icon_path_edit = QLineEdit()
        self.icon_path_edit.setReadOnly(True)
        self.icon_path_edit.setPlaceholderText("No icon selected")
        self.icon_path_edit.setStyleSheet("color: #000000; background: #f8f9fa;")  # Slightly gray for read-only
        icon_layout.addWidget(self.icon_path_edit)
        
        self.create_icon_btn = QPushButton("Create")
        self.create_icon_btn.setFixedWidth(60)
        self.create_icon_btn.clicked.connect(self.create_item_icon)
        icon_layout.addWidget(self.create_icon_btn)
        
        self.edit_icon_btn = QPushButton("Edit")
        self.edit_icon_btn.setFixedWidth(50)
        self.edit_icon_btn.clicked.connect(self.edit_item_icon)
        icon_layout.addWidget(self.edit_icon_btn)
        
        self.form_layout.addRow(icon_group)
            
    def setup_ui(self):
        """Setup UI with keyboard shortcuts"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left panel - Item list and controls
        left_panel = self.create_item_list_panel()
        left_panel.setFixedWidth(300)
        
        # Right panel - Item editor
        right_panel = self.create_item_editor_panel()
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+N for new item
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self.create_new_item)
        
        # Ctrl+S for save
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_current_item)
        
        # Delete key for delete item
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self.delete_current_item)
        
        # Ctrl+D for duplicate
        duplicate_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        duplicate_shortcut.activated.connect(self.duplicate_current_item)

    # Add search functionality:
    def create_item_list_panel(self):
        """Create item list panel with proper styling"""
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
            QLineEdit {
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4A90E2;
            }
            QComboBox {
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                background: white;
                border: 1px solid #ddd;
            }
            QComboBox::down-arrow {
                color: #000000;
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
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Item Manager")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000; padding: 10px 0px; background: transparent;")
        layout.addWidget(title)
        
        # Search box
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout(search_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search items...")
        self.search_edit.textChanged.connect(self.search_items)
        search_layout.addWidget(self.search_edit)
        layout.addWidget(search_group)
        
        # Category filter
        category_group = QGroupBox("Category Filter")
        category_layout = QVBoxLayout(category_group)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", "all")
        
        # Add categories from item system
        from engine.systems.item_system import ItemCategory
        for category in ItemCategory:
            self.category_combo.addItem(category.value.title(), category.value)
            
        self.category_combo.currentTextChanged.connect(self.filter_items)
        category_layout.addWidget(self.category_combo)
        layout.addWidget(category_group)
        
        # Item list
        self.item_list = QTreeWidget()
        self.item_list.setHeaderHidden(True)
        self.item_list.setStyleSheet("""
            QTreeWidget {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                color: #000000;
            }
            QTreeWidget::item {
                padding: 8px;
                border-radius: 3px;
                color: #000000;
            }
            QTreeWidget::item:hover {
                background: rgba(74, 144, 226, 0.1);
                color: #000000;
            }
            QTreeWidget::item:selected {
                background: rgba(74, 144, 226, 0.2);
                color: #000000;
            }
            QTreeWidget::branch {
                color: #000000;
            }
        """)
        self.item_list.itemClicked.connect(self.select_item)
        layout.addWidget(self.item_list)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        self.new_item_btn = ModernButton("New Item (Ctrl+N)", primary=True)
        self.new_item_btn.clicked.connect(self.create_new_item)
        button_layout.addWidget(self.new_item_btn)
        
        self.delete_item_btn = ModernButton("Delete Item (Del)")
        self.delete_item_btn.clicked.connect(self.delete_current_item)
        self.delete_item_btn.setEnabled(False)
        button_layout.addWidget(self.delete_item_btn)
        
        self.duplicate_item_btn = ModernButton("Duplicate (Ctrl+D)")
        self.duplicate_item_btn.clicked.connect(self.duplicate_current_item)
        self.duplicate_item_btn.setEnabled(False)
        button_layout.addWidget(self.duplicate_item_btn)
        
        # Export/Import buttons
        self.export_btn = ModernButton("Export Items")
        self.export_btn.clicked.connect(self.export_items)
        button_layout.addWidget(self.export_btn)
        
        self.import_btn = ModernButton("Import Items")
        self.import_btn.clicked.connect(self.import_items)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def export_items(self):
        """Export items to JSON file"""
        if not self.item_system:
            return
            
        try:
            from pathlib import Path
            export_dir = Path.home() / "hoomans" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            import time
            timestamp = int(time.time())
            filename = f"items_export_{timestamp}.json"
            filepath = export_dir / filename
            
            success = self.item_system.export_item_definitions(str(filepath))
            if success:
                print(f"Items exported to: {filepath}")
            else:
                print("Failed to export items")
                
        except Exception as e:
            print(f"Error exporting items: {e}")

    def import_items(self):
        """Import items from JSON file"""
        if not self.item_system:
            return
            
        try:
            from pathlib import Path
            import_dir = Path.home() / "hoomans" / "exports"
            
            if not import_dir.exists():
                print("No exports directory found")
                return
                
            # Find first JSON file (simplified - in real implementation use file dialog)
            json_files = list(import_dir.glob("*.json"))
            if not json_files:
                print("No JSON files found in exports directory")
                return
                
            filepath = json_files[0]
            imported_count = self.item_system.import_item_definitions(str(filepath))
            
            if imported_count > 0:
                self.refresh_item_list()
                print(f"Imported {imported_count} items from: {filepath}")
            else:
                print("No items were imported")
                
        except Exception as e:
            print(f"Error importing items: {e}")
    
    def search_items(self):
        """Search items by name or ID"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.item_list.topLevelItemCount()):
            category_item = self.item_list.topLevelItem(i)
            category_visible = False
            
            for j in range(category_item.childCount()):
                item = category_item.child(j)
                item_id = item.data(0, Qt.UserRole)
                item_name = item.text(0).lower()
                
                if not search_text or search_text in item_name or search_text in item_id.lower():
                    item.setHidden(False)
                    category_visible = True
                else:
                    item.setHidden(True)
            
            category_item.setHidden(not category_visible)

        
    def create_item_editor_panel(self):
        """Create the item editor panel with proper styling"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { 
                background: transparent;
                border: none; 
            }
            QLabel {
                color: #000000;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Editor title and status
        header_layout = QHBoxLayout()
        
        self.editor_title = QLabel("Item Editor")
        self.editor_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.editor_title.setStyleSheet("color: #000000; padding: 10px 0px; background: transparent;")
        header_layout.addWidget(self.editor_title)
        
        header_layout.addStretch()
        
        # Item count status
        self.status_label = QLabel("0 items")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #000000;
                background: #f8f9fa;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 11px;
                border: 1px solid #e0e0e0;
            }
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Scroll area for form
        scroll_area = QScrollArea()
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
        """)
        
        self.form_widget = QWidget()
        self.form_widget.setStyleSheet("background: transparent;")
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setSpacing(10)
        
        self.setup_item_form()
        
        scroll_area.setWidget(self.form_widget)
        layout.addWidget(scroll_area)
        
        # Save button
        self.save_btn = ModernButton("Save Item", primary=True)
        self.save_btn.clicked.connect(self.save_current_item)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        return panel
        

        
    def on_category_changed(self):
        """Handle category change to show/hide specific properties"""
        self.clear_specific_properties()
        
        category = self.category_edit.currentData()
        
        # Style for category-specific widgets
        widget_style = """
            QSpinBox, QDoubleSpinBox, QComboBox {
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
            }
            QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background: white;
                border: 1px solid #ddd;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow, QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                color: #000000;
            }
            QComboBox::drop-down {
                background: white;
                border: 1px solid #ddd;
            }
            QComboBox::down-arrow {
                color: #000000;
            }
            QLabel {
                color: #000000;
                background: transparent;
            }
        """
        
        if category == "food":
            self.hunger_value_spin = QSpinBox()
            self.hunger_value_spin.setRange(1, 20)
            self.hunger_value_spin.setValue(2)
            self.hunger_value_spin.valueChanged.connect(self.on_form_changed)
            self.hunger_value_spin.setStyleSheet(widget_style)
            
            hunger_label = QLabel("Hunger Value:")
            hunger_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(hunger_label, self.hunger_value_spin)
            
        elif category == "water":
            self.thirst_value_spin = QSpinBox()
            self.thirst_value_spin.setRange(1, 20)
            self.thirst_value_spin.setValue(2)
            self.thirst_value_spin.valueChanged.connect(self.on_form_changed)
            self.thirst_value_spin.setStyleSheet(widget_style)
            
            thirst_label = QLabel("Thirst Value:")
            thirst_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(thirst_label, self.thirst_value_spin)
            
        elif category == "tool":
            self.tool_type_combo = QComboBox()
            from engine.systems.item_system import ToolType
            for tool_type in ToolType:
                self.tool_type_combo.addItem(tool_type.value.title(), tool_type.value)
            self.tool_type_combo.currentTextChanged.connect(self.on_form_changed)
            self.tool_type_combo.setStyleSheet(widget_style)
            
            tool_label = QLabel("Tool Type:")
            tool_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(tool_label, self.tool_type_combo)
            
            self.durability_spin = QSpinBox()
            self.durability_spin.setRange(1, 1000)
            self.durability_spin.setValue(100)
            self.durability_spin.valueChanged.connect(self.on_form_changed)
            self.durability_spin.setStyleSheet(widget_style)
            
            durability_label = QLabel("Durability:")
            durability_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(durability_label, self.durability_spin)
            
            self.effectiveness_spin = QDoubleSpinBox()
            self.effectiveness_spin.setRange(0.1, 10.0)
            self.effectiveness_spin.setValue(1.0)
            self.effectiveness_spin.setSingleStep(0.1)
            self.effectiveness_spin.valueChanged.connect(self.on_form_changed)
            self.effectiveness_spin.setStyleSheet(widget_style)
            
            effectiveness_label = QLabel("Effectiveness:")
            effectiveness_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(effectiveness_label, self.effectiveness_spin)
            
        elif category == "schematic":
            self.structure_type_combo = QComboBox()
            from engine.systems.item_system import StructureType
            for structure_type in StructureType:
                self.structure_type_combo.addItem(structure_type.value.title(), structure_type.value)
            self.structure_type_combo.currentTextChanged.connect(self.on_form_changed)
            self.structure_type_combo.setStyleSheet(widget_style)
            
            structure_label = QLabel("Structure Type:")
            structure_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(structure_label, self.structure_type_combo)
            
            self.width_spin = QSpinBox()
            self.width_spin.setRange(1, 10)
            self.width_spin.setValue(1)
            self.width_spin.valueChanged.connect(self.on_form_changed)
            self.width_spin.setStyleSheet(widget_style)
            
            width_label = QLabel("Width:")
            width_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(width_label, self.width_spin)
            
            self.height_spin = QSpinBox()
            self.height_spin.setRange(1, 10)
            self.height_spin.setValue(1)
            self.height_spin.valueChanged.connect(self.on_form_changed)
            self.height_spin.setStyleSheet(widget_style)
            
            height_label = QLabel("Height:")
            height_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(height_label, self.height_spin)
        
        self.on_form_changed()


        
    def clear_specific_properties(self):
        """Clear category-specific property widgets"""
        while self.specific_props_layout.count():
            child = self.specific_props_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def on_form_changed(self):
        """Handle form changes with validation feedback"""
        self.save_btn.setEnabled(True)
        
        # Validate item ID
        item_id = self.item_id_edit.text().strip()
        id_valid = bool(item_id and item_id.replace('_', '').replace('-', '').isalnum())
        
        # Apply validation styling
        if item_id:  # Only apply styling if there's text
            self.item_id_edit.setStyleSheet(self.get_validation_style(id_valid))
        else:
            self.item_id_edit.setStyleSheet("""
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
            """)
        
        # Validate name
        name = self.name_edit.text().strip()
        name_valid = bool(name)
        
        if name:
            self.name_edit.setStyleSheet(self.get_validation_style(name_valid))
        else:
            self.name_edit.setStyleSheet("""
                color: #000000;
                background: white;
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 3px;
            """)
            
    def cleanup(self):
        """Cleanup resources when widget is destroyed"""
        if hasattr(self, 'item_system') and self.item_system:
            # Any cleanup needed for item system
            pass
        
    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup()
        super().closeEvent(event)
            
    def refresh_item_list(self):
        """Refresh the item list and update status with proper styling"""
        if not self.item_system:
            return
            
        self.item_list.clear()
        
        # Group items by category
        from engine.systems.item_system import ItemCategory
        category_items = {}
        total_items = 0
        
        for item in self.item_system.get_all_items():
            category = item.category.value
            if category not in category_items:
                category_items[category] = []
            category_items[category].append(item)
            total_items += 1
        
        # Add items to tree
        for category, items in category_items.items():
            category_item = QTreeWidgetItem(self.item_list, [f"{category.title()} ({len(items)})"])
            category_item.setExpanded(True)
            
            # Set category item styling
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            
            for item in sorted(items, key=lambda x: x.name):
                item_widget = QTreeWidgetItem(category_item, [item.name])
                item_widget.setData(0, Qt.UserRole, item.item_id)
                
        # Update status
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"{total_items} items")
                
    def filter_items(self):
        """Filter items by selected category"""
        selected_category = self.category_combo.currentData()
        
        for i in range(self.item_list.topLevelItemCount()):
            category_item = self.item_list.topLevelItem(i)
            category_name = category_item.text(0).lower()
            
            if selected_category == "all" or selected_category == category_name:
                category_item.setHidden(False)
            else:
                category_item.setHidden(True)
                
    def get_validation_style(self, is_valid):
        """Get CSS style for validation state with proper colors"""
        if is_valid:
            return """
                color: #000000;
                background: rgba(39, 174, 96, 0.1);
                border: 1px solid #27ae60;
                padding: 5px;
                border-radius: 3px;
            """
        else:
            return """
                color: #000000;
                background: rgba(231, 76, 60, 0.1);
                border: 1px solid #e74c3c;
                padding: 5px;
                border-radius: 3px;
            """

                
    def select_item(self, item):
        """Select an item and load it into the editor with preview"""
        item_id = item.data(0, Qt.UserRole)
        if not item_id or not self.item_system:
            return
            
        properties = self.item_system.get_item_properties(item_id)
        if not properties:
            return
            
        self.current_item = properties
        self.load_item_into_form(properties)
        self.delete_item_btn.setEnabled(True)
        self.duplicate_item_btn.setEnabled(True)
        self.editor_title.setText(f"Editing: {properties.name}")
        
        # Update status with item info
        from engine.systems.item_system import ConsumableProperties, ToolProperties, SchematicProperties
        
        status_text = f"ID: {properties.item_id} | Category: {properties.category.value}"
        if isinstance(properties, ConsumableProperties):
            status_text += f" | Effect: {properties.effect_value}"
        elif isinstance(properties, ToolProperties):
            status_text += f" | Durability: {properties.durability}"
        elif isinstance(properties, SchematicProperties):
            status_text += f" | Size: {properties.width}x{properties.height}"
        
        if hasattr(self, 'status_label'):
            self.status_label.setText(status_text)
        
    def load_item_into_form(self, properties):
        """Load item properties into the form"""
        self.item_id_edit.setText(properties.item_id)
        self.name_edit.setText(properties.name)
        self.description_edit.setText(properties.description)
        
        # Set category
        category_index = self.category_edit.findData(properties.category.value)
        if category_index >= 0:
            self.category_edit.setCurrentIndex(category_index)
            
        self.max_stack_spin.setValue(properties.max_stack)
        self.value_spin.setValue(properties.value)
        self.icon_path_edit.setText(properties.icon_path or "")
        
        # Load category-specific properties
        from engine.systems.item_system import ConsumableProperties, ToolProperties, SchematicProperties
        
        if isinstance(properties, ConsumableProperties):
            if hasattr(self, 'hunger_value_spin'):
                self.hunger_value_spin.setValue(properties.effect_value)
            elif hasattr(self, 'thirst_value_spin'):
                self.thirst_value_spin.setValue(properties.effect_value)
                
        elif isinstance(properties, ToolProperties):
            if hasattr(self, 'tool_type_combo'):
                tool_index = self.tool_type_combo.findData(properties.tool_type.value)
                if tool_index >= 0:
                    self.tool_type_combo.setCurrentIndex(tool_index)
            if hasattr(self, 'durability_spin'):
                self.durability_spin.setValue(properties.durability)
            if hasattr(self, 'effectiveness_spin'):
                self.effectiveness_spin.setValue(properties.effectiveness)
                
        elif isinstance(properties, SchematicProperties):
            if hasattr(self, 'structure_type_combo'):
                struct_index = self.structure_type_combo.findData(properties.structure_type.value)
                if struct_index >= 0:
                    self.structure_type_combo.setCurrentIndex(struct_index)
            if hasattr(self, 'width_spin'):
                self.width_spin.setValue(properties.width)
            if hasattr(self, 'height_spin'):
                self.height_spin.setValue(properties.height)
        
        self.save_btn.setEnabled(False)
        
    def create_new_item(self):
        """Create a new item"""
        self.current_item = None
        self.clear_form()
        self.editor_title.setText("Creating New Item")
        self.save_btn.setEnabled(True)
        self.delete_item_btn.setEnabled(False)
        self.duplicate_item_btn.setEnabled(False)
        
    def clear_form(self):
        """Clear the form for new item creation"""
        self.item_id_edit.clear()
        self.name_edit.clear()
        self.description_edit.clear()
        self.category_edit.setCurrentIndex(0)
        self.max_stack_spin.setValue(64)
        self.value_spin.setValue(0)
        self.icon_path_edit.clear()
        self.clear_specific_properties()
        
    def validate_form(self):
        """Validate form data before saving"""
        errors = []
        
        item_id = self.item_id_edit.text().strip()
        if not item_id:
            errors.append("Item ID is required")
        elif not item_id.replace('_', '').replace('-', '').isalnum():
            errors.append("Item ID can only contain letters, numbers, underscores, and hyphens")
        
        name = self.name_edit.text().strip()
        if not name:
            errors.append("Item name is required")
        
        # Check for duplicate ID (only if creating new item)
        if not self.current_item and self.item_system:
            existing = self.item_system.get_item_properties(item_id)
            if existing:
                errors.append(f"Item ID '{item_id}' already exists")
        
        return errors

    def save_current_item(self):
        """Save the current item with validation"""
        if not self.item_system:
            print("Item system not initialized")
            return
        
        # Validate form
        errors = self.validate_form()
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return
        
        try:
            item_id = self.item_id_edit.text().strip()
            name = self.name_edit.text().strip()
            description = self.description_edit.text().strip()
            category = self.category_edit.currentData()
            max_stack = self.max_stack_spin.value()
            value = self.value_spin.value()
            icon_path = self.icon_path_edit.text().strip() or None
            
            # Create item based on category
            success = False
            
            if category == "food":
                hunger_value = getattr(self, 'hunger_value_spin', None)
                hunger_val = hunger_value.value() if hunger_value else 2
                properties = self.item_system.create_food_item(
                    item_id, name, description, hunger_val, max_stack, value, 
                    icon_path=icon_path
                )
                success = properties is not None
                
            elif category == "water":
                thirst_value = getattr(self, 'thirst_value_spin', None)
                thirst_val = thirst_value.value() if thirst_value else 2
                properties = self.item_system.create_water_item(
                    item_id, name, description, thirst_val, max_stack, value,
                    icon_path=icon_path
                )
                success = properties is not None
                
            elif category == "tool":
                from engine.systems.item_system import ToolType
                tool_type_str = getattr(self, 'tool_type_combo', None)
                tool_type_val = tool_type_str.currentData() if tool_type_str else "axe"
                tool_type = ToolType(tool_type_val)
                
                durability = getattr(self, 'durability_spin', None)
                durability_val = durability.value() if durability else 100
                
                effectiveness = getattr(self, 'effectiveness_spin', None)
                effectiveness_val = effectiveness.value() if effectiveness else 1.0
                
                properties = self.item_system.create_tool_item(
                    item_id, name, description, tool_type, durability_val, 
                    effectiveness_val, value, icon_path=icon_path
                )
                success = properties is not None
                
            elif category == "schematic":
                from engine.systems.item_system import StructureType
                structure_type_str = getattr(self, 'structure_type_combo', None)
                structure_type_val = structure_type_str.currentData() if structure_type_str else "house"
                structure_type = StructureType(structure_type_val)
                
                width = getattr(self, 'width_spin', None)
                width_val = width.value() if width else 1
                
                height = getattr(self, 'height_spin', None)
                height_val = height.value() if height else 1
                
                properties = self.item_system.create_schematic_item(
                    item_id, name, description, structure_type, width_val, 
                    height_val, value, icon_path=icon_path
                )
                success = properties is not None
                
            else:  # resource or other
                properties = self.item_system.create_resource_item(
                    item_id, name, description, max_stack, value, 
                    icon_path=icon_path
                )
                success = properties is not None
            
            if success:
                self.current_item = properties
                self.refresh_item_list()
                self.save_btn.setEnabled(False)
                self.delete_item_btn.setEnabled(True)
                self.duplicate_item_btn.setEnabled(True)
                self.editor_title.setText(f"Editing: {name}")
                print(f"Successfully saved item: {name}")
            else:
                print("Failed to create item")
                
        except Exception as e:
            print(f"Error saving item: {e}")
            import traceback
            traceback.print_exc()
            
    def delete_current_item(self):
        """Delete the currently selected item"""
        if not self.current_item or not self.item_system:
            return
            
        try:
            success = self.item_system.delete_item(self.current_item.item_id)
            if success:
                self.refresh_item_list()
                self.clear_form()
                self.current_item = None
                self.editor_title.setText("Item Editor")
                self.delete_item_btn.setEnabled(False)
                self.duplicate_item_btn.setEnabled(False)
                print(f"Deleted item: {self.current_item.name}")
            else:
                print("Failed to delete item")
                
        except Exception as e:
            print(f"Error deleting item: {e}")
            
    def duplicate_current_item(self):
        """Duplicate the currently selected item"""
        if not self.current_item:
            return
            
        # Create new item ID
        base_id = self.current_item.item_id
        new_id = f"{base_id}_copy"
        counter = 1
        
        while self.item_system.get_item_properties(new_id):
            new_id = f"{base_id}_copy_{counter}"
            counter += 1
            
        # Update form with new ID and name
        self.item_id_edit.setText(new_id)
        self.name_edit.setText(f"{self.current_item.name} Copy")
        self.current_item = None
        self.editor_title.setText("Creating Duplicate Item")
        self.save_btn.setEnabled(True)
        self.delete_item_btn.setEnabled(False)
        self.duplicate_item_btn.setEnabled(False)
        
    def create_item_icon(self):
        """Create a new icon for the item"""
        if not self.item_system:
            return
            
        item_id = self.item_id_edit.text().strip()
        if not item_id:
            print("Enter an item ID first")
            return
            
        icon_path = self.item_system.create_new_icon(item_id)
        if icon_path:
            self.icon_path_edit.setText(icon_path)
            self.on_form_changed()
            
    def edit_item_icon(self):
        """Edit the current item's icon"""
        if not self.item_system:
            return
            
        item_id = self.item_id_edit.text().strip()
        if not item_id:
            print("Enter an item ID first")
            return
            
        success = self.item_system.edit_icon(item_id)
        if not success:
            print("Failed to open icon editor")



class ProjectCard(QFrame):
    projectSelected = Signal(str)
    
    def __init__(self, project_path: str, project_name: str):
        super().__init__()
        self.project_path = project_path
        self.project_name = project_name
        self.setup_ui()
        self.add_shadow_effect()
        
    def setup_ui(self):
        self.setFixedSize(300, 180)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 12px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f8ff);
                border: 2px solid #4A90E2;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 15)  # Reduced bottom margin
        layout.setSpacing(8)  # Reduced spacing between thumbnail and title
        
        # Project thumbnail with gradient background
        thumbnail = QLabel()
        thumbnail.setFixedSize(260, 120)
        thumbnail.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
                color: white;
            }
        """)
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setText("🎮")
        thumbnail.setFont(QFont("Arial", 32, QFont.Weight.Light))
        
        # Project name with modern typography
        name_label = QLabel(self.project_name)
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Medium))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 12px 0px 4px 0px;
            }
        """)
        
        layout.addWidget(thumbnail)
        layout.addWidget(name_label)
        
    def add_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.projectSelected.emit(self.project_path)


class ModernButton(QPushButton):
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setup_style()
        
    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4A90E2, stop:1 #357ABD);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5BA0F2, stop:1 #4A90E2);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #357ABD, stop:1 #2E6DA4);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #4A90E2;
                    border: 2px solid #4A90E2;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: rgba(74, 144, 226, 0.1);
                    border: 2px solid #5BA0F2;
                }
                QPushButton:pressed {
                    background: rgba(74, 144, 226, 0.2);
                }
            """)


class StudioUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.projects_path = Path.home() / "hoomans" / "project"
        self.open_tabs = {}  # Track open tabs
        self.setup_ui()
        self.load_projects()
        
    def setup_ui(self):
        self.setWindowTitle("Hoomans Studio")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # Modern dark-light hybrid theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                color: #2c3e50;
            }
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
        
        # Central widget with stacked layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Main content area
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Project loader view
        self.project_view = self.create_project_view()
        self.stacked_widget.addWidget(self.project_view)
        
        # Editor view
        self.editor_view = self.create_editor_view()
        self.stacked_widget.addWidget(self.editor_view)
        
        self.stacked_widget.setCurrentWidget(self.project_view)
        
    def create_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            }
        """)
        
        # Add subtle shadow to header
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        header.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo/Title with modern typography
        title = QLabel("Hoomans Studio")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setStyleSheet("""
            QLabel {
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                background: transparent;
            }
        """)
        
        layout.addWidget(title)
        layout.addStretch()
        
        # Header buttons with modern styling
        self.new_project_btn = ModernButton("New Project", primary=True)
        self.open_project_btn = ModernButton("Open Project", primary=False)
        
        # Connect the buttons to their functions
        self.new_project_btn.clicked.connect(self.create_new_project)
        self.open_project_btn.clicked.connect(self.go_back_to_projects)
        
        layout.addWidget(self.open_project_btn)
        layout.addSpacing(12)
        layout.addWidget(self.new_project_btn)
        
        # Hide open project button initially (we start in project selection)
        self.open_project_btn.hide()
        
        return header


    def create_new_project(self):
        """Placeholder for new project creation - will be implemented later"""
        print("New project creation - functionality to be implemented")
        # For now, just go back to project selection
        self.stacked_widget.setCurrentWidget(self.project_view)
        self.setWindowTitle("Hoomans Studio")

    def go_back_to_projects(self):
        """Navigate back to project selection view"""
        self.stacked_widget.setCurrentWidget(self.project_view)
        self.setWindowTitle("Hoomans Studio")
        # Hide the open project button when in project selection
        self.open_project_btn.hide()
        # Refresh the projects list in case new ones were added
        self.refresh_projects()


    def refresh_projects(self):
        """Refresh the projects grid"""
        # Clear existing project cards
        for i in reversed(range(self.projects_layout.count())): 
            self.projects_layout.itemAt(i).widget().setParent(None)
        
        # Reload projects
        self.load_projects()
        
    def create_project_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(40)
        
        # Welcome section with modern typography
        welcome_label = QLabel("Welcome to Hoomans Studio")
        welcome_label.setFont(QFont("SF Pro Display", 36, QFont.Weight.Light))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                margin-bottom: 10px;
            }
        """)
        
        subtitle = QLabel("Create amazing games with our modern development environment")
        subtitle.setFont(QFont("SF Pro Display", 16, QFont.Weight.Normal))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background: transparent;
                margin-bottom: 20px;
            }
        """)
        
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle)
        
        # Projects section
        projects_header = QLabel("Recent Projects")
        projects_header.setFont(QFont("SF Pro Display", 20, QFont.Weight.Medium))
        projects_header.setStyleSheet("""
            QLabel {
                color: #34495e;
                background: transparent;
                padding: 20px 0px 10px 0px;
            }
        """)
        layout.addWidget(projects_header)
        
        # Projects grid with modern scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.projects_widget = QWidget()
        self.projects_layout = QGridLayout(self.projects_widget)
        self.projects_layout.setSpacing(30)
        self.projects_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        scroll_area.setWidget(self.projects_widget)
        layout.addWidget(scroll_area)
        
        return widget
        
    def create_editor_view(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main splitter with modern styling
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(0, 0, 0, 0.1);
                width: 1px;
            }
            QSplitter::handle:hover {
                background: #4A90E2;
                width: 2px;
            }
        """)
        
        # Left panel (hierarchy/assets)
        left_panel = self.create_hierarchy_panel()
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(400)
        
        # Center panel (tabbed editor area)
        center_panel = self.create_tabbed_editor_panel()
        
        # Right panel (inspector)
        right_panel = self.create_panel("Inspector", "#f8f9fa")
        right_panel.setMinimumWidth(280)
        right_panel.setMaximumWidth(400)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 800, 300])
        
        layout.addWidget(splitter)
        return widget
    
    def create_hierarchy_panel(self):
        """Create the project hierarchy panel with map generator option"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Panel title
        title_label = QLabel("Project Hierarchy")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Medium))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                padding: 10px 0px;
                border-bottom: 2px solid rgba(74, 144, 226, 0.3);
            }
        """)
        layout.addWidget(title_label)
        
        # Hierarchy tree
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderHidden(True)
        self.hierarchy_tree.setStyleSheet("""
            QTreeWidget {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                color: #2c3e50;
            }
            QTreeWidget::item {
                padding: 5px;
                border-radius: 3px;
                color: #2c3e50;
            }
            QTreeWidget::item:hover {
                background: rgba(74, 144, 226, 0.1);
                color: #2c3e50;
            }
            QTreeWidget::item:selected {
                background: rgba(74, 144, 226, 0.2);
                color: #2c3e50;
            }
        """)
        
        # Add project structure
        self.setup_hierarchy_tree()
        
        # Connect context menu
        self.hierarchy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hierarchy_tree.customContextMenuRequested.connect(self.show_hierarchy_context_menu)
        
        layout.addWidget(self.hierarchy_tree)
        layout.addStretch()
        
        return panel

    def setup_hierarchy_tree(self):
        """Setup the hierarchy tree with project components"""
        self.hierarchy_tree.clear()
        
        # Project root
        project_root = QTreeWidgetItem(self.hierarchy_tree, ["Project"])
        project_root.setExpanded(True)
        
        # Assets folder
        assets_folder = QTreeWidgetItem(project_root, ["Assets"])
        assets_folder.setExpanded(True)
        
        # Maps folder
        maps_folder = QTreeWidgetItem(assets_folder, ["Maps"])
        
        # Items folder
        items_folder = QTreeWidgetItem(assets_folder, ["Items"])
        
        # Tools folder
        tools_folder = QTreeWidgetItem(project_root, ["Tools"])
        tools_folder.setExpanded(True)
        
        # Map Generator tool
        map_generator_item = QTreeWidgetItem(tools_folder, ["Map Generator"])
        map_generator_item.setData(0, Qt.UserRole, "map_generator")
        
        # Item Editor tool
        item_editor_item = QTreeWidgetItem(tools_folder, ["Item Editor"])
        item_editor_item.setData(0, Qt.UserRole, "item_editor")
        
        # Scripts folder
        scripts_folder = QTreeWidgetItem(project_root, ["Scripts"])
        
        # Connect double-click
        self.hierarchy_tree.itemDoubleClicked.connect(self.on_hierarchy_item_double_clicked)
    
    def create_tabbed_editor_panel(self):
        """Create the center panel with tab widget"""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #ffffff; border: none; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: "#2c3e50";
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QTabBar::tab:hover {
                background: #e9ecef;
            }
            QTabBar::close-button {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFYSURBVBiVY/z//z8DJQAggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRVHUAAcRIqjqAAGIkVR1AADGSLA4ggBhJVQcQQIykqgMIIEZS1QEEECO56gACiJFcdQABxEiuOoAAYiRXHUAAMZKrDiCAGMlVBxBAjOSqAwggRnLVAQQQI7nqAAKIkVx1AAHESKo6gABiJFUdQAAxkqoOIIAYSVUHEECMpKoDCCBGUtUBBBAjqeoAAoiRV
        """)
        # Connect tab close signal
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Default welcome tab
        welcome_widget = self.create_welcome_tab()
        self.tab_widget.addTab(welcome_widget, "Welcome")
        
        layout.addWidget(self.tab_widget)
        return panel
    
    def create_welcome_tab(self):
        """Create the default welcome tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        welcome_label = QLabel("Welcome to the Editor")
        welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Light))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #2c3e50; margin: 40px;")
        
        instruction_label = QLabel("Double-click items in the hierarchy to open them as tabs")
        instruction_label.setFont(QFont("Arial", 14))
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("color: #34495e; margin: 20px;")
        
        layout.addWidget(welcome_label)
        layout.addWidget(instruction_label)
        
        return widget
    
    def show_hierarchy_context_menu(self, position: QPoint):
        """Show context menu for hierarchy items"""
        item = self.hierarchy_tree.itemAt(position)
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        menu = QMenu(self.hierarchy_tree)
        
        if item_data == "map_generator":
            open_action = menu.addAction("Open Map Generator")
            open_action.triggered.connect(lambda: self.open_map_generator_tab())
        elif item_data == "item_editor":
            open_action = menu.addAction("Open Item Editor")
            open_action.triggered.connect(lambda: self.open_item_editor_tab())
            
        if menu.actions():
            menu.exec_(self.hierarchy_tree.mapToGlobal(position))
            
            
    def open_item_editor_tab(self):
        """Open the item editor in a new tab"""
        tab_name = "Item Editor"
        
        # Check if tab is already open
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_name:
                self.tab_widget.setCurrentIndex(i)
                return
        
        # Create new item editor widget
        item_editor = ItemEditorWidget()
        
        # Add tab
        tab_index = self.tab_widget.addTab(item_editor, tab_name)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Store reference
        self.open_tabs[tab_name] = item_editor
        
        print(f"Opened {tab_name} tab")
    
    def on_hierarchy_item_double_clicked(self, item, column):
        """Handle double-click on hierarchy items"""
        item_data = item.data(0, Qt.UserRole)
        
        if item_data == "map_generator":
            self.open_map_generator_tab()
        elif item_data == "item_editor":
            self.open_item_editor_tab()
    
    def open_map_generator_tab(self):
        """Open the map generator in a new tab"""
        tab_name = "Map Generator"
        
        # Check if tab is already open
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_name:
                self.tab_widget.setCurrentIndex(i)
                return
        
        # Create new map editor widget
        map_editor = MapEditorWidget()
        
        # Add tab
        tab_index = self.tab_widget.addTab(map_editor, tab_name)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Store reference
        self.open_tabs[tab_name] = map_editor
        
        print(f"Opened {tab_name} tab")
    
    def close_tab(self, index):
        """Close a tab"""
        if index == 0:  # Don't close welcome tab
            return
            
        tab_name = self.tab_widget.tabText(index)
        
        # Remove from open tabs tracking
        if tab_name in self.open_tabs:
            del self.open_tabs[tab_name]
        
        # Remove the tab
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        
        # Clean up the widget
        if widget:
            widget.deleteLater()
        
        print(f"Closed {tab_name} tab")
    
    def create_panel(self, title, bg_color, is_center=False):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Panel title
        title_label = QLabel(title)
        title_label.setFont(QFont("SF Pro Display", 16, QFont.Weight.Medium))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                padding: 10px 0px;
                border-bottom: 2px solid rgba(74, 144, 226, 0.3);
            }
        """)
        
        layout.addWidget(title_label)
        
        if is_center:
            # Add a placeholder for the main editor content
            content = QLabel("Main Editor Canvas")
            content.setAlignment(Qt.AlignCenter)
            content.setFont(QFont("SF Pro Display", 18, QFont.Weight.Light))
            content.setStyleSheet("""
                QLabel {
                    color: #95a5a6;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                    border: 2px dashed rgba(149, 165, 166, 0.5);
                    border-radius: 12px;
                    padding: 40px;
                    margin: 20px;
                }
            """)
            layout.addWidget(content)
        else:
            layout.addStretch()
        
        return panel
        
    def load_projects(self):
        if not self.projects_path.exists():
            self.projects_path.mkdir(parents=True, exist_ok=True)
            return
            
        projects = []
        for item in self.projects_path.iterdir():
            if item.is_dir():
                projects.append((str(item), item.name))
        
        # If no projects exist, show empty state
        if not projects:
            self.show_empty_state()
            return
                
        # Add projects to grid
        row, col = 0, 0
        max_cols = 3
        
        for project_path, project_name in projects:
            card = ProjectCard(project_path, project_name)
            card.projectSelected.connect(self.open_project)
            
            self.projects_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def show_empty_state(self):
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        # Empty state illustration
        empty_icon = QLabel("📁")
        empty_icon.setFont(QFont("SF Pro Display", 64))
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setStyleSheet("color: #bdc3c7; margin: 20px;")
        
        empty_text = QLabel("No projects found")
        empty_text.setFont(QFont("SF Pro Display", 18, QFont.Weight.Medium))
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setStyleSheet("color: #7f8c8d; margin: 10px;")
        
        empty_subtext = QLabel("Create your first project to get started")
        empty_subtext.setFont(QFont("SF Pro Display", 14))
        empty_subtext.setAlignment(Qt.AlignCenter)
        empty_subtext.setStyleSheet("color: #95a5a6; margin-bottom: 30px;")
        
        create_btn = ModernButton("Create New Project", primary=True)
        create_btn.setFixedWidth(200)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        empty_layout.addWidget(empty_subtext)
        empty_layout.addWidget(create_btn, alignment=Qt.AlignCenter)
        
        self.projects_layout.addWidget(empty_widget, 0, 0, 1, 3)
                
    def open_project(self, project_path: str):
        project_name = Path(project_path).name
        print(f"Opening project: {project_name}")
        self.stacked_widget.setCurrentWidget(self.editor_view)
        self.setWindowTitle(f"Hoomans Studio - {project_name}")
        # Show the open project button when in editor view
        self.open_project_btn.show()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide font with fallback
    font = QFont("Arial", 10)  # Use Arial instead of SF Pro Display
    app.setFont(font)
    
    studio = StudioUI()
    studio.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

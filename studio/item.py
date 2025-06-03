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
from studio.ui import ModernButton

# Import the map creator components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from world.tile import Tile
from world.map import WorldMap
from world.entity_tile import EntityTileManager, TreeEntityTile, HouseEntityTile
from world.biome_generator import ProceduralMapGenerator, BiomeType
from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import QPoint

class ItemEditorWidget(QWidget):
    """Item editor widget for creating and managing game items"""
    
    def __init__(self, project_path=None):
        super().__init__()
        self.project_path = project_path
        self.item_system = None
        self.current_item = None
        self.setup_ui()
        self.setup_item_system()
        
    def setup_item_system(self):
        """Initialize the item system"""
        try:
            # Use project path if provided, otherwise use current file directory
            if self.project_path:
                project_root = self.project_path
            else:
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

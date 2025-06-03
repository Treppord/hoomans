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

class EntityEditorWidget(QWidget):
    """Entity editor widget for creating and managing game entities"""
    
    def __init__(self):
        super().__init__()
        self.current_entity = None
        self.entity_data = {}
        self.load_entity_types()
        self.setup_ui()
        self.connect_auto_generation()  # Add this line
        self.setup_entity_tooltips()    # Add this line
        self.refresh_entity_list()
        
    def load_entity_types(self):
        """Load available entity types from the codebase with CNA integration"""
        from cna_utils import Gender, Culture, Nation
        
        self.entity_types = {
            "npc": {
                "name": "NPC",
                "class": "NPC", 
                "properties": ["hunger", "thirst", "energy", "ai_type", "cna_attributes"]
            },
            "food_npc": {
                "name": "Food NPC",
                "class": "FoodNPC",
                "properties": ["food_type", "nutrition_value", "cna_attributes"]
            },
            "player": {
                "name": "Player",
                "class": "Rectangle",
                "properties": ["controllable", "cna_attributes"]
            }
        }
        
        # Store CNA enums for UI
        self.cna_genders = [(g.name, g.value) for g in Gender]
        self.cna_cultures = [(c.name, c.value) for c in Culture]
        self.cna_nations = [(n.name, n.value) for n in Nation]
        
    def setup_ui(self):
        """Setup UI with keyboard shortcuts"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left panel - Entity list and controls
        left_panel = self.create_entity_list_panel()
        left_panel.setFixedWidth(300)
        
        # Right panel - Entity editor
        right_panel = self.create_entity_editor_panel()
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+N for new entity
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self.create_new_entity)
        
        # Ctrl+S for save
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_current_entity)
        
        # Delete key for delete entity
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self.delete_current_entity)
        
        # Ctrl+D for duplicate
        duplicate_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        duplicate_shortcut.activated.connect(self.duplicate_current_entity)

    def create_entity_list_panel(self):
        """Create entity list panel with proper styling"""
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
        title = QLabel("Entity Manager")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000; padding: 10px 0px; background: transparent;")
        layout.addWidget(title)
        
        # Search box
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout(search_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search entities...")
        self.search_edit.textChanged.connect(self.search_entities)
        search_layout.addWidget(self.search_edit)
        layout.addWidget(search_group)
        
        # Type filter
        type_group = QGroupBox("Type Filter")
        type_layout = QVBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", "all")
        self.type_combo.currentTextChanged.connect(self.filter_entities)
        type_layout.addWidget(self.type_combo)
        layout.addWidget(type_group)
        
        # Entity list
        self.entity_list = QTreeWidget()
        self.entity_list.setHeaderHidden(True)
        self.entity_list.setStyleSheet("""
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
        self.entity_list.itemClicked.connect(self.select_entity)
        layout.addWidget(self.entity_list)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        self.new_entity_btn = ModernButton("New Entity (Ctrl+N)", primary=True)
        self.new_entity_btn.clicked.connect(self.create_new_entity)
        button_layout.addWidget(self.new_entity_btn)
        
        self.delete_entity_btn = ModernButton("Delete Entity (Del)")
        self.delete_entity_btn.clicked.connect(self.delete_current_entity)
        self.delete_entity_btn.setEnabled(False)
        button_layout.addWidget(self.delete_entity_btn)
        
        self.duplicate_entity_btn = ModernButton("Duplicate (Ctrl+D)")
        self.duplicate_entity_btn.clicked.connect(self.duplicate_current_entity)
        self.duplicate_entity_btn.setEnabled(False)
        button_layout.addWidget(self.duplicate_entity_btn)
        
        # Export/Import buttons
        self.export_btn = ModernButton("Export Entities")
        self.export_btn.clicked.connect(self.export_entities)
        button_layout.addWidget(self.export_btn)
        
        self.import_btn = ModernButton("Import Entities")
        self.import_btn.clicked.connect(self.import_entities)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
        
        # Add CNA management section
        self.add_cna_management_buttons(layout)
        
        return panel

    def auto_generate_entity_name(self):
        """Auto-generate entity name based on CNA attributes"""
        if not (self.first_name_edit.text() and self.last_name_edit.text()):
            return
        
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        
        # Only update if name field is empty or matches previous auto-generated name
        current_name = self.name_edit.text().strip()
        auto_name = f"{first_name} {last_name}"
        
        if not current_name or current_name == auto_name:
            self.name_edit.setText(auto_name)
        
        # Auto-generate entity ID if empty
        current_id = self.entity_id_edit.text().strip()
        auto_id = f"{first_name}_{last_name}".lower().replace(" ", "_")
        
        if not current_id or current_id == auto_id:
            # Ensure unique ID
            base_id = auto_id
            counter = 1
            while auto_id in self.entity_data and self.current_entity and self.current_entity.get("id") != auto_id:
                auto_id = f"{base_id}_{counter}"
                counter += 1
            
            self.entity_id_edit.setText(auto_id)

    # Connect auto-generation to name field changes
    def connect_auto_generation(self):
        """Connect auto-generation to form field changes"""
        self.first_name_edit.textChanged.connect(self.auto_generate_entity_name)
        self.last_name_edit.textChanged.connect(self.auto_generate_entity_name)

    def setup_entity_tooltips(self):
        """Setup tooltips for entity list items with detailed CNA info"""
        def update_tooltip(item):
            entity_id = item.data(0, Qt.UserRole)
            if entity_id and entity_id in self.entity_data:
                entity_data = self.entity_data[entity_id]
                tooltip = self.get_entity_summary_info(entity_data)
                item.setToolTip(0, tooltip)
        
        # Connect to item creation/update
        self.entity_list.itemChanged.connect(update_tooltip)

    def validate_cna_compatibility(self, entity_data):
        """Validate that entity data is compatible with CNA system"""
        issues = []
        
        cna_data = entity_data.get("cna_attributes")
        if not cna_data:
            return issues
        
        try:
            from cna_utils import Gender, Culture, Nation
            
            # Validate enum values
            gender_val = cna_data.get("gender", 0)
            if not any(g.value == gender_val for g in Gender):
                issues.append(f"Invalid gender value: {gender_val}")
            
            culture_val = cna_data.get("culture", 0)
            if not any(c.value == culture_val for c in Culture):
                issues.append(f"Invalid culture value: {culture_val}")
            
            nation_val = cna_data.get("nation", 0)
            if not any(n.value == nation_val for n in Nation):
                issues.append(f"Invalid nation value: {nation_val}")
            
            # Validate ranges
            age = cna_data.get("age_minutes", 0)
            if not (0 <= age <= 60):
                issues.append(f"Age out of range: {age} (should be 0-60)")
            
            for health_type in ["physical_health", "mental_health", "generational_health"]:
                health_val = cna_data.get(health_type, 0)
                if not (0 <= health_val <= 5):
                    issues.append(f"{health_type} out of range: {health_val} (should be 0-5)")
            
            for factor_type in ["intelligence_factor", "adaptability", "immunity_strength"]:
                factor_val = cna_data.get(factor_type, 1.0)
                if not (0.1 <= factor_val <= 3.0):
                    issues.append(f"{factor_type} out of range: {factor_val} (should be 0.1-3.0)")
                    
        except Exception as e:
            issues.append(f"CNA validation error: {e}")
        
        return issues

    def get_entity_summary_info(self, entity_data):
        """Get summary information for entity display"""
        summary = []
        
        # Basic info
        entity_type = entity_data.get("type", "unknown")
        summary.append(f"Type: {entity_type.title()}")
        
        # Position
        x = entity_data.get("grid_x", 0)
        y = entity_data.get("grid_y", 0)
        summary.append(f"Position: ({x}, {y})")
        
        # CNA info if available
        cna_data = entity_data.get("cna_attributes")
        if cna_data:
            age = cna_data.get("age_minutes", 0)
            summary.append(f"Age: {age} minutes")
            
            try:
                from cna_utils import Gender, Culture, Nation
                gender = Gender(cna_data.get("gender", 0)).name.title()
                culture = Culture(cna_data.get("culture", 0)).name.title()
                nation = Nation(cna_data.get("nation", 0)).name
                summary.append(f"Profile: {gender}, {culture}, {nation}")
            except:
                pass
        
        # Type-specific info
        if entity_type == "npc":
            hunger = entity_data.get("hunger", 5)
            thirst = entity_data.get("thirst", 5)
            energy = entity_data.get("energy", 5)
            summary.append(f"Stats: H{hunger}/T{thirst}/E{energy}")
        elif entity_type == "food_npc":
            food_type = entity_data.get("food_type", "unknown")
            nutrition = entity_data.get("nutrition_value", 0)
            summary.append(f"Food: {food_type.title()} (N{nutrition})")
        
        return " | ".join(summary)

    def create_entity_editor_panel(self):
        """Create the entity editor panel with proper styling"""
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
        
        self.editor_title = QLabel("Entity Editor")
        self.editor_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.editor_title.setStyleSheet("color: #000000; padding: 10px 0px; background: transparent;")
        header_layout.addWidget(self.editor_title)
        
        header_layout.addStretch()
        
        # Entity count status
        self.status_label = QLabel("0 entities")
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
        
        self.setup_entity_form()
        
        scroll_area.setWidget(self.form_widget)
        layout.addWidget(scroll_area)
        
        # Save button
        self.save_btn = ModernButton("Save Entity", primary=True)
        self.save_btn.clicked.connect(self.save_current_entity)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        return panel

    def setup_entity_form(self):
        """Setup the entity editing form with proper styling"""
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
            QComboBox::drop-down {
                background: white;
                border: 1px solid #ddd;
            }
            QComboBox::down-arrow {
                color: #000000;
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
        """
        
        self.form_widget.setStyleSheet(form_style)
        
        # Basic properties
        self.entity_id_edit = QLineEdit()
        self.entity_id_edit.setPlaceholderText("unique_entity_id")
        self.entity_id_edit.textChanged.connect(self.on_form_changed)
        
        id_label = QLabel("Entity ID:")
        id_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(id_label, self.entity_id_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Display Name")
        self.name_edit.textChanged.connect(self.on_form_changed)
        
        name_label = QLabel("Name:")
        name_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(name_label, self.name_edit)
        
        # Entity type
        self.type_edit = QComboBox()
        for type_key, type_info in self.entity_types.items():
            self.type_edit.addItem(type_info["name"], type_key)
        self.type_edit.currentTextChanged.connect(self.on_type_changed)
        
        type_label = QLabel("Type:")
        type_label.setStyleSheet("color: #000000; background: transparent;")
        self.form_layout.addRow(type_label, self.type_edit)
        
        # Add CNA section
        cna_group = QGroupBox("CNA Attributes")
        cna_layout = QFormLayout(cna_group)
        
        # CNA File selection
        cna_file_layout = QHBoxLayout()
        self.cna_file_edit = QLineEdit()
        self.cna_file_edit.setPlaceholderText("Select CNA file or create new...")
        self.cna_file_edit.textChanged.connect(self.on_form_changed)
        
        self.browse_cna_btn = QPushButton("Browse")
        self.browse_cna_btn.clicked.connect(self.browse_cna_file)
        self.create_cna_btn = QPushButton("Create New")
        self.create_cna_btn.clicked.connect(self.create_new_cna)
        
        cna_file_layout.addWidget(self.cna_file_edit)
        cna_file_layout.addWidget(self.browse_cna_btn)
        cna_file_layout.addWidget(self.create_cna_btn)
        
        cna_file_label = QLabel("CNA File:")
        cna_file_label.setStyleSheet("color: #000000; background: transparent;")
        cna_layout.addRow(cna_file_label, cna_file_layout)
        
        # Basic CNA attributes
        self.first_name_edit = QLineEdit()
        self.first_name_edit.textChanged.connect(self.on_cna_changed)
        first_name_label = QLabel("First Name:")
        first_name_label.setStyleSheet("color: #000000; background: transparent;")
        cna_layout.addRow(first_name_label, self.first_name_edit)
        
        self.last_name_edit = QLineEdit()
        self.last_name_edit.textChanged.connect(self.on_cna_changed)
        last_name_label = QLabel("Last Name:")
        last_name_label.setStyleSheet("color: #000000; background: transparent;")
        cna_layout.addRow(last_name_label, self.last_name_edit)
        
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 60)
        self.age_spin.setSuffix(" minutes")
        self.age_spin.valueChanged.connect(self.on_cna_changed)
        age_label = QLabel("Age:")
        age_label.setStyleSheet("color: #000000; background: transparent;")
        cna_layout.addRow(age_label, self.age_spin)
        
        # Gender
        self.gender_combo = QComboBox()
        for name, value in self.cna_genders:
            self.gender_combo.addItem(name.title(), value)
        self.gender_combo.currentTextChanged.connect(self.on_cna_changed)
        gender_label = QLabel("Gender:")
        gender_label.setStyleSheet("color: #000000; background: transparent;")
        cna_layout.addRow(gender_label, self.gender_combo)
        
        # Culture
        self.culture_combo = QComboBox()
        for name, value in self.cna_cultures:
            self.culture_combo.addItem(name.title(), value)
        self.culture_combo.currentTextChanged.connect(self.on_cna_changed)
        culture_label = QLabel("Culture:")
        culture_label.setStyleSheet("color: #000000; background: transparent;")
        cna_layout.addRow(culture_label, self.culture_combo)
        
        # Nation
        self.nation_combo = QComboBox()
        for name, value in self.cna_nations:
            self.nation_combo.addItem(name.title(), value)
        self.nation_combo.currentTextChanged.connect(self.on_cna_changed)
        nation_label = QLabel("Nation:")
        nation_label.setStyleSheet("color: #000000; background: transparent;")
        cna_layout.addRow(nation_label, self.nation_combo)
        
        self.form_layout.addRow(cna_group)
        
        # Health attributes
        health_group = QGroupBox("Health Attributes")
        health_layout = QFormLayout(health_group)
        
        self.physical_health_spin = QSpinBox()
        self.physical_health_spin.setRange(0, 5)
        self.physical_health_spin.valueChanged.connect(self.on_cna_changed)
        ph_label = QLabel("Physical Health:")
        ph_label.setStyleSheet("color: #000000; background: transparent;")
        health_layout.addRow(ph_label, self.physical_health_spin)
        
        self.mental_health_spin = QSpinBox()
        self.mental_health_spin.setRange(0, 5)
        self.mental_health_spin.valueChanged.connect(self.on_cna_changed)
        mh_label = QLabel("Mental Health:")
        mh_label.setStyleSheet("color: #000000; background: transparent;")
        health_layout.addRow(mh_label, self.mental_health_spin)
        
        self.generational_health_spin = QSpinBox()
        self.generational_health_spin.setRange(0, 5)
        self.generational_health_spin.valueChanged.connect(self.on_cna_changed)
        gh_label = QLabel("Generational Health:")
        gh_label.setStyleSheet("color: #000000; background: transparent;")
        health_layout.addRow(gh_label, self.generational_health_spin)
        
        self.form_layout.addRow(health_group)
        
        # Extended attributes
        extended_group = QGroupBox("Extended Attributes")
        extended_layout = QFormLayout(extended_group)
        
        self.intelligence_spin = QDoubleSpinBox()
        self.intelligence_spin.setRange(0.1, 3.0)
        self.intelligence_spin.setSingleStep(0.1)
        self.intelligence_spin.setValue(1.0)
        self.intelligence_spin.valueChanged.connect(self.on_cna_changed)
        intel_label = QLabel("Intelligence Factor:")
        intel_label.setStyleSheet("color: #000000; background: transparent;")
        extended_layout.addRow(intel_label, self.intelligence_spin)
        
        self.adaptability_spin = QDoubleSpinBox()
        self.adaptability_spin.setRange(0.1, 3.0)
        self.adaptability_spin.setSingleStep(0.1)
        self.adaptability_spin.setValue(1.0)
        self.adaptability_spin.valueChanged.connect(self.on_cna_changed)
        adapt_label = QLabel("Adaptability:")
        adapt_label.setStyleSheet("color: #000000; background: transparent;")
        extended_layout.addRow(adapt_label, self.adaptability_spin)
        
        self.immunity_spin = QDoubleSpinBox()
        self.immunity_spin.setRange(0.1, 3.0)
        self.immunity_spin.setSingleStep(0.1)
        self.immunity_spin.setValue(1.0)
        self.immunity_spin.valueChanged.connect(self.on_cna_changed)
        immunity_label = QLabel("Immunity Strength:")
        immunity_label.setStyleSheet("color: #000000; background: transparent;")
        extended_layout.addRow(immunity_label, self.immunity_spin)
        
        self.form_layout.addRow(extended_group)
        
        # Color preview (calculated from CNA)
        color_group = QGroupBox("Calculated Color (from CNA)")
        color_layout = QVBoxLayout(color_group)
        
        self.color_preview = QLabel()
        self.color_preview.setFixedHeight(50)
        self.color_preview.setStyleSheet("border: 1px solid #ddd; background: #ffffff;")
        color_layout.addWidget(self.color_preview)
        
        self.form_layout.addRow(color_group)
        
        # Position
        position_group = QGroupBox("Position")
        position_layout = QFormLayout(position_group)
        
        self.grid_x_spin = QSpinBox()
        self.grid_x_spin.setRange(0, 999)
        self.grid_x_spin.valueChanged.connect(self.on_form_changed)
        
        x_label = QLabel("Grid X:")
        x_label.setStyleSheet("color: #000000; background: transparent;")
        position_layout.addRow(x_label, self.grid_x_spin)
        
        self.grid_y_spin = QSpinBox()
        self.grid_y_spin.setRange(0, 999)
        self.grid_y_spin.valueChanged.connect(self.on_form_changed)
        
        y_label = QLabel("Grid Y:")
        y_label.setStyleSheet("color: #000000; background: transparent;")
        position_layout.addRow(y_label, self.grid_y_spin)
        
        self.form_layout.addRow(position_group)
        
        # Visual properties
        visual_group = QGroupBox("Visual Properties")
        visual_layout = QFormLayout(visual_group)
        
        self.color_r_spin = QSpinBox()
        self.color_r_spin.setRange(0, 255)
        self.color_r_spin.setValue(255)
        self.color_r_spin.valueChanged.connect(self.on_form_changed)
        
        r_label = QLabel("Color R:")
        r_label.setStyleSheet("color: #000000; background: transparent;")
        visual_layout.addRow(r_label, self.color_r_spin)
        
        self.color_g_spin = QSpinBox()
        self.color_g_spin.setRange(0, 255)
        self.color_g_spin.setValue(255)
        self.color_g_spin.valueChanged.connect(self.on_form_changed)
        
        g_label = QLabel("Color G:")
        g_label.setStyleSheet("color: #000000; background: transparent;")
        visual_layout.addRow(g_label, self.color_g_spin)
        
        self.color_b_spin = QSpinBox()
        self.color_b_spin.setRange(0, 255)
        self.color_b_spin.setValue(255)
        self.color_b_spin.valueChanged.connect(self.on_form_changed)
        
        b_label = QLabel("Color B:")
        b_label.setStyleSheet("color: #000000; background: transparent;")
        visual_layout.addRow(b_label, self.color_b_spin)
        
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10.0)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.valueChanged.connect(self.on_form_changed)
        
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("color: #000000; background: transparent;")
        visual_layout.addRow(speed_label, self.speed_spin)
        
        self.form_layout.addRow(visual_group)
        
        # Type-specific properties container
        self.specific_props_widget = QWidget()
        self.specific_props_layout = QFormLayout(self.specific_props_widget)
        self.form_layout.addRow(self.specific_props_widget)

    def on_cna_changed(self):
        """Handle CNA attribute changes and update color preview"""
        self.update_color_preview()
        self.on_form_changed()
        
    def update_color_preview(self):
        """Update color preview based on CNA attributes"""
        try:
            from cna_utils import calculate_entity_color, Culture
            
            # Create temporary CNA attributes for color calculation
            culture_value = self.culture_combo.currentData()
            age_value = self.age_spin.value()
            
            # Mock CNA attributes object for color calculation
            class MockCNA:
                def __init__(self, culture, age):
                    self.culture = Culture(culture)
                    self.age_minutes = age
            
            mock_cna = MockCNA(culture_value, age_value)
            color = calculate_entity_color(mock_cna)
            
            # Update color preview
            self.color_preview.setStyleSheet(f"""
                border: 1px solid #ddd; 
                background: rgb({color[0]}, {color[1]}, {color[2]});
            """)
            
            # Update the RGB spinboxes to reflect calculated color
            self.color_r_spin.setValue(color[0])
            self.color_g_spin.setValue(color[1])
            self.color_b_spin.setValue(color[2])
            
        except Exception as e:
            print(f"Error updating color preview: {e}")

    def browse_cna_file(self):
        """Browse for existing CNA file"""
        try:
            from PySide6.QtWidgets import QFileDialog
            import os
            
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cna_dir = os.path.join(project_root, "cna", "data")
            
            filename, _ = QFileDialog.getOpenFileName(
                self, 
                "Select CNA File", 
                cna_dir,
                "CNA Files (*.cna);;All Files (*)"
            )
            
            if filename:
                self.load_cna_file(filename)
                
        except Exception as e:
            print(f"Error browsing CNA file: {e}")

    def load_cna_file(self, filepath):
        """Load CNA file and populate form"""
        try:
            from cna_utils import CNACodec
            
            cna_attributes = CNACodec.load_from_file(filepath)
            
            # Update form with CNA data
            self.cna_file_edit.setText(os.path.basename(filepath))
            self.first_name_edit.setText(cna_attributes.first_name)
            self.last_name_edit.setText(cna_attributes.last_name)
            self.age_spin.setValue(cna_attributes.age_minutes)
            
            # Set combo boxes
            gender_index = self.gender_combo.findData(cna_attributes.gender.value)
            if gender_index >= 0:
                self.gender_combo.setCurrentIndex(gender_index)
                
            culture_index = self.culture_combo.findData(cna_attributes.culture.value)
            if culture_index >= 0:
                self.culture_combo.setCurrentIndex(culture_index)
                
            nation_index = self.nation_combo.findData(cna_attributes.nation.value)
            if nation_index >= 0:
                self.nation_combo.setCurrentIndex(nation_index)
            
            # Health attributes
            self.physical_health_spin.setValue(cna_attributes.physical_health)
            self.mental_health_spin.setValue(cna_attributes.mental_health)
            self.generational_health_spin.setValue(cna_attributes.generational_health)
            
            # Extended attributes
            self.intelligence_spin.setValue(cna_attributes.intelligence_factor)
            self.adaptability_spin.setValue(cna_attributes.adaptability)
            self.immunity_spin.setValue(cna_attributes.immunity_strength)
            
            # Update entity name if empty
            if not self.name_edit.text():
                self.name_edit.setText(f"{cna_attributes.first_name} {cna_attributes.last_name}")
            
            self.update_color_preview()
            
        except Exception as e:
            print(f"Error loading CNA file: {e}")

    def create_new_cna(self):
        """Create new CNA file with current form data"""
        try:
            from cna_utils import CNAAttributes, CNACodec, Gender, Culture, Nation
            from PySide6.QtWidgets import QFileDialog
            import os
            
            # Create CNA attributes from form
            cna_attributes = CNAAttributes(
                first_name=self.first_name_edit.text() or "John",
                last_name=self.last_name_edit.text() or "Doe",
                age_minutes=self.age_spin.value(),
                gender=Gender(self.gender_combo.currentData()),
                culture=Culture(self.culture_combo.currentData()),
                nation=Nation(self.nation_combo.currentData()),
                physical_health=self.physical_health_spin.value(),
                mental_health=self.mental_health_spin.value(),
                generational_health=self.generational_health_spin.value(),
                intelligence_factor=self.intelligence_spin.value(),
                adaptability=self.adaptability_spin.value(),
                immunity_strength=self.immunity_spin.value()
            )
            
            # Save dialog
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cna_dir = os.path.join(project_root, "cna", "data")
            os.makedirs(cna_dir, exist_ok=True)
            
            suggested_name = f"{cna_attributes.first_name}_{cna_attributes.last_name}.cna"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save CNA File",
                os.path.join(cna_dir, suggested_name),
                "CNA Files (*.cna);;All Files (*)"
            )
            
            if filename:
                CNACodec.save_to_file(cna_attributes, filename)
                self.cna_file_edit.setText(os.path.basename(filename))
                print(f"Created new CNA file: {filename}")
                
        except Exception as e:
            print(f"Error creating CNA file: {e}")

    def import_from_game_cna_directory(self):
        """Import entities from game's CNA directory"""
        try:
            from pathlib import Path
            from cna_utils import CNACodec
            import os
            
            # Look for CNA files in the game directory
            project_root = Path(__file__).parent.parent
            cna_dir = project_root / "cna" / "data"
            
            if not cna_dir.exists():
                print("CNA directory not found")
                return
            
            imported_count = 0
            for cna_file in cna_dir.glob("*.cna"):
                try:
                    # Load CNA file
                    cna_attributes = CNACodec.load_from_file(str(cna_file))
                    
                    # Create entity ID from CNA
                    entity_id = f"{cna_attributes.first_name}_{cna_attributes.last_name}".lower().replace(" ", "_")
                    
                    # Skip if entity already exists
                    if entity_id in self.entity_data:
                        continue
                    
                    # Calculate color from CNA
                    from cna_utils import calculate_entity_color
                    color = calculate_entity_color(cna_attributes)
                    
                    # Create entity data
                    entity_data = {
                        "id": entity_id,
                        "name": f"{cna_attributes.first_name} {cna_attributes.last_name}",
                        "type": "npc",  # Default to NPC
                        "grid_x": 10,  # Default position
                        "grid_y": 10,
                        "color": list(color),
                        "speed": 1.0,
                        "hunger": 5,
                        "thirst": 5,
                        "energy": 5,
                        "ai_type": "random_wander",
                        "cna_attributes": {
                            "first_name": cna_attributes.first_name,
                            "last_name": cna_attributes.last_name,
                            "age_minutes": cna_attributes.age_minutes,
                            "gender": cna_attributes.gender.value,
                            "culture": cna_attributes.culture.value,
                            "nation": cna_attributes.nation.value,
                            "physical_health": cna_attributes.physical_health,
                            "mental_health": cna_attributes.mental_health,
                            "generational_health": cna_attributes.generational_health,
                            "intelligence_factor": cna_attributes.intelligence_factor,
                            "adaptability": cna_attributes.adaptability,
                            "immunity_strength": cna_attributes.immunity_strength,
                            "cna_file": cna_file.name
                        }
                    }
                    
                    self.entity_data[entity_id] = entity_data
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Error importing CNA file {cna_file}: {e}")
            
            if imported_count > 0:
                self.refresh_entity_list()
                print(f"Imported {imported_count} entities from CNA files")
            else:
                print("No new entities imported from CNA files")
                
        except Exception as e:
            print(f"Error importing from CNA directory: {e}")

    def export_entities_to_game(self):
        """Export entities to game engine format with CNA files"""
        try:
            from pathlib import Path
            import json
            from cna_utils import CNAAttributes, CNACodec, Gender, Culture, Nation
            
            export_dir = Path.home() / "hoomans" / "game_exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export entity definitions
            game_entities = []
            
            for entity_id, entity_data in self.entity_data.items():
                game_entity = {
                    "id": entity_id,
                    "name": entity_data.get("name"),
                    "type": entity_data.get("type"),
                    "position": {
                        "x": entity_data.get("grid_x", 0),
                        "y": entity_data.get("grid_y", 0)
                    },
                    "properties": {
                        "color": entity_data.get("color", [255, 255, 255]),
                        "speed": entity_data.get("speed", 1.0)
                    }
                }
                
                # Add type-specific properties
                entity_type = entity_data.get("type")
                if entity_type == "npc":
                    game_entity["properties"].update({
                        "hunger": entity_data.get("hunger", 5),
                        "thirst": entity_data.get("thirst", 5),
                        "energy": entity_data.get("energy", 5),
                        "ai_type": entity_data.get("ai_type", "random_wander")
                    })
                elif entity_type == "food_npc":
                    game_entity["properties"].update({
                        "food_type": entity_data.get("food_type", "fruit"),
                        "nutrition_value": entity_data.get("nutrition_value", 2)
                    })
                elif entity_type == "player":
                    game_entity["properties"]["controllable"] = True
                
                # Handle CNA data
                cna_data = entity_data.get("cna_attributes")
                if cna_data:
                    # Create CNA file if it doesn't exist
                    cna_filename = cna_data.get("cna_file")
                    if not cna_filename:
                        first_name = cna_data.get("first_name", "Unknown")
                        last_name = cna_data.get("last_name", "Entity")
                        cna_filename = f"{first_name}_{last_name}.cna"
                    
                    # Create CNA attributes object
                    cna_attributes = CNAAttributes(
                        first_name=cna_data.get("first_name", "Unknown"),
                        last_name=cna_data.get("last_name", "Entity"),
                        age_minutes=cna_data.get("age_minutes", 0),
                        gender=Gender(cna_data.get("gender", 0)),
                        culture=Culture(cna_data.get("culture", 0)),
                        nation=Nation(cna_data.get("nation", 0)),
                        physical_health=cna_data.get("physical_health", 3),
                        mental_health=cna_data.get("mental_health", 3),
                        generational_health=cna_data.get("generational_health", 3),
                        intelligence_factor=cna_data.get("intelligence_factor", 1.0),
                        adaptability=cna_data.get("adaptability", 1.0),
                        immunity_strength=cna_data.get("immunity_strength", 1.0)
                    )
                    
                    # Save CNA file
                    cna_export_dir = export_dir / "cna" / "data"
                    cna_export_dir.mkdir(parents=True, exist_ok=True)
                    cna_filepath = cna_export_dir / cna_filename
                    CNACodec.save_to_file(cna_attributes, str(cna_filepath))
                    
                    game_entity["cna_file"] = cna_filename
                
                game_entities.append(game_entity)
            
            # Save entities JSON
            entities_file = export_dir / "entities.json"
            with open(entities_file, 'w') as f:
                json.dump(game_entities, f, indent=2)
            
            print(f"Exported {len(game_entities)} entities to: {export_dir}")
            return str(export_dir)
            
        except Exception as e:
            print(f"Error exporting entities to game: {e}")
            return None


    def refresh_entity_list(self):
        """Refresh the entity list with CNA-aware display"""
        self.entity_list.clear()
        
        # Update type filter combo
        self.type_combo.clear()
        self.type_combo.addItem("All Types", "all")
        
        # Group entities by type
        type_entities = {}
        total_entities = 0
        
        for entity_id, entity_data in self.entity_data.items():
            entity_type = entity_data.get("type", "unknown")
            if entity_type not in type_entities:
                type_entities[entity_type] = []
                # Add to type filter
                type_info = self.entity_types.get(entity_type, {"name": entity_type.title()})
                self.type_combo.addItem(type_info["name"], entity_type)
            type_entities[entity_type].append((entity_id, entity_data))
            total_entities += 1
        
        # Add entities to tree with CNA info
        for entity_type, entities in type_entities.items():
            type_info = self.entity_types.get(entity_type, {"name": entity_type.title()})
            type_item = QTreeWidgetItem(self.entity_list, [f"{type_info['name']} ({len(entities)})"])
            type_item.setExpanded(True)
            
            # Set type item styling
            font = type_item.font(0)
            font.setBold(True)
            type_item.setFont(0, font)
            
            for entity_id, entity_data in sorted(entities, key=lambda x: x[1].get("name", x[0])):
                entity_name = entity_data.get("name", entity_id)
                
                # Add CNA info to display name if available
                cna_data = entity_data.get("cna_attributes")
                if cna_data:
                    first_name = cna_data.get("first_name", "")
                    last_name = cna_data.get("last_name", "")
                    if first_name or last_name:
                        cna_name = f"{first_name} {last_name}".strip()
                        if cna_name != entity_name:
                            entity_name = f"{entity_name} ({cna_name})"
                
                entity_widget = QTreeWidgetItem(type_item, [entity_name])
                entity_widget.setData(0, Qt.UserRole, entity_id)
                
                # Set color based on CNA culture if available
                if cna_data:
                    try:
                        from cna_utils import Culture
                        culture_value = cna_data.get("culture", 0)
                        culture = Culture(culture_value)
                        
                        # Set text color based on culture
                        culture_colors = {
                            Culture.RED: "#8B0000",
                            Culture.BLUE: "#000080", 
                            Culture.GREEN: "#006400",
                            Culture.YELLOW: "#B8860B",
                            Culture.PURPLE: "#4B0082",
                            Culture.ORANGE: "#FF4500",
                            Culture.PINK: "#C71585",
                            Culture.BROWN: "#8B4513",
                            Culture.GRAY: "#696969",
                            Culture.BLACK: "#000000",
                            Culture.WHITE: "#2F4F4F"  # Dark gray for visibility
                        }
                        
                        color = culture_colors.get(culture, "#000000")
                        entity_widget.setForeground(0, QColor(color))
                        
                    except Exception as e:
                        print(f"Error setting culture color: {e}")
        
        # Update status
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"{total_entities} entities")

    def search_entities(self):
        """Search entities by name or ID"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.entity_list.topLevelItemCount()):
            type_item = self.entity_list.topLevelItem(i)
            type_visible = False
            
            for j in range(type_item.childCount()):
                item = type_item.child(j)
                entity_id = item.data(0, Qt.UserRole)
                item_name = item.text(0).lower()
                
                if not search_text or search_text in item_name or search_text in entity_id.lower():
                    item.setHidden(False)
                    type_visible = True
                else:
                    item.setHidden(True)
            
            type_item.setHidden(not type_visible)

    def filter_entities(self):
        """Filter entities by selected type"""
        selected_type = self.type_combo.currentData()
        
        for i in range(self.entity_list.topLevelItemCount()):
            type_item = self.entity_list.topLevelItem(i)
            type_name = type_item.text(0).lower()
            
            if selected_type == "all" or selected_type in type_name:
                type_item.setHidden(False)
            else:
                type_item.setHidden(True)

    def on_type_changed(self):
        """Handle entity type change to show/hide specific properties"""
        self.clear_specific_properties()
        
        entity_type = self.type_edit.currentData()
        
        widget_style = """
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
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
        
        if entity_type == "npc":
            # NPC specific properties
            self.hunger_spin = QSpinBox()
            self.hunger_spin.setRange(0, 10)
            self.hunger_spin.setValue(5)
            self.hunger_spin.valueChanged.connect(self.on_form_changed)
            self.hunger_spin.setStyleSheet(widget_style)
            
            hunger_label = QLabel("Hunger:")
            hunger_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(hunger_label, self.hunger_spin)
            
            self.thirst_spin = QSpinBox()
            self.thirst_spin.setRange(0, 10)
            self.thirst_spin.setValue(5)
            self.thirst_spin.valueChanged.connect(self.on_form_changed)
            self.thirst_spin.setStyleSheet(widget_style)
            
            thirst_label = QLabel("Thirst:")
            thirst_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(thirst_label, self.thirst_spin)
            
            self.energy_spin = QSpinBox()
            self.energy_spin.setRange(0, 10)
            self.energy_spin.setValue(5)
            self.energy_spin.valueChanged.connect(self.on_form_changed)
            self.energy_spin.setStyleSheet(widget_style)
            
            energy_label = QLabel("Energy:")
            energy_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(energy_label, self.energy_spin)
            
            self.ai_type_combo = QComboBox()
            self.ai_type_combo.addItem("Random Wander", "random_wander")
            self.ai_type_combo.addItem("Idle", "idle")
            self.ai_type_combo.currentTextChanged.connect(self.on_form_changed)
            self.ai_type_combo.setStyleSheet(widget_style)
            
            ai_label = QLabel("AI Type:")
            ai_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(ai_label, self.ai_type_combo)
            
        elif entity_type == "food_npc":
            # Food NPC specific properties
            self.food_type_combo = QComboBox()
            self.food_type_combo.addItem("Fruit", "fruit")
            self.food_type_combo.addItem("Vegetable", "vegetable")
            self.food_type_combo.addItem("Berry", "berry")
            self.food_type_combo.addItem("Mushroom", "mushroom")
            self.food_type_combo.currentTextChanged.connect(self.on_form_changed)
            self.food_type_combo.setStyleSheet(widget_style)
            
            food_label = QLabel("Food Type:")
            food_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(food_label, self.food_type_combo)
            
            self.nutrition_spin = QSpinBox()
            self.nutrition_spin.setRange(1, 10)
            self.nutrition_spin.setValue(2)
            self.nutrition_spin.valueChanged.connect(self.on_form_changed)
            self.nutrition_spin.setStyleSheet(widget_style)
            
            nutrition_label = QLabel("Nutrition Value:")
            nutrition_label.setStyleSheet("color: #000000; background: transparent;")
            self.specific_props_layout.addRow(nutrition_label, self.nutrition_spin)
        
        self.on_form_changed()

    def clear_specific_properties(self):
        """Clear type-specific property widgets"""
        while self.specific_props_layout.count():
            child = self.specific_props_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def on_form_changed(self):
        """Handle form changes"""
        self.save_btn.setEnabled(True)

    def select_entity(self, item):
        """Select an entity and load it into the editor"""
        entity_id = item.data(0, Qt.UserRole)
        if not entity_id or entity_id not in self.entity_data:
            return
            
        entity_data = self.entity_data[entity_id]
        self.current_entity = entity_data
        self.load_entity_into_form(entity_data)
        self.delete_entity_btn.setEnabled(True)
        self.duplicate_entity_btn.setEnabled(True)
        self.editor_title.setText(f"Editing: {entity_data.get('name', entity_id)}")

    def load_entity_into_form(self, entity_data):
        """Load entity data into the form with CNA integration"""
        self.entity_id_edit.setText(entity_data.get("id", ""))
        self.name_edit.setText(entity_data.get("name", ""))
        
        # Set type
        entity_type = entity_data.get("type", "npc")
        type_index = self.type_edit.findData(entity_type)
        if type_index >= 0:
            self.type_edit.setCurrentIndex(type_index)
            
        # Position
        self.grid_x_spin.setValue(entity_data.get("grid_x", 0))
        self.grid_y_spin.setValue(entity_data.get("grid_y", 0))
        
        # Color
        color = entity_data.get("color", [255, 255, 255])
        self.color_r_spin.setValue(color[0])
        self.color_g_spin.setValue(color[1])
        self.color_b_spin.setValue(color[2])
        
        # Speed
        self.speed_spin.setValue(entity_data.get("speed", 1.0))
        
        # Load CNA attributes if present
        cna_data = entity_data.get("cna_attributes")
        if cna_data:
            self.cna_file_edit.setText(cna_data.get("cna_file", ""))
            self.first_name_edit.setText(cna_data.get("first_name", ""))
            self.last_name_edit.setText(cna_data.get("last_name", ""))
            self.age_spin.setValue(cna_data.get("age_minutes", 0))
            
            # Set combo boxes
            gender_index = self.gender_combo.findData(cna_data.get("gender", 0))
            if gender_index >= 0:
                self.gender_combo.setCurrentIndex(gender_index)
                
            culture_index = self.culture_combo.findData(cna_data.get("culture", 0))
            if culture_index >= 0:
                self.culture_combo.setCurrentIndex(culture_index)
                
            nation_index = self.nation_combo.findData(cna_data.get("nation", 0))
            if nation_index >= 0:
                self.nation_combo.setCurrentIndex(nation_index)
            
            # Health attributes
            self.physical_health_spin.setValue(cna_data.get("physical_health", 3))
            self.mental_health_spin.setValue(cna_data.get("mental_health", 3))
            self.generational_health_spin.setValue(cna_data.get("generational_health", 3))
            
            # Extended attributes
            self.intelligence_spin.setValue(cna_data.get("intelligence_factor", 1.0))
            self.adaptability_spin.setValue(cna_data.get("adaptability", 1.0))
            self.immunity_spin.setValue(cna_data.get("immunity_strength", 1.0))
            
            self.update_color_preview()
        else:
            # Clear CNA form if no data
            self.clear_cna_form()
        
        # Type-specific properties (existing code)
        if entity_type == "npc":
            if hasattr(self, 'hunger_spin'):
                self.hunger_spin.setValue(entity_data.get("hunger", 5))
            if hasattr(self, 'thirst_spin'):
                self.thirst_spin.setValue(entity_data.get("thirst", 5))
            if hasattr(self, 'energy_spin'):
                self.energy_spin.setValue(entity_data.get("energy", 5))
            if hasattr(self, 'ai_type_combo'):
                ai_index = self.ai_type_combo.findData(entity_data.get("ai_type", "random_wander"))
                if ai_index >= 0:
                    self.ai_type_combo.setCurrentIndex(ai_index)
                    
        elif entity_type == "food_npc":
            if hasattr(self, 'food_type_combo'):
                food_index = self.food_type_combo.findData(entity_data.get("food_type", "fruit"))
                if food_index >= 0:
                    self.food_type_combo.setCurrentIndex(food_index)
            if hasattr(self, 'nutrition_spin'):
                self.nutrition_spin.setValue(entity_data.get("nutrition_value", 2))
        
        self.save_btn.setEnabled(False)



    def create_new_entity(self):
        """Create a new entity"""
        self.current_entity = None
        self.clear_form()
        self.editor_title.setText("Creating New Entity")
        self.save_btn.setEnabled(True)
        self.delete_entity_btn.setEnabled(False)
        self.duplicate_entity_btn.setEnabled(False)

    def clear_cna_form(self):
        """Clear CNA-related form fields"""
        self.cna_file_edit.clear()
        self.first_name_edit.clear()
        self.last_name_edit.clear()
        self.age_spin.setValue(0)
        self.gender_combo.setCurrentIndex(0)
        self.culture_combo.setCurrentIndex(0)
        self.nation_combo.setCurrentIndex(0)
        self.physical_health_spin.setValue(3)
        self.mental_health_spin.setValue(3)
        self.generational_health_spin.setValue(3)
        self.intelligence_spin.setValue(1.0)
        self.adaptability_spin.setValue(1.0)
        self.immunity_spin.setValue(1.0)
        self.color_preview.setStyleSheet("border: 1px solid #ddd; background: #ffffff;")

    def clear_form(self):
        """Clear the form for new entity creation with CNA support"""
        self.entity_id_edit.clear()
        self.name_edit.clear()
        self.type_edit.setCurrentIndex(0)
        self.grid_x_spin.setValue(0)
        self.grid_y_spin.setValue(0)
        self.color_r_spin.setValue(255)
        self.color_g_spin.setValue(255)
        self.color_b_spin.setValue(255)
        self.speed_spin.setValue(1.0)
        self.clear_cna_form()
        self.clear_specific_properties()

    def save_current_entity(self):
        """Save the current entity with CNA integration"""
        # Validate form
        errors = self.validate_form()
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return
        
        try:
            entity_id = self.entity_id_edit.text().strip()
            
            # Create CNA attributes if CNA data is present
            cna_data = None
            if self.first_name_edit.text() or self.last_name_edit.text():
                from cna_utils import CNAAttributes, Gender, Culture, Nation
                
                cna_data = {
                    "first_name": self.first_name_edit.text() or "Unknown",
                    "last_name": self.last_name_edit.text() or "Entity",
                    "age_minutes": self.age_spin.value(),
                    "gender": self.gender_combo.currentData(),
                    "culture": self.culture_combo.currentData(),
                    "nation": self.nation_combo.currentData(),
                    "physical_health": self.physical_health_spin.value(),
                    "mental_health": self.mental_health_spin.value(),
                    "generational_health": self.generational_health_spin.value(),
                    "intelligence_factor": self.intelligence_spin.value(),
                    "adaptability": self.adaptability_spin.value(),
                    "immunity_strength": self.immunity_spin.value(),
                    "cna_file": self.cna_file_edit.text()
                }
            
            entity_data = {
                "id": entity_id,
                "name": self.name_edit.text().strip(),
                "type": self.type_edit.currentData(),
                "grid_x": self.grid_x_spin.value(),
                "grid_y": self.grid_y_spin.value(),
                "color": [self.color_r_spin.value(), self.color_g_spin.value(), self.color_b_spin.value()],
                "speed": self.speed_spin.value(),
                "cna_attributes": cna_data
            }
            
            # Add type-specific properties (existing code)
            entity_type = self.type_edit.currentData()
            if entity_type == "npc":
                if hasattr(self, 'hunger_spin'):
                    entity_data["hunger"] = self.hunger_spin.value()
                if hasattr(self, 'thirst_spin'):
                    entity_data["thirst"] = self.thirst_spin.value()
                if hasattr(self, 'energy_spin'):
                    entity_data["energy"] = self.energy_spin.value()
                if hasattr(self, 'ai_type_combo'):
                    entity_data["ai_type"] = self.ai_type_combo.currentData()
                    
            elif entity_type == "food_npc":
                if hasattr(self, 'food_type_combo'):
                    entity_data["food_type"] = self.food_type_combo.currentData()
                if hasattr(self, 'nutrition_spin'):
                    entity_data["nutrition_value"] = self.nutrition_spin.value()
            
            elif entity_type == "player":
                entity_data["controllable"] = True
            
            # Save entity data
            self.entity_data[entity_id] = entity_data
            self.current_entity = entity_data
            
            self.refresh_entity_list()
            self.save_btn.setEnabled(False)
            self.delete_entity_btn.setEnabled(True)
            self.duplicate_entity_btn.setEnabled(True)
            self.editor_title.setText(f"Editing: {entity_data['name']}")
            
            print(f"Successfully saved entity: {entity_data['name']}")
            
        except Exception as e:
            print(f"Error saving entity: {e}")

    def validate_form(self):
        """Enhanced validation with CNA checks"""
        errors = []
        
        entity_id = self.entity_id_edit.text().strip()
        if not entity_id:
            errors.append("Entity ID is required")
        elif not entity_id.replace('_', '').replace('-', '').isalnum():
            errors.append("Entity ID can only contain letters, numbers, underscores, and hyphens")
        
        name = self.name_edit.text().strip()
        if not name:
            errors.append("Entity name is required")
        
        # Check for duplicate ID (only if creating new entity)
        if not self.current_entity and entity_id in self.entity_data:
            errors.append(f"Entity ID '{entity_id}' already exists")
        
        # CNA validation
        if self.first_name_edit.text() or self.last_name_edit.text():
            if not self.first_name_edit.text().strip():
                errors.append("First name is required when using CNA attributes")
            if not self.last_name_edit.text().strip():
                errors.append("Last name is required when using CNA attributes")
            
            # Age validation
            if not (0 <= self.age_spin.value() <= 60):
                errors.append("Age must be between 0-60 minutes")
            
            # Health validation
            if not (0 <= self.physical_health_spin.value() <= 5):
                errors.append("Physical health must be between 0-5")
            if not (0 <= self.mental_health_spin.value() <= 5):
                errors.append("Mental health must be between 0-5")
            if not (0 <= self.generational_health_spin.value() <= 5):
                errors.append("Generational health must be between 0-5")
        
        return errors

    def delete_current_entity(self):
        """Delete the currently selected entity"""
        if not self.current_entity:
            return
            
        try:
            entity_id = self.current_entity.get("id")
            if entity_id and entity_id in self.entity_data:
                del self.entity_data[entity_id]
                
                self.refresh_entity_list()
                self.clear_form()
                self.current_entity = None
                self.editor_title.setText("Entity Editor")
                self.delete_entity_btn.setEnabled(False)
                self.duplicate_entity_btn.setEnabled(False)
                
                print(f"Deleted entity: {entity_id}")
                
        except Exception as e:
            print(f"Error deleting entity: {e}")

    def duplicate_current_entity(self):
        """Enhanced duplicate with CNA support"""
        if not self.current_entity:
            return
            
        # Create new entity ID
        base_id = self.current_entity.get("id", "entity")
        new_id = f"{base_id}_copy"
        counter = 1
        
        while new_id in self.entity_data:
            new_id = f"{base_id}_copy_{counter}"
            counter += 1
            
        # Update form with new ID and name
        self.entity_id_edit.setText(new_id)
        self.name_edit.setText(f"{self.current_entity.get('name', 'Entity')} Copy")
        
        # Update CNA names if present
        if self.first_name_edit.text():
            current_first = self.first_name_edit.text()
            self.first_name_edit.setText(f"{current_first} Copy")
        
        self.current_entity = None
        self.editor_title.setText("Creating Duplicate Entity")
        self.save_btn.setEnabled(True)
        self.delete_entity_btn.setEnabled(False)
        self.duplicate_entity_btn.setEnabled(False)

    def add_cna_management_buttons(self, layout):
        """Add CNA-specific management buttons"""
        cna_group = QGroupBox("CNA Management")
        cna_layout = QVBoxLayout(cna_group)
        
        # Import from CNA directory
        self.import_cna_btn = ModernButton("Import from CNA Directory")
        self.import_cna_btn.clicked.connect(self.import_from_game_cna_directory)
        cna_layout.addWidget(self.import_cna_btn)
        
        # Export to game
        self.export_game_btn = ModernButton("Export to Game", primary=True)
        self.export_game_btn.clicked.connect(self.export_entities_to_game)
        cna_layout.addWidget(self.export_game_btn)
        
        # Batch CNA operations
        self.batch_cna_btn = ModernButton("Batch CNA Operations")
        self.batch_cna_btn.clicked.connect(self.show_batch_cna_dialog)
        cna_layout.addWidget(self.batch_cna_btn)
        
        layout.addWidget(cna_group)

    def show_batch_cna_dialog(self):
        """Show dialog for batch CNA operations"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QProgressBar
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Batch CNA Operations")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Instructions
            label = QLabel("Select entities to perform batch operations:")
            layout.addWidget(label)
            
            # Entity list
            entity_list = QListWidget()
            for entity_id, entity_data in self.entity_data.items():
                item_text = f"{entity_data.get('name', entity_id)} ({entity_id})"
                entity_list.addItem(item_text)
            entity_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            layout.addWidget(entity_list)
            
            # Progress bar
            progress = QProgressBar()
            progress.setVisible(False)
            layout.addWidget(progress)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            generate_cna_btn = QPushButton("Generate Missing CNA")
            generate_cna_btn.clicked.connect(lambda: self.batch_generate_cna(entity_list, progress))
            button_layout.addWidget(generate_cna_btn)
            
            update_colors_btn = QPushButton("Update Colors from CNA")
            update_colors_btn.clicked.connect(lambda: self.batch_update_colors(entity_list, progress))
            button_layout.addWidget(update_colors_btn)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            print(f"Error showing batch CNA dialog: {e}")

    def batch_generate_cna(self, entity_list, progress_bar):
        """Generate CNA attributes for selected entities that don't have them"""
        try:
            from cna_utils import CNAAttributes, Gender, Culture, Nation
            import random
            
            selected_items = entity_list.selectedItems()
            if not selected_items:
                print("No entities selected")
                return
            
            progress_bar.setVisible(True)
            progress_bar.setMaximum(len(selected_items))
            progress_bar.setValue(0)
            
            generated_count = 0
            
            for i, item in enumerate(selected_items):
                # Extract entity ID from item text
                item_text = item.text()
                entity_id = item_text.split('(')[-1].rstrip(')')
                
                if entity_id in self.entity_data:
                    entity_data = self.entity_data[entity_id]
                    
                    # Skip if already has CNA data
                    if entity_data.get("cna_attributes"):
                        continue
                    
                    # Generate random CNA attributes
                    first_names = ["Alex", "Jordan", "Casey", "Taylor", "Morgan", "Riley", "Avery", "Quinn"]
                    last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Miller", "Moore", "Taylor"]
                    
                    cna_data = {
                        "first_name": random.choice(first_names),
                        "last_name": random.choice(last_names),
                        "age_minutes": random.randint(18, 45),
                        "gender": random.choice([g.value for g in Gender]),
                        "culture": random.choice([c.value for c in Culture]),
                        "nation": random.choice([n.value for n in Nation]),
                        "physical_health": random.randint(2, 5),
                        "mental_health": random.randint(2, 5),
                        "generational_health": random.randint(2, 4),
                        "intelligence_factor": round(random.uniform(0.8, 1.5), 2),
                        "adaptability": round(random.uniform(0.8, 1.5), 2),
                        "immunity_strength": round(random.uniform(0.8, 1.5), 2),
                        "cna_file": f"{cna_data['first_name']}_{cna_data['last_name']}.cna"
                    }
                    
                    entity_data["cna_attributes"] = cna_data
                    
                    # Update entity color based on CNA
                    from cna_utils import calculate_entity_color, Culture
                    mock_cna = type('MockCNA', (), {
                        'culture': Culture(cna_data["culture"]),
                        'age_minutes': cna_data["age_minutes"]
                    })()
                    
                    color = calculate_entity_color(mock_cna)
                    entity_data["color"] = list(color)
                    
                    generated_count += 1
                
                progress_bar.setValue(i + 1)
            
            progress_bar.setVisible(False)
            
            if generated_count > 0:
                self.refresh_entity_list()
                print(f"Generated CNA attributes for {generated_count} entities")
            else:
                print("No entities needed CNA generation")
                
        except Exception as e:
            print(f"Error in batch CNA generation: {e}")

    def batch_update_colors(self, entity_list, progress_bar):
        """Update colors for selected entities based on their CNA attributes"""
        try:
            from cna_utils import calculate_entity_color, Culture
            
            selected_items = entity_list.selectedItems()
            if not selected_items:
                print("No entities selected")
                return
            
            progress_bar.setVisible(True)
            progress_bar.setMaximum(len(selected_items))
            progress_bar.setValue(0)
            
            updated_count = 0
            
            for i, item in enumerate(selected_items):
                # Extract entity ID from item text
                item_text = item.text()
                entity_id = item_text.split('(')[-1].rstrip(')')
                
                if entity_id in self.entity_data:
                    entity_data = self.entity_data[entity_id]
                    cna_data = entity_data.get("cna_attributes")
                    
                    if cna_data:
                        # Create mock CNA object for color calculation
                        mock_cna = type('MockCNA', (), {
                            'culture': Culture(cna_data.get("culture", 0)),
                            'age_minutes': cna_data.get("age_minutes", 0)
                        })()
                        
                        color = calculate_entity_color(mock_cna)
                        entity_data["color"] = list(color)
                        updated_count += 1
                
                progress_bar.setValue(i + 1)
            
            progress_bar.setVisible(False)
            
            if updated_count > 0:
                self.refresh_entity_list()
                print(f"Updated colors for {updated_count} entities")
            else:
                print("No entities had CNA data for color updates")
                
        except Exception as e:
            print(f"Error in batch color update: {e}")


    def export_entities(self):
        """Export entities to JSON file"""
        try:
            from pathlib import Path
            import json
            import time
            
            export_dir = Path.home() / "hoomans" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            filename = f"entities_export_{timestamp}.json"
            filepath = export_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.entity_data, f, indent=2)
            
            print(f"Entities exported to: {filepath}")
            
        except Exception as e:
            print(f"Error exporting entities: {e}")

    def import_entities(self):
        """Import entities from JSON file"""
        try:
            from pathlib import Path
            import json
            
            import_dir = Path.home() / "hoomans" / "exports"
            
            if not import_dir.exists():
                print("No exports directory found")
                return
                
            # Find first JSON file (simplified - in real implementation use file dialog)
            json_files = list(import_dir.glob("entities_export_*.json"))
            if not json_files:
                print("No entity export files found in exports directory")
                return
                
            filepath = json_files[0]
            
            with open(filepath, 'r') as f:
                imported_data = json.load(f)
            
            imported_count = 0
            for entity_id, entity_data in imported_data.items():
                if entity_id not in self.entity_data:
                    self.entity_data[entity_id] = entity_data
                    imported_count += 1
            
            if imported_count > 0:
                self.refresh_entity_list()
                print(f"Imported {imported_count} entities from: {filepath}")
            else:
                print("No new entities were imported")
                
        except Exception as e:
            print(f"Error importing entities: {e}")

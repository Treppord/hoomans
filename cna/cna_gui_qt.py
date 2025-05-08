"""
CNA GUI Application using PyQt5 for reading, writing, and generating CNA files
"""

import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, 
                            QSlider, QTextEdit, QPushButton, QFileDialog, QMessageBox, 
                            QTreeWidget, QTreeWidgetItem, QGroupBox, QFormLayout, QSplitter)
from PyQt5.QtCore import Qt, QByteArray

from cna_format import CNAAttributes, Gender, Culture, Nation
from cna_codec import CNACodec
from cna_generator import CNAGenerator

class CNAApplicationQt(QMainWindow):
    """Main application window for CNA file manipulation using PyQt5"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("CNA Editor - Computerized Neural Attributes")
        self.resize(900, 700)
        self.setMinimumSize(800, 600)
        
        # Current working entity
        self.current_entity = None
        self.current_file = None
        
        # Create menu
        self.create_menu()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create notebook for tabs
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_editor_tab()
        self.create_generator_tab()
        self.create_binary_viewer_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Initialize with a new entity
        self.new_entity()
    
    def create_menu(self):
        """Create the application menu"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = file_menu.addAction("New")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_entity)
        
        open_action = file_menu.addAction("Open...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        
        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        
        save_as_action = file_menu.addAction("Save As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        random_action = edit_menu.addAction("Generate Random Entity")
        random_action.triggered.connect(self.generate_random)
        
        child_action = edit_menu.addAction("Generate Child Entity")
        child_action.triggered.connect(self.show_parent_selection)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
    
    def create_editor_tab(self):
        """Create the editor tab for editing CNA attributes"""
        editor_widget = QWidget()
        self.tab_widget.addTab(editor_widget, "Entity Editor")
        
        # Main layout
        form_layout = QVBoxLayout(editor_widget)
        
        # Create form fields
        self.editor_widgets = {}
        
        # Basic information section
        basic_group = QGroupBox("Basic Information")
        form_layout.addWidget(basic_group)
        
        basic_form = QFormLayout(basic_group)
        
        # First name
        self.editor_widgets["first_name"] = QLineEdit()
        basic_form.addRow("First Name:", self.editor_widgets["first_name"])
        
        # Last name
        self.editor_widgets["last_name"] = QLineEdit()
        basic_form.addRow("Last Name:", self.editor_widgets["last_name"])
        
        # Age
        self.editor_widgets["age_minutes"] = QSpinBox()
        self.editor_widgets["age_minutes"].setRange(0, 60)
        basic_form.addRow("Age (minutes):", self.editor_widgets["age_minutes"])
        
        # Gender
        self.editor_widgets["gender"] = QComboBox()
        self.editor_widgets["gender"].addItems([g.name for g in Gender])
        basic_form.addRow("Gender:", self.editor_widgets["gender"])
        
        # Culture
        self.editor_widgets["culture"] = QComboBox()
        self.editor_widgets["culture"].addItems([c.name for c in Culture])
        basic_form.addRow("Culture:", self.editor_widgets["culture"])
        
        # Nation
        self.editor_widgets["nation"] = QComboBox()
        self.editor_widgets["nation"].addItems([n.name for n in Nation])
        basic_form.addRow("Nation:", self.editor_widgets["nation"])
        
        # Health section
        health_group = QGroupBox("Health Attributes")
        form_layout.addWidget(health_group)
        
        health_form = QFormLayout(health_group)
        
        # Physical health
        health_layout = QHBoxLayout()
        self.editor_widgets["physical_health"] = QSlider(Qt.Horizontal)
        self.editor_widgets["physical_health"].setRange(0, 5)
        self.editor_widgets["physical_health"].setTickPosition(QSlider.TicksBelow)
        self.editor_widgets["physical_health"].setTickInterval(1)
        health_layout.addWidget(self.editor_widgets["physical_health"])
        
        self.physical_health_label = QLabel("0")
        health_layout.addWidget(self.physical_health_label)
        self.editor_widgets["physical_health"].valueChanged.connect(
            lambda v: self.physical_health_label.setText(str(v)))
        
        health_form.addRow("Physical Health:", health_layout)
        
        # Generational health
        health_layout = QHBoxLayout()
        self.editor_widgets["generational_health"] = QSlider(Qt.Horizontal)
        self.editor_widgets["generational_health"].setRange(0, 5)
        self.editor_widgets["generational_health"].setTickPosition(QSlider.TicksBelow)
        self.editor_widgets["generational_health"].setTickInterval(1)
        health_layout.addWidget(self.editor_widgets["generational_health"])
        
        self.generational_health_label = QLabel("0")
        health_layout.addWidget(self.generational_health_label)
        self.editor_widgets["generational_health"].valueChanged.connect(
            lambda v: self.generational_health_label.setText(str(v)))
        
        health_form.addRow("Generational Health:", health_layout)
        
        # Mental health
        health_layout = QHBoxLayout()
        self.editor_widgets["mental_health"] = QSlider(Qt.Horizontal)
        self.editor_widgets["mental_health"].setRange(0, 5)
        self.editor_widgets["mental_health"].setTickPosition(QSlider.TicksBelow)
        self.editor_widgets["mental_health"].setTickInterval(1)
        health_layout.addWidget(self.editor_widgets["mental_health"])
        
        self.mental_health_label = QLabel("0")
        health_layout.addWidget(self.mental_health_label)
        self.editor_widgets["mental_health"].valueChanged.connect(
            lambda v: self.mental_health_label.setText(str(v)))
        
        health_form.addRow("Mental Health:", health_layout)
        
        # Extended attributes section
        extended_group = QGroupBox("Extended Attributes")
        form_layout.addWidget(extended_group)
        
        extended_form = QFormLayout(extended_group)
        
        # Intelligence factor
        extended_layout = QHBoxLayout()
        self.editor_widgets["intelligence_factor"] = QDoubleSpinBox()
        self.editor_widgets["intelligence_factor"].setRange(0.5, 1.5)
        self.editor_widgets["intelligence_factor"].setSingleStep(0.1)
        self.editor_widgets["intelligence_factor"].setDecimals(2)
        extended_layout.addWidget(self.editor_widgets["intelligence_factor"])
        
        extended_form.addRow("Intelligence Factor:", self.editor_widgets["intelligence_factor"])
        
        # Adaptability
        self.editor_widgets["adaptability"] = QDoubleSpinBox()
        self.editor_widgets["adaptability"].setRange(0.5, 1.5)
        self.editor_widgets["adaptability"].setSingleStep(0.1)
        self.editor_widgets["adaptability"].setDecimals(2)
        extended_form.addRow("Adaptability:", self.editor_widgets["adaptability"])
        
        # Immunity strength
        self.editor_widgets["immunity_strength"] = QDoubleSpinBox()
        self.editor_widgets["immunity_strength"].setRange(0.5, 1.5)
        self.editor_widgets["immunity_strength"].setSingleStep(0.1)
        self.editor_widgets["immunity_strength"].setDecimals(2)
        extended_form.addRow("Immunity Strength:", self.editor_widgets["immunity_strength"])
        
        # Genetic markers and personality traits
        advanced_layout = QHBoxLayout()
        form_layout.addLayout(advanced_layout)
        
        # Genetic markers
        markers_group = QGroupBox("Genetic Markers")
        advanced_layout.addWidget(markers_group)
        
        markers_layout = QVBoxLayout(markers_group)
        self.genetic_markers_text = QTextEdit()
        markers_layout.addWidget(self.genetic_markers_text)
        
        # Personality traits
        traits_group = QGroupBox("Personality Traits")
        advanced_layout.addWidget(traits_group)
        
        traits_layout = QVBoxLayout(traits_group)
        self.personality_traits_text = QTextEdit()
        traits_layout.addWidget(self.personality_traits_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        form_layout.addLayout(button_layout)
        
        button_layout.addStretch()
        
        generate_button = QPushButton("Generate Random")
        generate_button.clicked.connect(self.generate_random)
        button_layout.addWidget(generate_button)
        
        update_button = QPushButton("Update Entity")
        update_button.clicked.connect(self.update_entity_from_form)
        button_layout.addWidget(update_button)
    
    def create_generator_tab(self):
        """Create the generator tab for batch generation"""
        generator_widget = QWidget()
        self.tab_widget.addTab(generator_widget, "Generator")
        
        # Main layout
        generator_layout = QVBoxLayout(generator_widget)
        
        # Controls frame
        controls_layout = QHBoxLayout()
        generator_layout.addLayout(controls_layout)
        
        # Batch generation
        controls_layout.addWidget(QLabel("Generate Entities:"))
        
        self.batch_count = QSpinBox()
        self.batch_count.setRange(1, 100)
        self.batch_count.setValue(10)
        controls_layout.addWidget(self.batch_count)
        
        generate_button = QPushButton("Generate")
        generate_button.clicked.connect(self.generate_batch)
        controls_layout.addWidget(generate_button)
        
        save_all_button = QPushButton("Save All...")
        save_all_button.clicked.connect(self.save_batch)
        controls_layout.addWidget(save_all_button)
        
        controls_layout.addStretch()
        
        # Parent selection for child generation
        parent_group = QGroupBox("Generate Child from Parents")
        generator_layout.addWidget(parent_group)
        
        parent_layout = QFormLayout(parent_group)
        
        self.parent1_combo = QComboBox()
        parent_layout.addRow("Parent 1:", self.parent1_combo)
        
        self.parent2_combo = QComboBox()
        parent_layout.addRow("Parent 2:", self.parent2_combo)
        
        parent_button_layout = QHBoxLayout()
        parent_layout.addRow("", parent_button_layout)
        
        parent_button_layout.addStretch()
        
        generate_child_button = QPushButton("Generate Child")
        generate_child_button.clicked.connect(self.generate_child)
        parent_button_layout.addWidget(generate_child_button)
        
        # Results list
        results_group = QGroupBox("Generated Entities")
        generator_layout.addWidget(results_group)
        results_layout = QVBoxLayout(results_group)
        
        # Create treeview for entities
        self.entity_tree = QTreeWidget()
        self.entity_tree.setHeaderLabels(["Name", "Age", "Gender", "Culture", "Nation", "Physical", "Generational", "Mental"])
        results_layout.addWidget(self.entity_tree)
        
        # Double-click to load entity
        self.entity_tree.itemDoubleClicked.connect(self.load_selected_entity)
        
        # Store generated entities
        self.generated_entities = []
    
    def create_binary_viewer_tab(self):
        """Create the binary viewer tab for viewing raw CNA data"""
        binary_widget = QWidget()
        self.tab_widget.addTab(binary_widget, "Binary Viewer")
        
        # Main layout
        binary_layout = QVBoxLayout(binary_widget)
        
        # Create text widget for hex view
        self.hex_text = QTextEdit()
        self.hex_text.setFont(QApplication.font("Monospace"))
        self.hex_text.setReadOnly(True)
        binary_layout.addWidget(self.hex_text)
    
    def new_entity(self):
        """Create a new empty entity"""
        self.current_entity = CNAGenerator.generate_random()
        self.current_file = None
        self.update_form_from_entity()
        self.update_binary_view()
        self.statusBar().showMessage("New entity created")
    
    def open_file(self):
        """Open a CNA file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open CNA File",
            "",
            "CNA Files (*.cna);;All Files (*.*)"
        )
        if not filepath:
            return
        
        try:
            self.current_entity = CNACodec.load_from_file(filepath)
            self.current_file = filepath
            self.update_form_from_entity()
            self.update_binary_view()
            self.statusBar().showMessage(f"Opened: {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
    
    def save_file(self):
        """Save the current entity to a file"""
        if not self.current_entity:
            QMessageBox.warning(self, "Warning", "No entity to save")
            return
        
        if not self.current_file:
            return self.save_file_as()
        
        try:
            self.update_entity_from_form()
            CNACodec.save_to_file(self.current_entity, self.current_file)
            self.statusBar().showMessage(f"Saved: {os.path.basename(self.current_file)}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
            return False
    
    def save_file_as(self):
        """Save the current entity to a new file"""
        if not self.current_entity:
            QMessageBox.warning(self, "Warning", "No entity to save")
            return False
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save CNA File",
            "",
            "CNA Files (*.cna);;All Files (*.*)"
        )
        
        if not filepath:
            return False
        
        self.current_file = filepath
        return self.save_file()
    
    def update_form_from_entity(self):
        """Update the form fields from the current entity"""
        if not self.current_entity:
            return
        
        # Update basic fields
        self.editor_widgets["first_name"].setText(self.current_entity.first_name)
        self.editor_widgets["last_name"].setText(self.current_entity.last_name)
        self.editor_widgets["age_minutes"].setValue(self.current_entity.age_minutes)
        self.editor_widgets["gender"].setCurrentText(self.current_entity.gender.name)
        self.editor_widgets["culture"].setCurrentText(self.current_entity.culture.name)
        self.editor_widgets["nation"].setCurrentText(self.current_entity.nation.name)
        
        # Update health attributes
        self.editor_widgets["physical_health"].setValue(self.current_entity.physical_health)
        self.editor_widgets["generational_health"].setValue(self.current_entity.generational_health)
        self.editor_widgets["mental_health"].setValue(self.current_entity.mental_health)
        
        # Update extended attributes
        self.editor_widgets["intelligence_factor"].setValue(self.current_entity.intelligence_factor)
        self.editor_widgets["adaptability"].setValue(self.current_entity.adaptability)
        self.editor_widgets["immunity_strength"].setValue(self.current_entity.immunity_strength)
        
        # Update genetic markers
        self.genetic_markers_text.clear()
        for i, marker in enumerate(self.current_entity.genetic_markers):
            self.genetic_markers_text.append(f"{i+1}: {marker}")
        
        # Update personality traits
        self.personality_traits_text.clear()
        for i, trait in enumerate(self.current_entity.personality_traits):
            self.personality_traits_text.append(f"{i+1}: {trait:.4f}")
    
    def update_entity_from_form(self):
        """Update the current entity from form fields"""
        if not self.current_entity:
            return
        
        try:
            # Update basic fields
            self.current_entity.first_name = self.editor_widgets["first_name"].text()
            self.current_entity.last_name = self.editor_widgets["last_name"].text()
            self.current_entity.age_minutes = self.editor_widgets["age_minutes"].value()
            self.current_entity.gender = Gender[self.editor_widgets["gender"].currentText()]
            self.current_entity.culture = Culture[self.editor_widgets["culture"].currentText()]
            self.current_entity.nation = Nation[self.editor_widgets["nation"].currentText()]
            
            # Update health attributes
            self.current_entity.physical_health = self.editor_widgets["physical_health"].value()
            self.current_entity.generational_health = self.editor_widgets["generational_health"].value()
            self.current_entity.mental_health = self.editor_widgets["mental_health"].value()
            
            # Update extended attributes
            self.current_entity.intelligence_factor = self.editor_widgets["intelligence_factor"].value()
            self.current_entity.adaptability = self.editor_widgets["adaptability"].value()
            self.current_entity.immunity_strength = self.editor_widgets["immunity_strength"].value()
            
            # Update genetic markers
            markers_text = self.genetic_markers_text.toPlainText().strip()
            if markers_text:
                markers = []
                for line in markers_text.split('\n'):
                    if ':' in line:
                        _, value = line.split(':', 1)
                        markers.append(int(value.strip()))
                self.current_entity.genetic_markers = markers
            
            # Update personality traits
            traits_text = self.personality_traits_text.toPlainText().strip()
            if traits_text:
                traits = []
                for line in traits_text.split('\n'):
                    if ':' in line:
                        _, value = line.split(':', 1)
                        traits.append(float(value.strip()))
                self.current_entity.personality_traits = traits
            
            # Update binary view
            self.update_binary_view()
            
            self.statusBar().showMessage("Entity updated")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update entity: {str(e)}")
            return False
    
    def update_binary_view(self):
        """Update the binary view with the current entity's binary representation"""
        if not self.current_entity:
            return
        
        try:
            # Get binary data
            binary_data = CNACodec.encode(self.current_entity)
            
            # Format as hex view
            hex_view = self._format_hex_view(binary_data)
            
            # Update text widget
            self.hex_text.setPlainText(hex_view)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update binary view: {str(e)}")
    
    def _format_hex_view(self, data: bytes) -> str:
        """Format binary data as a hex view with offset, hex, and ASCII columns"""
        result = []
        
        # Add header
        result.append("Offset    Hex                                                 ASCII")
        result.append("-" * 80)
        
        # Process 16 bytes per line
        for i in range(0, len(data), 16):
            # Get current chunk
            chunk = data[i:i+16]
            
            # Format offset
            offset = f"{i:08x}"
            
            # Format hex values
            hex_values = " ".join(f"{b:02x}" for b in chunk)
            hex_values = f"{hex_values:<48}"  # Pad to fixed width
            
            # Format ASCII representation
            ascii_values = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            
            # Combine all parts
            result.append(f"{offset}  {hex_values}  {ascii_values}")
        
        return "\n".join(result)
    
    def generate_random(self):
        """Generate a random entity and load it into the editor"""
        self.current_entity = CNAGenerator.generate_random()
        self.current_file = None
        self.update_form_from_entity()
        self.update_binary_view()
        self.statusBar().showMessage("Generated random entity")
    
    def generate_batch(self):
        """Generate a batch of random entities"""
        count = self.batch_count.value()
        if count < 1:
            QMessageBox.warning(self, "Warning", "Batch count must be at least 1")
            return
        
        # Generate entities
        self.generated_entities = CNAGenerator.generate_batch(count)
        
        # Update the treeview
        self.update_entity_tree()
        
        # Update parent selection dropdowns
        self.update_parent_dropdowns()
        
        self.statusBar().showMessage(f"Generated {count} random entities")
    
    def update_entity_tree(self):
        """Update the entity treeview with generated entities"""
        # Clear existing items
        self.entity_tree.clear()
        
        # Add new items
        for i, entity in enumerate(self.generated_entities):
            # Create a display name for the entity
            display_name = f"{entity.first_name} {entity.last_name}"
            
            # Add to treeview
            item = QTreeWidgetItem([
                display_name,
                str(entity.age_minutes),
                entity.gender.name,
                entity.culture.name,
                entity.nation.name,
                str(entity.physical_health),
                str(entity.generational_health),
                str(entity.mental_health)
            ])
            
            # Store the index in the user data
            item.setData(0, Qt.UserRole, i)
            
            self.entity_tree.addTopLevelItem(item)
        
        # Resize columns to content
        for i in range(self.entity_tree.columnCount()):
            self.entity_tree.resizeColumnToContents(i)
    
    def load_selected_entity(self, item, column):
        """Load the selected entity from the treeview into the editor"""
        # Get the selected entity index
        index = item.data(0, Qt.UserRole)
        if 0 <= index < len(self.generated_entities):
            self.current_entity = self.generated_entities[index]
            self.current_file = None
            self.update_form_from_entity()
            self.update_binary_view()
            self.statusBar().showMessage(f"Loaded entity: {self.current_entity.first_name} {self.current_entity.last_name}")
    
    def update_parent_dropdowns(self):
        """Update the parent selection dropdowns with generated entities"""
        if not self.generated_entities:
            return
        
        # Clear existing items
        self.parent1_combo.clear()
        self.parent2_combo.clear()
        
        # Create display names for entities
        names = [f"{entity.first_name} {entity.last_name}" for entity in self.generated_entities]
        
        # Update comboboxes
        self.parent1_combo.addItems(names)
        self.parent2_combo.addItems(names)
        
        # Set default selections if possible
        if len(names) > 0:
            self.parent1_combo.setCurrentIndex(0)
        if len(names) > 1:
            self.parent2_combo.setCurrentIndex(1)
    
    def generate_child(self):
        """Generate a child entity from selected parents"""
        if not self.generated_entities:
            QMessageBox.warning(self, "Warning", "No parent entities available")
            return
        
        # Get parent indices
        parent1_index = self.parent1_combo.currentIndex()
        parent2_index = self.parent2_combo.currentIndex()
        
        if parent1_index == -1 or parent2_index == -1:
            QMessageBox.warning(self, "Warning", "Please select valid parents")
            return
        
        # Generate child
        parent1 = self.generated_entities[parent1_index]
        parent2 = self.generated_entities[parent2_index]
        
        child = CNAGenerator.generate_child(parent1, parent2)
        
        # Add to generated entities
        self.generated_entities.append(child)
        
        # Update the treeview
        self.update_entity_tree()
        
        # Update parent selection dropdowns
        self.update_parent_dropdowns()
        
        # Load the child into the editor
        self.current_entity = child
        self.current_file = None
        self.update_form_from_entity()
        self.update_binary_view()
        
        self.statusBar().showMessage(f"Generated child: {child.first_name} {child.last_name}")
    
    def save_batch(self):
        """Save all generated entities to files"""
        if not self.generated_entities:
            QMessageBox.warning(self, "Warning", "No entities to save")
            return
        
        # Ask for directory
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save Entities")
        if not directory:
            return
        
        # Save each entity
        count = 0
        for entity in self.generated_entities:
            try:
                filename = f"{entity.first_name}_{entity.last_name}.cna"
                filepath = os.path.join(directory, filename)
                CNACodec.save_to_file(entity, filepath)
                count += 1
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save {entity.first_name} {entity.last_name}: {str(e)}")
        
        self.statusBar().showMessage(f"Saved {count} entities to {directory}")
    
    def show_parent_selection(self):
        """Show the parent selection dialog"""
        # Switch to the generator tab
        self.tab_widget.setCurrentIndex(1)  # Index 1 is the generator tab
        
        # If no entities are generated, generate some
        if not self.generated_entities:
            self.generate_batch()
    
    def show_about(self):
        """Show the about dialog"""
        about_text = """
        CNA Editor - Computerized Neural Attributes
        
        A tool for creating, editing, and generating CNA files.
        
        CNA is a binary format designed to efficiently store entity attributes
        for AI virtual worlds, inspired by human DNA.
        
        Version 1.0
        """
        
        QMessageBox.information(self, "About CNA Editor", about_text)

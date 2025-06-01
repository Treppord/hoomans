import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                               QScrollArea, QFrame, QSplitter, QStackedWidget,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon, QPainter, QLinearGradient

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
        left_panel = self.create_panel("Project Hierarchy", "#f8f9fa")
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(400)
        
        # Center panel (main editor)
        center_panel = self.create_panel("Scene View", "#ffffff", is_center=True)
        
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

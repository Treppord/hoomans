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

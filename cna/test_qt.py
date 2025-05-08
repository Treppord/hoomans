#!/usr/bin/env python3
"""
Test script for PyQt5
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget

def main():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("PyQt5 Test")
    window.setGeometry(100, 100, 300, 200)
    
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    layout = QVBoxLayout(central_widget)
    
    label = QLabel("Hello World")
    layout.addWidget(label)
    
    button = QPushButton("Click Me")
    button.clicked.connect(lambda: print("Button clicked"))
    layout.addWidget(button)
    
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
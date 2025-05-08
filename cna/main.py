#!/usr/bin/env python3
"""
CNA Editor - Main entry point for PyQt5 version
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

# Add the current directory to the path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the application"""
    try:
        from cna.cna_gui_qt import CNAApplicationQt
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for a consistent look
        
        window = CNAApplicationQt()
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
        
        # Show error in GUI if possible
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "CNA Editor - Error", 
                                f"Error starting application: {str(e)}\n\n{traceback.format_exc()}")
        except:
            pass

if __name__ == "__main__":
    main()

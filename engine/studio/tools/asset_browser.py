"""
Asset Browser Tool - Browse and manage game assets
"""

import os
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)
import pygame
import pygame_gui
from typing import Dict, Any, List, Optional
from engine.studio.studio_tools import EmbeddedTool

class AssetBrowser(EmbeddedTool):
    """Embedded asset browser for the studio"""
    
    def __init__(self, studio_instance):
        super().__init__(studio_instance, "asset_browser")
        self.current_path = "assets"
        self.selected_file = None
        
        # UI elements
        self.main_panel = None
        self.path_label = None
        self.file_list = None
        self.preview_panel = None
        self.info_panel = None
        
        # Asset types
        self.asset_types = {
            '.png': 'Image',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.gif': 'Image',
            '.wav': 'Audio',
            '.mp3': 'Audio',
            '.ogg': 'Audio',
            '.json': 'Data',
            '.txt': 'Text',
            '.py': 'Script',
            '.cna': 'Character'
        }
    
    def _create_ui(self):
        """Create the asset browser UI"""
        if not self.studio.ui_manager:
            return
        
        # Main panel
        panel_width = 900
        panel_height = 600
        panel_x = (self.studio.screen_size[0] - panel_width) // 2
        panel_y = (self.studio.screen_size[1] - panel_height) // 2
        
        self.main_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.studio.ui_manager
        )
        self.ui_elements.append(self.main_panel)
        
        # Title
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, panel_width - 20, 30),
            text="Asset Browser",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(title_label)
        
        # Path display
        self.path_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 50, panel_width - 120, 25),
            text=f"Path: {self.current_path}",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.path_label)
        
        # Close button
        close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_width - 100, 50, 80, 25),
            text="Close",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(close_button)
        
        # File list
        self.file_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 85, 400, panel_height - 150),
            item_list=[],
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.file_list)
        
        # Preview panel
        self.preview_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(420, 85, 300, 300),
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.preview_panel)
        
        preview_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 280, 25),
            text="Preview",
            manager=self.studio.ui_manager,
            container=self.preview_panel
        )
        self.ui_elements.append(preview_label)
        
        # Info panel
        self.info_panel = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(420, 395, 300, 150),
            html_text="Select a file to view information",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(self.info_panel)
        
        # Navigation buttons
        up_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, panel_height - 50, 80, 30),
            text="Up",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(up_button)
        
        refresh_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, panel_height - 50, 80, 30),
            text="Refresh",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(refresh_button)
        
        # Asset management buttons
        import_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(730, 85, 80, 30),
            text="Import",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(import_button)
        
        delete_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(730, 125, 80, 30),
            text="Delete",
            manager=self.studio.ui_manager,
            container=self.main_panel
        )
        self.ui_elements.append(delete_button)
        
        # Load initial file list
        self._refresh_file_list()
    
    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, 'text'):
                if event.ui_element.text == "Close":
                    self.close()
                elif event.ui_element.text == "Up":
                    self._navigate_up()
                elif event.ui_element.text == "Refresh":
                    self._refresh_file_list()
                elif event.ui_element.text == "Import":
                    self._import_asset()
                elif event.ui_element.text == "Delete":
                    self._delete_asset()
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.file_list:
                self._select_file(event.text)
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION:
            if event.ui_element == self.file_list:
                self._open_file(event.text)
    
    def _refresh_file_list(self):
        """Refresh the file list"""
        try:
            if not os.path.exists(self.current_path):
                os.makedirs(self.current_path, exist_ok=True)
            
            files = []
            
            # Add parent directory option if not at root
            if self.current_path != "assets":
                files.append(".. (Parent Directory)")
            
            # Add directories first
            for item in sorted(os.listdir(self.current_path)):
                item_path = os.path.join(self.current_path, item)
                if os.path.isdir(item_path):
                    files.append(f"📁 {item}")
            
            # Add files
            for item in sorted(os.listdir(self.current_path)):
                item_path = os.path.join(self.current_path, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    asset_type = self.asset_types.get(ext, 'Unknown')
                    icon = self._get_file_icon(ext)
                    files.append(f"{icon} {item}")
            
            # Update file list
            self.file_list.set_item_list(files)
            
            # Update path label
            self.path_label.set_text(f"Path: {self.current_path}")
            
        except Exception as e:
            print(f"Error refreshing file list: {e}")
    
    def _get_file_icon(self, extension: str) -> str:
        """Get icon for file type"""
        icons = {
            '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️',
            '.wav': '🔊', '.mp3': '🔊', '.ogg': '🔊',
            '.json': '📄', '.txt': '📄',
            '.py': '🐍',
            '.cna': '👤'
        }
        return icons.get(extension, '📄')
    
    def _navigate_up(self):
        """Navigate to parent directory"""
        if self.current_path != "assets":
            self.current_path = os.path.dirname(self.current_path)
            self._refresh_file_list()
    
    def _select_file(self, filename: str):
        """Select a file and show its information"""
        self.selected_file = filename
        
        # Remove icon prefix for actual filename
        if filename.startswith("📁 "):
            actual_name = filename[2:]
            file_path = os.path.join(self.current_path, actual_name)
            self._show_directory_info(file_path, actual_name)
        elif filename == ".. (Parent Directory)":
            self._show_parent_info()
        else:
            # Remove icon
            actual_name = filename[2:] if len(filename) > 2 else filename
            file_path = os.path.join(self.current_path, actual_name)
            self._show_file_info(file_path, actual_name)
    
    def _open_file(self, filename: str):
        """Open/navigate to selected file or directory"""
        if filename == ".. (Parent Directory)":
            self._navigate_up()
            return
        
        # Remove icon prefix
        if filename.startswith("📁 "):
            actual_name = filename[2:]
            new_path = os.path.join(self.current_path, actual_name)
            if os.path.isdir(new_path):
                self.current_path = new_path
                self._refresh_file_list()
        else:
            # For files, show detailed info or open with system default
            actual_name = filename[2:] if len(filename) > 2 else filename
            file_path = os.path.join(self.current_path, actual_name)
            self._open_file_externally(file_path)
    
    def _show_file_info(self, file_path: str, filename: str):
        """Show information about a file"""
        try:
            stat = os.stat(file_path)
            size = stat.st_size
            
            # Format size
            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            ext = os.path.splitext(filename)[1].lower()
            asset_type = self.asset_types.get(ext, 'Unknown')
            
            info_html = f"""
            <b>File:</b> {filename}<br>
            <b>Type:</b> {asset_type}<br>
            <b>Size:</b> {size_str}<br>
            <b>Extension:</b> {ext}<br>
            <b>Path:</b> {file_path}<br>
            """
            
            # Add type-specific information
            if asset_type == 'Image':
                info_html += self._get_image_info(file_path)
            elif asset_type == 'Audio':
                info_html += self._get_audio_info(file_path)
            elif asset_type == 'Character':
                info_html += self._get_character_info(file_path)
            
            self.info_panel.html_text = info_html
            self.info_panel.rebuild()
            
        except Exception as e:
            self.info_panel.html_text = f"Error reading file info: {e}"
            self.info_panel.rebuild()
    
    def _show_directory_info(self, dir_path: str, dirname: str):
        """Show information about a directory"""
        try:
            items = os.listdir(dir_path)
            file_count = len([f for f in items if os.path.isfile(os.path.join(dir_path, f))])
            dir_count = len([f for f in items if os.path.isdir(os.path.join(dir_path, f))])
            
            info_html = f"""
            <b>Directory:</b> {dirname}<br>
            <b>Files:</b> {file_count}<br>
            <b>Subdirectories:</b> {dir_count}<br>
            <b>Total Items:</b> {len(items)}<br>
            <b>Path:</b> {dir_path}<br>
            """
            
            self.info_panel.html_text = info_html
            self.info_panel.rebuild()
            
        except Exception as e:
            self.info_panel.html_text = f"Error reading directory info: {e}"
            self.info_panel.rebuild()
    
    def _show_parent_info(self):
        """Show parent directory info"""
        parent_path = os.path.dirname(self.current_path)
        self.info_panel.html_text = f"<b>Parent Directory:</b><br>{parent_path}"
        self.info_panel.rebuild()
    
    def _get_image_info(self, file_path: str) -> str:
        """Get additional info for image files"""
        try:
            import pygame
            image = pygame.image.load(file_path)
            width, height = image.get_size()
            return f"<b>Dimensions:</b> {width}x{height}<br>"
        except:
            return "<b>Dimensions:</b> Unable to read<br>"
    
    def _get_audio_info(self, file_path: str) -> str:
        """Get additional info for audio files"""
        # This would require additional audio libraries
        return "<b>Audio Info:</b> Available with audio library<br>"
    
    def _get_character_info(self, file_path: str) -> str:
        """Get additional info for character files"""
        try:
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            name = data.get('name', 'Unknown')
            return f"<b>Character Name:</b> {name}<br>"
        except:
            return "<b>Character Info:</b> Unable to read<br>"
    
    def _open_file_externally(self, file_path: str):
        """Open file with system default application"""
        try:
            import subprocess
            import sys
            
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])
                
        except Exception as e:
            print(f"Error opening file externally: {e}")
    
    def _import_asset(self):
        """Import a new asset"""
        # This would open a file dialog to import assets
        print("Import asset functionality would be implemented here")
        # For now, just refresh the list
        self._refresh_file_list()
    
    def _delete_asset(self):
        """Delete the selected asset"""
        if not self.selected_file or self.selected_file == ".. (Parent Directory)":
            return
        
        # Remove icon prefix
        actual_name = self.selected_file[2:] if len(self.selected_file) > 2 else self.selected_file
        file_path = os.path.join(self.current_path, actual_name)
        
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            elif os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)
                print(f"Deleted directory: {file_path}")
            
            self._refresh_file_list()
            self.info_panel.html_text = "Select a file to view information"
            self.info_panel.rebuild()
            
        except Exception as e:
            self.info_panel.html_text = f"<font color='#ff0000'>Error deleting: {e}</font>"
            self.info_panel.rebuild()
    
    def update(self, time_delta):
        """Update the asset browser"""
        pass

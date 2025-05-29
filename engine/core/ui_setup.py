"""UI setup and initialization"""
from engine.ui.panels.stats_panel import StatsPanel
from engine.ui.elements.chat_input import ChatInputBox
from engine.config.config_loader import get_config_loader

class UISetup:
    """Handles UI element setup and positioning"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.config = get_config_loader()
    
    def setup_ui_elements(self):
        """Set up all UI elements with configured positions and sizes"""
        self._setup_stats_panel()
        self._setup_chat_input()
    
    def _setup_stats_panel(self):
        """Set up the stats panel"""
        ui_config = self.config.get_setting('game_settings', 'ui', default={})
        stats_config = ui_config.get('stats_panel', {})
        
        width = stats_config.get('width', 200)
        height = stats_config.get('height', 120)
        margin_right = stats_config.get('margin_right', 10)
        margin_top = stats_config.get('margin_top', 10)
        
        x = self.game_engine.display_manager.width - width - margin_right
        y = margin_top
        
        stats_panel = StatsPanel(x, y, width, height, self.game_engine.data)
        self.game_engine.ui.add_element(stats_panel)
    
    def _setup_chat_input(self):
        """Set up the chat input box"""
        ui_config = self.config.get_setting('game_settings', 'ui', default={})
        chat_config = ui_config.get('chat_input', {})
        
        width = chat_config.get('width', 400)
        height = chat_config.get('height', 40)
        margin_right = chat_config.get('margin_right', 10)
        margin_bottom = chat_config.get('margin_bottom', 10)
        
        x = self.game_engine.display_manager.width - width - margin_right
        y = self.game_engine.display_manager.height - height - margin_bottom
        
        print("DEBUG: Creating chat input box")
        self.game_engine.chat_input = ChatInputBox(
            x, y, width, height,
            callback=self.game_engine.chat_manager.handle_chat_message
        )
        
        print(f"DEBUG: Adding chat input to UI manager: {self.game_engine.chat_input}")
        self.game_engine.ui.add_element(self.game_engine.chat_input)
    
    def update_ui_positions(self, width, height):
        """Update UI element positions when screen size changes"""
        # Update stats panel position
        for element in self.game_engine.ui.elements:
            if isinstance(element, StatsPanel):
                ui_config = self.config.get_setting('game_settings', 'ui', default={})
                stats_config = ui_config.get('stats_panel', {})
                margin_right = stats_config.get('margin_right', 10)
                element.x = width - element.width - margin_right
                break
        
        # Update chat input position
        if hasattr(self.game_engine, 'chat_input') and self.game_engine.chat_input:
            ui_config = self.config.get_setting('game_settings', 'ui', default={})
            chat_config = ui_config.get('chat_input', {})
            margin_right = chat_config.get('margin_right', 10)
            margin_bottom = chat_config.get('margin_bottom', 10)
            
            self.game_engine.chat_input.x = width - self.game_engine.chat_input.width - margin_right
            self.game_engine.chat_input.y = height - self.game_engine.chat_input.height - margin_bottom
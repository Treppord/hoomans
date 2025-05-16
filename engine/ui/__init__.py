"""UI system for the game engine"""
from engine.ui.ui_manager import UIManager
from engine.ui.elements.base import UIElement
from engine.ui.elements.text_bubble import TextBubble
from engine.ui.elements.chat_input import ChatInputBox
from engine.ui.panels.stats_panel import StatsPanel
from engine.ui.panels.character_info_panel import CharacterInfoPanel
from engine.ui.constants.colors import *

# Export the main classes
__all__ = [
    'UIManager',
    'UIElement',
    'TextBubble',
    'ChatInputBox',
    'StatsPanel',
    'CharacterInfoPanel'
]
"""UI Manager for handling all UI elements"""
import time
from engine.ui.panels.stats_panel import StatsPanel
from engine.ui.elements.text_bubble import TextBubble
from engine.ui.elements.chat_input import ChatInputBox
from engine.ui.panels.character_info_panel import CharacterInfoPanel

class UIManager:
    """Manages all UI elements"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.elements = []
        self.text_bubbles = []
        self.entity_info = None
        self.entity_info_time = 0
        self.entity_info_duration = 3.0  # How long to show entity info
        
        # Create character info panel
        panel_width = 600
        panel_height = 500
        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2
        self.char_info_panel = CharacterInfoPanel(panel_x, panel_y, panel_width, panel_height)
        self.elements.append(self.char_info_panel)
    
    def update_screen_size(self, screen_width, screen_height):
        """Update UI elements when screen size changes"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Reposition UI elements based on new screen size
        for element in self.elements:
            if isinstance(element, StatsPanel):
                # Keep stats panel in top right corner
                element.x = self.screen_width - element.width - 10
                element.y = 10
            elif isinstance(element, ChatInputBox):
                # Keep chat input in bottom right corner
                element.x = self.screen_width - element.width - 10
                element.y = self.screen_height - element.height - 10
            elif isinstance(element, CharacterInfoPanel):
                # Center character info panel
                element.x = (self.screen_width - element.width) // 2
                element.y = (self.screen_height - element.height) // 2

    def show_entity_info(self, entity):
        """Show the character info panel for an entity"""
        self.char_info_panel.set_entity(entity)
    
    def add_element(self, element):
        """Add a UI element"""
        self.elements.append(element)
        return element
        
    def add_text_bubble(self, text, entity, duration=3.0):
        """Add a speech bubble above an entity"""
        # Check for existing bubbles with the same text for this entity
        for existing_bubble in self.text_bubbles:
            if (existing_bubble.entity == entity and 
                existing_bubble.text == text and 
                not existing_bubble.is_expired()):
                # Don't create duplicate bubbles
                print(f"DEBUG: Skipping duplicate text bubble for entity {id(entity)}")
                return existing_bubble
        
        bubble = TextBubble(text, entity, duration)
        
        # Calculate vertical offset for stacking bubbles
        # Find existing bubbles for this entity
        entity_bubbles = [b for b in self.text_bubbles if b.entity == entity and not b.is_expired()]
        
        # Stack with newest at the bottom
        total_offset = 0
        for existing_bubble in entity_bubbles:
            total_offset += existing_bubble.height + 10  # 10px gap between bubbles
        
        bubble.vertical_offset = total_offset
        
        self.text_bubbles.append(bubble)
        
        # Also add to chat log if we have one
        chat_input = next((e for e in self.elements if isinstance(e, ChatInputBox)), None)
        if chat_input:
            # Get entity name if available
            entity_name = "NPC"
            if hasattr(entity, 'cna_data') and entity.cna_data and hasattr(entity.cna_data, 'name'):
                entity_name = entity.cna_data.name
            elif hasattr(entity, 'controllable') and entity.controllable:
                entity_name = "You"
            
            # Check for duplicate messages (same entity, same text, within last 5 seconds)
            current_time = time.time()
            recent_messages = [msg for msg in chat_input.chat_history 
                              if msg.get('sender') == entity_name and 
                                 msg.get('text') == text and 
                                 current_time - msg.get('time', 0) < 5.0]
            
            # Only add if not a duplicate
            if not recent_messages:
                chat_input.add_message(text, sender=entity_name, is_player=(hasattr(entity, 'controllable') and entity.controllable))
            else:
                print(f"DEBUG: Skipping duplicate chat log entry for {entity_name}")
        
        return bubble


        
        
    def handle_event(self, event):
        """Handle UI events"""
        # First check if character info panel is visible and should handle the event
        if self.char_info_panel.visible and self.char_info_panel.handle_event(event):
            return True
            
        # Then check other UI elements
        for element in self.elements:
            if hasattr(element, 'handle_event') and element.handle_event(event):
                return True
                
        return False
        
    def render(self, screen):
        """Render all UI elements"""
        # Render regular UI elements
        for element in self.elements:
            if hasattr(element, 'render'):
                element.render(screen)
        
        # Render text bubbles
        for bubble in self.text_bubbles[:]:
            if bubble.is_expired():
                self.text_bubbles.remove(bubble)
            else:
                bubble.render(screen)
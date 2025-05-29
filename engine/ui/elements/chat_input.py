"""Chat input box UI element"""
import pygame
import time
import re
from engine.ui.elements.base import UIElement
from engine.ui.constants.colors import (
    CHAT_INPUT_BG, BORDER_COLOR, TEXT_COLOR, PLACEHOLDER_COLOR, 
    SELECTION_COLOR, CHAT_LOG_BG, PLAYER_TEXT_COLOR, NPC_TEXT_COLOR,
    SCROLL_INDICATOR_COLOR
)

class ChatInputBox(UIElement):
    """Input box for typing chat messages"""
    def __init__(self, x, y, width, height, callback=None):
        super().__init__(x, y, width, height)
        self.callback = callback  # Function to call when Enter is pressed
        self.text = ""
        self.active = False
        self.visible = False  # Start hidden
        self.background_color = CHAT_INPUT_BG  # Using color constant
        self.border_color = BORDER_COLOR  # Using color constant
        self.text_color = TEXT_COLOR  # Using color constant
        self.placeholder_text = "Press T to chat..."
        self.placeholder_color = PLACEHOLDER_COLOR  # Using color constant
        self.font = pygame.font.Font("assets/font/CandC_LAN.ttf", 24)
        self.padding = 12
        self.cursor_visible = True
        self.cursor_timer = 0
        self.max_chars = 100  # Maximum characters allowed
        
        # For text selection
        self.selection_start = None
        self.selection_end = None
        self.shift_pressed = False
        
        # For clipboard operations
        self.clipboard_text = ""
        
        # Chat history
        self.chat_history = []
        self.max_visible_history = 8  # Number of messages to show in the log
        self.history_padding = 8
        self.history_font = pygame.font.SysFont(None, 20)
        self.history_line_height = self.history_font.get_linesize()
        
        # Chat log dimensions
        self.log_width = width
        self.log_height = self.max_visible_history * (self.history_line_height + self.history_padding)
        
        # For preventing duplicate messages
        self.skip_next_add = False
        
        # For scrolling chat history
        self.scroll_offset = 0
        self.max_scroll_offset = 0
    
    def handle_scroll(self, scroll_amount):
        """Handle mouse wheel scrolling in chat history"""
        # Always return True when in chat mode to capture the scroll event
        
        # Calculate the total number of messages
        total_messages = len(self.chat_history)
        
        # Calculate the maximum scroll offset (total messages - visible messages)
        self.max_scroll_offset = max(0, total_messages - self.max_visible_history)
        
        # Update scroll offset based on scroll amount
        # In pygame, positive scroll_amount means scroll up (show older messages)
        self.scroll_offset += scroll_amount
        
        # Clamp the scroll offset to valid range
        if self.scroll_offset < 0:
            self.scroll_offset = 0
        if self.scroll_offset > self.max_scroll_offset:
            self.scroll_offset = self.max_scroll_offset
        
        return True
    
    def render(self, screen):
        # Always render chat log
        self._render_chat_log(screen)
        
        if not self.visible:
            return
            
        # Create a surface with alpha for transparency
        box_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(box_surface, self.background_color, 
                        (0, 0, self.width, self.height), 
                        border_radius=8)
        
        # Draw border
        pygame.draw.rect(box_surface, self.border_color, 
                        (0, 0, self.width, self.height), 
                        border_radius=8, width=2)
        
        # Render text or placeholder
        if self.text:
            display_text = self.text
            text_color = self.text_color
        else:
            display_text = self.placeholder_text
            text_color = self.placeholder_color
        
        # Add blinking cursor if active
        self.cursor_timer += 1
        if self.cursor_timer > 30:  # Toggle cursor every 30 frames
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            
        # Render text with potential truncation if too long
        text_width = self.font.size(display_text)[0]
        
        # If text is too wide, show only the end portion
        if text_width > self.width - (self.padding * 2):
            # Calculate how many characters to show
            visible_width = self.width - (self.padding * 2)
            char_width = text_width / len(display_text)
            visible_chars = int(visible_width / char_width)
            
            # Show the last visible_chars characters
            display_text = display_text[-visible_chars:]
            text_width = self.font.size(display_text)[0]
        
        # Draw selection highlight if there's a selection
        if self.selection_start is not None and self.selection_end is not None and self.selection_start != self.selection_end:
            start = min(self.selection_start, self.selection_end)
            end = max(self.selection_start, self.selection_end)
            
            # Calculate selection rectangle
            selection_text = display_text[start:end]
            selection_width = self.font.size(selection_text)[0]
            selection_x = self.padding + self.font.size(display_text[:start])[0]
            
            # Draw selection highlight
            pygame.draw.rect(box_surface, SELECTION_COLOR,  # Using color constant
                            (selection_x, self.height // 2 - 10, selection_width, 20))
        
        # Render the text
        text_surface = self.font.render(display_text, True, text_color)
        box_surface.blit(text_surface, (self.padding, self.height // 2 - text_surface.get_height() // 2))
        
        # Add cursor at current position if visible
        if self.text and self.cursor_visible:
            cursor_pos = self.selection_end if self.selection_end is not None else len(self.text)
            cursor_x = self.padding + self.font.size(display_text[:cursor_pos])[0]
            pygame.draw.line(box_surface, self.text_color,
                            (cursor_x, self.height // 2 - 8),
                            (cursor_x, self.height // 2 + 8), 2)
        
        # Draw the input box on the screen
        screen.blit(box_surface, (self.x, self.y))
    
    # In the _render_chat_log method, update the color references
    def _render_chat_log(self, screen):
        """Render chat log in the bottom left corner"""
        if not self.chat_history:
            return
        
        # Calculate chat log position (bottom left)
        log_x = 10  # 10px from left edge
        log_y = screen.get_height() - self.log_height - 10  # 10px from bottom edge
        
        # If chat input is active, position log directly above input box
        if self.active:
            log_y = self.y - self.log_height - 5  # 5px gap between log and input
        
        # Create a surface with alpha for transparency
        log_surface = pygame.Surface((self.log_width, self.log_height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(log_surface, CHAT_LOG_BG,  # Using color constant
                        (0, 0, self.log_width, self.log_height), 
                        border_radius=8)
        
        # Simple approach: select messages based on scroll offset
        if self.scroll_offset == 0:
            # Show the most recent messages
            visible_messages = self.chat_history[-self.max_visible_history:] if len(self.chat_history) > self.max_visible_history else self.chat_history
        else:
            # Show older messages based on scroll offset
            end_idx = max(0, len(self.chat_history) - self.scroll_offset)
            start_idx = max(0, end_idx - self.max_visible_history)
            visible_messages = self.chat_history[start_idx:end_idx]
        
        
        # Render each message
        y_offset = self.log_height - self.history_padding
        for message in reversed(visible_messages):
            # Get message text and sender
            text = message.get('text', '')
            sender = message.get('sender', 'NPC')
            is_player = message.get('is_player', False)
            
            # Choose color based on sender
            if is_player:
                sender_color = PLAYER_TEXT_COLOR  # Using color constant
                text_color = TEXT_COLOR  # Using color constant
            else:
                sender_color = NPC_TEXT_COLOR  # Using color constant
                text_color = TEXT_COLOR  # Using color constant
            
            # Format message with sender
            formatted_text = f"{sender}: {text}"
            
            # Wrap text to fit within log width
            wrapped_lines = self._wrap_chat_text(formatted_text, self.log_width - (self.history_padding * 2))
            
            # Render each line from bottom to top
            for line in reversed(wrapped_lines):
                # Calculate position for this line
                y_offset -= self.history_line_height
                
                # Skip if we've gone beyond the top of the log
                if y_offset < 0:
                    continue
                
                # Render the line
                if ":" in line and line.split(":", 1)[0] == sender:
                    # Split sender and message for different colors
                    sender_part, message_part = line.split(":", 1)
                    
                    # Render sender
                    sender_surface = self.history_font.render(sender_part + ":", True, sender_color)
                    log_surface.blit(sender_surface, (self.history_padding, y_offset))
                    
                    # Render message
                    message_surface = self.history_font.render(message_part, True, text_color)
                    log_surface.blit(message_surface, (self.history_padding + sender_surface.get_width(), y_offset))
                else:
                    # Render the whole line in message color (for wrapped lines)
                    text_surface = self.history_font.render(line, True, text_color)
                    log_surface.blit(text_surface, (self.history_padding, y_offset))
                
            # Add spacing between messages
            y_offset -= self.history_padding
        
        # Draw scroll indicators if needed
        if self.scroll_offset > 0:
            # Draw up arrow to indicate more messages above
            pygame.draw.polygon(log_surface, SCROLL_INDICATOR_COLOR,  # Using color constant
                              [(self.log_width - 20, 10), (self.log_width - 10, 20), (self.log_width - 30, 20)])
        
        if self.scroll_offset < self.max_scroll_offset:
            # Draw down arrow to indicate more messages below
            pygame.draw.polygon(log_surface, SCROLL_INDICATOR_COLOR,  # Using color constant
                              [(self.log_width - 20, self.log_height - 10), 
                               (self.log_width - 10, self.log_height - 20), 
                               (self.log_width - 30, self.log_height - 20)])
        
        # Draw the chat log on the screen
        screen.blit(log_surface, (log_x, log_y))
    
    def _wrap_chat_text(self, text, max_width):
        """Wrap text to fit within a given width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        # Special handling for the first word (which may contain the sender name)
        if words and ":" in words[0]:
            # Keep sender name on the first line
            current_line.append(words[0])
            current_width = self.history_font.size(words[0])[0]
            words = words[1:]
        
        for word in words:
            word_width = self.history_font.size(word)[0]
            
            # Check if adding this word would exceed the max width
            if current_line:
                # Account for space between words
                space_width = self.history_font.size(' ')[0]
                test_width = current_width + space_width + word_width
            else:
                test_width = current_width + word_width
            
            if test_width <= max_width:
                current_line.append(word)
                current_width = test_width
            else:
                # Start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def toggle(self):
        """Toggle the input box visibility and activity"""
        self.active = not self.active
        self.visible = self.active
        if not self.active:
            self.text = ""
            self.selection_start = None
            self.selection_end = None



        
    def toggle(self):
        """Toggle the input box visibility and activity"""
        self.active = not self.active
        self.visible = self.active
        if not self.active:
            self.text = ""
            self.selection_start = None
            self.selection_end = None
    
    def handle_event(self, event):
        if not self.active:
            return False
            
        if event.type == pygame.KEYDOWN:
            # Set shift_pressed flag when shift key is pressed
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.shift_pressed = True
                return True
                
            # Skip processing if it's just a modifier key by itself
            if event.key in (pygame.K_LMETA, pygame.K_RMETA, pygame.K_LCTRL, pygame.K_RCTRL, 
                            pygame.K_LALT, pygame.K_RALT):
                return True
            
            # Handle Enter key - send message
            if event.key == pygame.K_RETURN:
                if self.text.strip() and self.callback:
                    # Set flag to skip the next add_message call from UIManager
                    self.skip_next_add = True
                    
                    # Add to chat history
                    self.chat_history.append({
                        "text": self.text,
                        "time": time.time(),
                        "is_player": True,
                        "sender": "You"
                    })
                    
                    # Call the callback
                    self.callback(self.text)
                

                # Always toggle off even if message was empty
                self.toggle()
                
                # If message was empty, also reset chat mode in input handler
                if not self.text.strip():
                    from engine.core.simple_game_engine import SimpleGameEngine
                    if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'input_handler'):
                        SimpleGameEngine.instance.input_handler.set_chat_mode(False)
                
                return True
                
            # Handle Escape key - cancel chat
            elif event.key == pygame.K_ESCAPE:
                self.toggle()
                from engine.core.simple_game_engine import SimpleGameEngine
                if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'input_handler'):
                    SimpleGameEngine.instance.input_handler.set_chat_mode(False)
                return True
                
            # Handle Backspace key - delete character or selection
            elif event.key == pygame.K_BACKSPACE:
                if self.selection_start is not None and self.selection_end is not None:
                    # Delete selected text
                    start = min(self.selection_start, self.selection_end)
                    end = max(self.selection_start, self.selection_end)
                    self.text = self.text[:start] + self.text[end:]
                    self.selection_start = None
                    self.selection_end = None
                elif len(self.text) > 0:
                    # Delete last character
                    self.text = self.text[:-1]
                return True
                
            # Handle Delete key - delete character or selection
            elif event.key == pygame.K_DELETE:
                if self.selection_start is not None and self.selection_end is not None:
                    # Delete selected text
                    start = min(self.selection_start, self.selection_end)
                    end = max(self.selection_start, self.selection_end)
                    self.text = self.text[:start] + self.text[end:]
                    self.selection_start = None
                    self.selection_end = None
                elif len(self.text) > 0 and self.cursor_pos < len(self.text):
                    # Delete character at cursor
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                return True
                
            # Handle Cmd+C - copy selected text
            elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_META:
                if self.selection_start is not None and self.selection_end is not None:
                    start = min(self.selection_start, self.selection_end)
                    end = max(self.selection_start, self.selection_end)
                    self.clipboard_text = self.text[start:end]
                    
                    # Copy to system clipboard
                    try:
                        import pyperclip
                        pyperclip.copy(self.clipboard_text)
                        print(f"Copied to system clipboard: {self.clipboard_text}")
                    except (ImportError, Exception) as e:
                        print(f"Could not copy to system clipboard: {e}")
                        print(f"Copied to internal clipboard: {self.clipboard_text}")
                return True

                
            # Handle Cmd+V - paste text
            elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_META:
                # Try to get text from system clipboard
                clipboard_text = ""
                try:
                    import pyperclip
                    clipboard_text = pyperclip.paste()
                    print(f"Pasted from system clipboard: {clipboard_text}")
                except (ImportError, Exception) as e:
                    # Fall back to our internal clipboard
                    clipboard_text = self.clipboard_text
                    print(f"Could not paste from system clipboard: {e}")
                    print(f"Using internal clipboard: {clipboard_text}")
                
                if clipboard_text:
                    if self.selection_start is not None and self.selection_end is not None:
                        # Replace selected text with clipboard content
                        start = min(self.selection_start, self.selection_end)
                        end = max(self.selection_start, self.selection_end)
                        new_text = self.text[:start] + clipboard_text + self.text[end:]
                        if len(new_text) <= self.max_chars:
                            self.text = new_text
                            self.selection_start = None
                            self.selection_end = None
                    else:
                        # Insert clipboard content at current position
                        if len(self.text) + len(clipboard_text) <= self.max_chars:
                            self.text += clipboard_text
                return True

                
            # Handle Ctrl+X - cut selected text
            elif event.key == pygame.K_x and pygame.key.get_mods() & pygame.KMOD_META:
                if self.selection_start is not None and self.selection_end is not None:
                    start = min(self.selection_start, self.selection_end)
                    end = max(self.selection_start, self.selection_end)
                    self.clipboard_text = self.text[start:end]
                    self.text = self.text[:start] + self.text[end:]
                    self.selection_start = None
                    self.selection_end = None
                    print(f"Cut to clipboard: {self.clipboard_text}")
                return True
                
            # Handle Ctrl+A - select all text
            elif event.key == pygame.K_a and pygame.key.get_mods() & pygame.KMOD_META:
                self.selection_start = 0
                self.selection_end = len(self.text)
                return True
                
            # Handle arrow keys for cursor movement and selection
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END):
                # Get current cursor position (end of text if no selection)
                cursor_pos = self.selection_end if self.selection_end is not None else len(self.text)
                
                if event.key == pygame.K_LEFT and cursor_pos > 0:
                    cursor_pos -= 1
                elif event.key == pygame.K_RIGHT and cursor_pos < len(self.text):
                    cursor_pos += 1
                elif event.key == pygame.K_HOME:
                    cursor_pos = 0
                elif event.key == pygame.K_END:
                    cursor_pos = len(self.text)
                
                if self.shift_pressed:
                    # Update selection
                    if self.selection_start is None:
                        self.selection_start = len(self.text)
                    self.selection_end = cursor_pos
                else:
                    # Clear selection and just move cursor
                    self.selection_start = cursor_pos
                    self.selection_end = cursor_pos
                
                return True
                
            else:
                # Add character to text if it's a printable character and under max length
                if event.unicode.isprintable() and len(self.text) < self.max_chars:
                    if self.selection_start is not None and self.selection_end is not None:
                        # Replace selected text with new character
                        start = min(self.selection_start, self.selection_end)
                        end = max(self.selection_start, self.selection_end)
                        self.text = self.text[:start] + event.unicode + self.text[end:]
                        self.selection_start = None
                        self.selection_end = None
                    else:
                        # Just add the character
                        self.text += event.unicode
                    return True
        
        elif event.type == pygame.KEYUP:
            # Handle key modifiers being released
            if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                self.shift_pressed = False
                return True
        
        # Handle mouse events for text selection
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if click is within the input box
            if (self.x <= event.pos[0] <= self.x + self.width and
                self.y <= event.pos[1] <= self.y + self.height):
                # Calculate character position based on click position
                click_x = event.pos[0] - self.x - self.padding
                if click_x < 0:
                    click_x = 0
                
                # Approximate character position based on average character width
                avg_char_width = self.font.size("X")[0]
                char_pos = int(click_x / avg_char_width)
                char_pos = max(0, min(char_pos, len(self.text)))
                
                if self.shift_pressed:
                    # Start or extend selection
                    if self.selection_start is None:
                        self.selection_start = char_pos
                    self.selection_end = char_pos
                else:
                    # Start new selection
                    self.selection_start = char_pos
                    self.selection_end = char_pos
                
                return True
        
        return False
    
    def add_message(self, text, sender=None, is_player=False):
        """Add a message to chat history"""
        # Check if we should skip this add (for player messages to avoid duplication)
        if self.skip_next_add and is_player:
            self.skip_next_add = False
            return
            
        self.chat_history.append({
            "text": text,
            "time": time.time(),
            "is_player": is_player,
            "sender": sender or ("You" if is_player else "NPC")
        })
    

    
    def _wrap_chat_text(self, text, max_width):
        """Wrap text to fit within a given width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        # Special handling for the first word (which may contain the sender name)
        if words and ":" in words[0]:
            # Keep sender name on the first line
            current_line.append(words[0])
            current_width = self.history_font.size(words[0])[0]
            words = words[1:]
        
        for word in words:
            word_width = self.history_font.size(word)[0]
            
            # Check if adding this word would exceed the max width
            if current_line:
                # Account for space between words
                space_width = self.history_font.size(' ')[0]
                test_width = current_width + space_width + word_width
            else:
                test_width = current_width + word_width
            
            if test_width <= max_width:
                current_line.append(word)
                current_width = test_width
            else:
                # Start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
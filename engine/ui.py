# At the top of the file, add:
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
from cna_utils import Gender, Culture, Nation

import pygame
import time

class UIElement:
    """Base class for UI elements"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        
    def render(self, screen):
        """Render the UI element - override in subclasses"""
        pass
    
    def handle_event(self, event):
        """Handle input events - override in subclasses"""
        pass

class StatsPanel(UIElement):
    """Panel that displays player stats"""
    def __init__(self, x, y, width, height, data_manager):
        super().__init__(x, y, width, height)
        self.data_manager = data_manager
        self.background_color = (100, 100, 100, 150)  # Gray with transparency
        self.text_color = (255, 255, 255)  # White
        self.font = pygame.font.SysFont(None, 24)
        self.padding = 10
        
    def render(self, screen):
        if not self.visible:
            return
        
    # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    
    # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                    (0, 0, self.width, self.height))
    
    # Get stats from data manager
        health = self.data_manager.get_player_stat("health")
        hunger = self.data_manager.get_player_stat("hunger")
        thirst = self.data_manager.get_player_stat("thirst")
    
    # Render text for each stat
        y_offset = self.padding
    
        if health:
            health_text = f"Health: {health.value}/{health.max_value}"
            text_surface = self.font.render(health_text, True, self.text_color)
            panel_surface.blit(text_surface, (self.padding, y_offset))
            y_offset += 30
    
        if hunger:
            hunger_text = f"Hunger: {hunger.value}/{hunger.max_value}"
            text_surface = self.font.render(hunger_text, True, self.text_color)
            panel_surface.blit(text_surface, (self.padding, y_offset))
            y_offset += 30
    
        if thirst:
            thirst_text = f"Thirst: {thirst.value}/{thirst.max_value}"
            text_surface = self.font.render(thirst_text, True, self.text_color)
            panel_surface.blit(text_surface, (self.padding, y_offset))
    
    # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))


class TextBubble:
    """Speech bubble that appears above an entity"""
    def __init__(self, text, entity, duration=3.0):
        self.text = text
        self.entity = entity
        self.creation_time = time.time()
        self.duration = duration
        self.font = pygame.font.SysFont(None, 20)
        self.padding = 10
        self.background_color = (40, 40, 40, 220)  # Dark gray with transparency
        self.border_color = (80, 80, 80, 255)  # Lighter gray border
        self.text_color = (255, 255, 255)  # White text
        self.max_width = 200  # Maximum width for text wrapping
        
        # Wrap text if needed
        self.wrapped_text = self._wrap_text(self.text, self.max_width)
        
        # Calculate size based on wrapped text
        max_line_width = max([self.font.render(line, True, self.text_color).get_width() for line in self.wrapped_text])
        self.width = max_line_width + self.padding * 2
        self.height = len(self.wrapped_text) * self.font.get_linesize() + self.padding * 2
        
        # Animation properties
        self.appear_time = 0.2  # Time in seconds for bubble to appear
        self.disappear_time = 0.3  # Time in seconds for bubble to disappear
        
        # For stacking bubbles
        self.vertical_offset = 0  # Will be set by UIManager
        
    def _wrap_text(self, text, max_width):
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = self.font.render(word, True, self.text_color)
            word_width = word_surface.get_width()
            
            # Add space width except for first word in line
            if current_line:
                space_width = self.font.render(' ', True, self.text_color).get_width()
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
        
    def is_expired(self):
        """Check if the bubble should disappear"""
        return time.time() - self.creation_time > self.duration
        
    def render(self, screen):
        if self.is_expired():
            return
            
        # Get camera from game engine
        from engine.core import SimpleGameEngine
        camera = None
        if hasattr(SimpleGameEngine, 'instance'):
            camera = SimpleGameEngine.instance.camera
            
        if not camera:
            return
            
        # Calculate position above entity in world coordinates
        world_x = self.entity.x + self.entity.width // 2
        world_y = self.entity.y - self.height - 5 - self.vertical_offset  # Add vertical offset for stacking
        
        # Apply camera transformation
        screen_x, screen_y, _, _ = camera.apply(world_x, world_y, 0, 0)
        
        # Adjust position to center the bubble
        screen_x -= self.width // 2
        
        # Keep bubble on screen
        screen_x = max(5, min(screen_x, screen.get_width() - self.width - 5))
        screen_y = max(5, min(screen_y, screen.get_height() - self.height - 5))
        
        # Calculate alpha based on time
        elapsed = time.time() - self.creation_time
        alpha = 255
        
        # Fade in
        if elapsed < self.appear_time:
            alpha = int(255 * (elapsed / self.appear_time))
        # Fade out
        elif elapsed > self.duration - self.disappear_time:
            alpha = int(255 * (1 - (elapsed - (self.duration - self.disappear_time)) / self.disappear_time))
        
        # Create a surface with alpha for transparency
        bubble_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw rounded rectangle background
        pygame.draw.rect(bubble_surface, (self.background_color[0], self.background_color[1], 
                                         self.background_color[2], int(self.background_color[3] * alpha / 255)), 
                        (0, 0, self.width, self.height), 
                        border_radius=8)
        
        # Draw border
        pygame.draw.rect(bubble_surface, (self.border_color[0], self.border_color[1], 
                                         self.border_color[2], int(self.border_color[3] * alpha / 255)), 
                        (0, 0, self.width, self.height), 
                        border_radius=8, width=2)
        
        # Draw little triangle pointer at the bottom
        pointer_points = [
            (self.width // 2 - 8, self.height),
            (self.width // 2, self.height + 8),
            (self.width // 2 + 8, self.height)
        ]
        pygame.draw.polygon(bubble_surface, (self.background_color[0], self.background_color[1], 
                                           self.background_color[2], int(self.background_color[3] * alpha / 255)), 
                          pointer_points)
        
        # Draw text
        y_offset = self.padding
        for line in self.wrapped_text:
            text_surface = self.font.render(line, True, (self.text_color[0], self.text_color[1], 
                                                       self.text_color[2], int(alpha)))
            bubble_surface.blit(text_surface, 
                              (self.padding, y_offset))
            y_offset += self.font.get_linesize()
        
        # Draw the bubble on the screen
        screen.blit(bubble_surface, (screen_x, screen_y))


class ChatInputBox(UIElement):
    """Input box for typing chat messages"""
    def __init__(self, x, y, width, height, callback=None):
        super().__init__(x, y, width, height)
        self.callback = callback  # Function to call when Enter is pressed
        self.text = ""
        self.active = False
        self.visible = False  # Start hidden
        self.background_color = (40, 40, 40, 220)  # Dark gray with transparency
        self.border_color = (80, 80, 80, 255)  # Lighter gray border
        self.text_color = (255, 255, 255)  # White
        self.placeholder_text = "Press T to chat..."
        self.placeholder_color = (170, 170, 170)  # Light gray
        self.font = pygame.font.SysFont(None, 24)
        self.padding = 12
        self.cursor_visible = True
        self.cursor_timer = 0
        self.max_chars = 100  # Maximum characters allowed
        
        # Chat history
        self.chat_history = []
        self.max_visible_history = 8  # Number of messages to show in the log
        self.history_padding = 8
        self.history_font = pygame.font.SysFont(None, 20)
        self.history_line_height = self.history_font.get_linesize()
        
        # Chat log dimensions
        self.log_width = width
        self.log_height = self.max_visible_history * (self.history_line_height + self.history_padding)
        
    def toggle(self):
        """Toggle the input box visibility and activity"""
        self.active = not self.active
        self.visible = self.active
        if not self.active:
            self.text = ""
    
    def handle_event(self, event):
        if not self.active:
            return False
            
        if event.type == pygame.KEYDOWN:
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
                    
                self.toggle()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.key == pygame.K_ESCAPE:
                self.toggle()
                return True
            else:
                # Add character to text if it's a printable character and under max length
                if event.unicode.isprintable() and len(self.text) < self.max_chars:
                    self.text += event.unicode
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
        
        # Add blinking cursor if there's text
        if self.text:
            self.cursor_timer += 1
            if self.cursor_timer > 30:  # Toggle cursor every 30 frames
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
                
            if self.cursor_visible:
                display_text += "|"
        
        # Render text with potential truncation if too long
        text_surface = self.font.render(display_text, True, text_color)
        text_width = text_surface.get_width()
        
        # If text is too wide, show only the end portion
        if text_width > self.width - (self.padding * 2):
            # Calculate how many characters to show
            visible_width = self.width - (self.padding * 2)
            char_width = text_width / len(display_text)
            visible_chars = int(visible_width / char_width)
            
            # Show the last visible_chars characters
            display_text = display_text[-visible_chars:]
            text_surface = self.font.render(display_text, True, text_color)
        
        box_surface.blit(text_surface, (self.padding, self.height // 2 - text_surface.get_height() // 2))
        
        # Draw the input box on the screen
        screen.blit(box_surface, (self.x, self.y))
    
    def _render_chat_log(self, screen):
        """Render chat log in the bottom left corner"""
        if not self.chat_history:
            return
        
        # Calculate chat log position (bottom left)
        log_x = 10  # 10px from left edge
        log_y = screen.get_height() - self.height - self.log_height - 10  # Above input box
        
        # Create a surface for the chat log
        log_surface = pygame.Surface((self.log_width, self.log_height), pygame.SRCALPHA)
        
        # Draw semi-transparent background for the log
        pygame.draw.rect(log_surface, (0, 0, 0, 150), 
                        (0, 0, self.log_width, self.log_height),
                        border_radius=8)
        
        # Get the messages to display (last N messages)
        display_messages = self.chat_history[-self.max_visible_history:] if len(self.chat_history) > self.max_visible_history else self.chat_history
        
        # Render each message
        y_offset = self.log_height - (len(display_messages) * (self.history_line_height + self.history_padding))
        if y_offset < 0:
            y_offset = 0
            
        for msg in display_messages:
            # Determine text color based on sender
            if msg["is_player"]:
                text_color = (255, 255, 255)  # White for player
            else:
                text_color = (170, 170, 255)  # Light blue for NPCs
            
            # Format message with sender
            formatted_text = f"{msg['sender']}: {msg['text']}"
            
            # Wrap text if needed
            wrapped_lines = self._wrap_chat_text(formatted_text, self.log_width - 20)
            
            for line in wrapped_lines:
                text_surface = self.history_font.render(line, True, text_color)
                log_surface.blit(text_surface, (10, y_offset))
                y_offset += self.history_line_height
            
            # Add padding between messages
            y_offset += self.history_padding
        
        # Draw the chat log on the screen
        screen.blit(log_surface, (log_x, log_y))
        
        # If chat is active, draw the input box connected to the log
        if self.active:
            # Position the input box directly below the chat log
            self.x = log_x
            self.y = log_y + self.log_height + 5
    
    def _wrap_chat_text(self, text, max_width):
        """Wrap chat text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = self.history_font.render(word, True, (255, 255, 255))
            word_width = word_surface.get_width()
            
            # Add space width except for first word in line
            if current_line:
                space_width = self.history_font.render(' ', True, (255, 255, 255)).get_width()
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


        
    def show_entity_info(self, entity):
        """Show information about an entity"""
        self.entity_info = entity
        self.entity_info_time = time.time()
        
    def handle_event(self, event):
        """Handle UI events"""
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
        
        # Render entity info if active
        if self.entity_info and time.time() - self.entity_info_time < self.entity_info_duration:
            self._render_entity_info(screen)
    
    def _render_entity_info(self, screen):
        """Render information about the selected entity"""
        entity = self.entity_info
        
        # Create info text
        info_lines = []
        
        # Add entity type
        entity_type = entity.__class__.__name__
        info_lines.append(f"Type: {entity_type}")
        
        # Add position
        if hasattr(entity, 'grid_x') and hasattr(entity, 'grid_y'):
            info_lines.append(f"Position: ({entity.grid_x}, {entity.grid_y})")
        
        # Add CNA data if available
        if hasattr(entity, 'cna_data') and entity.cna_data:
            if hasattr(entity.cna_data, 'name'):
                info_lines.append(f"Name: {entity.cna_data.name}")
            if hasattr(entity.cna_data, 'culture'):
                info_lines.append(f"Culture: {entity.cna_data.culture}")
        
        # Add thirst if available
        if hasattr(entity, 'thirst'):
            info_lines.append(f"Thirst: {entity.thirst}/10")
        
        # Add exploration info for NPCs
        if entity_type == "NPC" and hasattr(entity, 'exploration_mode'):
            info_lines.append(f"Mode: {entity.exploration_mode}")
            if hasattr(entity, 'interesting_locations'):
                water_count = len(entity.interesting_locations.get('water', []))
                info_lines.append(f"Known water sources: {water_count}")
        
        # Calculate info box dimensions
        font = pygame.font.SysFont(None, 20)
        line_height = font.get_linesize()
        padding = 10
        
        # Calculate width based on longest line
        max_width = max([font.render(line, True, (255, 255, 255)).get_width() for line in info_lines])
        box_width = max_width + padding * 2
        box_height = len(info_lines) * line_height + padding * 2
        
        # Position in top left
        box_x = 10
        box_y = 10
        
        # Create info surface
        info_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        
        # Draw background
        pygame.draw.rect(info_surface, (0, 0, 0, 180), 
                        (0, 0, box_width, box_height), 
                        border_radius=8)
        
        # Draw border
        pygame.draw.rect(info_surface, (100, 100, 100, 255), 
                        (0, 0, box_width, box_height), 
                        border_radius=8, width=2)
        
        # Draw text
        y_offset = padding
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            info_surface.blit(text_surface, (padding, y_offset))
            y_offset += line_height
        
        # Draw on screen
        screen.blit(info_surface, (box_x, box_y))


class CharacterInfoPanel(UIElement):
    """Panel that displays character information from CNA data"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.entity = None
        self.background_color = (60, 60, 60, 230)  # Dark gray with transparency
        self.text_color = (255, 255, 255)  # White
        self.title_color = (200, 200, 100)  # Light yellow
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 20)
        self.padding = 15
        self.visible = False
        self.animation_timer = 0
        self.current_frame = 0
        self.animation_speed = 0.5  # Slower animation for the info panel
        
    def set_entity(self, entity):
        """Set the entity to display information for"""
        self.entity = entity
        self.visible = (entity is not None and entity.cna_data is not None)
        
    def update_animation(self, delta_time=1/60):
        """Update the animation frame"""
        self.animation_timer += delta_time
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
                self.current_frame = (self.current_frame + 1) % len(self.entity.animation_frames)
        
    def render(self, screen):
        if not self.visible or not self.entity or not self.entity.cna_data:
            return
            
        # Update animation
        self.update_animation()
            
        # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                        (0, 0, self.width, self.height),
                        border_radius=10)
        
        # Draw divider line down the middle
        divider_x = self.width // 2
        pygame.draw.line(panel_surface, (100, 100, 100, 200),
                        (divider_x, 10), (divider_x, self.height - 10), 2)
        
        # Get CNA data
        cna = self.entity.cna_data
        
        # Draw title
        title_text = f"{cna.first_name} {cna.last_name}"
        title_surface = self.title_font.render(title_text, True, self.title_color)
        panel_surface.blit(title_surface, (self.padding, self.padding))
        
        # Left side - Entity visualization
        # Check if entity has animation frames
        if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
            # Calculate position and size for the sprite display
            sprite_rect = pygame.Rect(
                self.padding, 
                self.padding + 40, 
                (self.width // 2) - (self.padding * 2), 
                100
            )
            
            # Get the current animation frame
            if 0 <= self.current_frame < len(self.entity.animation_frames):
                current_frame = self.entity.animation_frames[self.current_frame]
                
                # Apply color tint if the entity has this method
                if hasattr(self.entity, 'apply_color_tint'):
                    current_frame = self.entity.apply_color_tint(current_frame)
                
                # Scale the sprite to fit the display area while maintaining aspect ratio
                frame_width, frame_height = current_frame.get_size()
                scale_factor = min(sprite_rect.width / frame_width, sprite_rect.height / frame_height)
                scaled_width = int(frame_width * scale_factor * 1.5)  # Make it 3x larger
                scaled_height = int(frame_height * scale_factor * 1.5)
                
                # Center the sprite in the display area
                sprite_x = sprite_rect.x + (sprite_rect.width - scaled_width) // 2
                sprite_y = sprite_rect.y + (sprite_rect.height - scaled_height) // 2
                
                # Scale and draw the sprite
                scaled_frame = pygame.transform.scale(current_frame, (scaled_width, scaled_height))
                panel_surface.blit(scaled_frame, (sprite_x, sprite_y))
                
                
            else:
                # Fallback: draw a colored rectangle
                pygame.draw.rect(panel_surface, self.entity.color, sprite_rect)
        else:
            # Fallback: draw a colored rectangle
            entity_rect = pygame.Rect(
                self.padding, 
                self.padding + 40, 
                (self.width // 2) - (self.padding * 2), 
                100
            )
            pygame.draw.rect(panel_surface, self.entity.color, entity_rect)
        
        # Add entity stats below the visualization
        stats_y = self.padding + 40 + 100 + 20  # Below the entity rectangle with some spacing
        
        # Display entity stats if available
        if hasattr(self.entity, 'thirst') or hasattr(self.entity, 'hunger') or hasattr(self.entity, 'health'):
            stats_title = self.font.render("Entity Stats", True, self.title_color)
            panel_surface.blit(stats_title, (self.padding, stats_y))
            stats_y += 30
            
            # Display thirst if available
            if hasattr(self.entity, 'thirst'):
                thirst_text = f"Thirst: {self.entity.thirst}/10"
                thirst_surface = self.small_font.render(thirst_text, True, self.text_color)
                panel_surface.blit(thirst_surface, (self.padding, stats_y))
                stats_y += 25
            
            # Display hunger if available
            if hasattr(self.entity, 'hunger'):
                hunger_text = f"Hunger: {self.entity.hunger}/10"
                hunger_surface = self.small_font.render(hunger_text, True, self.text_color)
                panel_surface.blit(hunger_surface, (self.padding, stats_y))
                stats_y += 25
            
            # Display health if available
            if hasattr(self.entity, 'health'):
                health_text = f"Health: {self.entity.health}/20"
                health_surface = self.small_font.render(health_text, True, self.text_color)
                panel_surface.blit(health_surface, (self.padding, stats_y))
                stats_y += 25
        
        # Right side - CNA attributes
        right_x = (self.width // 2) + self.padding
        y_offset = self.padding
        
        # Basic info section
        y_offset += 10
        info_text = self.font.render("Basic Information", True, self.title_color)
        panel_surface.blit(info_text, (right_x, y_offset))
        y_offset += 30
        
        # Gender, Culture, Nation
        attributes = [
            f"Gender: {cna.gender.name}",
            f"Culture: {cna.culture.name}",
            f"Nation: {cna.nation.name}",
            f"Age: {cna.age_minutes} minutes"
        ]
        
        for attr in attributes:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Health section
        y_offset += 10
        health_text = self.font.render("Health Attributes", True, self.title_color)
        panel_surface.blit(health_text, (right_x, y_offset))
        y_offset += 30
        
        health_attrs = [
            f"Physical: {cna.physical_health}/5",
            f"Generational: {cna.generational_health}/5",
            f"Mental: {cna.mental_health}/5"
        ]
        
        for attr in health_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Extended attributes section
        y_offset += 10
        ext_text = self.font.render("Extended Attributes", True, self.title_color)
        panel_surface.blit(ext_text, (right_x, y_offset))
        y_offset += 30
        
        ext_attrs = [
            f"Intelligence: {cna.intelligence_factor:.2f}",
            f"Adaptability: {cna.adaptability:.2f}",
            f"Immunity: {cna.immunity_strength:.2f}"
        ]
        
        for attr in ext_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))
        
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False
            return True
        return False

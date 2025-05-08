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


class ChatInputBox(UIElement):
    """Input box for typing chat messages"""
    def __init__(self, x, y, width, height, callback=None):
        super().__init__(x, y, width, height)
        self.callback = callback  # Function to call when Enter is pressed
        self.text = ""
        self.active = False
        self.visible = False  # Start hidden
        self.background_color = (80, 80, 80, 200)  # Dark gray with transparency
        self.text_color = (255, 255, 255)  # White
        self.font = pygame.font.SysFont(None, 24)
        self.padding = 10
        self.cursor_visible = True
        self.cursor_timer = 0
        
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
                # Add character to text if it's a printable character
                if event.unicode.isprintable():
                    self.text += event.unicode
                    return True
        
        return False
        
    def render(self, screen):
        if not self.visible:
            return
            
        # Create a surface with alpha for transparency
        box_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(box_surface, self.background_color, 
                        (0, 0, self.width, self.height), 
                        border_radius=10)
        
        # Render text
        display_text = self.text
        
        # Add blinking cursor
        self.cursor_timer += 1
        if self.cursor_timer > 30:  # Toggle cursor every 30 frames
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            
        if self.cursor_visible:
            display_text += "|"
            
        text_surface = self.font.render(display_text, True, self.text_color)
        box_surface.blit(text_surface, (self.padding, self.height // 2 - text_surface.get_height() // 2))
        
        # Draw the input box on the screen
        screen.blit(box_surface, (self.x, self.y))

class TextBubble:
    """Speech bubble that appears above an entity"""
    def __init__(self, text, entity, duration=3.0):
        self.text = text
        self.entity = entity
        self.creation_time = time.time()
        self.duration = duration
        self.font = pygame.font.SysFont(None, 20)
        self.padding = 10
        self.background_color = (220, 220, 220, 200)  # Light gray with transparency
        self.text_color = (0, 0, 0)  # Black
        
        # Calculate size based on text
        text_surface = self.font.render(self.text, True, self.text_color)
        self.width = text_surface.get_width() + self.padding * 2
        self.height = text_surface.get_height() + self.padding * 2
        
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
        world_y = self.entity.y - self.height - 5  # 5px gap between entity and bubble
        
        # Apply camera transformation
        screen_x, screen_y, _, _ = camera.apply(world_x, world_y, 0, 0)
        
        # Adjust position to center the bubble
        screen_x -= self.width // 2
        
        # Keep bubble on screen
        screen_x = max(5, min(screen_x, screen.get_width() - self.width - 5))
        screen_y = max(5, min(screen_y, screen.get_height() - self.height - 5))
        
        # Create a surface with alpha for transparency
        bubble_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw rounded rectangle background
        pygame.draw.rect(bubble_surface, self.background_color, 
                        (0, 0, self.width, self.height), 
                        border_radius=10)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        bubble_surface.blit(text_surface, 
                          (self.padding, self.padding))
        
        # Draw the bubble on the screen
        screen.blit(bubble_surface, (screen_x, screen_y))

class UIManager:
    """Manages all UI elements"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.elements = []
        self.text_bubbles = []
        
        # Create character info panel for full-screen display
        self.character_info_panel = self.add_element(
            CharacterInfoPanel(0, 0, screen_width, screen_height)
        )
        
    def add_element(self, element):
        """Add a UI element"""
        self.elements.append(element)
        return element
        
    def add_text_bubble(self, text, entity, duration=3.0):
        """Add a text bubble above an entity"""
        bubble = TextBubble(text, entity, duration)
        self.text_bubbles.append(bubble)
        return bubble
    
    def show_entity_info(self, entity):
        """Show the character info panel for an entity"""
        self.character_info_panel.set_entity(entity)
        
    def handle_event(self, event):
        """Handle input events for all UI elements"""
        for element in self.elements:
            if hasattr(element, 'handle_event'):
                if element.handle_event(event):
                    return True  # Event was handled
        return False
        
    def render(self, screen):
        """Render all UI elements"""
        # Remove expired text bubbles
        self.text_bubbles = [b for b in self.text_bubbles if not b.is_expired()]
        
        # Render UI elements
        for element in self.elements:
            element.render(screen)
            
        # Render text bubbles
        for bubble in self.text_bubbles:
            bubble.render(screen)


class CharacterInfoPanel(UIElement):
    """Panel that displays character information from CNA data"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.entity = None
        self.background_color = (20, 20, 30, 230)  # Dark blue-gray with transparency
        self.text_color = (255, 255, 255)  # White
        self.title_color = (220, 220, 100)  # Light yellow
        self.section_color = (180, 180, 220)  # Light blue-gray
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 32)
        self.section_font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 20)
        self.padding = 20
        self.visible = False
        
    def set_entity(self, entity):
        """Set the entity to display information for"""
        self.entity = entity
        self.visible = (entity is not None and entity.cna_data is not None)
        
    def render(self, screen):
        if not self.visible or not self.entity or not self.entity.cna_data:
            return
            
        # Make the panel full screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.x = 0
        self.y = 0
            
        # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                        (0, 0, self.width, self.height))
        
        # Get CNA data
        cna = self.entity.cna_data
        
        # Draw title at the top
        title_text = f"{cna.first_name} {cna.last_name}"
        title_surface = self.title_font.render(title_text, True, self.title_color)
        title_x = (self.width - title_surface.get_width()) // 2  # Center the title
        panel_surface.blit(title_surface, (title_x, self.padding))
        
        # Calculate column widths and positions
        col_width = (self.width - (self.padding * 4)) // 3
        col1_x = self.padding
        col2_x = col1_x + col_width + self.padding
        col3_x = col2_x + col_width + self.padding
        
        # Start y position below title
        y_pos = self.padding + title_surface.get_height() + 20
        
        # Draw entity visualization in the first column
        self._draw_entity_visualization(panel_surface, col1_x, y_pos, col_width)
        
        # Draw basic info in the second column
        self._draw_basic_info(panel_surface, col2_x, y_pos, col_width, cna)
        
        # Draw extended attributes in the third column
        self._draw_extended_attributes(panel_surface, col3_x, y_pos, col_width, cna)
        
        # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))
        
        # Draw close button
        close_text = "Press ESC to close"
        close_surface = self.small_font.render(close_text, True, self.text_color)
        screen.blit(close_surface, (
            self.width - close_surface.get_width() - self.padding,
            self.height - close_surface.get_height() - self.padding
        ))
        
    def _draw_entity_visualization(self, surface, x, y, width):
        """Draw entity visualization and stats"""
        # Section title
        section_title = "Entity Visualization"
        title_surface = self.section_font.render(section_title, True, self.section_color)
        surface.blit(title_surface, (x, y))
        y += title_surface.get_height() + 10
        
        # Entity visualization - a larger rectangle with the entity's color
        vis_height = 200
        vis_rect = pygame.Rect(x, y, width, vis_height)
        pygame.draw.rect(surface, self.entity.color, vis_rect)
        pygame.draw.rect(surface, (255, 255, 255), vis_rect, 2)  # White border
        y += vis_height + 20
        
        # Entity stats section
        stats_title = "Entity Stats"
        stats_surface = self.section_font.render(stats_title, True, self.section_color)
        surface.blit(stats_surface, (x, y))
        y += stats_surface.get_height() + 10
        
        # Display entity stats if available
        stats = [
            ("Physical Health", f"{self.entity.cna_data.physical_health}/5"),
            ("Mental Health", f"{self.entity.cna_data.mental_health}/5"),
            ("Generational Health", f"{self.entity.cna_data.generational_health}/5")
        ]
        
        for label, value in stats:
            # Draw label
            label_surface = self.font.render(label, True, self.text_color)
            surface.blit(label_surface, (x, y))
            
            # Draw value
            value_surface = self.font.render(value, True, self.title_color)
            value_x = x + width - value_surface.get_width()
            surface.blit(value_surface, (value_x, y))
            
            y += label_surface.get_height() + 10
            
        # If entity has brain with needs, display them
        if hasattr(self.entity, 'brain') and hasattr(self.entity.brain, 'needs'):
            y += 20
            needs_title = "Current Needs"
            needs_surface = self.section_font.render(needs_title, True, self.section_color)
            surface.blit(needs_surface, (x, y))
            y += needs_surface.get_height() + 10
            
            for need, value in self.entity.brain.needs.items():
                # Draw need name
                need_surface = self.font.render(need.name, True, self.text_color)
                surface.blit(need_surface, (x, y))
                
                # Draw need value
                value_text = f"{value:.2f}"
                value_surface = self.font.render(value_text, True, self.title_color)
                value_x = x + width - value_surface.get_width()
                surface.blit(value_surface, (value_x, y))
                
                y += need_surface.get_height() + 10
    
    def _draw_basic_info(self, surface, x, y, width, cna):
        """Draw basic information about the entity"""
        # Section title
        section_title = "Basic Information"
        title_surface = self.section_font.render(section_title, True, self.section_color)
        surface.blit(title_surface, (x, y))
        y += title_surface.get_height() + 10
        
        # Basic info items
        info_items = [
            ("Gender", cna.gender.name),
            ("Culture", cna.culture.name),
            ("Nation", cna.nation.name),
            ("Age", f"{cna.age_minutes} minutes")
        ]
        
        for label, value in info_items:
            # Draw label
            label_surface = self.font.render(label, True, self.text_color)
            surface.blit(label_surface, (x, y))
            
            # Draw value
            value_surface = self.font.render(value, True, self.title_color)
            value_x = x + width - value_surface.get_width()
            surface.blit(value_surface, (value_x, y))
            
            y += label_surface.get_height() + 10
        
        # Add genetic markers section if available
        if hasattr(cna, 'genetic_markers') and cna.genetic_markers:
            y += 20
            markers_title = "Genetic Markers"
            markers_surface = self.section_font.render(markers_title, True, self.section_color)
            surface.blit(markers_surface, (x, y))
            y += markers_surface.get_height() + 10
            
            # Display first 5 genetic markers
            for i, marker in enumerate(cna.genetic_markers[:5]):
                marker_text = f"Marker {i+1}: {marker}"
                marker_surface = self.font.render(marker_text, True, self.text_color)
                surface.blit(marker_surface, (x, y))
                y += marker_surface.get_height() + 5
            
            if len(cna.genetic_markers) > 5:
                more_text = f"... and {len(cna.genetic_markers) - 5} more"
                more_surface = self.small_font.render(more_text, True, self.text_color)
                surface.blit(more_surface, (x, y))
                y += more_surface.get_height() + 10
        
        # Add memories section if available
        if hasattr(self.entity, 'brain') and hasattr(self.entity.brain, 'memories'):
            y += 20
            memories_title = "Recent Memories"
            memories_surface = self.section_font.render(memories_title, True, self.section_color)
            surface.blit(memories_surface, (x, y))
            y += memories_surface.get_height() + 10
            
            # Display most recent memories
            for i, memory in enumerate(reversed(self.entity.brain.memories[:5])):
                # Wrap text to fit column width
                memory_text = memory['content']
                wrapped_text = self._wrap_text(memory_text, self.small_font, width - 10)
                
                for line in wrapped_text:
                    line_surface = self.small_font.render(line, True, self.text_color)
                    surface.blit(line_surface, (x, y))
                    y += line_surface.get_height() + 2
                
                y += 8  # Extra space between memories
    
    def _draw_extended_attributes(self, surface, x, y, width, cna):
        """Draw extended attributes"""
        # Section title
        section_title = "Extended Attributes"
        title_surface = self.section_font.render(section_title, True, self.section_color)
        surface.blit(title_surface, (x, y))
        y += title_surface.get_height() + 10
        
        # Extended attributes
        ext_attrs = [
            ("Intelligence Factor", f"{cna.intelligence_factor:.2f}"),
            ("Adaptability", f"{cna.adaptability:.2f}"),
            ("Immunity Strength", f"{cna.immunity_strength:.2f}")
        ]
        
        for label, value in ext_attrs:
            # Draw label
            label_surface = self.font.render(label, True, self.text_color)
            surface.blit(label_surface, (x, y))
            
            # Draw value
            value_surface = self.font.render(value, True, self.title_color)
            value_x = x + width - value_surface.get_width()
            surface.blit(value_surface, (value_x, y))
            
            y += label_surface.get_height() + 10
        
        # Add personality traits section if available
        if hasattr(cna, 'personality_traits') and cna.personality_traits:
            y += 20
            traits_title = "Personality Traits"
            traits_surface = self.section_font.render(traits_title, True, self.section_color)
            surface.blit(traits_surface, (x, y))
            y += traits_surface.get_height() + 10
            
            # Define trait names (these are just examples, adjust as needed)
            trait_names = [
                "Openness",
                "Conscientiousness",
                "Extraversion",
                "Agreeableness",
                "Neuroticism"
            ]
            
            # Display personality traits
            for i, trait_value in enumerate(cna.personality_traits):
                trait_name = trait_names[i] if i < len(trait_names) else f"Trait {i+1}"
                
                # Draw trait name
                trait_surface = self.font.render(trait_name, True, self.text_color)
                surface.blit(trait_surface, (x, y))
                
                # Draw trait value
                value_text = f"{trait_value:.2f}"
                value_surface = self.font.render(value_text, True, self.title_color)
                value_x = x + width - value_surface.get_width()
                surface.blit(value_surface, (value_x, y))
                
                # Draw visual bar
                bar_y = y + trait_surface.get_height() + 5
                bar_height = 10
                bar_bg_rect = pygame.Rect(x, bar_y, width, bar_height)
                bar_fill_rect = pygame.Rect(x, bar_y, int(width * trait_value), bar_height)
                
                # Draw background and fill
                pygame.draw.rect(surface, (80, 80, 80), bar_bg_rect)
                pygame.draw.rect(surface, self.title_color, bar_fill_rect)
                
                y += trait_surface.get_height() + bar_height + 15
    
    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within a given width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Try adding the word to the current line
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                # Word fits, add it to the current line
                current_line.append(word)
            else:
                # Word doesn't fit, start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # If the word is too long for a line, split it
                    lines.append(word)
        
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines
        
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False
            return True
        return False


class EventLog(UIElement):
    """Displays recent events in the game world"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.messages = []
        self.max_messages = 5
        self.font = pygame.font.SysFont(None, 18)
        self.background_color = (0, 0, 0, 150)  # Black with transparency
        self.text_color = (200, 200, 200)  # Light gray
        self.message_lifetime = 5.0  # Messages disappear after 5 seconds
        
    def add_message(self, text):
        """Add a new message to the log"""
        self.messages.append({
            'text': text,
            'time': time.time()
        })
        
        # Limit the number of messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def render(self, screen):
        """Render the event log"""
        if not self.visible:
            return
            
        # Remove expired messages
        current_time = time.time()
        self.messages = [m for m in self.messages if current_time - m['time'] < self.message_lifetime]
        
        if not self.messages:
            return
            
        # Calculate height based on number of messages
        total_height = len(self.messages) * 25
        
        # Create a surface with alpha for transparency
        log_surface = pygame.Surface((self.width, total_height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(log_surface, self.background_color, 
                        (0, 0, self.width, total_height),
                        border_radius=5)
        
        # Render messages
        for i, message in enumerate(self.messages):
            # Calculate fade based on age
            age = current_time - message['time']
            alpha = max(0, min(255, int(255 * (1 - age / self.message_lifetime))))
            
            text_color = (*self.text_color, alpha)
            text_surface = self.font.render(message['text'], True, text_color)
            
            log_surface.blit(text_surface, (10, i * 25 + 5))
        
        # Draw the log on the screen
        screen.blit(log_surface, (self.x, self.y))

class EntityInfoPanel(UIElement):
    """Panel that displays information about a selected entity"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.entity = None
        self.background_color = (50, 50, 50, 200)  # Dark gray with transparency
        self.text_color = (255, 255, 255)  # White
        self.title_color = (200, 200, 100)  # Gold
        self.font = pygame.font.SysFont(None, 20)
        self.title_font = pygame.font.SysFont(None, 24)
        self.padding = 10
        self.visible = False
        
    def set_entity(self, entity):
        """Set the entity to display information about"""
        self.entity = entity
        self.visible = entity is not None
    
    def render(self, screen):
        """Render the entity info panel"""
        if not self.visible or not self.entity:
            return
            
        # Get entity info
        if hasattr(self.entity, 'get_info'):
            info_lines = self.entity.get_info()
        else:
            info_lines = [
                f"Type: {self.entity.__class__.__name__}",
                f"Position: ({self.entity.grid_x}, {self.entity.grid_y})"
            ]
        
        # Calculate panel height based on content
        line_height = 22
        content_height = len(info_lines) * line_height + self.padding * 2
        panel_height = min(self.height, content_height)
        
        # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, panel_height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                        (0, 0, self.width, panel_height),
                        border_radius=10)
        
        # Render info lines
        y_offset = self.padding
        
        for i, line in enumerate(info_lines):
            # Use title color for the first line
            color = self.title_color if i == 0 else self.text_color
            font = self.title_font if i == 0 else self.font
            
            text_surface = font.render(line, True, color)
            panel_surface.blit(text_surface, (self.padding, y_offset))
            y_offset += line_height
        
        # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))

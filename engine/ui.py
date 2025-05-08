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
            
        # Calculate position above entity
        x = self.entity.x + self.entity.width // 2 - self.width // 2
        y = self.entity.y - self.height - 5  # 5px gap between entity and bubble
        
        # Keep bubble on screen
        x = max(5, min(x, screen.get_width() - self.width - 5))
        y = max(5, min(y, screen.get_height() - self.height - 5))
        
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
        screen.blit(bubble_surface, (x, y))

class UIManager:
    """Manages all UI elements"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.elements = []
        self.text_bubbles = []
        
    def add_element(self, element):
        """Add a UI element"""
        self.elements.append(element)
        return element
        
    def add_text_bubble(self, text, entity, duration=3.0):
        """Add a text bubble above an entity"""
        bubble = TextBubble(text, entity, duration)
        self.text_bubbles.append(bubble)
        return bubble
        
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

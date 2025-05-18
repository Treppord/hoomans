"""Base panel class for UI elements"""
import pygame

class Panel:
    """Base class for UI panels"""
    
    def __init__(self, x, y, width, height, background_color=(40, 40, 40, 220)):
        """Initialize a panel"""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background_color = background_color
        self.border_color = (100, 100, 100)
        self.title = ""
        self.title_color = (255, 255, 255)
        self.visible = True
        self.draggable = False
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
    
    def set_title(self, title):
        """Set the panel title"""
        self.title = title
    
    def set_draggable(self, draggable):
        """Set whether the panel can be dragged"""
        self.draggable = draggable
    
    def contains_point(self, x, y):
        """Check if a point is within the panel"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def handle_event(self, event):
        """Handle events for the panel"""
        if not self.visible:
            return False
            
        # Handle dragging
        if self.draggable:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.contains_point(event.pos[0], event.pos[1]):
                    # Check if clicking in the title bar area (top 20px)
                    if event.pos[1] <= self.y + 20:
                        self.dragging = True
                        self.drag_offset_x = event.pos[0] - self.x
                        self.drag_offset_y = event.pos[1] - self.y
                        return True
                        
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.dragging = False
                    return True
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.x = event.pos[0] - self.drag_offset_x
                    self.y = event.pos[1] - self.drag_offset_y
                    return True
        
        return False
    
    def render(self, screen):
        """Render the panel"""
        if not self.visible:
            return
            
        # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                        (0, 0, self.width, self.height),
                        border_radius=5)
        
        # Draw border
        pygame.draw.rect(panel_surface, self.border_color, 
                        (0, 0, self.width, self.height), 
                        width=2, border_radius=5)
        
        # Draw title if present
        if self.title:
            font = pygame.font.Font(None, 24)
            title_surface = font.render(self.title, True, self.title_color)
            panel_surface.blit(title_surface, (10, 5))
            
            # Draw title separator line
            pygame.draw.line(panel_surface, self.border_color, 
                            (5, 25), (self.width - 5, 25), 1)
        
        # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))

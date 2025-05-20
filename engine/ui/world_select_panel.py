"""World Selection Panel for choosing a world to load"""
import pygame
import os
import json
from engine.ui.elements.base import UIElement
from engine.ui.elements.button import Button
from engine.ui.constants.colors import DARK_PANEL_BG, TEXT_COLOR, TITLE_COLOR, BORDER_COLOR

class WorldSelectPanel(UIElement):
    """Panel for selecting a world to load from cache files"""
    
    def __init__(self, screen_width, screen_height, on_select_callback=None, on_back_callback=None):
        """Initialize the world selection panel
        
        Args:
            screen_width: Width of the screen
            screen_height: Height of the screen
            on_select_callback: Function to call when a world is selected (receives seed as parameter)
            on_back_callback: Function to call when back button is clicked
        """
        # Create a full-screen panel
        super().__init__(0, 0, screen_width, screen_height, background_color=(20, 20, 30, 255))
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.on_select_callback = on_select_callback
        self.on_back_callback = on_back_callback
        
        # UI elements
        self.title_font = None
        self.normal_font = None
        self.small_font = None
        self.buttons = []
        self.world_buttons = []
        
        # Scrolling
        self.scroll_y = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        
        # World data
        self.worlds = []
        
        # Initialize
        self._initialize_fonts()
        self._create_buttons()
        self._load_world_list()
    
    def _initialize_fonts(self):
        """Initialize fonts for the panel"""
        try:
            self.title_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 48)
            self.normal_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 24)
            self.small_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 18)
        except:
            # Fallback to default fonts
            self.title_font = pygame.font.SysFont(None, 48)
            self.normal_font = pygame.font.SysFont(None, 24)
            self.small_font = pygame.font.SysFont(None, 18)
    
    def _create_buttons(self):
        """Create navigation buttons"""
        # Back button
        back_button = Button(
            x=20,
            y=20,
            width=100,
            height=40,
            text="Back",
            callback=self.on_back_callback
        )
        self.buttons.append(back_button)
    
    def _load_world_list(self):
        """Load the list of available world cache files"""
        self.worlds = []
        self.world_buttons = []
        
        # Check if cache directory exists
        cache_dir = "cache"
        if not os.path.exists(cache_dir):
            return
        
        # Find all world_*.json files
        for filename in os.listdir(cache_dir):
            if filename.startswith("world_") and filename.endswith(".json"):
                try:
                    # Extract seed from filename
                    seed = int(filename.replace("world_", "").replace(".json", ""))
                    
                    # Load world data to get more info
                    world_path = os.path.join(cache_dir, filename)
                    world_info = self._load_world_info(world_path)
                    
                    # Add to worlds list
                    self.worlds.append({
                        "seed": seed,
                        "filename": filename,
                        "path": world_path,
                        "info": world_info,
                        "last_updated": world_info.get("last_updated", 0)
                    })
                except (ValueError, IOError) as e:
                    print(f"Error loading world file {filename}: {e}")
        
        # Sort worlds by last updated time (newest first)
        self.worlds.sort(key=lambda w: w.get("last_updated", 0), reverse=True)
        
        # Create buttons for each world
        self._create_world_buttons()
    
    def _load_world_info(self, path):
        """Load basic info from a world cache file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"Error reading world file {path}: {e}")
            return {}
    
    # Add delete_world method
    def _delete_world(self, seed):
        """Delete a world cache file"""
        # Find the world data
        world_to_delete = None
        for world in self.worlds:
            if world["seed"] == seed:
                world_to_delete = world
                break
        
        if not world_to_delete:
            print(f"Error: World with seed {seed} not found")
            return
        
        # Confirm deletion
        # In a real implementation, you'd show a confirmation dialog
        # For now, we'll just print a message and delete the file
        print(f"Deleting world with seed {seed}")
        
        try:
            # Delete the file
            import os
            os.remove(world_to_delete["path"])
            print(f"Deleted world file: {world_to_delete['path']}")
            
            # Refresh the world list
            self._load_world_list()
        except Exception as e:
            print(f"Error deleting world file: {e}")
    
    def _create_world_buttons(self):
        """Create buttons for each world in the list"""
        self.world_buttons = []
        
        # Calculate layout
        button_width = 200
        button_height = 160  # Increased height to accommodate buttons below
        padding = 20
        buttons_per_row = max(1, (self.screen_width - 100) // (button_width + padding))
        
        # Create a button for each world
        for i, world in enumerate(self.worlds):
            row = i // buttons_per_row
            col = i % buttons_per_row
            
            x = 50 + col * (button_width + padding)
            y = 100 + row * (button_height + padding)
            
            # Create a custom button for this world
            world_button = WorldButton(
                x=x,
                y=y,
                width=button_width,
                height=button_height,
                world_data=world,
                callback=self._select_world,
                delete_callback=self._delete_world
            )
            self.world_buttons.append(world_button)
        
        # Calculate max scroll based on content height
        if self.worlds:
            rows = (len(self.worlds) + buttons_per_row - 1) // buttons_per_row
            content_height = 100 + rows * (button_height + padding)
            self.max_scroll = max(0, content_height - (self.screen_height - 100))
        else:
            self.max_scroll = 0

    def _select_world(self, seed):
        """Handle world selection"""
        print(f"Selected world with seed: {seed}")
        if self.on_select_callback:
            self.on_select_callback(seed)
    
    def update_screen_size(self, screen_width, screen_height):
        """Update panel when screen size changes"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = screen_width
        self.height = screen_height
        
        # Recreate buttons with new positions
        self._create_buttons()
        self._create_world_buttons()
    
    def handle_event(self, event):
        """Handle panel events"""
        # Handle mouse wheel for scrolling
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * self.scroll_speed
            # Clamp scroll value
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            return True
        
        # Pass events to buttons
        for button in self.buttons:
            if button.handle_event(event):
                return True
                
        # Adjust world button positions for scrolling
        for button in self.world_buttons:
            # Only handle events for buttons that are visible
            adjusted_y = button.y - self.scroll_y
            if 0 <= adjusted_y <= self.screen_height:
                # Create a copy of the event with adjusted position for scrolling
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    # Get original mouse position
                    mouse_x, mouse_y = event.pos
                    
                    # Check if mouse is over this button (considering scroll)
                    if button.x <= mouse_x <= button.x + button.width and adjusted_y <= mouse_y <= adjusted_y + button.height:
                        # For MOUSEBUTTONDOWN, we need to preserve the button attribute
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            # Create adjusted event with position relative to the button's original position
                            adjusted_event = pygame.event.Event(
                                event.type, 
                                pos=(mouse_x, mouse_y + self.scroll_y),
                                button=event.button
                            )
                        else:
                            # For other event types
                            adjusted_event = pygame.event.Event(
                                event.type, 
                                pos=(mouse_x, mouse_y + self.scroll_y)
                            )
                        
                        # Pass the adjusted event to the button
                        if button.handle_event(adjusted_event):
                            print(f"Button event handled for world {button.world_data['seed']}")
                            return True
        
        return False


    
    def render(self, screen):
        """Render the world selection panel"""
        # Draw background
        screen.fill((20, 20, 30))
        
        # Draw title
        title_text = "Select World"
        title_surface = self.title_font.render(title_text, True, TITLE_COLOR)
        title_rect = title_surface.get_rect(midtop=(self.screen_width // 2, 30))
        screen.blit(title_surface, title_rect)
        
        # Draw navigation buttons
        for button in self.buttons:
            button.render(screen)
        
        # Create a clipping rect for the scrollable area
        scroll_rect = pygame.Rect(0, 80, self.screen_width, self.screen_height - 100)
        
        # Save the original clip area
        original_clip = screen.get_clip()
        
        # Set the clipping area
        screen.set_clip(scroll_rect)
        
        # Draw world buttons with scrolling
        if self.world_buttons:
            for button in self.world_buttons:
                # Adjust button position for scrolling
                adjusted_y = button.y - self.scroll_y
                
                # Only render buttons that are visible
                if adjusted_y + button.height >= 80 and adjusted_y <= self.screen_height:
                    button.render_at(screen, button.x, adjusted_y)
        else:
            # No worlds found
            no_worlds_text = "No worlds found. Start a new game to create one."
            no_worlds_surface = self.normal_font.render(no_worlds_text, True, TEXT_COLOR)
            no_worlds_rect = no_worlds_surface.get_rect(center=(self.screen_width // 2, 200))
            screen.blit(no_worlds_surface, no_worlds_rect)
        
        # Restore the original clip area
        screen.set_clip(original_clip)
        
        # Draw scroll indicators if needed
        if self.max_scroll > 0:
            if self.scroll_y > 0:
                # Draw up arrow
                pygame.draw.polygon(screen, (200, 200, 200), [
                    (self.screen_width - 30, 90),
                    (self.screen_width - 20, 80),
                    (self.screen_width - 10, 90)
                ])
            
            if self.scroll_y < self.max_scroll:
                # Draw down arrow
                pygame.draw.polygon(screen, (200, 200, 200), [
                    (self.screen_width - 30, self.screen_height - 20),
                    (self.screen_width - 20, self.screen_height - 10),
                    (self.screen_width - 10, self.screen_height - 20)
                ])


class WorldButton:
    """Custom button for displaying world information"""
    
    def __init__(self, x, y, width, height, world_data, callback=None, delete_callback=None):
        """Initialize the world button
        
        Args:
            x, y: Position
            width, height: Size
            world_data: Dictionary with world information
            callback: Function to call when Start button is clicked
            delete_callback: Function to call when Delete button is clicked
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.world_data = world_data
        self.callback = callback
        self.delete_callback = delete_callback
        self.text = f"World {world_data['seed']}"
        self.hover = False
        
        # Adjust height to accommodate buttons below the frame
        self.frame_height = height - 40  # Reserve space for buttons
        
        # Action buttons - now positioned below the frame
        self.start_button = {
            "rect": pygame.Rect(x + 10, y + self.frame_height + 10, 80, 25),
            "text": "Start",
            "hover": False
        }
        
        self.delete_button = {
            "rect": pygame.Rect(x + width - 90, y + self.frame_height + 10, 80, 25),
            "text": "Delete",
            "hover": False
        }
        
        # Initialize fonts
        try:
            self.title_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 20)
            self.normal_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 16)
            self.small_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 14)
            self.button_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 16)
        except:
            # Fallback to default fonts
            self.title_font = pygame.font.SysFont(None, 20)
            self.normal_font = pygame.font.SysFont(None, 16)
            self.small_font = pygame.font.SysFont(None, 14)
            self.button_font = pygame.font.SysFont(None, 16)
    
    def handle_event(self, event):
        """Handle button events"""
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            self.hover = self._is_point_inside(mouse_x, mouse_y)
            
            # Update button hover states
            self.start_button["hover"] = self._is_point_inside_rect(mouse_x, mouse_y, self.start_button["rect"])
            self.delete_button["hover"] = self._is_point_inside_rect(mouse_x, mouse_y, self.delete_button["rect"])
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            
            # Check if start button was clicked
            if self._is_point_inside_rect(mouse_x, mouse_y, self.start_button["rect"]):
                print(f"Start button clicked for world {self.world_data['seed']}")
                if self.callback:
                    self.callback(self.world_data["seed"])
                return True
            
            # Check if delete button was clicked
            elif self._is_point_inside_rect(mouse_x, mouse_y, self.delete_button["rect"]):
                print(f"Delete button clicked for world {self.world_data['seed']}")
                if self.delete_callback:
                    self.delete_callback(self.world_data["seed"])
                return True
        
        return False
    
    def _is_point_inside(self, x, y):
        """Check if a point is inside the button"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def _is_point_inside_rect(self, x, y, rect):
        """Check if a point is inside a rectangle"""
        return rect.collidepoint(x, y)
    
    def render(self, screen):
        """Render the button at its position"""
        self.render_at(screen, self.x, self.y)
    
    def render_at(self, screen, x, y):
        """Render the button at the specified position"""
        # Update button positions based on new coordinates
        self.start_button["rect"].x = x + 10
        self.start_button["rect"].y = y + self.frame_height + 10
        
        self.delete_button["rect"].x = x + self.width - 90
        self.delete_button["rect"].y = y + self.frame_height + 10
        
        # Draw main frame background
        frame_rect = pygame.Rect(x, y, self.width, self.frame_height)
        
        if self.hover:
            pygame.draw.rect(screen, (50, 50, 70), frame_rect, border_radius=5)
        else:
            pygame.draw.rect(screen, (40, 40, 60), frame_rect, border_radius=5)
        
        # Draw frame border
        pygame.draw.rect(screen, BORDER_COLOR, frame_rect, width=2, border_radius=5)
        
        # Draw world seed
        seed_text = f"Seed: {self.world_data['seed']}"
        seed_surface = self.title_font.render(seed_text, True, TITLE_COLOR)
        screen.blit(seed_surface, (x + 10, y + 10))
        
        # Draw last played time
        import datetime
        last_updated = self.world_data.get("last_updated", 0)
        if last_updated:
            date_str = datetime.datetime.fromtimestamp(last_updated).strftime("%Y-%m-%d %H:%M")
            date_surface = self.small_font.render(f"Last played: {date_str}", True, TEXT_COLOR)
            screen.blit(date_surface, (x + 10, y + 35))
        
        # Draw world stats
        info = self.world_data.get("info", {})
        
        # Count discovered locations
        location_count = 0
        discovered_locations = info.get("discovered_locations", {})
        for location_type, locations in discovered_locations.items():
            location_count += len(locations)
        
        stats_text = f"Discovered locations: {location_count}"
        stats_surface = self.normal_font.render(stats_text, True, TEXT_COLOR)
        screen.blit(stats_surface, (x + 10, y + 60))
        
        # Count entities with memories
        entity_count = len(info.get("entity_memories", {}))
        entities_text = f"Entities with memories: {entity_count}"
        entities_surface = self.normal_font.render(entities_text, True, TEXT_COLOR)
        screen.blit(entities_surface, (x + 10, y + 85))
        
        # Draw action buttons
        # Start button
        if self.start_button["hover"]:
            pygame.draw.rect(screen, (60, 120, 60), self.start_button["rect"], border_radius=3)
        else:
            pygame.draw.rect(screen, (40, 100, 40), self.start_button["rect"], border_radius=3)
        pygame.draw.rect(screen, (100, 200, 100), self.start_button["rect"], width=1, border_radius=3)
        
        start_text = self.button_font.render(self.start_button["text"], True, (255, 255, 255))
        start_text_rect = start_text.get_rect(center=self.start_button["rect"].center)
        screen.blit(start_text, start_text_rect)
        
        # Delete button
        if self.delete_button["hover"]:
            pygame.draw.rect(screen, (120, 60, 60), self.delete_button["rect"], border_radius=3)
        else:
            pygame.draw.rect(screen, (100, 40, 40), self.delete_button["rect"], border_radius=3)
        pygame.draw.rect(screen, (200, 100, 100), self.delete_button["rect"], width=1, border_radius=3)
        
        delete_text = self.button_font.render(self.delete_button["text"], True, (255, 255, 255))
        delete_text_rect = delete_text.get_rect(center=self.delete_button["rect"].center)
        screen.blit(delete_text, delete_text_rect)

"""Interaction menu system for player actions"""
import pygame
import math
import os
from engine.ui.elements.base import UIElement

class InteractionMenu(UIElement):
    """Circular menu for player interactions"""
    
    def __init__(self, player):
        """Initialize the interaction menu
        
        Args:
            player: The player entity that owns this menu
        """
        super().__init__(0, 0, 0, 0, background_color=(0, 0, 0, 0))
        self.player = player
        self.visible = False
        self.options = []
        self.hover_index = -1
        self.selected_option = None
        self.radius = 80  # Distance from player to options
        self.option_size = 40  # Size of each option button
        self.tooltip_font = None
        self.tooltip_text = ""
        self.tooltip_timer = 0
        
        # Load assets
        self.load_assets()
        
        # Register default options
        self.register_default_options()
    
    def load_assets(self):
        """Load menu assets"""
        # Initialize font
        pygame.font.init()
        self.tooltip_font = pygame.font.Font(None, 24)
        
        # Get project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # Create assets directory if it doesn't exist
        icons_dir = os.path.join(project_root, "assets", "ui", "icons")
        os.makedirs(icons_dir, exist_ok=True)
        
        # Define icon paths
        self.icon_paths = {
            "consume": os.path.join(icons_dir, "consume_icon.png"),
            "construct": os.path.join(icons_dir, "construct_icon.png"),
        }
        
        # Load or create icons
        self.icons = {}
        for name, path in self.icon_paths.items():
            if os.path.exists(path):
                try:
                    self.icons[name] = pygame.image.load(path).convert_alpha()
                except Exception as e:
                    print(f"Error loading icon {name}: {e}")
                    self.icons[name] = self._create_placeholder_icon(name)
            else:
                print(f"Creating placeholder icon for {name}")
                self.icons[name] = self._create_placeholder_icon(name)
                # Save the placeholder
                pygame.image.save(self.icons[name], path)
    
    def _create_placeholder_icon(self, name):
        """Create a placeholder icon"""
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Fill with a base color
        if name == "consume":
            # Food/drink icon (apple shape)
            pygame.draw.circle(surface, (220, 60, 60), (16, 16), 12)  # Red apple
            pygame.draw.rect(surface, (101, 67, 33), (15, 4, 2, 8))  # Brown stem
            pygame.draw.polygon(surface, (50, 120, 50), [(15, 4), (19, 0), (17, 4)])  # Leaf
        elif name == "construct":
            # Construction icon (house shape)
            pygame.draw.polygon(surface, (180, 140, 100), [(6, 16), (16, 6), (26, 16)])  # Roof
            pygame.draw.rect(surface, (180, 140, 100), (8, 16, 16, 12))  # House body
            pygame.draw.rect(surface, (101, 67, 33), (14, 20, 4, 8))  # Door
        else:
            # Generic icon
            pygame.draw.rect(surface, (150, 150, 150), (4, 4, 24, 24))
            pygame.draw.rect(surface, (100, 100, 100), (4, 4, 24, 24), 2)  # Border
            
            # Add text label
            try:
                font = pygame.font.Font(None, 14)
                text = font.render(name[:4].upper(), True, (255, 255, 255))
                text_rect = text.get_rect(center=(16, 16))
                surface.blit(text, text_rect)
            except:
                pass
        
        return surface
    
    def register_default_options(self):
        """Register the default interaction options"""
        self.options = [
            {
                "id": "consume",
                "name": "Consume",
                "icon": self.icons.get("consume"),
                "tooltip": "Consume food or drink",
                "action": self.start_consume_action
            },
            {
                "id": "construct",
                "name": "Construct",
                "icon": self.icons.get("construct"),
                "tooltip": "Build structures from schematics",
                "action": self.start_construct_action
            }
        ]
    
    def toggle(self):
        """Toggle the menu visibility"""
        print(f"DEBUG: Toggling menu from {self.visible} to {not self.visible}")
        self.visible = not self.visible
        if not self.visible:
            # Reset state when closing
            self.selected_option = None
            self.hover_index = -1
        print(f"DEBUG: Menu visibility is now {self.visible}")
            
    def handle_event(self, event):
        """Handle input events"""
        if not self.visible:
            return False
        
        # Allow F key to close the menu
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            print("DEBUG: F key pressed while menu is open - closing menu")
            self.toggle()
            return True
        
        # Handle mouse movement for hover effects
        if event.type == pygame.MOUSEMOTION:
            self.handle_hover(event.pos)
            return True
        
        # Handle mouse clicks
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            print(f"DEBUG: Menu handling click at {event.pos}")
            return self.handle_click(event.pos)
        
        # Handle escape key to cancel
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.toggle()
            return True
        
        return True  # Consume all events when visible

    def handle_hover(self, mouse_pos):
        """Handle mouse hover over options"""
        if self.selected_option:
            # If an option is selected, let its handler deal with hover
            if hasattr(self.selected_option, "handle_hover"):
                self.selected_option.handle_hover(mouse_pos)
            return
        
        # Check each option
        self.hover_index = -1
        for i, option in enumerate(self.options):
            option_rect = self._get_option_rect(i)
            if option_rect.collidepoint(mouse_pos):
                self.hover_index = i
                self.tooltip_text = option["tooltip"]
                self.tooltip_timer = pygame.time.get_ticks()
                break
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks on options"""
        if self.selected_option:
            # If an option is selected, let its handler deal with clicks
            if hasattr(self.selected_option, "handle_click"):
                result = self.selected_option.handle_click(mouse_pos)
                if result == "close":
                    self.selected_option = None
                return True
            return False
        
        # Check if clicked on an option
        for i, option in enumerate(self.options):
            option_rect = self._get_option_rect(i)
            if option_rect.collidepoint(mouse_pos):
                # Call the option's action
                if "action" in option and callable(option["action"]):
                    result = option["action"]()
                    if isinstance(result, InteractionHandler):
                        self.selected_option = result
                    return True
        
        # If clicked outside options, close the menu
        self.toggle()
        return True
    
    def _get_option_rect(self, index):
        """Get the rectangle for an option button"""
        # Calculate position in a circle around the player
        angle = 2 * math.pi * index / len(self.options)
        
        # Get player screen position (center of screen if not available)
        from engine.core.simple_game_engine import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and SimpleGameEngine.instance:
            engine = SimpleGameEngine.instance
            player_x, player_y, _, _ = engine.camera.apply(
                self.player.grid_x * 16 + 8, 
                self.player.grid_y * 16 + 8,
                16, 16
            )
        else:
            screen = pygame.display.get_surface()
            player_x = screen.get_width() // 2
            player_y = screen.get_height() // 2
        
        # Calculate option position
        x = player_x + self.radius * math.cos(angle)
        y = player_y + self.radius * math.sin(angle)
        
        # Return the rectangle
        return pygame.Rect(
            x - self.option_size // 2,
            y - self.option_size // 2,
            self.option_size,
            self.option_size
        )
    
    def start_consume_action(self):
        """Start the consume action"""
        return ConsumeHandler(self.player)
    
    def start_construct_action(self):
        """Start the construct action"""
        return ConstructHandler(self.player)
    
    def render(self, screen):
        """Render the interaction menu"""
        if not self.visible:
            return
        
        
        # If an option is selected, render its handler
        if self.selected_option:
            if hasattr(self.selected_option, "render"):
                self.selected_option.render(screen)
            return
        
        # Get player screen position
        from engine.core.simple_game_engine import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and SimpleGameEngine.instance:
            engine = SimpleGameEngine.instance
            player_x, player_y, _, _ = engine.camera.apply(
                self.player.grid_x * 16 + 8, 
                self.player.grid_y * 16 + 8,
                16, 16
            )
        else:
            screen_surface = pygame.display.get_surface()
            player_x = screen_surface.get_width() // 2
            player_y = screen_surface.get_height() // 2
        
        
        # Draw background circle
        bg_surface = pygame.Surface((self.radius * 2 + 40, self.radius * 2 + 40), pygame.SRCALPHA)
        pygame.draw.circle(bg_surface, (0, 0, 0, 100), (bg_surface.get_width() // 2, bg_surface.get_height() // 2), self.radius + 10)
        screen.blit(bg_surface, (player_x - bg_surface.get_width() // 2, player_y - bg_surface.get_height() // 2))
        
        # Draw each option
        for i, option in enumerate(self.options):
            option_rect = self._get_option_rect(i)
            
            # Draw button background
            if i == self.hover_index:
                # Highlighted background for hovered option
                pygame.draw.rect(screen, (80, 80, 80, 200), option_rect, border_radius=5)
            else:
                # Normal background
                pygame.draw.rect(screen, (50, 50, 50, 180), option_rect, border_radius=5)
            
            # Draw border
            pygame.draw.rect(screen, (200, 200, 200, 150), option_rect, width=2, border_radius=5)
            
            # Draw icon
            if "icon" in option and option["icon"]:
                icon = option["icon"]
                icon_rect = icon.get_rect(center=option_rect.center)
                screen.blit(icon, icon_rect)
                
                # Draw option name below icon
                font = pygame.font.Font(None, 18)
                name_text = font.render(option["name"], True, (255, 255, 255))
                name_rect = name_text.get_rect(midtop=(option_rect.centerx, option_rect.bottom + 2))
                screen.blit(name_text, name_rect)
        
        # Draw tooltip for hovered option
        if self.hover_index >= 0 and self.tooltip_font:
            tooltip_text = self.options[self.hover_index]["tooltip"]
            tooltip_surface = self.tooltip_font.render(tooltip_text, True, (255, 255, 255))
            tooltip_rect = tooltip_surface.get_rect(midtop=(player_x, player_y + self.radius + 20))
            
            # Draw tooltip background
            padding = 5
            bg_rect = tooltip_rect.inflate(padding * 2, padding * 2)
            pygame.draw.rect(screen, (40, 40, 40, 200), bg_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 100, 150), bg_rect, width=1, border_radius=3)
            
            # Draw tooltip text
            screen.blit(tooltip_surface, tooltip_rect)



class InteractionHandler:
    """Base class for interaction handlers"""
    
    def __init__(self, player):
        """Initialize the handler
        
        Args:
            player: The player entity
        """
        self.player = player
    
    def handle_hover(self, mouse_pos):
        """Handle mouse hover"""
        pass
    
    def handle_click(self, mouse_pos):
        """Handle mouse click
        
        Returns:
            "close" to close the handler, None to keep it open
        """
        return "close"
    
    def render(self, screen):
        """Render the handler UI"""
        pass


class ConsumeHandler(InteractionHandler):
    """Handler for consuming items"""
    
    def __init__(self, player):
        super().__init__(player)
        self.consumable_items = []
        self.hover_index = -1
        self.item_rects = []
        self.find_consumable_items()
    
    def find_consumable_items(self):
        """Find all consumable items in the player's inventory"""
        self.consumable_items = []
        
        # Check each inventory slot
        for i, slot in enumerate(self.player.inventory.slots):
            if not slot.is_empty():
                item = slot.item
                # Check if item is consumable (expanded criteria)
                is_consumable = False
                
                # Check for new hunger/thirst values
                if hasattr(item, 'hunger_value') and item.hunger_value > 0:
                    is_consumable = True
                elif hasattr(item, 'thirst_value') and item.thirst_value > 0:
                    is_consumable = True
                # Check for legacy effect_type and effect_value
                elif hasattr(item, 'effect_type') and hasattr(item, 'effect_value'):
                    if item.effect_type in ['hunger', 'thirst']:
                        is_consumable = True
                
                if is_consumable:
                    self.consumable_items.append({
                        "item": item,
                        "slot_index": i
                    })

    
    def handle_hover(self, mouse_pos):
        """Handle mouse hover over consumable items"""
        self.hover_index = -1
        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.hover_index = i
                break
    
    def handle_click(self, mouse_pos):
        """Handle mouse click on consumable items"""
        for i, rect in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                # Consume the item
                if i < len(self.consumable_items):
                    item_data = self.consumable_items[i]
                    item = item_data["item"]
                    slot_index = item_data["slot_index"]
                    
                    # NEW: Apply item effects to player based on item type
                    consumed = self._consume_item_with_effects(item)
                    
                    if consumed:
                        print(f"Consumed {item.name}")
                        
                        # Reduce item quantity
                        item.quantity -= 1
                        
                        # If item quantity is now 0, remove it from inventory
                        if item.quantity <= 0:
                            self.player.inventory.slots[slot_index].item = None
                    
                    # Close the handler
                    return "close"
        
        # If clicked outside items, close the handler
        return "close"

    def _consume_item_with_effects(self, item):
        """Apply the item's effects to the player based on item type"""
        try:
            # DEBUG: Print item details
            print(f"DEBUG: Attempting to consume {item.name}")
            print(f"DEBUG: Item has hunger_value: {getattr(item, 'hunger_value', 'None')}")
            print(f"DEBUG: Item has thirst_value: {getattr(item, 'thirst_value', 'None')}")
            print(f"DEBUG: Item has effect_type: {getattr(item, 'effect_type', 'None')}")
            print(f"DEBUG: Item has effect_value: {getattr(item, 'effect_value', 'None')}")
            print(f"DEBUG: Player current thirst: {getattr(self.player, 'thirst', 'None')}")
            print(f"DEBUG: Player current hunger: {getattr(self.player, 'hunger', 'None')}")
            
            # Check if player has hunger/thirst attributes
            if not hasattr(self.player, 'hunger'):
                self.player.hunger = 10  # Initialize if missing
                print("DEBUG: Initialized player hunger to 10")
            if not hasattr(self.player, 'thirst'):
                self.player.thirst = 10  # Initialize if missing
                print("DEBUG: Initialized player thirst to 10")
            
            # Apply effects based on item properties
            consumed = False
            
            # Check for hunger restoration (food items)
            if hasattr(item, 'hunger_value') and item.hunger_value > 0:
                print(f"DEBUG: Processing hunger item with value {item.hunger_value}")
                old_hunger = self.player.hunger
                self.player.hunger = min(10, self.player.hunger + item.hunger_value)
                hunger_restored = self.player.hunger - old_hunger
                
                if hunger_restored > 0:
                    print(f"Restored {hunger_restored} hunger (now {self.player.hunger}/10)")
                    consumed = True
                else:
                    print("Hunger is already full!")
                    return False
            
            # Check for thirst restoration (water items)
            elif hasattr(item, 'thirst_value') and item.thirst_value > 0:
                print(f"DEBUG: Processing thirst item with value {item.thirst_value}")
                old_thirst = self.player.thirst
                self.player.thirst = min(10, self.player.thirst + item.thirst_value)
                thirst_restored = self.player.thirst - old_thirst
                
                print(f"DEBUG: Old thirst: {old_thirst}, New thirst: {self.player.thirst}, Restored: {thirst_restored}")
                
                if thirst_restored > 0:
                    print(f"Restored {thirst_restored} thirst (now {self.player.thirst}/10)")
                    consumed = True
                else:
                    print("Thirst is already full!")
                    return False
            
            # Fallback: check for generic effect_type and effect_value
            elif hasattr(item, 'effect_type') and hasattr(item, 'effect_value'):
                print(f"DEBUG: Processing legacy item with effect_type: {item.effect_type}, effect_value: {item.effect_value}")
                if item.effect_type == 'hunger':
                    old_hunger = self.player.hunger
                    self.player.hunger = min(10, self.player.hunger + item.effect_value)
                    hunger_restored = self.player.hunger - old_hunger
                    
                    if hunger_restored > 0:
                        print(f"Restored {hunger_restored} hunger (now {self.player.hunger}/10)")
                        consumed = True
                    else:
                        print("Hunger is already full!")
                        return False
                        
                elif item.effect_type == 'thirst':
                    print(f"DEBUG: Processing legacy thirst item")
                    old_thirst = self.player.thirst
                    self.player.thirst = min(10, self.player.thirst + item.effect_value)
                    thirst_restored = self.player.thirst - old_thirst
                    
                    print(f"DEBUG: Legacy thirst - Old: {old_thirst}, New: {self.player.thirst}, Restored: {thirst_restored}")
                    
                    if thirst_restored > 0:
                        print(f"Restored {thirst_restored} thirst (now {self.player.thirst}/10)")
                        consumed = True
                    else:
                        print("Thirst is already full!")
                        return False
            else:
                print("DEBUG: Item is not consumable - no valid hunger/thirst values found")
                return False
            
            # Play consumption sound if available
            if consumed and hasattr(self.player, 'sound_manager'):
                if hasattr(item, 'thirst_value') or (hasattr(item, 'effect_type') and item.effect_type == 'thirst'):
                    self.player.sound_manager.play_sound("drink", volume=0.6)
                else:
                    # Play eating sound (you may need to add this sound)
                    self.player.sound_manager.play_sound("eat", volume=0.6)
            
            print(f"DEBUG: Consumption result: {consumed}")
            return consumed
            
        except Exception as e:
            print(f"Error consuming item: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def render(self, screen):
        """Render the consumable items menu"""
        # Reset item rects
        self.item_rects = []
        
        # If no consumable items, show a message
        if not self.consumable_items:
            font = pygame.font.Font(None, 24)
            text = font.render("No consumable items in inventory", True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
            
            # Draw background
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (40, 40, 40, 200), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100, 150), bg_rect, width=1, border_radius=5)
            
            # Draw text
            screen.blit(text, text_rect)
            return
        
        # Calculate layout
        item_size = 48
        padding = 10
        items_per_row = min(8, len(self.consumable_items))
        rows = (len(self.consumable_items) + items_per_row - 1) // items_per_row
        
        # Calculate total size
        total_width = items_per_row * (item_size + padding) - padding
        total_height = rows * (item_size + padding) - padding
        
        # Calculate starting position (centered)
        start_x = (screen.get_width() - total_width) // 2
        start_y = (screen.get_height() - total_height) // 2
        
        # Draw background panel
        bg_rect = pygame.Rect(
            start_x - 10, 
            start_y - 40, 
            total_width + 20, 
            total_height + 80
        )
        pygame.draw.rect(screen, (40, 40, 40, 220), bg_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100, 150), bg_rect, width=2, border_radius=5)
        
        # Draw title
        font = pygame.font.Font(None, 28)
        title = font.render("Use Item", True, (255, 255, 255))
        title_rect = title.get_rect(midtop=(bg_rect.centerx, bg_rect.top + 10))
        screen.blit(title, title_rect)
        
        # Draw items
        for i, item_data in enumerate(self.consumable_items):
            item = item_data["item"]
            
            # Calculate position
            row = i // items_per_row
            col = i % items_per_row
            x = start_x + col * (item_size + padding)
            y = start_y + row * (item_size + padding)
            
            # Create item rect
            item_rect = pygame.Rect(x, y, item_size, item_size)
            self.item_rects.append(item_rect)
            
            # Draw item background
            if i == self.hover_index:
                # Highlighted background for hovered item
                pygame.draw.rect(screen, (80, 80, 80, 220), item_rect, border_radius=3)
            else:
                # Normal background
                pygame.draw.rect(screen, (60, 60, 60, 200), item_rect, border_radius=3)
            
            # Draw border
            pygame.draw.rect(screen, (150, 150, 150, 150), item_rect, width=1, border_radius=3)
            
            # FIXED: Draw item with proper parameters
            item_size_inner = item_size - 8
            item_x = x + 4  # Center the item with 4px padding
            item_y = y + 4  # Center the item with 4px padding
            
            # Check if item has a render method and what parameters it expects
            if hasattr(item, 'render'):
                try:
                    # Try the standard render method with screen, x, y, width, height
                    item.render(screen, item_x, item_y, item_size_inner, item_size_inner)
                except TypeError:
                    # Fallback: try with just screen and position
                    try:
                        item.render(screen, item_x, item_y)
                    except TypeError:
                        # Last resort: draw a placeholder
                        pygame.draw.rect(screen, (100, 100, 100), 
                                    (item_x, item_y, item_size_inner, item_size_inner))
                        
                        # Draw item name as text
                        font = pygame.font.Font(None, 16)
                        text = font.render(item.name[:4], True, (255, 255, 255))
                        text_rect = text.get_rect(center=(item_x + item_size_inner//2, item_y + item_size_inner//2))
                        screen.blit(text, text_rect)
            else:
                # Item doesn't have render method, draw placeholder
                pygame.draw.rect(screen, (100, 100, 100), 
                            (item_x, item_y, item_size_inner, item_size_inner))
                
                # Draw item name as text
                font = pygame.font.Font(None, 16)
                text = font.render(getattr(item, 'name', 'Item')[:4], True, (255, 255, 255))
                text_rect = text.get_rect(center=(item_x + item_size_inner//2, item_y + item_size_inner//2))
                screen.blit(text, text_rect)
            
            # Draw quantity
            if hasattr(item, 'quantity') and item.quantity > 1:
                small_font = pygame.font.Font(None, 20)
                qty_text = small_font.render(str(item.quantity), True, (255, 255, 255))
                screen.blit(qty_text, (item_x + item_size_inner - qty_text.get_width() - 2, item_y + item_size_inner - qty_text.get_height() - 2))
        
        # Draw tooltip for hovered item
        if self.hover_index >= 0 and self.hover_index < len(self.consumable_items):
            item = self.consumable_items[self.hover_index]["item"]
            
            # Create tooltip text with proper restoration values
            tooltip_lines = [item.name]
            
            # Check for hunger restoration
            if hasattr(item, 'hunger_value') and item.hunger_value > 0:
                tooltip_lines.append(f"Restores {item.hunger_value} Hunger")
            # Check for thirst restoration  
            elif hasattr(item, 'thirst_value') and item.thirst_value > 0:
                tooltip_lines.append(f"Restores {item.thirst_value} Thirst")
            # Fallback to legacy effect system
            elif hasattr(item, 'effect_type') and hasattr(item, 'effect_value'):
                tooltip_lines.append(f"Restores {item.effect_value} {item.effect_type.capitalize()}")
            
            if hasattr(item, 'description') and item.description:
                tooltip_lines.append("")
                tooltip_lines.append(item.description)
            
            # Draw tooltip
            self._draw_tooltip(screen, tooltip_lines, pygame.mouse.get_pos())
    
    def _draw_tooltip(self, screen, lines, pos):
        """Draw a multi-line tooltip"""
        if not lines:
            return
            
        font = pygame.font.Font(None, 20)
        line_height = font.get_linesize()
        
        # Calculate tooltip dimensions
        max_width = 0
        for line in lines:
            text_width = font.size(line)[0]
            max_width = max(max_width, text_width)
        
        tooltip_width = max_width + 20
        tooltip_height = len(lines) * line_height + 10
        
        # Position tooltip near the mouse but ensure it stays on screen
        tooltip_x = pos[0] + 15
        tooltip_y = pos[1] + 15
        
        # Adjust if tooltip would go off screen
        if tooltip_x + tooltip_width > screen.get_width():
            tooltip_x = screen.get_width() - tooltip_width - 5
        if tooltip_y + tooltip_height > screen.get_height():
            tooltip_y = screen.get_height() - tooltip_height - 5
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(screen, (40, 40, 40, 220), tooltip_rect, border_radius=3)
        pygame.draw.rect(screen, (100, 100, 100, 150), tooltip_rect, width=1, border_radius=3)
        
        # Draw tooltip text
        for i, line in enumerate(lines):
            if line:  # Skip empty lines
                text_surface = font.render(line, True, (255, 255, 255))
                screen.blit(text_surface, (tooltip_x + 10, tooltip_y + 5 + i * line_height))


class ConstructHandler(InteractionHandler):
    """Handler for constructing buildings from schematics"""
    
    def __init__(self, player):
        super().__init__(player)
        self.schematics = []
        self.hover_index = -1
        self.schematic_rects = []
        self.selected_schematic = None
        self.preview_position = None
        self.can_place = False
        self.find_schematics()
    
    def find_schematics(self):
        """Find all schematics in the player's inventory"""
        self.schematics = []
        
        # Check each inventory slot
        for i, slot in enumerate(self.player.inventory.slots):
            if not slot.is_empty():
                item = slot.item
                # Check if item is a schematic
                if hasattr(item, 'is_schematic') and item.is_schematic:
                    self.schematics.append({
                        "item": item,
                        "slot_index": i
                    })
    
    def handle_hover(self, mouse_pos):
        """Handle mouse hover over schematics or preview"""
        if self.selected_schematic:
            # Update preview position based on mouse position
            self._update_preview_position(mouse_pos)
        else:
            # Check hover over schematic items
            self.hover_index = -1
            for i, rect in enumerate(self.schematic_rects):
                if rect.collidepoint(mouse_pos):
                    self.hover_index = i
                    break
    
    def handle_click(self, mouse_pos):
        """Handle mouse click on schematics or preview"""
        if self.selected_schematic:
            # Try to place the schematic
            if self.can_place:
                self._place_schematic()
                return "close"
            else:
                # Cancel placement
                self.selected_schematic = None
                return None
        else:
            # Check click on schematic items
            for i, rect in enumerate(self.schematic_rects):
                if rect.collidepoint(mouse_pos):
                    # Select this schematic
                    if i < len(self.schematics):
                        self.selected_schematic = self.schematics[i]
                        return None
            
            # If clicked outside items, close the handler
            return "close"
    
    def _update_preview_position(self, mouse_pos):
        """Update the preview position based on mouse position"""
        # Convert screen position to world position
        from engine.core.simple_game_engine import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance') or not SimpleGameEngine.instance:
            return
            
        engine = SimpleGameEngine.instance
        world_x, world_y = engine.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        
        # Convert to grid coordinates
        grid_x = int(world_x // 16)
        grid_y = int(world_y // 16)
        
        # Store preview position
        self.preview_position = (grid_x, grid_y)
        
        # Check if placement is valid
        self.can_place = self._check_valid_placement(grid_x, grid_y)
    
    def _check_valid_placement(self, grid_x, grid_y):
        """Check if the schematic can be placed at the given position"""
        if not self.selected_schematic:
            return False
            
        item = self.selected_schematic["item"]
        
        # Get schematic dimensions
        width = item.width
        height = item.height
        
        # Get world map
        from engine.core.simple_game_engine import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance') or not SimpleGameEngine.instance:
            return False
            
        engine = SimpleGameEngine.instance
        if not hasattr(engine, 'world_map'):
            return False
            
        world_map = engine.world_map
        
        # Check if all tiles in the footprint are valid for placement
        for y in range(grid_y, grid_y + height):
            for x in range(grid_x, grid_x + width):
                # Check if tile is walkable and doesn't have an entity tile
                
                # Check if the world_map has is_walkable method
                if hasattr(world_map, 'is_walkable'):
                    is_walkable = world_map.is_walkable(x, y)
                else:
                    # Fallback: check if the tile exists and is walkable
                    tile = world_map.get_tile(x, y)
                    is_walkable = tile and tile.is_walkable()
                
                # Check if there's an entity tile at this position
                has_entity = False
                if hasattr(world_map, 'entity_tile_manager'):
                    has_entity = world_map.entity_tile_manager.get_component_at(x, y) is not None
                
                if not is_walkable or has_entity:
                    return False
        
        return True

    
    def _place_schematic(self):
        """Place the selected schematic at the preview position"""
        if not self.selected_schematic or not self.preview_position or not self.can_place:
            return False
            
        item = self.selected_schematic["item"]
        slot_index = self.selected_schematic["slot_index"]
        grid_x, grid_y = self.preview_position
        
        # Get world map
        from engine.core.simple_game_engine import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance') or not SimpleGameEngine.instance:
            return False
            
        engine = SimpleGameEngine.instance
        if not hasattr(engine, 'world_map'):
            return False
            
        world_map = engine.world_map
        
        # Get player entity ID for construction tracking
        player_id = None
        if hasattr(self.player, 'get_entity_id'):
            player_id = self.player.get_entity_id()
        
        # Place the entity tile based on structure type and mark as constructed
        placed = False
        
        if item.structure_type == "house":
            placed_tile = world_map.add_house(grid_x, grid_y, mark_constructed=True, constructed_by=player_id)
            placed = placed_tile is not None
        elif item.structure_type == "campfire":
            # Add campfire support when implemented
            placed_tile = world_map.add_campfire(grid_x, grid_y, mark_constructed=True, constructed_by=player_id)
            placed = placed_tile is not None
        # Add more structure types as needed
        
        # If placement was successful, consume the schematic item
        if placed:
            print(f"Placed {item.name} at ({grid_x}, {grid_y}) - marked as constructed by player")
            
            # Reduce quantity
            item.quantity -= 1
            
            # If item quantity is now 0, remove it from inventory
            if item.quantity <= 0:
                self.player.inventory.slots[slot_index].item = None
            
            return True
        
        return False
    
    def render(self, screen):
        """Render the schematic selection or preview"""
        if self.selected_schematic:
            self._render_preview(screen)
        else:
            self._render_schematic_selection(screen)
    
    def _render_schematic_selection(self, screen):
        """Render the schematic selection menu"""
        # Reset schematic rects
        self.schematic_rects = []
        
        # If no schematics, show a message
        if not self.schematics:
            font = pygame.font.Font(None, 24)
            text = font.render("No building schematics in inventory", True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
            
            # Draw background
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (40, 40, 40, 200), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100, 150), bg_rect, width=1, border_radius=5)
            
            # Draw text
            screen.blit(text, text_rect)
            return
        
        # Calculate layout
        item_size = 48
        padding = 10
        items_per_row = min(8, len(self.schematics))
        rows = (len(self.schematics) + items_per_row - 1) // items_per_row
        
        # Calculate total size
        total_width = items_per_row * (item_size + padding) - padding
        total_height = rows * (item_size + padding) - padding
        
        # Calculate starting position (centered)
        start_x = (screen.get_width() - total_width) // 2
        start_y = (screen.get_height() - total_height) // 2
        
        # Draw background panel
        bg_rect = pygame.Rect(
            start_x - 10, 
            start_y - 40, 
            total_width + 20, 
            total_height + 80
        )
        pygame.draw.rect(screen, (40, 40, 40, 220), bg_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100, 150), bg_rect, width=2, border_radius=5)
        
        # Draw title
        font = pygame.font.Font(None, 28)
        title = font.render("Select Building to Construct", True, (255, 255, 255))
        title_rect = title.get_rect(midtop=(bg_rect.centerx, bg_rect.top + 10))
        screen.blit(title, title_rect)
        
        # Draw instructions
        small_font = pygame.font.Font(None, 20)
        instructions = small_font.render("Click a schematic to preview placement", True, (200, 200, 200))
        instructions_rect = instructions.get_rect(midbottom=(bg_rect.centerx, bg_rect.bottom - 10))
        screen.blit(instructions, instructions_rect)
        
        # Draw items
        for i, schematic_data in enumerate(self.schematics):
            item = schematic_data["item"]
            
            # Calculate position
            row = i // items_per_row
            col = i % items_per_row
            x = start_x + col * (item_size + padding)
            y = start_y + row * (item_size + padding)
            
            # Create item rect
            item_rect = pygame.Rect(x, y, item_size, item_size)
            self.schematic_rects.append(item_rect)
            
            # Draw item background
            if i == self.hover_index:
                # Highlighted background for hovered item
                pygame.draw.rect(screen, (80, 80, 80, 220), item_rect, border_radius=3)
            else:
                # Normal background
                pygame.draw.rect(screen, (60, 60, 60, 200), item_rect, border_radius=3)
            
            # Draw border
            pygame.draw.rect(screen, (150, 150, 150, 150), item_rect, width=1, border_radius=3)
            
            # Draw item
            item_size_inner = item_size - 8
            item_x = x + (item_size - item_size_inner) // 2
            item_y = y + (item_size - item_size_inner) // 2
            item.render(screen, item_x, item_y, item_size_inner, item_size_inner)
            
            # Draw quantity
            if item.quantity > 1:
                small_font = pygame.font.Font(None, 20)
                qty_text = small_font.render(str(item.quantity), True, (255, 255, 255))
                screen.blit(qty_text, (x + item_size - qty_text.get_width() - 2, y + item_size - qty_text.get_height() - 2))
        
        # Draw tooltip for hovered item
        if self.hover_index >= 0 and self.hover_index < len(self.schematics):
            item = self.schematics[self.hover_index]["item"]
            
            # Create tooltip text
            tooltip_lines = [
                item.name,
                f"Type: {item.structure_type.capitalize()}"
            ]
            
            if hasattr(item, 'description') and item.description:
                tooltip_lines.append("")
                tooltip_lines.append(item.description)
            
            # Draw tooltip
            self._draw_tooltip(screen, tooltip_lines, pygame.mouse.get_pos())
    
    def _render_preview(self, screen):
        """Render the schematic placement preview"""
        if not self.selected_schematic or not self.preview_position:
            return
            
        item = self.selected_schematic["item"]
        grid_x, grid_y = self.preview_position
        
        # Get world map and camera
        from engine.core.simple_game_engine import SimpleGameEngine
        if not hasattr(SimpleGameEngine, 'instance') or not SimpleGameEngine.instance:
            return
            
        engine = SimpleGameEngine.instance
        if not hasattr(engine, 'camera'):
            return
            
        camera = engine.camera
        
        # Draw preview rectangle
        preview_x, preview_y, preview_width, preview_height = camera.apply(
            grid_x * 16, grid_y * 16, item.width * 16, item.height * 16
        )
        
        preview_rect = pygame.Rect(preview_x, preview_y, preview_width, preview_height)
        
        # If the item has a preview texture, use it
        if hasattr(item, 'preview_texture') and item.preview_texture:
            # Scale the preview texture to match the preview rectangle
            scaled_preview = pygame.transform.scale(item.preview_texture, (preview_width, preview_height))
            
            # Create a colored overlay based on placement validity
            overlay = pygame.Surface((preview_width, preview_height), pygame.SRCALPHA)
            if self.can_place:
                # Valid placement - green overlay
                overlay.fill((0, 255, 0, 100))
            else:
                # Invalid placement - red overlay
                overlay.fill((255, 0, 0, 100))
            
            # Draw the preview texture with overlay
            screen.blit(scaled_preview, (preview_x, preview_y))
            screen.blit(overlay, (preview_x, preview_y))
            
            # Draw border
            border_color = (0, 255, 0, 180) if self.can_place else (255, 0, 0, 180)
            pygame.draw.rect(screen, border_color, preview_rect, width=2)
        else:
            # Fallback to simple rectangle if no preview texture
            if self.can_place:
                # Valid placement - green
                pygame.draw.rect(screen, (0, 255, 0, 100), preview_rect)
                pygame.draw.rect(screen, (0, 255, 0, 180), preview_rect, width=2)
            else:
                # Invalid placement - red
                pygame.draw.rect(screen, (255, 0, 0, 100), preview_rect)
                pygame.draw.rect(screen, (255, 0, 0, 180), preview_rect, width=2)
        
        # Draw instructions
        font = pygame.font.Font(None, 24)
        if self.can_place:
            instructions = font.render("Click to place building", True, (255, 255, 255))
        else:
            instructions = font.render("Invalid placement location", True, (255, 100, 100))
        
        instructions_rect = instructions.get_rect(midbottom=(screen.get_width() // 2, screen.get_height() - 20))
        
        # Draw background for instructions
        bg_rect = instructions_rect.inflate(20, 10)
        pygame.draw.rect(screen, (40, 40, 40, 200), bg_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100, 150), bg_rect, width=1, border_radius=5)
        
        # Draw text
        screen.blit(instructions, instructions_rect)
        
        # Draw schematic info
        info_lines = [
            f"{item.name}",
            f"Size: {item.width}x{item.height}"
        ]
        
        # Draw info box
        self._draw_tooltip(screen, info_lines, (20, 20), fixed_pos=True)
    
    def _draw_tooltip(self, screen, lines, pos, fixed_pos=False):
        """Draw a multi-line tooltip"""
        if not lines:
            return
            
        font = pygame.font.Font(None, 20)
        line_height = font.get_linesize()
        
        # Calculate tooltip dimensions
        max_width = 0
        for line in lines:
            text_width = font.size(line)[0]
            max_width = max(max_width, text_width)
        
        tooltip_width = max_width + 20
        tooltip_height = len(lines) * line_height + 10
        
        # Position tooltip
        if fixed_pos:
            tooltip_x, tooltip_y = pos
        else:
            # Position near the mouse but ensure it stays on screen
            tooltip_x = pos[0] + 15
            tooltip_y = pos[1] + 15
            
            # Adjust if tooltip would go off screen
            if tooltip_x + tooltip_width > screen.get_width():
                tooltip_x = screen.get_width() - tooltip_width - 5
            if tooltip_y + tooltip_height > screen.get_height():
                tooltip_y = screen.get_height() - tooltip_height - 5
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(screen, (40, 40, 40, 220), tooltip_rect, border_radius=3)
        pygame.draw.rect(screen, (100, 100, 100, 150), tooltip_rect, width=1, border_radius=3)
        
        # Draw tooltip text
        for i, line in enumerate(lines):
            if line:  # Skip empty lines
                text_surface = font.render(line, True, (255, 255, 255))
                screen.blit(text_surface, (tooltip_x + 10, tooltip_y + 5 + i * line_height))

"""UI panel for displaying and interacting with the player's inventory"""
import pygame
from engine.ui.elements.base import UIElement
from entities.inventory import Inventory
from engine.ui.constants.colors import DARK_PANEL_BG, BORDER_COLOR, TEXT_COLOR

class InventoryPanel(UIElement):
    """Panel for displaying and interacting with inventory"""
    
    def __init__(self, x, y, width, height, inventory=None):
        """Initialize the inventory panel"""
        super().__init__(x, y, width, height, background_color=DARK_PANEL_BG)
        self.inventory = inventory or Inventory()
        self.visible = False
        self.slot_size = 40
        self.padding = 4
        self.tooltip_text = None
        self.tooltip_timer = 0
        
        # Calculate slots per row based on panel width
        self.slots_per_row = max(1, (width - 20) // (self.slot_size + self.padding))
        
        # Set title
        self.set_title("Inventory")
    
    def toggle_visibility(self):
        """Toggle panel visibility"""
        self.visible = not self.visible
        # Reset dragging state when hiding panel
        if not self.visible and self.inventory.dragging_item:
            self.inventory.return_dragged_item()
    
    def handle_event(self, event):
        """Handle mouse events for inventory interaction"""
        if not self.visible:
            return False
            
        # First, let the base class handle dragging
        if super().handle_event(event):
            return True
            
        # Check if the event is within the panel
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            mouse_pos = pygame.mouse.get_pos()
            if not self.contains_point(mouse_pos[0], mouse_pos[1]):
                # If clicking outside the panel with a dragged item, drop it
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.inventory.dragging_item:
                    self.inventory.return_dragged_item()
                return False
        
        # Handle mouse movement for hover effects
        if event.type == pygame.MOUSEMOTION:
            # Update hover slot - adjust Y position upward by half a slot height
            adjusted_y = event.pos[1] - (self.slot_size // 2)  # Move hover area up by half slot height
            self.inventory.update_hover_slot(
                event.pos[0], adjusted_y, 
                self.x, self.y, 
                self.slot_size, self.padding, 
                self.slots_per_row,
            )

            # Update tooltip timer
            if self.inventory.hover_slot >= 0 and self.inventory.hover_slot < self.inventory.size:
                slot = self.inventory.slots[self.inventory.hover_slot]
                if not slot.is_empty():
                    if self.tooltip_timer <= 0:
                        self.tooltip_timer = 30  # Show tooltip after 30 frames (0.5 seconds)
                    else:
                        self.tooltip_timer -= 1
                        if self.tooltip_timer <= 0:
                            # Generate tooltip text
                            self.tooltip_text = self.inventory.generate_tooltip(self.inventory.hover_slot)
                else:
                    self.tooltip_timer = 0
                    self.tooltip_text = None
            else:
                self.tooltip_timer = 0
                self.tooltip_text = None
            
        # Handle mouse clicks for item selection and dragging
        elif event.type == pygame.MOUSEBUTTONDOWN:
            slot_index = self.inventory.get_slot_at_position(
                event.pos[0], event.pos[1], 
                self.x, self.y, 
                self.slot_size, self.padding, 
                self.slots_per_row,
                title_height=30
            )

            # Left click - pick up/place items
            if event.button == 1:
                if slot_index >= 0 and slot_index < self.inventory.size:
                    # Select the slot
                    self.inventory.select_slot(slot_index)
                    
                    # If already dragging an item, try to drop it
                    if self.inventory.dragging_item:
                        self.inventory.drop_dragged_item(slot_index)
                    else:
                        # Start dragging - take whole stack if no modifiers, otherwise take one
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            # Shift+click for quick move
                            self.inventory.shift_click_slot(slot_index)
                        else:
                            # Normal click - take whole stack
                            self.inventory.start_drag_item(slot_index)
                
                return True

            # Right click - split stack or use item
            elif event.button == 3:
                if slot_index >= 0 and slot_index < self.inventory.size:
                    # Handle right-click interaction
                    self.inventory.right_click_slot(slot_index)
                
                return True

            # Middle click - quick move (e.g., to hotbar)
            elif event.button == 2:
                if slot_index >= 0 and slot_index < self.inventory.size:
                    # Handle middle-click interaction (quick move)
                    self.inventory.middle_click_slot(slot_index)
                
                return True

        # Handle mouse release for dropping items
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left click release
            if self.inventory.dragging_item:
                slot_index = self.inventory.get_slot_at_position(
                    event.pos[0], event.pos[1], 
                    self.x, self.y, 
                    self.slot_size, self.padding, 
                    self.slots_per_row
                )
                
                if slot_index >= 0 and slot_index < self.inventory.size:
                    # Try to place the item in this slot
                    self.inventory.drop_dragged_item(slot_index)
                else:
                    # Drop the item back in the original slot if we're not over a valid slot
                    self.inventory.return_dragged_item()
            
            return True
            
        # Handle keyboard shortcuts
        elif event.type == pygame.KEYDOWN:
            # Number keys to select hotbar slots
            if pygame.K_1 <= event.key <= pygame.K_9:
                slot_num = event.key - pygame.K_1
                if slot_num < self.inventory.size:
                    self.inventory.select_slot(slot_num)
                    return True
        
        return False
    
    def render(self, screen):
        """Render the inventory panel"""
        if not self.visible:
            return
            
        # Draw panel background
        super().render(screen)
        
        # Calculate rows needed
        rows = (self.inventory.size + self.slots_per_row - 1) // self.slots_per_row
        
        # Draw inventory slots
        for i, slot in enumerate(self.inventory.slots):
            row = i // self.slots_per_row
            col = i % self.slots_per_row
            
            slot_x = self.x + 10 + col * (self.slot_size + self.padding)
            slot_y = self.y + 30 + row * (self.slot_size + self.padding)  # Adjusted for title bar
            
            # Draw slot background
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            
            # Different background for hover and selected slots
            if i == self.inventory.hover_slot:
                pygame.draw.rect(screen, (70, 70, 70), slot_rect)
            else:
                pygame.draw.rect(screen, (60, 60, 60), slot_rect)
            
            # Highlight selected slot
            if i == self.inventory.selected_slot_index:
                pygame.draw.rect(screen, (200, 200, 0), slot_rect, 2)
            else:
                pygame.draw.rect(screen, (100, 100, 100), slot_rect, 1)
            
            # Draw item if slot is not empty
            if not slot.is_empty():
                # Calculate item position (centered in slot)
                item_size = self.slot_size - 8
                item_x = slot_x + (self.slot_size - item_size) // 2
                item_y = slot_y + (self.slot_size - item_size) // 2
                
                # Render item
                slot.item.render(screen, item_x, item_y, item_size, item_size)
        
        # Draw item being dragged
        if self.inventory.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            item_size = self.slot_size - 8
            item_x = mouse_pos[0] - item_size // 2
            item_y = mouse_pos[1] - item_size // 2
            
            self.inventory.dragging_item.render(screen, item_x, item_y, item_size, item_size)
        
        # Draw tooltip if needed
        if self.tooltip_text and self.inventory.hover_slot >= 0:
            self._render_tooltip(screen)
    
    def _render_tooltip(self, screen):
        """Render a tooltip for the hovered item"""
        if not self.tooltip_text:
            return
            
        # Set up font
        font = pygame.font.Font(None, 20)
        
        # Calculate tooltip dimensions
        line_height = 22
        tooltip_width = 0
        tooltip_height = len(self.tooltip_text) * line_height + 10
        
        # Find the widest line
        for line in self.tooltip_text:
            text_width = font.size(line)[0]
            tooltip_width = max(tooltip_width, text_width)
        
        tooltip_width += 20  # Add padding
        
        # Get mouse position for tooltip placement
        mouse_pos = pygame.mouse.get_pos()
        
        # Position tooltip near the mouse but ensure it stays on screen
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] + 15
        
        # Adjust if tooltip would go off screen
        screen_width, screen_height = screen.get_size()
        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = screen_width - tooltip_width - 5
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = screen_height - tooltip_height - 5
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(screen, (40, 40, 40, 220), tooltip_rect)
        pygame.draw.rect(screen, (100, 100, 100), tooltip_rect, 1)
        
        # Draw tooltip text
        for i, line in enumerate(self.tooltip_text):
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (tooltip_x + 10, tooltip_y + 5 + i * line_height))

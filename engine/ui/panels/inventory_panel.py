"""UI panel for displaying and interacting with the player's inventory"""
import pygame
from engine.ui.panels.panel_base import Panel
from entities.inventory import Inventory

class InventoryPanel(Panel):
    """Panel for displaying and interacting with inventory"""
    
    def __init__(self, x, y, width, height, inventory=None):
        """Initialize the inventory panel"""
        super().__init__(x, y, width, height)
        self.inventory = inventory or Inventory()
        self.visible = False
        self.dragging_item = None
        self.dragging_from_slot = -1
        self.hover_slot = -1
        self.slot_size = 40
        self.padding = 4
        
        # Calculate slots per row based on panel width
        self.slots_per_row = max(1, (width - 20) // (self.slot_size + self.padding))
    
    def toggle_visibility(self):
        """Toggle panel visibility"""
        self.visible = not self.visible
    
    def handle_event(self, event):
        """Handle mouse events for inventory interaction"""
        if not self.visible:
            return False
            
        # Check if the event is within the panel
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            mouse_pos = pygame.mouse.get_pos()
            if not self.contains_point(mouse_pos[0], mouse_pos[1]):
                return False
        
        # Handle mouse movement for hover effects
        if event.type == pygame.MOUSEMOTION:
            self.update_hover_slot(event.pos[0], event.pos[1])
            
        # Handle mouse clicks for item selection and dragging
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            slot_index = self.get_slot_at_position(event.pos[0], event.pos[1])
            if slot_index >= 0 and slot_index < self.inventory.size:
                # Select the slot
                self.inventory.select_slot(slot_index)
                
                # Start dragging if the slot has an item
                slot = self.inventory.slots[slot_index]
                if not slot.is_empty():
                    # If shift is held, split the stack
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        half_quantity = slot.item.quantity // 2
                        if half_quantity > 0:
                            self.dragging_item = slot.item.split(half_quantity)
                    else:
                        # Take the whole stack
                        self.dragging_item = slot.remove_item(slot.item.quantity)
                    
                    self.dragging_from_slot = slot_index
            
            return True
            
        # Handle mouse release for dropping items
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left click release
            if self.dragging_item:
                slot_index = self.get_slot_at_position(event.pos[0], event.pos[1])
                if slot_index >= 0 and slot_index < self.inventory.size:
                    # Try to place the item in this slot
                    target_slot = self.inventory.slots[slot_index]
                    
                    # If the slot is empty or can stack with our item
                    if target_slot.is_empty() or target_slot.can_accept(self.dragging_item):
                        # Add the item to the slot
                        remaining = target_slot.add_item(self.dragging_item)
                        
                        # If there are remaining items, keep them in hand
                        if remaining > 0:
                            self.dragging_item.quantity = remaining
                        else:
                            self.dragging_item = None
                    else:
                        # Swap items
                        temp_item = target_slot.item
                        target_slot.item = self.dragging_item
                        self.dragging_item = temp_item
                else:
                    # Drop the item back in the original slot if we're not over a valid slot
                    if 0 <= self.dragging_from_slot < self.inventory.size:
                        self.inventory.slots[self.dragging_from_slot].add_item(self.dragging_item)
                    
                    self.dragging_item = None
                
                self.dragging_from_slot = -1
            
            return True
            
        # Handle right-click for splitting stacks
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
            slot_index = self.get_slot_at_position(event.pos[0], event.pos[1])
            if slot_index >= 0 and slot_index < self.inventory.size:
                slot = self.inventory.slots[slot_index]
                if not slot.is_empty() and slot.item.quantity > 1:
                    # Take one item
                    self.dragging_item = slot.remove_item(1)
                    self.dragging_from_slot = slot_index
            
            return True
        
        return False
    
    def update_hover_slot(self, mouse_x, mouse_y):
        """Update which slot the mouse is hovering over"""
        self.hover_slot = self.get_slot_at_position(mouse_x, mouse_y)
    
    def get_slot_at_position(self, x, y):
        """Get the inventory slot at the given screen position"""
        # Convert to panel-relative coordinates
        rel_x = x - self.x
        rel_y = y - self.y
        
        # Account for panel padding
        rel_x -= 10
        rel_y -= 10
        
        if rel_x < 0 or rel_y < 0:
            return -1
            
        # Calculate row and column
        col = rel_x // (self.slot_size + self.padding)
        row = rel_y // (self.slot_size + self.padding)
        
        # Check if within valid range
        if col >= self.slots_per_row or rel_x >= self.slots_per_row * (self.slot_size + self.padding):
            return -1
            
        # Calculate slot index
        slot_index = row * self.slots_per_row + col
        
        if slot_index >= self.inventory.size:
            return -1
            
        return slot_index
    
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
            slot_y = self.y + 10 + row * (self.slot_size + self.padding)
            
            # Draw slot background
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            
            # Different background for hover and selected slots
            if i == self.hover_slot:
                pygame.draw.rect(screen, (70, 70, 70), slot_rect)
            else:
                pygame.draw.rect(screen, (60, 60, 60), slot_rect)
            
            # Highlight selected slot
            if i == self.inventory.selected_slot_index:
                pygame.draw.rect(screen, (200, 200, 0), slot_rect, 2)
            else:
                pygame.draw.rect(screen, (100, 100, 100), slot_rect, 1)
            
            # Draw item if slot is not empty and not being dragged
            if not slot.is_empty() and (self.dragging_from_slot != i or self.dragging_item is None):
                # Calculate item position (centered in slot)
                item_size = self.slot_size - 8
                item_x = slot_x + (self.slot_size - item_size) // 2
                item_y = slot_y + (self.slot_size - item_size) // 2
                
                # Render item
                slot.item.render(screen, item_x, item_y, item_size, item_size)
        
        # Draw item being dragged
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            item_size = self.slot_size - 8
            item_x = mouse_pos[0] - item_size // 2
            item_y = mouse_pos[1] - item_size // 2
            
            self.dragging_item.render(screen, item_x, item_y, item_size, item_size)
"""Inventory system for storing and managing items"""
from typing import List, Dict, Optional, Tuple
import pygame
from entities.items.item_base import Item

class InventorySlot:
    """A single slot in an inventory that can hold an item stack"""
    
    def __init__(self, item=None):
        """Initialize an inventory slot"""
        self.item = item
    
    def is_empty(self) -> bool:
        """Check if the slot is empty"""
        return self.item is None or self.item.quantity <= 0
    
    def can_accept(self, item) -> bool:
        """Check if this slot can accept the given item"""
        if self.is_empty():
            return True
        
        return self.item.can_stack_with(item)
    
    def add_item(self, item) -> int:
        """
        Add an item to this slot
        
        Returns:
            int: Number of items that couldn't be added (overflow)
        """
        if self.is_empty():
            self.item = item
            return 0
        
        return self.item.stack_with(item)
    
    def remove_item(self, quantity=1) -> Optional[Item]:
        """
        Remove items from this slot
        
        Returns:
            Item: The removed items, or None if the slot is empty
        """
        if self.is_empty():
            return None
        
        if quantity >= self.item.quantity:
            # Remove all items
            item = self.item
            self.item = None
            return item
        
        # Remove a portion of the stack
        return self.item.split(quantity)
    
    def to_dict(self) -> Dict:
        """Convert slot to a dictionary for serialization"""
        if self.is_empty():
            return {"empty": True}
        
        return {"empty": False, "item": self.item.to_dict()}
    
    @classmethod
    def from_dict(cls, data) -> 'InventorySlot':
        """Create a slot from serialized data"""
        slot = cls()
        
        if not data.get("empty", True):
            item_data = data.get("item", {})
            slot.item = Item.from_dict(item_data)
            
        return slot


class Inventory:
    """Container for multiple inventory slots"""
    
    def __init__(self, size=16):
        """Initialize an inventory with the specified number of slots"""
        self.size = size
        self.slots = [InventorySlot() for _ in range(size)]
        self.selected_slot_index = 0
    
    def get_selected_slot(self) -> InventorySlot:
        """Get the currently selected inventory slot"""
        return self.slots[self.selected_slot_index]
    
    def get_selected_item(self) -> Optional[Item]:
        """Get the item in the currently selected slot"""
        slot = self.get_selected_slot()
        return slot.item if not slot.is_empty() else None
    
    def select_slot(self, index):
        """Select a specific inventory slot"""
        if 0 <= index < self.size:
            self.selected_slot_index = index
    
    def add_item(self, item) -> bool:
        """
        Add an item to the inventory
        
        Returns:
            bool: True if the item was added successfully, False if inventory is full
        """
        if item is None or item.quantity <= 0:
            return True
        
        # First try to stack with existing items
        remaining = item.quantity
        for slot in self.slots:
            if not slot.is_empty() and slot.can_accept(item):
                # Try to add to this slot
                remaining = slot.add_item(item)
                if remaining == 0:
                    return True
                
                # Update the item quantity for the next slot
                item.quantity = remaining
        
        # If there are still items remaining, try to find an empty slot
        if remaining > 0:
            for slot in self.slots:
                if slot.is_empty():
                    # Add to empty slot
                    slot.add_item(item)
                    return True
        
        # If we get here, the inventory is full
        return False
    
    def remove_item(self, item_id, quantity=1) -> int:
        """
        Remove items of the specified type from the inventory
        
        Returns:
            int: Number of items actually removed
        """
        removed = 0
        remaining = quantity
        
        # Remove from slots containing this item type
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_id == item_id:
                # Calculate how many to remove from this slot
                to_remove = min(remaining, slot.item.quantity)
                
                # Remove items
                slot.remove_item(to_remove)
                
                # Update counters
                removed += to_remove
                remaining -= to_remove
                
                if remaining <= 0:
                    break
        
        return removed
    
    def count_item(self, item_id) -> int:
        """Count how many of a specific item type are in the inventory"""
        count = 0
        
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_id == item_id:
                count += slot.item.quantity
                
        return count
    
    def has_item(self, item_id, quantity=1) -> bool:
        """Check if the inventory has at least the specified quantity of an item"""
        return self.count_item(item_id) >= quantity
    
    def to_dict(self) -> Dict:
        """Convert inventory to a dictionary for serialization"""
        return {
            "size": self.size,
            "selected_slot": self.selected_slot_index,
            "slots": [slot.to_dict() for slot in self.slots]
        }
    
    @classmethod
    def from_dict(cls, data) -> 'Inventory':
        """Create an inventory from serialized data"""
        size = data.get("size", 16)
        inventory = cls(size)
        
        # Set selected slot
        inventory.selected_slot_index = data.get("selected_slot", 0)
        
        # Load slots
        slots_data = data.get("slots", [])
        for i, slot_data in enumerate(slots_data):
            if i < size:
                inventory.slots[i] = InventorySlot.from_dict(slot_data)
                
        return inventory
    
    def render(self, surface, x, y, slot_size=40, padding=4, highlight_selected=True):
        """Render the inventory on the screen"""
        # Calculate dimensions
        slots_per_row = min(8, self.size)
        rows = (self.size + slots_per_row - 1) // slots_per_row
        
        total_width = slots_per_row * slot_size + (slots_per_row - 1) * padding
        total_height = rows * slot_size + (rows - 1) * padding
        
        # Draw background
        bg_rect = pygame.Rect(x, y, total_width, total_height)
        pygame.draw.rect(surface, (40, 40, 40), bg_rect)
        pygame.draw.rect(surface, (80, 80, 80), bg_rect, 2)
        
        # Draw slots
        for i, slot in enumerate(self.slots):
            row = i // slots_per_row
            col = i % slots_per_row
            
            slot_x = x + col * (slot_size + padding)
            slot_y = y + row * (slot_size + padding)
            
            # Draw slot background
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            pygame.draw.rect(surface, (60, 60, 60), slot_rect)
            
            # Highlight selected slot
            if highlight_selected and i == self.selected_slot_index:
                pygame.draw.rect(surface, (200, 200, 0), slot_rect, 2)
            else:
                pygame.draw.rect(surface, (100, 100, 100), slot_rect, 1)
            
            # Draw item if slot is not empty
            if not slot.is_empty():
                # Calculate item position (centered in slot)
                item_size = slot_size - 8
                item_x = slot_x + (slot_size - item_size) // 2
                item_y = slot_y + (slot_size - item_size) // 2
                
                # Render item
                slot.item.render(surface, item_x, item_y, item_size, item_size)
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
        if item is None:
            return 0
            
        if self.is_empty():
            self.item = item
            print(f"DEBUG: Added {item.name} x{item.quantity} to empty slot")
            return 0
        
        # If items can stack, stack them
        if self.item.can_stack_with(item):
            overflow = self.item.stack_with(item)
            print(f"DEBUG: Stacked items, {self.item.quantity} in slot, {overflow} overflow")
            return overflow
        
        # If items can't stack, return the full quantity
        print(f"DEBUG: Cannot add {item.name} to slot with {self.item.name}")
        return item.quantity
    
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
        removed_item = self.item.split(quantity)
        # Ensure the original item still exists in the slot
        if self.item.quantity <= 0:
            self.item = None
            
        return removed_item
    
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
        
        # UI interaction state
        self.dragging_item = None
        self.dragging_from_slot = -1
        self.hover_slot = -1
    
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
                    item.quantity = remaining  # Ensure correct quantity
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
    
    # Enhanced methods for inventory functionality
    
    def find_empty_slot(self) -> int:
        """Find the index of an empty slot, or -1 if none available"""
        for i, slot in enumerate(self.slots):
            if slot.is_empty():
                return i
        return -1
    
    def find_stackable_slot(self, item) -> int:
        """Find a slot that can stack with the given item, or -1 if none available"""
        if item is None:
            return -1
            
        for i, slot in enumerate(self.slots):
            if not slot.is_empty() and slot.item.can_stack_with(item):
                return i
        return -1
    
    def count_items(self) -> int:
        """Count the total number of items in the inventory"""
        count = 0
        for slot in self.slots:
            if not slot.is_empty():
                count += slot.item.quantity
        return count
    
    def swap_slots(self, index1, index2) -> bool:
        """Swap the contents of two inventory slots"""
        if 0 <= index1 < self.size and 0 <= index2 < self.size:
            self.slots[index1].item, self.slots[index2].item = self.slots[index2].item, self.slots[index1].item
            return True
        return False
    
    def move_to_slot(self, from_index, to_index) -> bool:
        """Move an item from one slot to another, stacking if possible"""
        if not (0 <= from_index < self.size and 0 <= to_index < self.size):
            return False
            
        source_slot = self.slots[from_index]
        target_slot = self.slots[to_index]
        
        # If source is empty, nothing to do
        if source_slot.is_empty():
            return False
            
        # If target is empty, just move the item
        if target_slot.is_empty():
            target_slot.item = source_slot.item
            source_slot.item = None
            return True
            
        # If items can stack, try to stack them
        if target_slot.item.can_stack_with(source_slot.item):
            # Store original quantities for debugging
            original_source_qty = source_slot.item.quantity
            original_target_qty = target_slot.item.quantity
            
            # Try to stack
            overflow = target_slot.item.stack_with(source_slot.item)
            
            # Update source slot based on overflow
            if overflow > 0:
                # Some items couldn't be stacked
                source_slot.item.quantity = overflow
                print(f"DEBUG: Stacked {original_source_qty - overflow} items, {overflow} remain in source slot")
            else:
                # All items were stacked
                source_slot.item = None
                print(f"DEBUG: Stacked all {original_source_qty} items, target now has {target_slot.item.quantity}")
            
            return True
            
        # If items can't stack, swap them
        source_slot.item, target_slot.item = target_slot.item, source_slot.item
        print(f"DEBUG: Swapped items between slots {from_index} and {to_index}")
        return True
    
    def split_stack(self, slot_index, amount=None) -> Optional[Item]:
        """
        Split a stack of items in the specified slot
        
        Args:
            slot_index: The index of the slot to split
            amount: The amount to split off (default: half the stack, rounded up)
            
        Returns:
            The split-off item, or None if the slot is empty or has only 1 item
        """
        if not (0 <= slot_index < self.size):
            return None
            
        slot = self.slots[slot_index]
        if slot.is_empty() or slot.item.quantity <= 1:
            return None
            
        # Default to splitting half the stack (rounded up)
        if amount is None:
            amount = (slot.item.quantity + 1) // 2
        elif amount <= 0:
            return None
            
        # Make sure we don't take more than what's in the stack
        amount = min(amount, slot.item.quantity - 1)
        
        # Split the stack
        split_item = slot.item.split(amount)
        
        # Verify the split worked correctly
        if split_item is None:
            print(f"ERROR: Failed to split stack in slot {slot_index}")
            return None
            
        # Verify quantities after split
        print(f"DEBUG: Split {amount} from stack, original now has {slot.item.quantity}, new item has {split_item.quantity}")
        
        # Ensure the original item still exists in the slot if it should
        if slot.item.quantity <= 0:
            print(f"WARNING: Original item quantity is {slot.item.quantity} after split, setting slot to empty")
            slot.item = None
            
        return split_item
    
    def try_stack_similar(self, item) -> int:
        """
        Try to stack an item with existing similar items
        
        Returns:
            The remaining quantity that couldn't be stacked
        """
        if item is None:
            return 0
            
        remaining = item.quantity
        
        # Try to stack with existing items
        for slot in self.slots:
            if not slot.is_empty() and slot.item.can_stack_with(item):
                # Calculate how much can be added to this slot
                space_available = slot.item.max_stack - slot.item.quantity
                amount_to_add = min(remaining, space_available)
                
                if amount_to_add > 0:
                    # Add to this slot
                    slot.item.quantity += amount_to_add
                    remaining -= amount_to_add
                    
                    # If all items have been stacked, we're done
                    if remaining <= 0:
                        return 0
        
        # Return the remaining quantity
        return remaining
    
    def get_first_item_of_type(self, item_id) -> Optional[Tuple[int, Item]]:
        """
        Find the first slot containing an item of the specified type
        
        Returns:
            Tuple of (slot_index, item) or None if not found
        """
        for i, slot in enumerate(self.slots):
            if not slot.is_empty() and slot.item.item_id == item_id:
                return (i, slot.item)
        return None
    
    def get_all_items_of_type(self, item_id) -> List[Tuple[int, Item]]:
        """
        Find all slots containing items of the specified type
        
        Returns:
            List of tuples (slot_index, item)
        """
        result = []
        for i, slot in enumerate(self.slots):
            if not slot.is_empty() and slot.item.item_id == item_id:
                result.append((i, slot.item))
        return result
    
    def sort_inventory(self):
        """Sort inventory items by type and stack similar items"""
        # First, collect all items
        all_items = []
        for slot in self.slots:
            if not slot.is_empty():
                all_items.append(slot.item)
                slot.item = None
        
        # Sort items by ID and then by durability (if applicable)
        all_items.sort(key=lambda item: (item.item_id, 
                                         getattr(item, 'durability', 0) if hasattr(item, 'durability') else 0))
        
        # Try to stack similar items
        stacked_items = []
        for item in all_items:
            # If we already have an item of this type that can stack
            found_stack = False
            for existing_item in stacked_items:
                if existing_item.can_stack_with(item):
                    # Try to stack
                    overflow = existing_item.stack_with(item)
                    if overflow == 0:
                        # Item fully stacked
                        found_stack = True
                        break
                    else:
                        # Item partially stacked, update quantity
                        item.quantity = overflow
            
            # If item couldn't be fully stacked, add it to the list
            if not found_stack:
                stacked_items.append(item)
        
        # Put items back into inventory
        for i, item in enumerate(stacked_items):
            if i < self.size:
                self.slots[i].item = item
    
    def clear(self):
        """Clear all items from the inventory"""
        for slot in self.slots:
            slot.item = None
    
    def is_full(self) -> bool:
        """Check if the inventory is full"""
        return self.find_empty_slot() == -1
    
    def get_item_at(self, index) -> Optional[Item]:
        """Get the item at the specified slot index"""
        if 0 <= index < self.size:
            slot = self.slots[index]
            return slot.item if not slot.is_empty() else None
        return None
    
    def set_item_at(self, index, item) -> bool:
        """Set the item at the specified slot index"""
        if 0 <= index < self.size:
            self.slots[index].item = item
            return True
        return False
    
    def transfer_to(self, other_inventory, slot_index, quantity=None) -> bool:
        """
        Transfer an item from this inventory to another inventory
        
        Args:
            other_inventory: The target inventory
            slot_index: The source slot index in this inventory
            quantity: The quantity to transfer (None = all)
            
        Returns:
            True if the transfer was successful, False otherwise
        """
        if not (0 <= slot_index < self.size):
            return False
            
        source_slot = self.slots[slot_index]
        if source_slot.is_empty():
            return False
            
        # Determine quantity to transfer
        if quantity is None or quantity >= source_slot.item.quantity:
            # Transfer the whole stack
            item_to_transfer = source_slot.item
            source_slot.item = None
        else:
            # Transfer a portion of the stack
            item_to_transfer = source_slot.item.split(quantity)
            if item_to_transfer is None:
                return False
        
        # Try to add the item to the other inventory
        if other_inventory.add_item(item_to_transfer):
            return True
        else:
            # If transfer failed, return the item to the source slot
            if source_slot.is_empty():
                source_slot.item = item_to_transfer
            else:
                # Try to stack back with the original stack
                overflow = source_slot.item.stack_with(item_to_transfer)
                if overflow > 0:
                    # This shouldn't happen, but just in case
                    print(f"WARNING: Item transfer failed and couldn't restore original state. {overflow} items lost.")
            return False
            
    def take_one_item(self, slot_index) -> Optional[Item]:
        """
        Take a single item from a stack
        
        Args:
            slot_index: The index of the slot to take from
            
        Returns:
            A single item from the stack, or None if the slot is empty
        """
        if not (0 <= slot_index < self.size):
            return None
            
        slot = self.slots[slot_index]
        if slot.is_empty():
            return None
            
        # If there's only one item, remove it completely
        if slot.item.quantity == 1:
            item = slot.item
            slot.item = None
            return item
            
        # Otherwise, split off one item
        return slot.remove_item(1)
        
    def place_item(self, item, slot_index) -> Optional[Item]:
        """
        Place an item in a specific slot, returning any displaced item
        
        Args:
            item: The item to place
            slot_index: The slot to place it in
            
        Returns:
            Any item that was displaced (if the slot wasn't empty and couldn't stack)
        """
        if item is None or not (0 <= slot_index < self.size):
            return None
            
        target_slot = self.slots[slot_index]
        
        # If slot is empty, just place the item
        if target_slot.is_empty():
            target_slot.item = item
            return None
            
        # If items can stack, try to stack them
        if target_slot.item.can_stack_with(item):
            overflow = target_slot.item.stack_with(item)
            
            # If there's overflow, create a new item with the overflow quantity
            if overflow > 0:
                overflow_item = item.create_instance()
                overflow_item.quantity = overflow
                return overflow_item
                
            # If no overflow, all items were stacked
            return None
            
        # If items can't stack, swap them
        displaced_item = target_slot.item
        target_slot.item = item
        return displaced_item
    
    # New methods for UI interaction
    
    def start_drag_item(self, slot_index, amount=None):
        """
        Start dragging an item from a slot
        
        Args:
            slot_index: The index of the slot to drag from
            amount: The amount to drag (None = all, 1 = single item)
            
        Returns:
            The item being dragged, or None if the slot is empty
        """
        if not (0 <= slot_index < self.size):
            return None
            
        slot = self.slots[slot_index]
        if slot.is_empty():
            return None
            
        # If amount is None, take the whole stack
        if amount is None:
            self.dragging_item = slot.item
            self.dragging_from_slot = slot_index
            slot.item = None
            return self.dragging_item
            
        # If amount is 1 and there's only one item, take it all
        if amount == 1 and slot.item.quantity == 1:
            self.dragging_item = slot.item
            self.dragging_from_slot = slot_index
            slot.item = None
            return self.dragging_item
            
        # Otherwise, split the stack
        if amount == 1:
            # Take just one item
            self.dragging_item = slot.item.split(1)
        else:
            # Take the specified amount
            self.dragging_item = slot.item.split(amount)
            
        self.dragging_from_slot = slot_index
        return self.dragging_item
    
    def drop_dragged_item(self, slot_index):
        """
        Drop the currently dragged item into a slot
        
        Args:
            slot_index: The index of the slot to drop into
            
        Returns:
            True if the drop was successful, False otherwise
        """
        if self.dragging_item is None:
            return False
            
        if not (0 <= slot_index < self.size):
            # Return item to original slot if dropping outside inventory
            self.return_dragged_item()
            return False
            
        target_slot = self.slots[slot_index]
        
        # If target slot is empty, just place the item
        if target_slot.is_empty():
            target_slot.item = self.dragging_item
            self.dragging_item = None
            self.dragging_from_slot = -1
            return True
            
        # If items can stack, try to stack them
        if target_slot.item.can_stack_with(self.dragging_item):
            overflow = target_slot.item.stack_with(self.dragging_item)
            
            # If there's overflow, keep dragging the remaining items
            if overflow > 0:
                self.dragging_item.quantity = overflow
                return True
                
            # If no overflow, all items were stacked
            self.dragging_item = None
            self.dragging_from_slot = -1
            return True
            
        # If items can't stack, swap them
        temp_item = target_slot.item
        target_slot.item = self.dragging_item
        self.dragging_item = temp_item
        # Keep dragging the new item
        return True
    
    def return_dragged_item(self):
        """Return the dragged item to its original slot or find a new slot for it"""
        if self.dragging_item is None:
            return
            
        # Try to return to original slot first
        if 0 <= self.dragging_from_slot < self.size:
            original_slot = self.slots[self.dragging_from_slot]
            
            # If original slot is empty, just place it back
            if original_slot.is_empty():
                original_slot.item = self.dragging_item
                self.dragging_item = None
                self.dragging_from_slot = -1
                return
                
            # If items can stack, try to stack them
            if original_slot.item.can_stack_with(self.dragging_item):
                overflow = original_slot.item.stack_with(self.dragging_item)
                
                # If there's overflow, find another slot
                if overflow > 0:
                    self.dragging_item.quantity = overflow
                else:
                    # If no overflow, all items were stacked
                    self.dragging_item = None
                    self.dragging_from_slot = -1
                    return
        
        # If we couldn't return to the original slot or there's overflow,
        # try to find another slot for the item
        if self.dragging_item:
            # Try to stack with existing items
            for i, slot in enumerate(self.slots):
                if not slot.is_empty() and slot.item.can_stack_with(self.dragging_item):
                    overflow = slot.item.stack_with(self.dragging_item)
                    
                    # If there's no overflow, we're done
                    if overflow == 0:
                        self.dragging_item = None
                        self.dragging_from_slot = -1
                        return
                        
                    # Update quantity for remaining items
                    self.dragging_item.quantity = overflow
            
            # If we still have items, find an empty slot
            if self.dragging_item:
                for i, slot in enumerate(self.slots):
                    if slot.is_empty():
                        slot.item = self.dragging_item
                        self.dragging_item = None
                        self.dragging_from_slot = -1
                        return
                        
                # If we get here, the inventory is full and we couldn't place the item
                # This shouldn't happen in normal gameplay, but we'll handle it anyway
                print("WARNING: Could not return dragged item to inventory - inventory is full")
                # The item will remain being dragged
    
    def right_click_slot(self, slot_index):
        """
        Handle right-click on a slot (take half or one item)
        
        Args:
            slot_index: The index of the slot that was right-clicked
            
        Returns:
            The item taken from the slot, or None if the slot was empty
        """
        # If already dragging an item, try to place one in this slot
        if self.dragging_item:
            if not (0 <= slot_index < self.size):
                return None
                
            target_slot = self.slots[slot_index]
            
            # If target slot is empty, place one item
            if target_slot.is_empty():
                # Create a new item with quantity 1
                new_item = self.dragging_item.create_instance()
                new_item.quantity = 1
                target_slot.item = new_item
                
                # Reduce quantity of dragged item
                self.dragging_item.quantity -= 1
                
                # If dragged item is now empty, clear it
                if self.dragging_item.quantity <= 0:
                    self.dragging_item = None
                    self.dragging_from_slot = -1
                
                return new_item
                
            # If items can stack, add one to the stack
            elif target_slot.item.can_stack_with(self.dragging_item):
                # Check if the target stack is full
                if target_slot.item.quantity >= target_slot.item.max_stack:
                    return None
                    
                # Add one to the target stack
                target_slot.item.quantity += 1
                
                # Reduce quantity of dragged item
                self.dragging_item.quantity -= 1
                
                # If dragged item is now empty, clear it
                if self.dragging_item.quantity <= 0:
                    self.dragging_item = None
                    self.dragging_from_slot = -1
                
                return target_slot.item
            
            # If items can't stack, do nothing
            return None
        
        # If not dragging an item, pick up half the stack or one item
        if not (0 <= slot_index < self.size):
            return None
            
        slot = self.slots[slot_index]
        if slot.is_empty():
            return None
            
        # If there's only one item, take it
        if slot.item.quantity == 1:
            self.dragging_item = slot.item
            self.dragging_from_slot = slot_index
            slot.item = None
            return self.dragging_item
            
        # If there's more than one item, take half (rounded up)
        amount = (slot.item.quantity + 1) // 2
        self.dragging_item = slot.item.split(amount)
        self.dragging_from_slot = slot_index
        return self.dragging_item
    
    def shift_click_slot(self, slot_index):
        """
        Handle shift+click on a slot (quick move)
        
        Args:
            slot_index: The index of the slot that was shift-clicked
            
        Returns:
            True if the operation was successful, False otherwise
        """
        # This is a placeholder for quick-move functionality
        # In a real implementation, this would move items between inventory sections
        # (e.g., between main inventory and hotbar)
        print(f"DEBUG: Shift-click on slot {slot_index}")
        return True
    
    def middle_click_slot(self, slot_index):
        """
        Handle middle-click on a slot (quick move or special action)
        
        Args:
            slot_index: The index of the slot that was middle-clicked
            
        Returns:
            True if the operation was successful, False otherwise
        """
        # This is a placeholder for middle-click functionality
        # In a real implementation, this could be used for special actions
        print(f"DEBUG: Middle-click on slot {slot_index}")
        return True
    
    def get_slot_at_position(self, x, y, panel_x, panel_y, slot_size, padding, slots_per_row, title_height=30):
        """
        Get the inventory slot at the given screen position
        
        Args:
            x, y: Screen coordinates
            panel_x, panel_y: Panel position
            slot_size: Size of each inventory slot
            padding: Padding between slots
            slots_per_row: Number of slots per row
            title_height: Height of the title bar
            
        Returns:
            The slot index at the given position, or -1 if not over a slot
        """
        # Convert to panel-relative coordinates
        rel_x = x - panel_x
        rel_y = y - panel_y
        
        # Account for panel padding and title bar
        # The inventory section starts at a specific Y position in the panel
        # For character_info_panel, this is at height - 220
        # For inventory_panel, this is at 30 (title bar height)
        content_x = 10  # Standard padding inside panels
        
        # Adjust relative coordinates to content area
        rel_x -= content_x
        rel_y -= title_height  # This is the key adjustment
        
        if rel_x < 0 or rel_y < 0:
            return -1
            
        # Calculate row and column
        col = rel_x // (slot_size + padding)
        row = rel_y // (slot_size + padding)
        
        # Check if within valid range
        if col >= slots_per_row or rel_x >= slots_per_row * (slot_size + padding):
            return -1
            
        # Calculate slot index
        slot_index = row * slots_per_row + col
        
        if slot_index >= self.size:
            return -1
            
        return slot_index


    
    def update_hover_slot(self, mouse_x, mouse_y, panel_x, panel_y, slot_size, padding, slots_per_row, title_height=30):
        """Update which slot the mouse is hovering over"""
        self.hover_slot = self.get_slot_at_position(
            mouse_x, mouse_y, panel_x, panel_y, slot_size, padding, slots_per_row, title_height
        )
        return self.hover_slot

    
    def generate_tooltip(self, slot_index):
        """
        Generate tooltip text for an item in the specified slot
        
        Args:
            slot_index: The index of the slot to generate a tooltip for
            
        Returns:
            A list of text lines for the tooltip, or None if the slot is empty
        """
        if not (0 <= slot_index < self.size):
            return None
            
        slot = self.slots[slot_index]
        if slot.is_empty():
            return None
            
        item = slot.item
        lines = [
            item.name,
            f"Quantity: {item.quantity}"
        ]
        
        # Add description if available
        if hasattr(item, 'description') and item.description:
            lines.append("")
            lines.append(item.description)
        
        # Add durability if applicable
        if hasattr(item, 'durability') and item.durability is not None:
            durability_percent = int((item.durability / item.max_durability) * 100)
            lines.append(f"Durability: {durability_percent}%")
        
        # Add effect info for consumables
        if hasattr(item, 'effect_type') and hasattr(item, 'effect_value'):
            effect_name = item.effect_type.capitalize()
            lines.append(f"Restores {item.effect_value} {effect_name}")
        
        return lines

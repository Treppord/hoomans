"""Base item class and item registry system"""
import pygame
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable

class Item(ABC):
    """Base class for all items in the game"""
    
    # Class registry to store all item types
    registry = {}
    
    # Default item size
    ITEM_SIZE = 16
    
    def __init__(self, item_id: str, name: str, description: str, icon_path: str = None, 
                 max_stack: int = 1, durability: int = None):
        """Initialize base item properties
        
        Args:
            item_id: Unique identifier for this item type
            name: Display name of the item
            description: Item description text
            icon_path: Path to the item's icon (relative to assets/items/)
            max_stack: Maximum number of items that can stack in one inventory slot
            durability: Maximum durability if applicable, None for items without durability
        """
        self.item_id = item_id
        self.name = name
        self.description = description
        self.max_stack = max_stack
        self.max_durability = durability
        self.durability = durability
        self.quantity = 1
        self.icon = None
        self.icon_path = icon_path
        self._load_icon()
        
        # Register this item type if not already registered
        if item_id not in Item.registry:
            Item.registry[item_id] = self.__class__
    
    def _load_icon(self):
        """Load the item's icon from the assets directory"""
        # Don't try to load icons before pygame is initialized
        if not pygame.get_init():
            self.icon = None
            return
            
        if not self.icon_path:
            # Create a default icon if none specified
            self.icon = pygame.Surface((self.ITEM_SIZE, self.ITEM_SIZE), pygame.SRCALPHA)
            self.icon.fill((100, 100, 100, 200))
            return
            
        # Get the path to the assets directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Make sure the icon path starts with "items/" if it doesn't already
        if not self.icon_path.startswith("items/"):
            self.icon_path = os.path.join("items", self.icon_path)
            
        full_path = os.path.join(project_root, "assets", self.icon_path)
        
        try:
            if os.path.exists(full_path):
                # Load the image
                loaded_image = pygame.image.load(full_path).convert_alpha()
                
                # Check if the image needs to be resized to 16x16
                if loaded_image.get_width() != self.ITEM_SIZE or loaded_image.get_height() != self.ITEM_SIZE:
                    print(f"Resizing item icon {self.icon_path} from {loaded_image.get_width()}x{loaded_image.get_height()} to {self.ITEM_SIZE}x{self.ITEM_SIZE}")
                    self.icon = pygame.transform.scale(loaded_image, (self.ITEM_SIZE, self.ITEM_SIZE))
                else:
                    self.icon = loaded_image
                    
                print(f"Successfully loaded item icon: {self.icon_path}")
            else:
                print(f"Warning: Item icon not found: {full_path}")
                # Create a placeholder icon with item ID text
                self.icon = pygame.Surface((self.ITEM_SIZE, self.ITEM_SIZE), pygame.SRCALPHA)
                self.icon.fill((255, 0, 255, 128))  # Magenta semi-transparent
                
                # Try to add text if font is available
                try:
                    font = pygame.font.Font(None, 10)  # Small font
                    text = font.render(self.item_id[:4], True, (255, 255, 255))
                    text_rect = text.get_rect(center=(self.ITEM_SIZE//2, self.ITEM_SIZE//2))
                    self.icon.blit(text, text_rect)
                except:
                    # If font rendering fails, just use the colored square
                    pass
        except Exception as e:
            print(f"Error loading item icon {self.icon_path}: {e}")
            # Create a placeholder icon
            self.icon = pygame.Surface((self.ITEM_SIZE, self.ITEM_SIZE), pygame.SRCALPHA)
            self.icon.fill((255, 0, 255, 128))  # Magenta semi-transparent
    
    def ensure_icon_loaded(self):
        """Ensure the icon is loaded (call this after pygame is initialized)"""
        if self.icon is None:
            self._load_icon()

    def can_stack_with(self, other: 'Item') -> bool:
        """Check if this item can stack with another item"""
        if self.item_id != other.item_id:
            return False
        
        # Items with durability generally don't stack unless they're at full durability
        if self.durability is not None:
            return (self.durability == self.max_durability and 
                    other.durability == other.max_durability)
        
        return True
    
    def stack_with(self, other: 'Item') -> int:
        """
        Stack this item with another item of the same type
        
        Returns:
            int: Number of items that couldn't be stacked (overflow)
        """
        if not self.can_stack_with(other):
            return other.quantity
        
        total = self.quantity + other.quantity
        if total <= self.max_stack:
            self.quantity = total
            return 0
        else:
            self.quantity = self.max_stack
            return total - self.max_stack
    
    def split(self, amount: int) -> Optional['Item']:
        """
        Split this stack into two stacks
        
        Args:
            amount: Number of items to take from this stack
            
        Returns:
            Item: A new item with the specified quantity, or None if not enough items
        """
        if amount <= 0 or amount >= self.quantity:
            return None
            
        # Create a new item of the same type
        new_item = self.create_instance()
        new_item.quantity = amount
        self.quantity -= amount
        
        # Copy durability if applicable
        if self.durability is not None:
            new_item.durability = self.durability
            
        return new_item
    
    def create_instance(self) -> 'Item':
        """Create a new instance of this item type"""
        # This will be overridden by subclasses to create proper instances
        new_item = self.__class__(
            self.item_id, 
            self.name, 
            self.description, 
            self.icon_path, 
            self.max_stack, 
            self.max_durability
        )
        return new_item
    
    def use(self, user, world=None) -> bool:
        """
        Use this item
        
        Args:
            user: The entity using the item
            world: The world context for item use
            
        Returns:
            bool: True if the item was used successfully
        """
        # Base implementation does nothing
        return False
    
    def reduce_durability(self, amount: int = 1) -> bool:
        """
        Reduce item durability
        
        Returns:
            bool: True if the item is still usable, False if it broke
        """
        if self.durability is None:
            return True
            
        self.durability = max(0, self.durability - amount)
        return self.durability > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to a dictionary for serialization"""
        data = {
            "item_id": self.item_id,
            "quantity": self.quantity
        }
        
        # Only include durability if the item has it
        if self.durability is not None:
            data["durability"] = self.durability
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['Item']:
        """Create an item instance from serialized data"""
        item_id = data.get("item_id")
        if item_id not in cls.registry:
            print(f"Warning: Unknown item type {item_id}")
            return None
            
        # Create an instance of the correct item type
        item_class = cls.registry[item_id]
        item = item_class.create_template()
        
        # Set quantity and durability
        item.quantity = data.get("quantity", 1)
        if "durability" in data and item.durability is not None:
            item.durability = data["durability"]
            
        return item
    
    @classmethod
    def create_template(cls) -> 'Item':
        """Create a template instance of this item class"""
        # This should be implemented by each item subclass
        raise NotImplementedError("Item subclasses must implement create_template")
    
    def render(self, surface, x, y, width=32, height=32):
        """Render the item icon at the specified position"""
        # Make sure icon is loaded
        if self.icon is None:
            self._load_icon()
            
        if self.icon:
            # Scale icon if needed
            if self.icon.get_width() != width or self.icon.get_height() != height:
                scaled_icon = pygame.transform.scale(self.icon, (width, height))
            else:
                scaled_icon = self.icon
                
            surface.blit(scaled_icon, (x, y))
            
            # Draw quantity if more than 1
            if self.quantity > 1:
                font = pygame.font.Font(None, 20)
                text = font.render(str(self.quantity), True, (255, 255, 255))
                text_rect = text.get_rect(bottomright=(x + width - 2, y + height - 2))
                
                # Draw text shadow
                shadow = font.render(str(self.quantity), True, (0, 0, 0))
                shadow_rect = shadow.get_rect(bottomright=(x + width - 1, y + height - 1))
                surface.blit(shadow, shadow_rect)
                
                # Draw text
                surface.blit(text, text_rect)
                
            # Draw durability bar if applicable
            if self.durability is not None and self.max_durability > 0:
                bar_width = width - 4
                bar_height = 4
                bar_x = x + 2
                bar_y = y + height - 6
                
                # Background
                pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
                
                # Durability percentage
                durability_percent = self.durability / self.max_durability
                fill_width = int(bar_width * durability_percent)
                
                # Choose color based on durability
                if durability_percent > 0.6:
                    color = (0, 200, 0)  # Green
                elif durability_percent > 0.3:
                    color = (200, 200, 0)  # Yellow
                else:
                    color = (200, 0, 0)  # Red
                    
                pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))

"""Consumable items like food and potions"""
from entities.items.item_base import Item

class ConsumableItem(Item):
    """Base class for items that can be consumed"""
    
    def __init__(self, item_id, name, description, icon_path=None, 
                 max_stack=16, effect_value=0, effect_type=None):
        """Initialize a consumable item
        
        Args:
            effect_value: The magnitude of the effect when consumed
            effect_type: The type of effect (e.g., "health", "hunger", "thirst")
        """
        super().__init__(item_id, name, description, icon_path, max_stack)
        self.effect_value = effect_value
        self.effect_type = effect_type
    
    def use(self, user, world=None):
        """Consume the item and apply its effect"""
        if not hasattr(user, self.effect_type):
            print(f"Warning: User doesn't have attribute {self.effect_type}")
            return False
            
        # Apply the effect
        current_value = getattr(user, self.effect_type)
        max_value = 10  # Default max value
        
        # Check if there's a max value attribute
        max_attr = f"max_{self.effect_type}"
        if hasattr(user, max_attr):
            max_value = getattr(user, max_attr)
            
        # Apply the effect (capped at max value)
        new_value = min(current_value + self.effect_value, max_value)
        setattr(user, self.effect_type, new_value)
        
        # Reduce quantity
        self.quantity -= 1
        
        # Return True if the item was consumed
        return True
    
    def create_instance(self):
        """Create a new instance of this consumable item"""
        # The error is here - we're passing too many arguments to the constructor
        # Let's fix it by explicitly calling the correct subclass constructor
        
        # For FoodItem
        if isinstance(self, FoodItem):
            return FoodItem(
                self.item_id,
                self.name,
                self.description,
                self.icon_path,
                self.max_stack,
                self.effect_value  # This is hunger_value for FoodItem
            )
        # For WaterBottleItem
        elif isinstance(self, WaterBottleItem):
            return WaterBottleItem(
                self.item_id,
                self.name,
                self.description,
                self.icon_path,
                self.max_stack,
                self.effect_value  # This is thirst_value for WaterBottleItem
            )
        # For generic ConsumableItem
        else:
            return ConsumableItem(
                self.item_id,
                self.name,
                self.description,
                self.icon_path,
                self.max_stack,
                self.effect_value,
                self.effect_type
            )
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this consumable item"""
        # This should be implemented by specific consumable subclasses
        raise NotImplementedError("Consumable subclasses must implement create_template")


class FoodItem(ConsumableItem):
    """Food items that restore hunger"""
    
    def __init__(self, item_id, name, description, icon_path=None, 
                 max_stack=16, hunger_value=2):
        """Initialize a food item"""
        super().__init__(
            item_id, name, description, icon_path, max_stack, 
            effect_value=hunger_value, effect_type="hunger"
        )
    
    def create_instance(self):
        """Create a new instance of this food item"""
        return FoodItem(
            self.item_id,
            self.name,
            self.description,
            self.icon_path,
            self.max_stack,
            self.effect_value  # This is hunger_value
        )
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this food item"""
        return cls("food_generic", "Food", "A generic food item", "items/food_generic.png", 16, 2)


class WaterBottleItem(ConsumableItem):
    """Water bottles that restore thirst"""
    
    def __init__(self, item_id, name, description, icon_path=None, 
                 max_stack=16, thirst_value=2):
        """Initialize a water bottle item"""
        super().__init__(
            item_id, name, description, icon_path, max_stack, 
            effect_value=thirst_value, effect_type="thirst"
        )
    
    def create_instance(self):
        """Create a new instance of this water bottle item"""
        return WaterBottleItem(
            self.item_id,
            self.name,
            self.description,
            self.icon_path,
            self.max_stack,
            self.effect_value  # This is thirst_value
        )
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this water bottle item"""
        return cls("water_bottle", "Water Bottle", "A bottle of fresh water", "items/water_bottle.png", 16, 2)

class GameData:
    """Container for a single game value with optional min/max constraints"""
    
    def __init__(self, initial_value=0, min_value=None, max_value=None):
        self.value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self._observers = []
    
    def set(self, new_value):
        """Set value with constraints"""
        old_value = self.value
        
        # Apply constraints
        if self.min_value is not None:
            new_value = max(self.min_value, new_value)
        if self.max_value is not None:
            new_value = min(self.max_value, new_value)
            
        self.value = new_value
        
        # Notify observers if value changed
        if old_value != new_value:
            self.notify_observers(old_value, new_value)
        
        return self.value
    
    def add(self, amount):
        """Add to current value"""
        return self.set(self.value + amount)
    
    def subtract(self, amount):
        """Subtract from current value"""
        return self.set(self.value - amount)
    
    def add_observer(self, observer):
        """Add a function to call when value changes"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove an observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, old_value, new_value):
        """Notify all observers of value change"""
        for observer in self._observers:
            observer(old_value, new_value)


class DataManager:
    """Manages game data values and provides access to them"""
    
    def __init__(self):
        self.values = {}
        self.player_stats = {}
        self.game_state = {}
        self.inventory = {}
    
    def create_value(self, key, initial_value=0, min_value=None, max_value=None):
        """Create a new game value"""
        self.values[key] = GameData(initial_value, min_value, max_value)
        return self.values[key]
    
    def get_value(self, key):
        """Get a game value object"""
        return self.values.get(key)
    
    def set_value(self, key, value):
        """Set a game value"""
        if key in self.values:
            return self.values[key].set(value)
        else:
            # Create new value if it doesn't exist
            self.values[key] = GameData(value)
            return value
    
    def add_to_value(self, key, amount):
        """Add to a game value"""
        if key in self.values:
            return self.values[key].add(amount)
        else:
            # Create new value if it doesn't exist
            return self.set_value(key, amount)
    
    def create_player_stat(self, stat_name, initial_value=0, min_value=0, max_value=100):
        """Create a player statistic"""
        self.player_stats[stat_name] = GameData(initial_value, min_value, max_value)
        return self.player_stats[stat_name]
    
    def get_player_stat(self, stat_name):
        """Get a player statistic"""
        return self.player_stats.get(stat_name)
    
    def add_inventory_item(self, item_id, quantity=1):
        """Add an item to inventory"""
        current = self.inventory.get(item_id, 0)
        self.inventory[item_id] = current + quantity
        return self.inventory[item_id]
    
    def remove_inventory_item(self, item_id, quantity=1):
        """Remove an item from inventory"""
        if item_id in self.inventory:
            self.inventory[item_id] = max(0, self.inventory[item_id] - quantity)
            if self.inventory[item_id] == 0:
                del self.inventory[item_id]
            return True
        return False
    
    def get_inventory_quantity(self, item_id):
        """Get quantity of an item in inventory"""
        return self.inventory.get(item_id, 0)
    
    def save_game_state(self):
        """Save current game state to a dictionary (could be extended to save to file)"""
        state = {
            'values': {k: v.value for k, v in self.values.items()},
            'player_stats': {k: v.value for k, v in self.player_stats.items()},
            'inventory': dict(self.inventory)
        }
        return state
    
    def load_game_state(self, state):
        """Load game state from a dictionary"""
        # Load values
        for k, v in state.get('values', {}).items():
            self.set_value(k, v)
            
        # Load player stats
        for k, v in state.get('player_stats', {}).items():
            if k in self.player_stats:
                self.player_stats[k].set(v)
            else:
                self.create_player_stat(k, v)
                
        # Load inventory
        self.inventory = dict(state.get('inventory', {}))
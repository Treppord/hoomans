"""Game data initialization and management"""
from engine.config.config_loader import get_config_loader

class GameDataManager:
    """Manages initialization of game data based on configuration"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.config = get_config_loader()
    
    def setup_initial_game_data(self):
        """Set up initial game values from configuration"""
        game_stats = self.config.get_setting('game_settings', 'game_stats', default={})
        
        # Create player stats
        health = game_stats.get('starting_health', 20)
        hunger = game_stats.get('starting_hunger', 10)
        thirst = game_stats.get('starting_thirst', 10)
        
        self.data_manager.create_player_stat("health", health, 0, health)
        self.data_manager.create_player_stat("hunger", hunger, 0, hunger)
        self.data_manager.create_player_stat("thirst", thirst, 0, thirst)
        self.data_manager.create_player_stat("score", 0, 0, None)
        
        # Create game values
        self.data_manager.create_value("game_time", 0)
        self.data_manager.create_value("enemies_defeated", 0)
        
        # Add starting inventory
        starting_inventory = game_stats.get('starting_inventory', {})
        for item_id, quantity in starting_inventory.items():
            self.data_manager.add_inventory_item(item_id, quantity)
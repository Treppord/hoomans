"""
test Game Configuration
A new game configuration
"""
from config.game_config import GameConfig, SystemConfig, EntityConfig, WorldItemConfig

def get_test_game_config():
    """Get the test game configuration"""
    return GameConfig(
        name="test",
        description="A new game configuration",

        world_width=256,
        world_height=256,

        systems=[
            SystemConfig(name="sound_system", enabled=True),
            SystemConfig(name="entity_manager", enabled=True),
            SystemConfig(name="item_system", enabled=True),
            SystemConfig(name="world_map", enabled=True, config={'width': 256, 'height': 256}),
            SystemConfig(name="world_cache", enabled=True),
            SystemConfig(name="ai_universe", enabled=True),
        ],

        entities=[
            EntityConfig(entity_type="player", grid_x=128, grid_y=128, color=(255, 0, 0), speed=1),
            EntityConfig(entity_type="npc", grid_x=133, grid_y=133, color=(0, 255, 0), speed=1),
            EntityConfig(entity_type="npc", grid_x=123, grid_y=123, color=(0, 0, 255), speed=1),
            EntityConfig(entity_type="food_npcs", color=(255, 255, 255), speed=1, count=30),
        ],

        world_items=[
            WorldItemConfig(item_type="apple", x=131, y=131, quantity=3),
            WorldItemConfig(item_type="berries", x=125, y=125, quantity=1),
            WorldItemConfig(item_type="water_bottle", x=128, y=133, quantity=2),
        ]
    )
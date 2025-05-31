"""
Hoomans Minimal Game Configuration
"""
from config.game_config import GameConfig, SystemConfig, EntityConfig, WorldItemConfig

def get_minimal_game_config():
    """Get the hoomans minimal game configuration"""
    return GameConfig(
        name="Hoomans Minimal",
        description="Minimal Hoomans game for testing",
        
        world_width=128,
        world_height=128,
        
        systems=[
        SystemConfig(
            name="entity_manager",
            enabled=True,
            config={}
        ),        SystemConfig(
            name="world_map",
            enabled=True,
            config={'width': 128, 'height': 128}
        ),        SystemConfig(
            name="ai_universe",
            enabled=False,
            config={}
        )
        ],
        
        entities=[
        EntityConfig(
            entity_type="player",
            grid_x=10,
            grid_y=10,
            color=(255, 0, 0),
            speed=1,
            cna_filename=None,
            count=1
        ),        EntityConfig(
            entity_type="food_npcs",
            grid_x=None,
            grid_y=None,
            color=(255, 255, 255),
            speed=1,
            cna_filename=None,
            count=5
        )
        ],
        
        world_items=[
        WorldItemConfig(
            item_type="apple",
            x=15,
            y=15,
            quantity=1
        )
        ]
    )

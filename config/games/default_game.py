"""
Default Game Configuration
"""
from config.game_config import GameConfig, SystemConfig, EntityConfig, WorldItemConfig

def get_default_game_config():
    """Get the default game configuration"""
    return GameConfig(
        name="Hoomans Default",
        description="Default Hoomans game with standard entities and world",
        
        world_width=256,
        world_height=256,
        
        systems=[
            SystemConfig(
                name="sound_system",
                enabled=True,
                config={
                    "master_volume": 0.7,
                    "sfx_volume": 0.8,
                    "music_volume": 0.6
                }
            ),
            SystemConfig(
                name="entity_manager",
                enabled=True
            ),
            SystemConfig(
                name="item_system",
                enabled=True
            ),
            SystemConfig(
                name="sprite_assets",
                enabled=True
            ),
            SystemConfig(
                name="world_map",
                enabled=True,
                config={
                    "width": 256,
                    "height": 256
                }
            ),
            SystemConfig(
                name="world_cache",
                enabled=True
            ),
            SystemConfig(
                name="ai_universe",
                enabled=True,
                config={
                    "use_llm": True,
                    "use_local_model": True
                }
            )
        ],
        
        entities=[
            EntityConfig(
                entity_type="player",
                grid_x=25,
                grid_y=19,
                color=(255, 0, 0),
                speed=1
            ),
            EntityConfig(
                entity_type="npc",
                grid_x=26,
                grid_y=30,
                color=(0, 255, 0),
                speed=1,
                cna_filename="Skyler_Smith.cna"
            ),
            EntityConfig(
                entity_type="npc",
                grid_x=37,
                grid_y=25,
                color=(0, 0, 255),
                speed=1,
                cna_filename="Dakota_Brown.cna"
            ),
            EntityConfig(
                entity_type="food_npcs",
                count=30
            )
        ],
        
        world_items=[
            WorldItemConfig(item_type="apple", x=30, y=20, quantity=3),
            WorldItemConfig(item_type="berries", x=25, y=22, quantity=1),
            WorldItemConfig(item_type="water_bottle", x=35, y=15, quantity=2),
            WorldItemConfig(item_type="stone_axe", x=28, y=22, quantity=1)
        ],
        
        pre_init_hooks=[
            "sprite_assets"
        ],
        
        post_init_hooks=[
            "finalize_world_items",
            "initialize_npc_exploration"
        ]
    )
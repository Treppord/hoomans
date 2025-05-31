"""
Survival Game Configuration - Enhanced survival experience
"""
from config.game_config import GameConfig, SystemConfig, EntityConfig, WorldItemConfig

def get_survival_game_config():
    """Get a survival-focused game configuration"""
    return GameConfig(
        name="Hoomans Survival",
        description="Survival-focused Hoomans game with more resources and challenges",
        
        world_width=512,
        world_height=512,
        
        systems=[
            SystemConfig(
                name="sound_system",
                enabled=True,
                config={
                    "master_volume": 0.8,
                    "sfx_volume": 0.9,
                    "music_volume": 0.5
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
                name="world_map",
                enabled=True,
                config={
                    "width": 512,
                    "height": 512
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
                grid_x=256,
                grid_y=256,
                color=(255, 0, 0),
                speed=1
            ),
            EntityConfig(
                entity_type="npc",
                grid_x=260,
                grid_y=260,
                color=(0, 255, 0),
                speed=1,
                cna_filename="Skyler_Smith.cna"
            ),
            EntityConfig(
                entity_type="npc",
                grid_x=250,
                grid_y=250,
                color=(0, 0, 255),
                speed=1,
                cna_filename="Dakota_Brown.cna"
            ),
            EntityConfig(
                entity_type="npc",
                grid_x=270,
                grid_y=240,
                color=(255, 255, 0),
                speed=1,
                cna_filename="Alex_Johnson.cna"
            ),
            EntityConfig(
                entity_type="food_npcs",
                count=100  # More food sources for survival
            )
        ],
        
        world_items=[
            # More scattered resources
            WorldItemConfig(item_type="apple", x=200, y=200, quantity=5),
            WorldItemConfig(item_type="berries", x=300, y=300, quantity=3),
            WorldItemConfig(item_type="water_bottle", x=250, y=280, quantity=4),
            WorldItemConfig(item_type="stone_axe", x=280, y=220, quantity=2),
            WorldItemConfig(item_type="apple", x=150, y=350, quantity=2),
            WorldItemConfig(item_type="berries", x=400, y=150, quantity=2),
            WorldItemConfig(item_type="water_bottle", x=100, y=400, quantity=3)
        ]
    )
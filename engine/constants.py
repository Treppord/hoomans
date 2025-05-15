"""
Game constants module - centralizes all configurable values used throughout the game
"""

# Time constants (in milliseconds)
class TimeConstants:
    # Movement timing
    PLAYER_MOVE_COOLDOWN = 250  # Time between player movements (250ms = 4 tiles per second)
    NPC_MOVE_COOLDOWN = 500    # Time between NPC movements (1 second per tile)
    FOOD_MOVE_COOLDOWN = 1500   # Time between food movements (slower than NPCs)
    
    # Need decay rates
    THIRST_DECREASE_INTERVAL = 10000  # Thirst decreases every 10 seconds
    HUNGER_DECREASE_INTERVAL = 15000  # Hunger decreases every 15 seconds
    
    # Replenishment rates
    THIRST_REPLENISH_COOLDOWN = 2000  # Time between drinking water (2 seconds)
    HUNGER_REPLENISH_COOLDOWN = 3000  # Time between eating food (3 seconds)
    
    # AI decision making
    AI_DECISION_COOLDOWN = 30   # Frames between AI decisions
    CHAT_RESPONSE_COOLDOWN = 5000  # Milliseconds to wait before processing another chat response
    CHAT_RESPONSE_TIMEOUT = 60000  # Timeout for chat responses (60 seconds)
    
    # Exploration timers
    EXPLORATION_COOLDOWN = 10000  # Time between exploration decisions
    MEMORY_RECORD_COOLDOWN = 10000  # Time between memory recordings
    
    # Food entity behavior
    FOOD_DIRECTION_CHANGE_COOLDOWN = 5000  # Time between food direction changes
    FOOD_CONSUMPTION_ANIMATION_DURATION = 500  # Duration of food consumption animation

# Game balance constants
class GameBalanceConstants:
    # Need values
    MAX_THIRST = 10
    MAX_HUNGER = 10
    MAX_HEALTH = 20
    
    # Starting values
    STARTING_THIRST = 10
    STARTING_HUNGER = 10
    STARTING_HEALTH = 20
    
    # Consumption values
    FOOD_NUTRITION_VALUE = 5  # How much hunger is restored when food is consumed
    WATER_HYDRATION_VALUE = 2  # How much thirst is restored per drink
    
    # View ranges
    NPC_FOOD_VIEW_RANGE = 8  # Tiles around NPC to search for food
    NPC_WATER_VIEW_RANGE = 8  # Tiles around NPC to search for water
    NPC_PLAYER_VIEW_RANGE = 8  # Tiles around NPC to detect player

# Movement and animation constants
class MovementConstants:
    # Visual interpolation factor (smoothness of movement)
    MOVE_LERP_FACTOR = 0.2
    
    # Animation speeds
    ANIMATION_SPEED = 0.1
    ANIMATION_TIMER_MULTIPLIER = 0.25
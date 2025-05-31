"""
Refactored Game Engine Entry Point
Now uses dynamic configuration system
"""
import sys
from engine.core.simple_game_engine import SimpleGameEngine
from engine.core.game_initializer import GameInitializer
from config.game_args import parse_game_arguments
from config.game_loader import GameConfigLoader

def main():
    """Main entry point for the game"""
    # Parse command line arguments
    print("Parsing command line arguments...")
    args = parse_game_arguments()
    
    # Initialize game configuration loader
    config_loader = GameConfigLoader()
    
    # Handle list games command
    if args.list_games:
        print("\nAvailable game configurations:")
        for game_name in config_loader.list_available_games():
            info = config_loader.get_game_info(game_name)
            print(f"  {game_name}:")
            print(f"    Name: {info['name']}")
            print(f"    Description: {info['description']}")
            print(f"    World Size: {info['world_size']}")
            print(f"    Entities: {info['entity_count']}")
            print(f"    Systems: {info['system_count']}")
            print()
        return
    
    # Load game configuration
    try:
        print(f"Loading game configuration: {args.game_config}")
        game_config = config_loader.get_game_config(args.game_config)
        print(f"Loaded: {game_config.name}")
        print(f"Description: {game_config.description}")
    except Exception as e:
        print(f"Error loading game configuration: {e}")
        print(f"Available configurations: {config_loader.list_available_games()}")
        sys.exit(1)
    
    # Create the main game engine
    engine = SimpleGameEngine(
        title="Hoomans", 
        width=args.width, 
        height=args.height, 
        map_seed=args.seed
    )
    
    # Initialize game using configuration
    initializer = GameInitializer(engine)
    
    # Register custom post-initialization hooks
    initializer.register_hook("finalize_world_items", _finalize_world_items)
    initializer.register_hook("initialize_npc_exploration", _initialize_npc_exploration)
    
    # Initialize the game
    initializer.initialize_game(game_config, args)
    
    # Set game state based on arguments
    if args.skip_menu:
        from engine.core.game_state_manager import GameState
        game_state = GameState()
        engine.game_state = game_state.RUNNING
        engine.load_item_icons()
    else:
        from engine.core.game_state_manager import GameState
        game_state = GameState()
        engine.game_state = game_state.MAIN_MENU
    
    # Handle display mode arguments
    if args.fullscreen:
        engine.toggle_fullscreen()
    elif args.borderless:
        engine.toggle_borderless_fullscreen()
    
    # Start the main game loop
    print("Starting game loop...")
    engine.run()

def _finalize_world_items(config, args):
    """Custom hook to finalize world items"""
    engine = SimpleGameEngine.instance
    
    if hasattr(engine, 'world_map') and engine.world_map:
        # Update and save world items
        if hasattr(engine.world_map, 'world_item_manager'):
            engine.world_map.update_world_items()
        
        # Save world items to cache periodically
        if hasattr(engine, 'world_cache') and engine.world_cache:
            engine.world_map.world_item_manager.save_to_cache(engine.world_cache)
        
        # Load world items from cache if available
        if hasattr(engine, 'world_cache') and engine.world_cache:
            engine.world_map.world_item_manager.load_from_cache(engine.world_cache)
        
        print("World items finalized and cached")

def _initialize_npc_exploration(config, args):
    """Custom hook to initialize NPC exploration attributes"""
    engine = SimpleGameEngine.instance
    
    if hasattr(engine, 'entity_manager') and engine.entity_manager:
        print("Initializing NPC exploration attributes...")
        engine.entity_manager.initialize_all_npc_exploration_attributes()
        print("NPC exploration attributes initialized")

if __name__ == "__main__":
    main()

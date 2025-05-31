"""
Enhanced Game Arguments Parser
"""
import argparse

def parse_game_arguments():
    """Parse command line arguments with game configuration support"""
    parser = argparse.ArgumentParser(description='Hoomans Game Engine')
    
    # Display options
    parser.add_argument('--width', type=int, default=1024, help='Window width')
    parser.add_argument('--height', type=int, default=768, help='Window height')
    parser.add_argument('--fullscreen', action='store_true', help='Start in fullscreen mode')
    parser.add_argument('--borderless', action='store_true', help='Start in borderless fullscreen mode')
    
    # Game options
    parser.add_argument('--seed', type=int, help='World generation seed')
    parser.add_argument('--skip-menu', action='store_true', help='Skip main menu and start game directly')
    parser.add_argument('--game-config', type=str, default='default', 
                       help='Game configuration to use (default, minimal, survival, or custom)')
    
    # Debug options
    parser.add_argument('--map-debug', action='store_true', help='Enable map debug mode')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI Universe Controller')
    
    # List available configurations
    parser.add_argument('--list-games', action='store_true', help='List available game configurations')
    
    return parser.parse_args()

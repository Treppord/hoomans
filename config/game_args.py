"""
Game command line arguments configuration
Centralizes all argument parsing to reduce clutter in main game_engine.py
"""
import argparse

class GameArgumentParser:
    """Handles all command line argument parsing for the game"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Hoomans - A Grid-Based RPG Game',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python game_engine.py --seed 42 --fullscreen
  python game_engine.py --width 1920 --height 1080 --skip-menu
  python game_engine.py --seed 123 --borderless
            """
        )
        self._setup_arguments()
    
    def _setup_arguments(self):
        """Set up all command line arguments"""
        
        # World Generation Arguments
        world_group = self.parser.add_argument_group('World Generation')
        world_group.add_argument(
            '--seed', 
            type=int, 
            default=39,
            help='Seed for map generation (default: 39)'
        )
        
        # Display Arguments
        display_group = self.parser.add_argument_group('Display Options')
        display_group.add_argument(
            '--fullscreen', 
            action='store_true', 
            help='Start in fullscreen mode'
        )
        display_group.add_argument(
            '--borderless', 
            action='store_true', 
            help='Start in borderless fullscreen mode'
        )
        display_group.add_argument(
            '--width', 
            type=int, 
            default=800, 
            help='Window width in pixels (default: 800)'
        )
        display_group.add_argument(
            '--height', 
            type=int, 
            default=600, 
            help='Window height in pixels (default: 600)'
        )
        
        # Game Flow Arguments
        flow_group = self.parser.add_argument_group('Game Flow')
        flow_group.add_argument(
            '--skip-menu', 
            action='store_true', 
            help='Skip main menu and start game directly'
        )
        
        # Debug Arguments
        debug_group = self.parser.add_argument_group('Debug Options')
        debug_group.add_argument(
            '--debug', 
            action='store_true', 
            help='Enable debug mode with additional logging'
        )
        debug_group.add_argument(
            '--no-ai', 
            action='store_true', 
            help='Disable AI Universe Controller for testing'
        )
        debug_group.add_argument(
            '--map-debug', 
            action='store_true', 
            help='Enable map generation debug visualization'
        )
        
        # Performance Arguments
        perf_group = self.parser.add_argument_group('Performance')
        perf_group.add_argument(
            '--fps', 
            type=int, 
            default=60, 
            help='Target FPS (default: 60)'
        )
        perf_group.add_argument(
            '--vsync', 
            action='store_true', 
            help='Enable vertical sync'
        )
    
    def parse_args(self):
        """Parse and return command line arguments"""
        args = self.parser.parse_args()
        
        # Validate arguments
        self._validate_args(args)
        
        return args
    
    def _validate_args(self, args):
        """Validate parsed arguments"""
        # Validate display dimensions
        if args.width < 400:
            self.parser.error("Window width must be at least 400 pixels")
        if args.height < 300:
            self.parser.error("Window height must be at least 300 pixels")
        
        # Validate FPS
        if args.fps < 1 or args.fps > 300:
            self.parser.error("FPS must be between 1 and 300")
        
        # Validate seed
        if args.seed < 0:
            self.parser.error("Seed must be a positive integer")
        
        # Check for conflicting display options
        if args.fullscreen and args.borderless:
            self.parser.error("Cannot use both --fullscreen and --borderless")
    
    def print_args_summary(self, args):
        """Print a summary of the parsed arguments"""
        print("=== Game Configuration ===")
        print(f"Seed: {args.seed}")
        print(f"Display: {args.width}x{args.height}")
        if args.fullscreen:
            print("Mode: Fullscreen")
        elif args.borderless:
            print("Mode: Borderless Fullscreen")
        else:
            print("Mode: Windowed")
        print(f"FPS Target: {args.fps}")
        print(f"Skip Menu: {args.skip_menu}")
        print(f"Debug Mode: {args.debug}")
        print(f"AI Disabled: {args.no_ai}")
        print(f"Map Debug: {args.map_debug}")
        print("=" * 27)

# Convenience function for easy importing
def parse_game_arguments():
    """Parse game arguments and return the result"""
    parser = GameArgumentParser()
    args = parser.parse_args()
    
    # Print summary if debug mode is enabled
    if args.debug:
        parser.print_args_summary(args)
    
    return args
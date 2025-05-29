"""
Sound Manager - Handles all audio in the game
"""

import pygame
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SoundManager:
    """Manages all sound effects and music in the game"""
    
    def __init__(self, master_volume=0.7, sfx_volume=0.8, music_volume=0.6):
        """Initialize the sound manager"""
        self.master_volume = master_volume
        self.sfx_volume = sfx_volume
        self.music_volume = music_volume
        
        # Sound storage
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_tracks: Dict[str, str] = {}  # name -> file path
        
        # State
        self.sound_enabled = True
        self.music_enabled = True
        self.current_music = None
        self.music_paused = False
        
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                print("Sound system initialized")
            except pygame.error as e:
                print(f"Could not initialize sound system: {e}")
                self.sound_enabled = False
                return
        
        # Load all sounds
        self._load_sounds()
        self._load_music()
        
    def _load_music(self):
        """Load all music files from the assets directory"""
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        music_dir = os.path.join(project_root, "assets", "music")
        
        if not os.path.exists(music_dir):
            print(f"Music directory not found: {music_dir}")
            os.makedirs(music_dir, exist_ok=True)
            print(f"Created music directory: {music_dir}")
            return
        
        # Define music mappings
        music_files = {
            "track_main": "track_main.wav",
            "track_game": "track_game.wav",
        }
        
        # Load each music file
        for music_name, filename in music_files.items():
            file_path = os.path.join(music_dir, filename)
            
            if os.path.exists(file_path):
                self.music_tracks[music_name] = file_path
                print(f"Loaded music track: {music_name} from {filename}")
            else:
                print(f"Music file not found: {file_path}")
        
        print(f"Sound manager loaded {len(self.music_tracks)} music tracks")
    
    def _load_sounds(self):
        """Load all sound files from the assets directory"""
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sound_dir = os.path.join(project_root, "assets", "sound")
        
        if not os.path.exists(sound_dir):
            print(f"Sound directory not found: {sound_dir}")
            return
        
        # Define sound mappings
        sound_files = {
            "click": "click.wav",
            "confirm": "confirm.wav",
            # Add more sounds here as you create them
            "menu_hover": "hover.wav",  # Reuse click for now
            "error": "click.wav",  # Placeholder
            "success": "confirm.wav",  # Reuse confirm
            "eat": "eat.wav",
            "drink": "drink.wav",
            "walk": "walk.wav",
        }
        
        # Load each sound file
        for sound_name, filename in sound_files.items():
            file_path = os.path.join(sound_dir, filename)
            
            if os.path.exists(file_path):
                try:
                    sound = pygame.mixer.Sound(file_path)
                    self.sounds[sound_name] = sound
                    print(f"Loaded sound: {sound_name} from {filename}")
                except pygame.error as e:
                    print(f"Could not load sound {filename}: {e}")
            else:
                print(f"Sound file not found: {file_path}")
        
        print(f"Sound manager loaded {len(self.sounds)} sounds")
    
    def play_sound(self, sound_name: str, volume: Optional[float] = None):
        """Play a sound effect"""
        if not self.sound_enabled or sound_name not in self.sounds:
            return
        
        try:
            sound = self.sounds[sound_name]
            
            # Calculate final volume
            final_volume = self.master_volume * self.sfx_volume
            if volume is not None:
                final_volume *= volume
            
            # Set volume and play
            sound.set_volume(final_volume)
            sound.play()
            
        except pygame.error as e:
            print(f"Error playing sound {sound_name}: {e}")
    
    def play_ui_click(self):
        """Play UI click sound"""
        self.play_sound("click")
        
    
    def play_ui_confirm(self):
        """Play UI confirm sound"""
        self.play_sound("confirm")
    
    def play_ui_hover(self):
        """Play UI hover sound"""
        self.play_sound("menu_hover", volume=0.5)  # Quieter hover sound
    
    def play_error(self):
        """Play error sound"""
        self.play_sound("error")
    
    def play_success(self):
        """Play success sound"""
        self.play_sound("success")
        
    def play_eat_sound(self):
        """Play eating sound"""
        self.play_sound("eat")
        
    def play_drink_sound(self):
        """Play drinking sound"""
        self.play_sound("drink")
        
    def play_walk_sound(self):
        """Play walking sound"""
        self.play_sound("walk")
    
    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))
        # Update current music volume if playing
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self.master_volume * self.music_volume)
        print(f"Master volume set to {self.master_volume}")
    
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))
        print(f"SFX volume set to {self.sfx_volume}")
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self.master_volume * self.music_volume)
        print(f"Music volume set to {self.music_volume}")
    
    def toggle_sound(self):
        """Toggle sound effects on/off"""
        self.sound_enabled = not self.sound_enabled
        print(f"Sound effects {'enabled' if self.sound_enabled else 'disabled'}")
        return self.sound_enabled
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_enabled = not self.music_enabled
        
        if not self.music_enabled and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.music_paused = True
        elif self.music_enabled and self.music_paused:
            pygame.mixer.music.unpause()
            self.music_paused = False
        
        print(f"Music {'enabled' if self.music_enabled else 'disabled'}")
        return self.music_enabled
    
    def play_music(self, name: str, loops: int = -1, fade_in: int = 0):
        """Play a music track"""
        if not self.music_enabled or name not in self.music_tracks:
            print(f"Cannot play music: enabled={self.music_enabled}, track_exists={name in self.music_tracks}")
            return
        
        # Don't restart the same track
        if self.current_music == name and pygame.mixer.music.get_busy():
            print(f"Music track {name} is already playing")
            return
        
        try:
            music_path = self.music_tracks[name]
            pygame.mixer.music.load(music_path)
            
            # Set volume
            pygame.mixer.music.set_volume(self.master_volume * self.music_volume)
            
            # Play music
            if fade_in > 0:
                pygame.mixer.music.play(loops, fade_ms=fade_in)
            else:
                pygame.mixer.music.play(loops)
            
            self.current_music = name
            self.music_paused = False
            print(f"Playing music: {name}")
            
        except pygame.error as e:
            print(f"Error playing music {name}: {e}")
    
    def stop_music(self, fade_out: int = 0):
        """Stop the current music"""
        if pygame.mixer.music.get_busy():
            if fade_out > 0:
                pygame.mixer.music.fadeout(fade_out)
            else:
                pygame.mixer.music.stop()
            
            self.current_music = None
            self.music_paused = False
            print("Music stopped")
    
    def pause_music(self):
        """Pause the current music"""
        if pygame.mixer.music.get_busy() and not self.music_paused:
            pygame.mixer.music.pause()
            self.music_paused = True
            print("Music paused")
    
    def resume_music(self):
        """Resume paused music"""
        if self.music_paused:
            pygame.mixer.music.unpause()
            self.music_paused = False
            print("Music resumed")
    
    def is_music_playing(self):
        """Check if music is currently playing"""
        return pygame.mixer.music.get_busy() and not self.music_paused
    
    def get_volume_settings(self):
        """Get current volume settings"""
        return {
            "master": self.master_volume,
            "sfx": self.sfx_volume,
            "music": self.music_volume,
            "sound_enabled": self.sound_enabled,
            "music_enabled": self.music_enabled
        }
    
    
    def _load_music(self):
        """Load all music files from the assets directory"""
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        music_dir = os.path.join(project_root, "assets", "music")
        
        if not os.path.exists(music_dir):
            print(f"Music directory not found: {music_dir}")
            os.makedirs(music_dir, exist_ok=True)
            print(f"Created music directory: {music_dir}")
            return
        
        # Define music mappings
        music_files = {
            "track_main": "track_main.wav",
            "track_game": "track_game.wav",
        }
        
        # Load each music file
        for music_name, filename in music_files.items():
            file_path = os.path.join(music_dir, filename)
            
            if os.path.exists(file_path):
                self.music_tracks[music_name] = file_path
                print(f"Loaded music track: {music_name} from {filename}")
            else:
                print(f"Music file not found: {file_path}")
        
        print(f"Sound manager loaded {len(self.music_tracks)} music tracks")
    
    
    
    
    def apply_volume_settings(self, settings: dict):
        """Apply volume settings from a dictionary"""
        if "master" in settings:
            self.set_master_volume(settings["master"])
        if "sfx" in settings:
            self.set_sfx_volume(settings["sfx"])
        if "music" in settings:
            self.set_music_volume(settings["music"])
        if "sound_enabled" in settings:
            self.sound_enabled = settings["sound_enabled"]
        if "music_enabled" in settings:
            self.music_enabled = settings["music_enabled"]
    
    def cleanup(self):
        """Clean up sound resources"""
        try:
            pygame.mixer.music.stop()
            for sound in self.sounds.values():
                sound.stop()
            print("Sound manager cleaned up")
        except:
            pass

# Global sound manager instance
_sound_manager = None

def get_sound_manager() -> SoundManager:
    """Get the global sound manager instance"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager

def initialize_sound_manager(**kwargs) -> SoundManager:
    """Initialize the global sound manager with custom settings"""
    global _sound_manager
    _sound_manager = SoundManager(**kwargs)
    return _sound_manager
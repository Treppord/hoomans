"""Enhanced Stats panel UI element with modern cozy aesthetic"""
import pygame
import math
import os
from engine.ui.elements.base import UIElement
from engine.ui.constants.colors import (
    STATS_PANEL_BG, STATS_PANEL_BORDER, STATS_PANEL_INNER_BG,
    HEALTH_FULL, HEALTH_HIGH, HEALTH_MID, HEALTH_LOW, HEALTH_EMPTY, HEALTH_BG,
    HUNGER_FULL, HUNGER_HIGH, HUNGER_MID, HUNGER_LOW, HUNGER_EMPTY, HUNGER_BG,
    THIRST_FULL, THIRST_HIGH, THIRST_MID, THIRST_LOW, THIRST_EMPTY, THIRST_BG,
    ICON_HEALTH_COLOR, ICON_HUNGER_COLOR, ICON_THIRST_COLOR, ICON_BORDER_COLOR,
    ACCENT_GLOW, WARM_WHITE, COZY_SHADOW
)

class StatsPanel(UIElement):
    """Enhanced panel that displays player stats with modern cozy aesthetic"""
    
    def __init__(self, x, y, width, height, data_manager):
        super().__init__(x, y, width, height)
        self.data_manager = data_manager
        self.background_color = STATS_PANEL_BG
        
        # Enhanced styling
        self.border_radius = 12
        self.inner_padding = 16
        self.stat_spacing = 20
        self.icon_size = 16
        self.bar_width = 80
        self.bar_height = 8
        self.bar_border_radius = 4
        
        # Animation properties
        self.pulse_timer = 0
        self.low_health_pulse = False
        
        # Font setup
        try:
            self.font = pygame.font.Font("assets/font/CandC_LAN.ttf", 18)
            self.small_font = pygame.font.Font("assets/font/CandC_LAN.ttf", 14)
        except:
            self.font = pygame.font.Font(None, 18)
            self.small_font = pygame.font.Font(None, 14)
        
        # Load stat icons
        self.stat_icons = {}
        self._load_stat_icons()
    
    def _load_stat_icons(self):
        """Load stat icons from assets/ui/ directory"""
        # Method 1: Try to find the project root by looking for game_engine.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = None
        
        # Walk up the directory tree to find the root (where game_engine.py is)
        search_dir = current_dir
        for _ in range(10):  # Limit search to prevent infinite loop
            if os.path.exists(os.path.join(search_dir, "game_engine.py")):
                project_root = search_dir
                break
            parent_dir = os.path.dirname(search_dir)
            if parent_dir == search_dir:  # Reached filesystem root
                break
            search_dir = parent_dir
        
        # Method 2: Fallback - assume we're in engine/ui/panels/ and go up 3 levels
        if not project_root:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        
        ui_assets_path = os.path.join(project_root, "assets", "ui")
        
        print(f"DEBUG: Project root detected as: {project_root}")
        print(f"DEBUG: Looking for stat icons in: {ui_assets_path}")
        print(f"DEBUG: Assets directory exists: {os.path.exists(os.path.join(project_root, 'assets'))}")
        print(f"DEBUG: UI assets directory exists: {os.path.exists(ui_assets_path)}")
        
        # Define icon files to load
        icon_files = {
            "health": "health.png",
            "hunger": "hunger.png", 
            "thirst": "thirst.png"
        }
        
        # Load each icon
        for stat_type, filename in icon_files.items():
            icon_path = os.path.join(ui_assets_path, filename)
            
            try:
                if os.path.exists(icon_path):
                    # Load and scale the icon to the desired size
                    icon = pygame.image.load(icon_path).convert_alpha()
                    icon = pygame.transform.scale(icon, (self.icon_size, self.icon_size))
                    self.stat_icons[stat_type] = icon
                    print(f"SUCCESS: Loaded stat icon: {stat_type} from {icon_path}")
                else:
                    print(f"WARNING: Stat icon file not found: {icon_path}")
                    # List what files ARE in the directory
                    if os.path.exists(ui_assets_path):
                        files_in_dir = os.listdir(ui_assets_path)
                        print(f"DEBUG: Files in {ui_assets_path}: {files_in_dir}")
                    else:
                        print(f"DEBUG: Directory {ui_assets_path} does not exist")
                    
                    # Create fallback placeholder
                    self.stat_icons[stat_type] = self._create_fallback_icon(stat_type)
            except Exception as e:
                print(f"ERROR loading stat icon {stat_type}: {e}")
                # Create fallback placeholder
                self.stat_icons[stat_type] = self._create_fallback_icon(stat_type)

    
    def _create_fallback_icon(self, stat_type):
        """Create a fallback icon if the file doesn't exist"""
        icon = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
        
        # Get color based on stat type
        if stat_type == "health":
            color = ICON_HEALTH_COLOR
        elif stat_type == "hunger":
            color = ICON_HUNGER_COLOR
        elif stat_type == "thirst":
            color = ICON_THIRST_COLOR
        else:
            color = WARM_WHITE
        
        # Soft rounded background
        pygame.draw.rect(icon, (*color, 200), (0, 0, self.icon_size, self.icon_size), border_radius=3)
        pygame.draw.rect(icon, ICON_BORDER_COLOR, (0, 0, self.icon_size, self.icon_size), width=1, border_radius=3)
        
        # Icon-specific shapes (placeholders for missing files)
        center_x, center_y = self.icon_size // 2, self.icon_size // 2
        
        if stat_type == "health":
            # Heart shape placeholder
            pygame.draw.circle(icon, WARM_WHITE, (center_x - 2, center_y - 1), 3)
            pygame.draw.circle(icon, WARM_WHITE, (center_x + 2, center_y - 1), 3)
            pygame.draw.polygon(icon, WARM_WHITE, [
                (center_x - 5, center_y),
                (center_x, center_y + 5),
                (center_x + 5, center_y),
                (center_x + 3, center_y - 2),
                (center_x - 3, center_y - 2)
            ])
        elif stat_type == "hunger":
            # Apple/food shape placeholder
            pygame.draw.circle(icon, WARM_WHITE, (center_x, center_y + 1), 4)
            pygame.draw.rect(icon, WARM_WHITE, (center_x - 1, center_y - 4, 2, 3))
            pygame.draw.polygon(icon, WARM_WHITE, [
                (center_x + 1, center_y - 4),
                (center_x + 3, center_y - 5),
                (center_x + 2, center_y - 2)
            ])
        elif stat_type == "thirst":
            # Water drop shape placeholder
            pygame.draw.circle(icon, WARM_WHITE, (center_x, center_y + 2), 4)
            pygame.draw.polygon(icon, WARM_WHITE, [
                (center_x, center_y - 4),
                (center_x - 3, center_y + 1),
                (center_x + 3, center_y + 1)
            ])
        
        return icon
    
    def _create_icon_placeholder(self, color, icon_type):
        """Create a 16x16 placeholder icon with modern styling - DEPRECATED"""
        # This method is now deprecated in favor of loading actual icon files
        # Return the loaded icon or fallback
        return self.stat_icons.get(icon_type, self._create_fallback_icon(icon_type))
    
    def _get_stat_color(self, value, max_value, stat_type):
        """Get color based on stat value and type"""
        percentage = value / max_value if max_value > 0 else 0
        
        if stat_type == "health":
            if percentage > 0.7:
                return HEALTH_FULL
            elif percentage > 0.4:
                return HEALTH_HIGH
            elif percentage > 0.2:
                return HEALTH_MID
            else:
                return HEALTH_LOW
        elif stat_type == "hunger":
            if percentage > 0.7:
                return HUNGER_FULL
            elif percentage > 0.4:
                return HUNGER_HIGH
            elif percentage > 0.2:
                return HUNGER_MID
            else:
                return HUNGER_LOW
        elif stat_type == "thirst":
            if percentage > 0.7:
                return THIRST_FULL
            elif percentage > 0.4:
                return THIRST_HIGH
            elif percentage > 0.2:
                return THIRST_MID
            else:
                return THIRST_LOW
        
        return WARM_WHITE
    
    def _draw_modern_bar(self, surface, x, y, value, max_value, stat_type):
        """Draw a modern, cozy-styled progress bar"""
        # Background bar with subtle shadow
        shadow_rect = pygame.Rect(x + 1, y + 1, self.bar_width, self.bar_height)
        pygame.draw.rect(surface, COZY_SHADOW, shadow_rect, border_radius=self.bar_border_radius)
        
        # Background bar
        bg_color = HEALTH_BG if stat_type == "health" else (HUNGER_BG if stat_type == "hunger" else THIRST_BG)
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(surface, bg_color, bg_rect, border_radius=self.bar_border_radius)
        
        # Fill bar
        if value > 0 and max_value > 0:
            fill_width = int((value / max_value) * self.bar_width)
            if fill_width > 0:
                fill_rect = pygame.Rect(x, y, fill_width, self.bar_height)
                fill_color = self._get_stat_color(value, max_value, stat_type)
                pygame.draw.rect(surface, fill_color, fill_rect, border_radius=self.bar_border_radius)
                
                # Subtle highlight on top of bar
                if fill_width > 2:
                    highlight_rect = pygame.Rect(x + 1, y + 1, fill_width - 2, 2)
                    highlight_color = (*fill_color[:3], 100)
                    pygame.draw.rect(surface, highlight_color, highlight_rect, border_radius=1)
        
        # Subtle border
        pygame.draw.rect(surface, ICON_BORDER_COLOR, bg_rect, width=1, border_radius=self.bar_border_radius)
    
    def _draw_segmented_display(self, surface, x, y, value, max_value, stat_type):
        """Alternative: Draw segmented orb-style display"""
        segments = 10  # Total segments
        segment_width = 6
        segment_height = 8
        segment_spacing = 2
        
        filled_segments = int((value / max_value) * segments) if max_value > 0 else 0
        
        for i in range(segments):
            seg_x = x + i * (segment_width + segment_spacing)
            seg_y = y
            
            # Create rounded segment
            segment_rect = pygame.Rect(seg_x, seg_y, segment_width, segment_height)
            
            if i < filled_segments:
                # Filled segment
                color = self._get_stat_color(value, max_value, stat_type)
                pygame.draw.rect(surface, color, segment_rect, border_radius=2)
                # Highlight
                highlight_rect = pygame.Rect(seg_x + 1, seg_y + 1, segment_width - 2, 2)
                pygame.draw.rect(surface, (*color[:3], 150), highlight_rect, border_radius=1)
            else:
                # Empty segment
                empty_color = HEALTH_EMPTY if stat_type == "health" else (HUNGER_EMPTY if stat_type == "hunger" else THIRST_EMPTY)
                pygame.draw.rect(surface, empty_color, segment_rect, border_radius=2)
            
            # Subtle border
            pygame.draw.rect(surface, ICON_BORDER_COLOR, segment_rect, width=1, border_radius=2)
    

    
    def update(self, delta_time=1/60):
        """Update animations"""
        self.pulse_timer += delta_time * 3  # Pulse speed
        
        # Check for low health pulse
        health = self.data_manager.get_player_stat("health")
        if health and health.value <= health.max_value * 0.2:
            self.low_health_pulse = True
        else:
            self.low_health_pulse = False
    
    def render(self, screen):
        """Render the enhanced stats panel"""
        if not self.visible:
            return
        
        # Update animations
        self.update()
        
        # Create main panel surface with alpha
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw soft shadow
        shadow_rect = pygame.Rect(2, 2, self.width - 2, self.height - 2)
        pygame.draw.rect(panel_surface, COZY_SHADOW, shadow_rect, border_radius=self.border_radius)
        
        # Draw main background with rounded corners
        main_rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(panel_surface, self.background_color, main_rect, border_radius=self.border_radius)
        
        # Draw subtle inner background
        inner_rect = pygame.Rect(4, 4, self.width - 8, self.height - 8)
        pygame.draw.rect(panel_surface, STATS_PANEL_INNER_BG, inner_rect, border_radius=self.border_radius - 2)
        
        # Draw border with subtle glow effect
        pygame.draw.rect(panel_surface, STATS_PANEL_BORDER, main_rect, width=2, border_radius=self.border_radius)
        
        # Add subtle accent glow - Fix color format
        try:
            # Ensure ACCENT_GLOW is a valid RGB tuple
            if isinstance(ACCENT_GLOW, (tuple, list)) and len(ACCENT_GLOW) >= 3:
                # Extract RGB values and ensure they're integers
                r, g, b = int(ACCENT_GLOW[0]), int(ACCENT_GLOW[1]), int(ACCENT_GLOW[2])
                # Clamp values to valid range
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                accent_color = (r, g, b, 30)  # Add alpha
            else:
                # Fallback to a safe default color
                accent_color = (100, 150, 200, 30)  # Light blue with alpha
            
            glow_rect = pygame.Rect(1, 1, self.width - 2, self.height - 2)
            pygame.draw.rect(panel_surface, accent_color, glow_rect, width=1, border_radius=self.border_radius - 1)
        except Exception as e:
            # If there's any issue with the accent glow, skip it
            print(f"Warning: Could not draw accent glow: {e}")
        
        # Starting position for stats
        current_y = self.inner_padding
        
        # Get player stats
        health = self.data_manager.get_player_stat("health")
        hunger = self.data_manager.get_player_stat("hunger") 
        thirst = self.data_manager.get_player_stat("thirst")
        
        # Draw stats with loaded icons
        if health:
            current_y = self._draw_stat_row(
                panel_surface, 
                self.inner_padding, 
                current_y,
                "Health", 
                health.value, 
                health.max_value, 
                ICON_HEALTH_COLOR,
                "health"
            )
            current_y += self.stat_spacing - 4  # Adjust spacing
        
        if hunger:
            current_y = self._draw_stat_row(
                panel_surface, 
                self.inner_padding, 
                current_y,
                "Hunger", 
                hunger.value, 
                hunger.max_value, 
                ICON_HUNGER_COLOR,
                "hunger"
            )
            current_y += self.stat_spacing - 4  # Adjust spacing
        
        if thirst:
            current_y = self._draw_stat_row(
                panel_surface, 
                self.inner_padding, 
                current_y,
                "Thirst", 
                thirst.value, 
                thirst.max_value, 
                ICON_THIRST_COLOR,
                "thirst"
            )
        
        # Blit the panel to the main screen
        screen.blit(panel_surface, (self.x, self.y))
    
    def _draw_stat_row(self, surface, x, y, stat_name, value, max_value, icon_color, stat_type):
        """Draw a complete stat row with icon and visual indicator"""
        # Draw the loaded icon (or fallback)
        icon = self.stat_icons.get(stat_type)
        if icon:
            # Apply color tint if needed for low health pulse
            if stat_type == "health" and self.low_health_pulse:
                # Create a tinted version for pulsing effect
                pulse_intensity = (math.sin(self.pulse_timer) + 1) * 0.3 + 0.4
                tinted_icon = icon.copy()
                # Safe color tinting
                try:
                    if isinstance(ICON_HEALTH_COLOR, (tuple, list)) and len(ICON_HEALTH_COLOR) >= 3:
                        r, g, b = int(ICON_HEALTH_COLOR[0]), int(ICON_HEALTH_COLOR[1]), int(ICON_HEALTH_COLOR[2])
                        tint_color = (r, g, b, int(255 * pulse_intensity))
                        tinted_icon.fill(tint_color, special_flags=pygame.BLEND_RGBA_MULT)
                    surface.blit(tinted_icon, (x, y))
                except Exception:
                    # If tinting fails, just draw the normal icon
                    surface.blit(icon, (x, y))
            else:
                surface.blit(icon, (x, y))
        else:
            # Fallback to old method if no icon loaded
            fallback_icon = self._create_fallback_icon(stat_type)
            surface.blit(fallback_icon, (x, y))
        
        # Position for the visual indicator
        indicator_x = x + self.icon_size + 8
        indicator_y = y + (self.icon_size - self.bar_height) // 2
        
        # Draw the progress bar
        self._draw_modern_bar(surface, indicator_x, indicator_y, value, max_value, stat_type)
        
        # Optional: Draw numeric value (small and subtle) - Fix color format
        value_text = f"{value}/{max_value}"
        try:
            # Safe color handling for text
            if isinstance(WARM_WHITE, (tuple, list)) and len(WARM_WHITE) >= 3:
                r, g, b = int(WARM_WHITE[0]), int(WARM_WHITE[1]), int(WARM_WHITE[2])
                text_color = (r, g, b)
            else:
                text_color = (255, 255, 255)  # Fallback to white
            
            text_surface = self.small_font.render(value_text, True, text_color)
            text_x = indicator_x + self.bar_width + 6
            text_y = y + (self.icon_size - text_surface.get_height()) // 2
            surface.blit(text_surface, (text_x, text_y))
        except Exception as e:
            print(f"Warning: Could not render stat text: {e}")
        
        return y + self.icon_size + 4  # Return next Y position
    
    def _draw_modern_bar(self, surface, x, y, value, max_value, stat_type):
        """Draw a modern, cozy-styled progress bar"""
        # Background bar with subtle shadow
        shadow_rect = pygame.Rect(x + 1, y + 1, self.bar_width, self.bar_height)
        pygame.draw.rect(surface, COZY_SHADOW, shadow_rect, border_radius=self.bar_border_radius)
        
        # Background bar
        bg_color = HEALTH_BG if stat_type == "health" else (HUNGER_BG if stat_type == "hunger" else THIRST_BG)
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(surface, bg_color, bg_rect, border_radius=self.bar_border_radius)
        
        # Fill bar
        if value > 0 and max_value > 0:
            fill_width = int((value / max_value) * self.bar_width)
            if fill_width > 0:
                fill_rect = pygame.Rect(x, y, fill_width, self.bar_height)
                fill_color = self._get_stat_color(value, max_value, stat_type)
                pygame.draw.rect(surface, fill_color, fill_rect, border_radius=self.bar_border_radius)
                
                # Subtle highlight on top of bar - Fix color format
                if fill_width > 2:
                    highlight_rect = pygame.Rect(x + 1, y + 1, fill_width - 2, 2)
                    try:
                        if isinstance(fill_color, (tuple, list)) and len(fill_color) >= 3:
                            r, g, b = int(fill_color[0]), int(fill_color[1]), int(fill_color[2])
                            highlight_color = (r, g, b, 100)
                        else:
                            highlight_color = (255, 255, 255, 100)
                        pygame.draw.rect(surface, highlight_color, highlight_rect, border_radius=1)
                    except Exception:
                        # Skip highlight if there's an issue
                        pass
        
        # Subtle border
        pygame.draw.rect(surface, ICON_BORDER_COLOR, bg_rect, width=1, border_radius=self.bar_border_radius)

"""Enhanced Stats panel UI element with modern cozy aesthetic"""
import pygame
import math
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
    
    def _create_icon_placeholder(self, color, icon_type):
        """Create a 16x16 placeholder icon with modern styling"""
        icon = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
        
        # Soft rounded background
        pygame.draw.rect(icon, (*color, 200), (0, 0, self.icon_size, self.icon_size), border_radius=3)
        pygame.draw.rect(icon, ICON_BORDER_COLOR, (0, 0, self.icon_size, self.icon_size), width=1, border_radius=3)
        
        # Icon-specific shapes (placeholders for future pixel art)
        center_x, center_y = self.icon_size // 2, self.icon_size // 2
        
        if icon_type == "health":
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
        elif icon_type == "hunger":
            # Apple/food shape placeholder
            pygame.draw.circle(icon, WARM_WHITE, (center_x, center_y + 1), 4)
            pygame.draw.rect(icon, WARM_WHITE, (center_x - 1, center_y - 4, 2, 3))
            pygame.draw.polygon(icon, WARM_WHITE, [
                (center_x + 1, center_y - 4),
                (center_x + 3, center_y - 5),
                (center_x + 2, center_y - 2)
            ])
        elif icon_type == "thirst":
            # Water drop shape placeholder
            pygame.draw.circle(icon, WARM_WHITE, (center_x, center_y + 2), 4)
            pygame.draw.polygon(icon, WARM_WHITE, [
                (center_x, center_y - 4),
                (center_x - 3, center_y + 1),
                (center_x + 3, center_y + 1)
            ])
        
        return icon
    
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
    
    def _draw_stat_row(self, surface, x, y, stat_name, value, max_value, icon_color, stat_type):
        """Draw a complete stat row with icon and visual indicator"""
        # Create and draw icon
        icon = self._create_icon_placeholder(icon_color, stat_type)
        surface.blit(icon, (x, y))
        
        # Position for the visual indicator
        indicator_x = x + self.icon_size + 8
        indicator_y = y + (self.icon_size - self.bar_height) // 2
        
        # Draw the progress bar
        self._draw_modern_bar(surface, indicator_x, indicator_y, value, max_value, stat_type)
        
        # Optional: Draw numeric value (small and subtle)
        value_text = f"{value}/{max_value}"
        text_surface = self.small_font.render(value_text, True, (*WARM_WHITE, 180))
        text_x = indicator_x + self.bar_width + 6
        text_y = y + (self.icon_size - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))
        
        return y + self.icon_size + 4  # Return next Y position
    
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
        
        # Draw accent border with glow effect
        pygame.draw.rect(panel_surface, STATS_PANEL_BORDER, main_rect, width=2, border_radius=self.border_radius)
        
        # Optional: Subtle glow effect
        glow_rect = pygame.Rect(-1, -1, self.width + 2, self.height + 2)
        pygame.draw.rect(panel_surface, ACCENT_GLOW, glow_rect, width=1, border_radius=self.border_radius + 1)
        
        # Get stats from data manager
        health = self.data_manager.get_player_stat("health")
        hunger = self.data_manager.get_player_stat("hunger")
        thirst = self.data_manager.get_player_stat("thirst")
        
        # Starting position for stats
        current_y = self.inner_padding
        
        # Draw each stat row
        if health:
            # Add pulse effect for low health
            health_color = ICON_HEALTH_COLOR
            if self.low_health_pulse:
                pulse_intensity = (math.sin(self.pulse_timer) + 1) * 0.3 + 0.4
                health_color = (*ICON_HEALTH_COLOR[:3], int(255 * pulse_intensity))
            
            current_y = self._draw_stat_row(
                panel_surface, self.inner_padding, current_y,
                "Health", health.value, health.max_value, health_color, "health"
            ) + 6
        
        if hunger:
            current_y = self._draw_stat_row(
                panel_surface, self.inner_padding, current_y,
                "Hunger", hunger.value, hunger.max_value, ICON_HUNGER_COLOR, "hunger"
            ) + 6
        
        if thirst:
            current_y = self._draw_stat_row(
                panel_surface, self.inner_padding, current_y,
                "Thirst", thirst.value, thirst.max_value, ICON_THIRST_COLOR, "thirst"
            )
        
        # Draw the completed panel to the screen
        screen.blit(panel_surface, (self.x, self.y))

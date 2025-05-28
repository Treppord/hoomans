"""Stats panel UI element"""
import pygame
from engine.ui.elements.base import UIElement
from engine.ui.constants.colors import PANEL_BG, TEXT_COLOR

class StatsPanel(UIElement):
    """Panel that displays player stats"""
    def __init__(self, x, y, width, height, data_manager):
        super().__init__(x, y, width, height)
        self.data_manager = data_manager
        self.background_color = PANEL_BG
        self.text_color = TEXT_COLOR
        self.font = pygame.font.Font("assets/font/CandC_LAN.ttf", 24)
        self.padding = 10
        
    def render(self, screen):
        if not self.visible:
            return
        
    # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    
    # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                    (0, 0, self.width, self.height))
    
    # Get stats from data manager
        health = self.data_manager.get_player_stat("health")
        hunger = self.data_manager.get_player_stat("hunger")
        thirst = self.data_manager.get_player_stat("thirst")
    
    # Render text for each stat
        y_offset = self.padding
    
        if health:
            health_text = f"Health: {health.value}/{health.max_value}"
            text_surface = self.font.render(health_text, True, self.text_color)
            panel_surface.blit(text_surface, (self.padding, y_offset))
            y_offset += 30
    
        if hunger:
            hunger_text = f"Hunger: {hunger.value}/{hunger.max_value}"
            text_surface = self.font.render(hunger_text, True, self.text_color)
            panel_surface.blit(text_surface, (self.padding, y_offset))
            y_offset += 30
    
        if thirst:
            thirst_text = f"Thirst: {thirst.value}/{thirst.max_value}"
            text_surface = self.font.render(thirst_text, True, self.text_color)
            panel_surface.blit(text_surface, (self.padding, y_offset))
    
    # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))



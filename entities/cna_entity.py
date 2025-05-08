import pygame
from entities.rectangle import Rectangle
from entities.entity_brain import EntityBrain
from cna.cna_format import CNAAttributes, Gender, Culture, Nation
from cna.cna_codec import CNACodec
import random
import os

class CNAEntity(Rectangle):
    """Entity with CNA attributes that influence behavior"""
    
    def __init__(self, grid_x, grid_y, cna_data=None, cna_file=None, color=None, speed=1, controllable=False):
        # Load CNA data if provided
        self.cna_data = cna_data
        
        # If a file is provided but no data, load from file
        if not self.cna_data and cna_file:
            try:
                print(f"Attempting to load CNA from file: {cna_file}")
                self.cna_data = CNACodec.load_from_file(cna_file)
                print(f"Successfully loaded CNA from file: {cna_file}")
            except Exception as e:
                print(f"Error loading CNA file: {e}")
                self.cna_data = None
        
        # If still no data, generate random CNA
        if not self.cna_data:
            try:
                print("Attempting to generate random CNA")
                from cna.cna_generator import CNAGenerator
                self.cna_data = CNAGenerator.generate_random()
                print("Successfully generated random CNA")
            except Exception as e:
                print(f"Error generating random CNA: {e}")
                
                # Create a minimal CNA data object with required attributes
                print("Creating fallback CNA data")
                self.cna_data = CNAAttributes(
                    first_name="Unknown",
                    last_name="Entity",
                    age_minutes=30,
                    gender=Gender.MALE,
                    culture=Culture.RED,
                    nation=Nation.NL,
                    physical_health=3,
                    generational_health=3,
                    mental_health=3
                )
        
        # Double-check that cna_data is not None
        if self.cna_data is None:
            print("WARNING: cna_data is still None after all attempts to create it!")
            # Create emergency fallback
            self.cna_data = CNAAttributes(
                first_name="Emergency",
                last_name="Fallback",
                age_minutes=30,
                gender=Gender.MALE,
                culture=Culture.RED,
                nation=Nation.NL,
                physical_health=3,
                generational_health=3,
                mental_health=3
            )
        
        # Store a copy of cna_data before calling super().__init__
        cna_data_copy = self.cna_data
        
        # Determine color based on CNA if not provided
        if color is None:
            color = self._derive_color_from_cna()
        
        # Call parent class constructor
        super().__init__(grid_x, grid_y, color, speed, controllable)
        
        # Restore cna_data in case it was overwritten
        self.cna_data = cna_data_copy
        
        # Set name from CNA
        self.name = f"{self.cna_data.first_name} {self.cna_data.last_name}"
        
        # Initialize brain
        self.brain = EntityBrain(self)
        
        # Register with universe AI
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'universe_ai'):
            SimpleGameEngine.instance.universe_ai.register_entity(self)
    
    def _derive_color_from_cna(self):
        """Derive entity color from CNA attributes"""
        if not self.cna_data:
            return (255, 0, 0)  # Default red
            
        # Use culture to influence color
        culture_colors = {
            Culture.RED: (200, 50, 50),
            Culture.BLUE: (50, 50, 200)
        }
        
        base_color = culture_colors.get(self.cna_data.culture, (150, 150, 150))
        
        # Adjust based on personality traits
        if hasattr(self.cna_data, 'personality_traits') and len(self.cna_data.personality_traits) >= 3:
            # Use first trait to adjust red
            r_adjust = int(self.cna_data.personality_traits[0] * 100) - 50
            # Use second trait to adjust green
            g_adjust = int(self.cna_data.personality_traits[1] * 100) - 50
            # Use third trait to adjust blue
            b_adjust = int(self.cna_data.personality_traits[2] * 100) - 50
            
            # Apply adjustments with clamping
            r = max(0, min(255, base_color[0] + r_adjust))
            g = max(0, min(255, base_color[1] + g_adjust))
            b = max(0, min(255, base_color[2] + b_adjust))
            
            return (r, g, b)
        
        return base_color
    
    def update(self):
        """Update entity state"""
        super().update()
        
        # Brain updates are handled by the universe AI
    
    def render(self, screen, camera):
        """Render the entity with camera transformations"""
        super().render(screen, camera)
        
        # Render name above entity if zoomed in enough
        if camera.zoom >= 0.75:
            font = pygame.font.SysFont(None, int(16 * camera.zoom))
            name_surface = font.render(self.name, True, (255, 255, 255))
            
            # Calculate position above entity
            name_x, name_y, _, _ = camera.apply(
                self.x + self.width // 2, 
                self.y - 10, 
                0, 0
            )
            
            # Center the name
            name_x -= name_surface.get_width() // 2
            
            # Draw with a dark outline for visibility
            outline_positions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dx, dy in outline_positions:
                screen.blit(name_surface, (name_x + dx, name_y + dy))
                
            screen.blit(name_surface, (name_x, name_y))
    
    def get_info(self):
        """Get information about this entity for UI display"""
        info = [
            f"Name: {self.name}",
            f"Gender: {self.cna_data.gender.name}",
            f"Culture: {self.cna_data.culture.name}",
            f"Nation: {self.cna_data.nation.name}",
            f"Health: {self.cna_data.physical_health}/5",
            f"Intelligence: {self.cna_data.intelligence_factor:.2f}"
        ]
        
        # Add brain state if available
        if hasattr(self, 'brain'):
            info.append("")
            info.append("Needs:")
            for need, value in self.brain.needs.items():
                info.append(f"- {need.name}: {value:.2f}")
                
            info.append("")
            info.append("Recent Memories:")
            for i, memory in enumerate(reversed(self.brain.memories[:3])):
                info.append(f"- {memory['content']}")
        
        return info

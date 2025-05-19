"""Theme manager for handling game visual styles and effects"""
import pygame
import os
import random
import math

class ThemeManager:
    """Manages visual themes, effects, and decorative elements"""
    
    def __init__(self):
        self.theme = "default"
        self.assets = {}
        self.particles = []
        self.ambient_effects = []
        self.background_elements = []
        self.foreground_elements = []
        self.last_particle_time = 0
        self.particle_interval = 100  # ms between particle spawns
        
        # Visual settings
        self.use_ambient_effects = True
        self.use_particles = True
        self.use_decorative_elements = True
        self.use_lighting = True
        
        # Load theme assets
        self.load_assets()
    
    def load_assets(self):
        """Load theme assets like textures, particles, etc."""
        # Get project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Define asset paths
        asset_paths = {
            # Background textures
            "bg_texture": os.path.join(project_root, "assets", "themes", "bg_texture.png"),
            "vignette": os.path.join(project_root, "assets", "themes", "vignette.png"),
            
            # Particles
            "circle": os.path.join(project_root, "assets", "themes", "circle.png"),
            "square": os.path.join(project_root, "assets", "themes", "square.png"),
            "gust": os.path.join(project_root, "assets", "themes", "gust.png"),

            
            # Decorative elements
            "border_corner": os.path.join(project_root, "assets", "themes", "border_corner.png"),
            "border_edge": os.path.join(project_root, "assets", "themes", "border_edge.png"),
        }
        
        # Create assets directory if it doesn't exist
        os.makedirs(os.path.join(project_root, "assets", "themes"), exist_ok=True)
        
        # Load assets or create placeholders
        for name, path in asset_paths.items():
            if os.path.exists(path):
                try:
                    self.assets[name] = pygame.image.load(path).convert_alpha()
                    print(f"Loaded theme asset: {name}")
                except Exception as e:
                    print(f"Error loading {name}: {e}")
                    self.assets[name] = self._create_placeholder(name)
            else:
                print(f"Creating placeholder for missing asset: {name}")
                self.assets[name] = self._create_placeholder(name)
                # Save the placeholder
                pygame.image.save(self.assets[name], path)
    
    def _create_placeholder(self, asset_name):
        """Create a placeholder image for missing assets"""
        if "particle" in asset_name:
            # Create a small particle placeholder
            surface = pygame.Surface((16, 16), pygame.SRCALPHA)
            if "circle" in asset_name:
                pygame.draw.circle(surface, (255, 255, 255, 180), (8, 8), 6)
            else:
                pygame.draw.rect(surface, (255, 255, 255, 180), (4, 4, 8, 8))
            return surface
            
        elif "vignette" in asset_name:
            # Create a vignette effect
            size = 512
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            for y in range(size):
                for x in range(size):
                    # Calculate distance from center (normalized)
                    dx = x / size - 0.5
                    dy = y / size - 0.5
                    distance = math.sqrt(dx*dx + dy*dy) * 2  # *2 to reach corners
                    
                    # Calculate alpha (transparent in center, opaque at edges)
                    alpha = int(min(255, max(0, distance * 255)))
                    
                    # Set pixel color
                    surface.set_at((x, y), (0, 0, 0, alpha))
            return surface
            
        elif "border" in asset_name:
            # Create a border element
            surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            if "corner" in asset_name:
                # Draw a corner element
                pygame.draw.line(surface, (200, 200, 200, 200), (0, 10), (10, 10), 2)
                pygame.draw.line(surface, (200, 200, 200, 200), (10, 0), (10, 10), 2)
            else:
                # Draw an edge element
                pygame.draw.line(surface, (200, 200, 200, 200), (0, 10), (32, 10), 2)
            return surface
            
        else:
            # Default placeholder (checkerboard pattern)
            size = 128
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            square_size = 16
            for y in range(0, size, square_size):
                for x in range(0, size, square_size):
                    color = (100, 100, 100, 50) if (x // square_size + y // square_size) % 2 == 0 else (50, 50, 50, 30)
                    pygame.draw.rect(surface, color, (x, y, square_size, square_size))
            return surface
    
    def add_particle(self, x, y, type="default", lifetime=2.0, size=None, color=None, velocity=None):
        """Add a particle effect at the specified position"""
        if not self.use_particles:
            return
            
        # Default values
        if size is None:
            size = random.uniform(0.5, 1.5)
        if color is None:
            color = (
                random.randint(200, 255),
                random.randint(200, 255),
                random.randint(200, 255),
                random.randint(150, 255)
            )
        if velocity is None:
            velocity = (
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5)
            )
        
        # Create particle
        particle = {
            "x": x,
            "y": y,
            "type": type,
            "size": size,
            "color": color,
            "velocity": velocity,
            "lifetime": lifetime,
            "age": 0,
            "rotation": random.uniform(0, 360),
            "rotation_speed": random.uniform(-2, 2)
        }
        
        self.particles.append(particle)
    
    def update(self, delta_time):
        """Update visual effects"""
        # Update particles
        self._update_particles(delta_time)
        
        # Update ambient effects
        self._update_ambient_effects(delta_time)
        
        # Update decorative elements
        self._update_decorative_elements(delta_time)
    
    def _update_particles(self, delta_time):
        """Update particle effects"""
        # Update existing particles
        for particle in self.particles[:]:
            # Update age
            particle["age"] += delta_time
            
            # Remove expired particles
            if particle["age"] >= particle["lifetime"]:
                self.particles.remove(particle)
                continue
            
            # Update position
            particle["x"] += particle["velocity"][0]
            particle["y"] += particle["velocity"][1]
            
            # Update rotation
            particle["rotation"] += particle["rotation_speed"]
            
            # Fade out over lifetime
            age_factor = particle["age"] / particle["lifetime"]
            particle["color"] = (
                particle["color"][0],
                particle["color"][1],
                particle["color"][2],
                int(particle["color"][3] * (1 - age_factor))
            )
    
    def _update_ambient_effects(self, delta_time):
        """Update ambient visual effects"""
        # Update existing ambient effects
        for effect in self.ambient_effects[:]:
            effect["age"] += delta_time
            if effect["age"] >= effect["lifetime"]:
                self.ambient_effects.remove(effect)
    
    def _update_decorative_elements(self, delta_time):
        """Update decorative elements"""
        # Update any animated decorative elements
        pass
    
    def render_background(self, screen, camera):
        """Render background visual elements"""
        if "bg_texture" in self.assets and self.use_decorative_elements:
            # Tile the background texture based on camera position
            texture = self.assets["bg_texture"]
            texture_width, texture_height = texture.get_size()
            
            # Calculate visible area in world coordinates
            screen_width, screen_height = screen.get_size()
            world_width = screen_width / camera.zoom
            world_height = screen_height / camera.zoom
            
            # Calculate texture tiling
            start_x = int(camera.offset_x // texture_width) * texture_width
            start_y = int(camera.offset_y // texture_height) * texture_height
            
            # Draw tiled background with parallax effect (slower than camera)
            parallax_factor = 0.3
            for y in range(start_y, int(start_y + world_height + texture_height), texture_height):
                for x in range(start_x, int(start_x + world_width + texture_width), texture_width):
                    # Apply parallax offset
                    parallax_x = x - (camera.offset_x * parallax_factor)
                    parallax_y = y - (camera.offset_y * parallax_factor)
                    
                    # Convert to screen coordinates
                    screen_x, screen_y = camera.world_to_screen(parallax_x, parallax_y)
                    
                    # Draw with reduced alpha for subtle effect
                    texture.set_alpha(30)  # Very subtle
                    screen.blit(texture, (screen_x, screen_y))
    
    def render_foreground(self, screen, camera):
        """Render foreground visual elements"""
        # Render particles
        self._render_particles(screen, camera)
        
        # Render ambient effects
        self._render_ambient_effects(screen)
        
        # Render decorative elements
        self._render_decorative_elements(screen)
        
        # Apply vignette effect
        self._apply_vignette(screen)
    
    def _render_particles(self, screen, camera):
        """Render particle effects"""
        if not self.use_particles:
            return
            
        for particle in self.particles:
            # Convert world position to screen position
            screen_x, screen_y = camera.world_to_screen(particle["x"], particle["y"])
            
            # Skip if off screen
            if (screen_x < -50 or screen_x > screen.get_width() + 50 or
                screen_y < -50 or screen_y > screen.get_height() + 50):
                continue
            
            # Get particle texture based on type
            if particle["type"] == "gust":
                texture = self.assets.get("gust")
            elif particle["type"] == "circle":
                texture = self.assets.get("circle")
            else:
                texture = self.assets.get("square")
                
            
            if texture:
                # Scale texture
                size = int(10 * particle["size"] * camera.zoom)
                if size <= 0:
                    continue
                    
                scaled_texture = pygame.transform.scale(texture, (size, size))
                
                # Apply color tint
                if particle["color"] != (255, 255, 255, 255):
                    colored_texture = scaled_texture.copy()
                    colored_texture.fill(particle["color"], special_flags=pygame.BLEND_RGBA_MULT)
                else:
                    colored_texture = scaled_texture
                
                # Apply rotation if needed
                if particle["rotation"] != 0:
                    colored_texture = pygame.transform.rotate(colored_texture, particle["rotation"])
                
                # Draw particle
                screen.blit(colored_texture, (
                    screen_x - colored_texture.get_width() // 2,
                    screen_y - colored_texture.get_height() // 2
                ))
    
    def _render_ambient_effects(self, screen):
        """Render ambient visual effects"""
        # Render any ambient effects (like weather, lighting, etc.)
        pass
    
    def _render_decorative_elements(self, screen):
        """Render decorative UI elements"""
        if not self.use_decorative_elements:
            return
            
        # Get screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Draw border corners
        corner = self.assets.get("border_corner")
        if corner:
            # Top-left
            screen.blit(corner, (10, 10))
            
            # Top-right (rotate 90°)
            rotated = pygame.transform.rotate(corner, 270)
            screen.blit(rotated, (screen_width - rotated.get_width() - 10, 10))
            
            # Bottom-left (rotate 90°)
            rotated = pygame.transform.rotate(corner, 90)
            screen.blit(rotated, (10, screen_height - rotated.get_height() - 10))
            
            # Bottom-right (rotate 180°)
            rotated = pygame.transform.rotate(corner, 180)
            screen.blit(rotated, (screen_width - rotated.get_width() - 10, 
                                 screen_height - rotated.get_height() - 10))
    
    def _apply_vignette(self, screen):
        """Apply vignette effect to screen edges"""
        if not self.use_lighting:
            return
            
        vignette = self.assets.get("vignette")
        if vignette:
            # Scale vignette to screen size
            screen_width, screen_height = screen.get_size()
            scaled_vignette = pygame.transform.scale(vignette, (screen_width, screen_height))
            
            # Apply with reduced opacity for subtle effect
            scaled_vignette.set_alpha(100)  # Adjust for desired intensity
            screen.blit(scaled_vignette, (0, 0))
    
    def add_ambient_particles(self, camera, count=5):
        """Add ambient particles within the visible area"""
        if not self.use_particles:
            return
            
        current_time = pygame.time.get_ticks()
        if current_time - self.last_particle_time < self.particle_interval:
            return
            
        self.last_particle_time = current_time
        
        # Get visible area in world coordinates
        screen_width, screen_height = pygame.display.get_surface().get_size()
        visible_width = screen_width / camera.zoom
        visible_height = screen_height / camera.zoom
        
        # Add particles within visible area
        for _ in range(count):
            x = camera.offset_x + random.uniform(0, visible_width)
            y = camera.offset_y + random.uniform(0, visible_height)
            
            # Create particle with random properties
            self.add_particle(
                x, y,
                type="gust" if random.random() < 0.7 else "gust",
                lifetime=random.uniform(1.0, 3.0),
                size=random.uniform(0.2, 0.8),
                color=(
                    random.randint(200, 255),
                    random.randint(200, 255),
                    random.randint(200, 255),
                    random.randint(30, 80)  # Low alpha for subtle effect
                ),
                velocity=(
                    random.uniform(-0.2, 0.2),
                    random.uniform(-0.2, 0.2)
                )
            )
    
    def add_impact_particles(self, x, y, count=10, color=None, size_range=(0.3, 0.7), 
                            lifetime_range=(0.3, 0.8), velocity_range=(0.5, 2.0)):
        """Add particles for impact effects (like footsteps, collisions)"""
        if not self.use_particles:
            return
            
        if color is None:
            color = (255, 255, 255, 150)
            
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(velocity_range[0], velocity_range[1])
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            
            self.add_particle(
                x, y,
                type="gust" if random.random() < 0.7 else "circle",
                lifetime=random.uniform(lifetime_range[0], lifetime_range[1]),
                size=random.uniform(size_range[0], size_range[1]),
                color=color,
                velocity=velocity
            )

    
    def toggle_ambient_effects(self):
        """Toggle ambient visual effects on/off"""
        self.use_ambient_effects = not self.use_ambient_effects
        return self.use_ambient_effects
    
    def toggle_particles(self):
        """Toggle particle effects on/off"""
        self.use_particles = not self.use_particles
        if not self.use_particles:
            self.particles.clear()  # Clear existing particles
        return self.use_particles
    
    def toggle_decorative_elements(self):
        """Toggle decorative elements on/off"""
        self.use_decorative_elements = not self.use_decorative_elements
        return self.use_decorative_elements
    
    def toggle_lighting(self):
        """Toggle lighting effects on/off"""
        self.use_lighting = not self.use_lighting
        return self.use_lighting

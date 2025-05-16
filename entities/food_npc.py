import random
import pygame
import hashlib
import os
from entities.rectangle import Rectangle
from engine.ai import RandomWanderAI
from engine.constants import TimeConstants, GameBalanceConstants, MovementConstants


class FoodNPC(Rectangle):
    """A food entity that wanders around and can be consumed by players or NPCs"""
    
    def __init__(self, grid_x, grid_y, color=(255, 165, 0), speed=0.5, ai_controller=None):
        # Set food type before calling super().__init__ since generate_persistent_id uses it
        self.food_type = random.choice(["fruit", "vegetable", "berry", "mushroom"])
        
        # Initialize with orange color by default (can be customized)
        super().__init__(grid_x, grid_y, color, speed, controllable=False)
        
        # Set up AI controller if not provided
        if not ai_controller:
            self.ai_controller = RandomWanderAI(self)
        else:
            self.ai_controller = ai_controller
            self.ai_controller.set_entity(self)
        
        # Food properties
        self.nutrition_value = GameBalanceConstants.FOOD_NUTRITION_VALUE
        self.is_consumed = False  # Flag to track if this food has been consumed
        self.consumption_progress = 0  # Track consumption animation progress
        self.consumption_time = 0  # Time when consumption started
        self.load__food_sprite_sheet()
        # Set color based on food type
        self.set_color_by_food_type()
        
        # Movement patterns
        self.movement_cooldown = random.randint(2000, 5000)  # Time between movements
        self.last_movement_time = 0
        self.movement_range = 3  # Maximum tiles to move at once
        
        # Override entity_id to ensure it's unique for food
        self.entity_id = self.generate_persistent_id()
    
    def set_color_by_food_type(self):
        """Set the color based on food type"""
        if self.food_type == "fruit":
            self.color = (255, 0, 0)  # Red for fruits
        elif self.food_type == "vegetable":
            self.color = (0, 180, 0)  # Green for vegetables
        elif self.food_type == "berry":
            self.color = (128, 0, 128)  # Purple for berries
        elif self.food_type == "mushroom":
            self.color = (210, 180, 140)  # Tan for mushrooms
    
    def generate_persistent_id(self):
        """Generate a persistent ID based on entity characteristics"""
        # Create a string with entity properties that should remain consistent
        id_string = f"FoodNPC_{self.grid_x}_{self.grid_y}_{self.food_type}_{random.randint(1000, 9999)}"
        
        # Hash the string to create a consistent ID
        hash_object = hashlib.md5(id_string.encode())
        # Return a formatted binary-like string (first 16 chars of hex digest)
        return f"0b{hash_object.hexdigest()[:16]}"
    
    def get_entity_id(self):
        """Get the persistent entity ID"""
        return self.entity_id
    
    # Override load_cna_file to do nothing for food NPCs
    def load_cna_file(self, file_path):
        """Food NPCs don't use CNA files"""
        return
    
    def update(self):
        """Update entity state"""
        # If consumed, handle consumption animation and removal
        if self.is_consumed:
            current_time = pygame.time.get_ticks()
            elapsed_time = current_time - self.consumption_time
            
            # Consumption animation takes 500ms
            if elapsed_time < TimeConstants.FOOD_CONSUMPTION_ANIMATION_DURATION:
                self.consumption_progress = elapsed_time / TimeConstants.FOOD_CONSUMPTION_ANIMATION_DURATION
                # Shrink the entity as it's being consumed
                self.visual_scale = 1.0 - self.consumption_progress
            else:
                # Mark for removal after consumption animation completes
                self.mark_for_removal = True
            
            # Update visual position with smooth interpolation
            self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
            self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
            
            # Update animation
            self.update_animation()
            return
        
        # Normal update for non-consumed food
        current_time = pygame.time.get_ticks()
        
        # Update AI controller if available
        if self.ai_controller:
            from engine.core import SimpleGameEngine
            world_map = None
            objects = []  # Changed from entities to objects
            
            if hasattr(SimpleGameEngine, 'instance'):
                world_map = SimpleGameEngine.instance.world_map
                objects = SimpleGameEngine.instance.objects  # Changed from entities to objects
            
            self.ai_controller.update(world_map, objects)  # Pass objects instead of entities
        
        # Check if any entity is on top of this food
        self.check_for_consumption()
        
        # Update visual position with smooth interpolation
        self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
        self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
        
        # Update animation
        self.update_animation()
        
        # Handle movement with timing control
        if self.is_moving:
            # Only move if enough time has passed (slower movement for food)
            if not hasattr(self, 'last_move_time'):
                self.last_move_time = current_time
                
            if current_time - self.last_move_time >= TimeConstants.FOOD_MOVE_COOLDOWN:
                # Calculate direction to target
                dx = self.target_grid_x - self.grid_x
                dy = self.target_grid_y - self.grid_y
                
                # Check if we've reached the target
                if dx == 0 and dy == 0:
                    self.is_moving = False
                else:
                    # Store current position before moving
                    self.previous_grid_x = self.grid_x
                    self.previous_grid_y = self.grid_y
                    
                    # Determine movement direction
                    if dx != 0:
                        move_x = 1 if dx > 0 else -1
                        self.grid_x += move_x
                    elif dy != 0:
                        move_y = 1 if dy > 0 else -1
                        self.grid_y += move_y
                    
                    # Reset the movement timer
                    self.last_move_time = current_time

    
    def check_for_consumption(self):
        """Check if any entity is on top of this food and should consume it"""
        from engine.core import SimpleGameEngine
        
        if not hasattr(SimpleGameEngine, 'instance') or not SimpleGameEngine.instance:
            return
            
        objects = SimpleGameEngine.instance.objects  # Changed from entities to objects
        
        for entity in objects:
            # Skip if this is the food itself or if the entity doesn't have grid position
            if entity == self or not hasattr(entity, 'grid_x') or not hasattr(entity, 'grid_y'):
                continue
                
            # Check if entity is on the same tile
            if entity.grid_x == self.grid_x and entity.grid_y == self.grid_y:
                # Entity is on top of food, trigger consumption
                self.be_consumed_by(entity)
                break

    def be_consumed_by(self, consumer):
        """Handle being consumed by an entity"""
        if self.is_consumed:
            return  # Already being consumed
            
        # Debug output
        print(f"DEBUG: Food being consumed by entity at ({consumer.grid_x}, {consumer.grid_y})")
        print(f"DEBUG: Consumer has hunger attribute: {hasattr(consumer, 'hunger')}")
        if hasattr(consumer, 'hunger'):
            print(f"DEBUG: Consumer hunger before: {consumer.hunger}")
                
        # Mark as consumed and start consumption animation
        self.is_consumed = True
        self.consumption_time = pygame.time.get_ticks()
        
        # Increase consumer's hunger if it has that attribute
        if hasattr(consumer, 'hunger'):
            old_hunger = consumer.hunger
            consumer.hunger = min(10, consumer.hunger + self.nutrition_value)
            
            # Update last eat time if the consumer has it
            if hasattr(consumer, 'last_eat_time'):
                consumer.last_eat_time = pygame.time.get_ticks()
                
            print(f"NPC {consumer.get_entity_id()} consumed food, hunger increased from {old_hunger} to {consumer.hunger}")
            
            # Show a speech bubble for the consumer
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                eating_speeches = [
                    "Mmm, delicious!",
                    "That was tasty!",
                    "Yum!",
                    "That hit the spot!",
                    f"This {self.food_type} is so good!"
                ]
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(eating_speeches), consumer, duration=2.0)

    
    def be_consumed_by(self, consumer):
        """Handle being consumed by an entity"""
        if self.is_consumed:
            return  # Already being consumed
            
        # Mark as consumed and start consumption animation
        self.is_consumed = True
        self.consumption_time = pygame.time.get_ticks()
        
        # Increase consumer's hunger if it has that attribute
        if hasattr(consumer, 'hunger'):
            old_hunger = consumer.hunger
            consumer.hunger = min(10, consumer.hunger + self.nutrition_value)
            
            # Update last eat time if the consumer has it
            if hasattr(consumer, 'last_eat_time'):
                consumer.last_eat_time = pygame.time.get_ticks()
                
            print(f"NPC {consumer.get_entity_id()} consumed food, hunger increased from {old_hunger} to {consumer.hunger}")
            
            # Show a speech bubble for the consumer
            from engine.core import SimpleGameEngine
            if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
                eating_speeches = [
                    "Mmm, delicious!",
                    "That was tasty!",
                    "Yum!",
                    "That hit the spot!",
                    f"This {self.food_type} is so good!"
                ]
                SimpleGameEngine.instance.ui.add_text_bubble(random.choice(eating_speeches), consumer, duration=2.0)
    
    def render(self, screen, camera):
        """Render the food entity with camera transformations"""
        if hasattr(self, 'mark_for_removal') and self.mark_for_removal:
            return  # Skip rendering if marked for removal
            
        # Calculate screen position using camera and visual position
        screen_x, screen_y, width, height = camera.apply(
            self.visual_x * 16, self.visual_y * 16, 16, 16
        )
        
        # Skip rendering if off-screen
        if (screen_x + width < 0 or screen_x > screen.get_width() or
            screen_y + height < 0 or screen_y > screen.get_height()):
            return
        
        # Get the current animation frame - FIXED: ensure index is in bounds
        frames = self.get_current_animation_frames() if hasattr(self, 'get_current_animation_frames') else self.animation_frames
        frame_index = self.current_frame % len(frames)  # Ensure index is in bounds
        current_frame = frames[frame_index]
        
        # Apply color tint
        tinted_frame = self.apply_color_tint(current_frame)
        
        # If being consumed, scale down the sprite
        if self.is_consumed and hasattr(self, 'visual_scale'):
            # Scale the sprite based on consumption progress
            new_width = int(width * self.visual_scale)
            new_height = int(height * self.visual_scale)
            
            # Center the scaled sprite
            offset_x = (width - new_width) // 2
            offset_y = (height - new_height) // 2
            
            # Scale the frame
            if new_width > 0 and new_height > 0:  # Prevent scaling to zero
                tinted_frame = pygame.transform.scale(tinted_frame, (new_width, new_height))
                screen_x += offset_x
                screen_y += offset_y
        elif width != 16 or height != 16:
            # Normal scaling if needed
            tinted_frame = pygame.transform.scale(tinted_frame, (int(width), int(height)))
        
        # Draw the sprite
        screen.blit(tinted_frame, (screen_x, screen_y))
        
        # Draw food type indicator (small colored dot)
        indicator_color = self.color
        pygame.draw.circle(screen, indicator_color, (screen_x + width - 3, screen_y + 3), 2)

    def load__food_sprite_sheet(self):
        """Load the sprite sheet and extract frames"""
        try:
            # Get the path to the sprite sheet
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sprite_path = os.path.join(project_root, "assets", "food_sheet.png")
            walk_sprite_path = os.path.join(project_root, "assets", "food_walk.png")
            
            # Load the sprite sheet
            self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
            
            # Extract the two frames (each 16x16)
            frame1 = self.sprite_sheet.subsurface((0, 0, 16, 16))
            frame2 = self.sprite_sheet.subsurface((16, 0, 16, 16))
            
            # Store the frames
            self.animation_frames = [frame1, frame2]
            
            # Load the walking sprite sheet if it exists
            if os.path.exists(walk_sprite_path):
                self.walk_sprite_sheet = pygame.image.load(walk_sprite_path).convert_alpha()
                
                # Extract the walking frames (each 16x16)
                # Assuming the walk sheet has at least 2 frames
                walk_frame1 = self.walk_sprite_sheet.subsurface((0, 0, 16, 16))
                walk_frame2 = self.walk_sprite_sheet.subsurface((16, 0, 16, 16))
                
                # Store the walking frames
                self.walk_animation_frames = [walk_frame1, walk_frame2]
                
                print(f"DEBUG: Food NPC loaded walk sprite sheet with {len(self.walk_animation_frames)} frames")
            else:
                # If walk sprite sheet doesn't exist, use idle frames for walking too
                self.walk_animation_frames = self.animation_frames
                print("Food walk sprite sheet not found, using idle frames for walking")
            
        except Exception as e:
            print(f"Error loading food sprite sheets: {e}")
            # Create fallback frames (colored squares)
            self.animation_frames = [
                pygame.Surface((16, 16), pygame.SRCALPHA),
                pygame.Surface((16, 16), pygame.SRCALPHA)
            ]
            self.walk_animation_frames = self.animation_frames
            for frame in self.animation_frames:
                frame.fill(self.color)
    
    def get_current_animation_frames(self):
        """Get the appropriate animation frames based on movement state"""
        if self.is_moving and hasattr(self, 'walk_animation_frames') and self.walk_animation_frames:
            return self.walk_animation_frames
        return self.animation_frames

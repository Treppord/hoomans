import pygame
import os
import math

from entities.inventory import Inventory
from entities.items.item_factory import ItemFactory

class Rectangle:
    """Base class for all rectangular entities in the game"""
    
import pygame
import os
import math
import hashlib

class Rectangle:
    """Base class for all rectangular entities in the game"""
    
    def __init__(self, grid_x, grid_y, color=(255, 255, 255), speed=1, controllable=False):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.previous_grid_x = grid_x  # Initialize previous position
        self.previous_grid_y = grid_y  # Initialize previous position
        self.color = color
        self.speed = speed
        self.controllable = controllable
        
        # For smooth movement
        self.target_grid_x = grid_x
        self.target_grid_y = grid_y
        self.is_moving = False
        
        # For visual interpolation (smooth rendering)
        self.visual_x = float(grid_x)
        self.visual_y = float(grid_y)
        self.move_lerp_factor = 0.2  # Adjust for smoother/faster visual transitions
        

        # For animation
        self.sprite_sheet = None
        self.walk_sprite_sheet = None  # Add walk sprite sheet
        self.animation_frames = []
        self.walk_animation_frames = []  # Add walk animation frames
        self.current_frame = 0
        self.animation_speed = 0.1  # Adjust as needed
        self.animation_timer = 0
        self.load_sprite_sheets()  # Changed to load multiple sprite sheets
        
        # Add these new attributes for animation control
        self.force_walk_animation = False
        self.walk_animation_start_time = 0
        self.walk_animation_duration = 500  # milliseconds to show walking animation
        
        # For CNA data
        self.cna_data = None
        self.cna_file = None
        
        # Add properties for camera compatibility
        self.width = 16
        self.height = 16
        
        # Add inventory
        self.inventory = Inventory(16)  # 16 slots by default
        
        # Add facing direction for item use
        self.facing = 'down'  # Default facing direction
        
        self.starter_items_added = False

        
        # Generate a persistent ID
        self.entity_id = self.generate_persistent_id()
        
        self.item_use_cooldown = 0
        self.item_use_cooldown_duration = 500
        
    
    def generate_persistent_id(self):
        """Generate a persistent ID based on entity characteristics"""
        # Create a string with entity properties that should remain consistent
        id_string = f"{self.__class__.__name__}_{self.grid_x}_{self.grid_y}_{self.color}_{self.controllable}"
        
        # If CNA file exists, include it in the ID calculation
        if hasattr(self, 'cna_file') and self.cna_file:
            id_string += f"_{os.path.basename(self.cna_file)}"
        
        # Hash the string to create a consistent ID
        hash_object = hashlib.md5(id_string.encode())
        # Return a formatted binary-like string (first 16 chars of hex digest)
        return f"0b{hash_object.hexdigest()[:16]}"
    
    def get_entity_id(self):
        """Get the persistent entity ID"""
        return self.entity_id

    
    # Add properties for camera compatibility
    @property
    def x(self):
        return self.visual_x * 16  # Use visual position for rendering
    
    @property
    def y(self):
        return self.visual_y * 16  # Use visual position for rendering
    
    def load_sprite_sheets(self):
        """Load both idle and walking sprite sheets and extract frames"""
        try:
            # Get the path to the sprite sheets
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            idle_sprite_path = os.path.join(project_root, "assets", "ai_sheet.png")
            walk_sprite_path = os.path.join(project_root, "assets", "ai_walk.png")
            
            # Load the idle sprite sheet
            self.sprite_sheet = pygame.image.load(idle_sprite_path).convert_alpha()
            
            # Extract the idle frames (each 16x16)
            idle_frame1 = self.sprite_sheet.subsurface((0, 0, 16, 16))
            idle_frame2 = self.sprite_sheet.subsurface((16, 0, 16, 16))
            
            # Store the idle frames
            self.animation_frames = [idle_frame1, idle_frame2]
            
            # Load the walking sprite sheet if it exists
            if os.path.exists(walk_sprite_path):
                self.walk_sprite_sheet = pygame.image.load(walk_sprite_path).convert_alpha()
                
                # Extract the walking frames (each 16x16)
                # Assuming the walk sheet has at least 2 frames
                walk_frame1 = self.walk_sprite_sheet.subsurface((0, 0, 16, 16))
                walk_frame2 = self.walk_sprite_sheet.subsurface((16, 0, 16, 16))
                walk_frame3 = self.walk_sprite_sheet.subsurface((32, 0, 16, 16))
                walk_frame4 = self.walk_sprite_sheet.subsurface((48, 0, 16, 16))

                
                # Store the walking frames
                self.walk_animation_frames = [walk_frame1, walk_frame2, walk_frame3, walk_frame4]
                
                # Debug output for player
                if hasattr(self, 'controllable') and self.controllable:
                    print(f"DEBUG: Player loaded walk sprite sheet with {len(self.walk_animation_frames)} frames")
            else:
                # If walk sprite sheet doesn't exist, use idle frames for walking too
                self.walk_animation_frames = self.animation_frames
                print("Walk sprite sheet not found, using idle frames for walking")
            
        except Exception as e:
            print(f"Error loading sprite sheets: {e}")
            # Create fallback frames (colored squares)
            self.animation_frames = [
                pygame.Surface((16, 16), pygame.SRCALPHA),
                pygame.Surface((16, 16), pygame.SRCALPHA)
            ]
            self.walk_animation_frames = self.animation_frames
            for frame in self.animation_frames:
                frame.fill(self.color)

    
    def update_animation(self, delta_time=1/60):
        """Update the animation frame"""
        self.animation_timer += delta_time * 0.25
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.get_current_animation_frames())
    
    def get_current_animation_frames(self):
        """Get the appropriate animation frames based on movement state"""
        if self.is_moving and hasattr(self, 'walk_animation_frames') and self.walk_animation_frames:
            return self.walk_animation_frames
        return self.animation_frames


    
    def apply_color_tint(self, frame):
        """Apply color tint to the sprite based on entity color"""
        # Create a copy of the frame to modify
        tinted_frame = frame.copy()
        
        # Get the white color to replace (255, 255, 255)
        white_color = (255, 255, 255)
        
        # Replace white pixels with the entity's color
        for y in range(tinted_frame.get_height()):
            for x in range(tinted_frame.get_width()):
                pixel_color = tinted_frame.get_at((x, y))
                # If the pixel is white (or close to white), replace it with the entity color
                if (pixel_color[0] > 240 and pixel_color[1] > 240 and pixel_color[2] > 240):
                    # Keep the alpha value
                    alpha = pixel_color[3]
                    new_color = (self.color[0], self.color[1], self.color[2], alpha)
                    tinted_frame.set_at((x, y), new_color)
        
        return tinted_frame
    
    def load_cna_file(self, cna_file_path):
        """Load CNA data from a file and update entity attributes"""
        self.cna_file = cna_file_path
        try:
            from cna_utils import CNACodec
            self.cna_data = CNACodec.load_from_file(cna_file_path)
            
            # Update entity color based on CNA data
            if self.cna_data:
                from cna_utils import calculate_entity_color
                self.color = calculate_entity_color(self.cna_data)
                print(f"Updated entity color to {self.color} based on CNA data")
        except Exception as e:
            print(f"Error loading CNA file: {e}")
    
    def update(self):
        """Update entity state"""
        
    
        if not self.starter_items_added and pygame.get_init():
            print(f"DEBUG: Adding starter items for entity {self.get_entity_id()}, controllable={self.controllable}")
            self._add_starter_items()
            self.starter_items_added = True
            print(f"DEBUG: Starter items added: {self.starter_items_added}")
        # Store previous position before updating
        self.previous_grid_x = self.grid_x
        self.previous_grid_y = self.grid_y
        
        # Update visual position with smooth interpolation
        self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
        self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
        
        # Update animation
        self.update_animation()

        # Check if we're near water and replenish thirst if needed
        if hasattr(self, 'check_and_replenish_thirst'):
            self.check_and_replenish_thirst()
        
        # Decrease hunger over time if the entity has hunger attribute
        if hasattr(self, 'hunger') and hasattr(self, 'last_hunger_update'):
            current_time = pygame.time.get_ticks()
            if current_time - self.last_hunger_update > 15000:  # 15 seconds
                if self.hunger > 0:
                    self.hunger -= 1
                    print(f"NPC {self.get_entity_id()} hunger decreased to {self.hunger}")
                self.last_hunger_update = current_time
        
        # Update item use cooldown
        if self.item_use_cooldown > 0:
            current_time = pygame.time.get_ticks()
            if current_time >= self.item_use_cooldown:
                self.item_use_cooldown = 0
                
        # Handle movement towards target
        if self.is_moving:
            # Check if we've reached the target
            if self.grid_x == self.target_grid_x and self.grid_y == self.target_grid_y:
                # Only set is_moving to False if we're not a player or if no movement keys are pressed
                if not (hasattr(self, 'controllable') and self.controllable):
                    self.is_moving = False
                else:
                    # For player, keep is_moving true if force_walk_animation is active
                    if hasattr(self, 'force_walk_animation') and self.force_walk_animation:
                        self.is_moving = True
                    else:
                        self.is_moving = False
            else:
                # Get the next step towards the target
                next_x = self.grid_x
                next_y = self.grid_y
                
                if self.grid_x < self.target_grid_x:
                    next_x += self.speed
                    self.facing = 'right'
                elif self.grid_x > self.target_grid_x:
                    next_x -= self.speed
                    self.facing = 'left'
                    
                if self.grid_y < self.target_grid_y:
                    next_y += self.speed
                    self.facing = 'down'
                elif self.grid_y > self.target_grid_y:
                    next_y -= self.speed
                    self.facing = 'up'
                
                # Check for collision with entity tiles before moving
                from engine.core import SimpleGameEngine
                if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'world_map'):
                    world_map = SimpleGameEngine.instance.world_map
                    if hasattr(world_map, 'entity_tile_manager'):
                        component = world_map.entity_tile_manager.get_component_at(next_x, next_y)
                        if component and hasattr(component, 'is_walkable') and not component.is_walkable():
                            # Collision detected, stop movement
                            self.is_moving = False
                            self.target_grid_x = self.grid_x
                            self.target_grid_y = self.grid_y
                            return
                
                # Move to the next position
                self.grid_x = next_x
                self.grid_y = next_y

        # Check if we should turn off force_walk_animation
        if hasattr(self, 'force_walk_animation') and self.force_walk_animation:
            current_time = pygame.time.get_ticks()
            if current_time - self.walk_animation_start_time > self.walk_animation_duration:
                self.force_walk_animation = False
                # Only set is_moving to False if we're not actively moving
                if self.grid_x == self.target_grid_x and self.grid_y == self.target_grid_y:
                    self.is_moving = False
    
    def use_selected_item(self):
        """Use the currently selected item"""
        # Check cooldown
        current_time = pygame.time.get_ticks()
        if self.item_use_cooldown > 0 and current_time < self.item_use_cooldown:
            return False
        
        # Get the selected item
        selected_item = self.inventory.get_selected_item()
        if not selected_item:
            return False
        
        # Get the world from the game engine
        from engine.core import SimpleGameEngine
        world = None
        if hasattr(SimpleGameEngine, 'instance'):
            world = SimpleGameEngine.instance.world_map
        
        # Use the item
        if selected_item.use(self, world):
            # Set cooldown
            self.item_use_cooldown = current_time + self.item_use_cooldown_duration
            
            # If the item quantity is now 0, remove it from inventory
            if selected_item.quantity <= 0:
                slot = self.inventory.get_selected_slot()
                slot.item = None
            
            return True
        
        return False
    
    def add_item(self, item_id, quantity=1):
        """Add an item to the inventory"""
        item = ItemFactory.create_item(item_id, quantity)
        if item:
            return self.inventory.add_item(item)
        return False
    
    def has_item(self, item_id, quantity=1):
        """Check if the entity has a specific item"""
        return self.inventory.has_item(item_id, quantity)
    
    def remove_item(self, item_id, quantity=1):
        """Remove an item from the inventory"""
        return self.inventory.remove_item(item_id, quantity)

    
    def render(self, screen, camera):
        """Render the entity with camera transformations"""
        # Calculate screen position using camera and visual position
        screen_x, screen_y, width, height = camera.apply(
            self.visual_x * 16, self.visual_y * 16, 16, 16
        )
        
        # Skip rendering if off-screen
        if (screen_x + width < 0 or screen_x > screen.get_width() or
            screen_y + height < 0 or screen_y > screen.get_height()):
            return
        
        # Get the current animation frame based on movement state
        animation_frames = self.get_current_animation_frames()
        current_frame = animation_frames[self.current_frame % len(animation_frames)]
        
        # Apply color tint
        tinted_frame = self.apply_color_tint(current_frame)
        
        # Scale the frame if needed
        if width != 16 or height != 16:
            tinted_frame = pygame.transform.scale(tinted_frame, (int(width), int(height)))
        
        # Draw the sprite
        screen.blit(tinted_frame, (screen_x, screen_y))



    
    def contains_point(self, screen_x, screen_y, camera):
        """Check if a screen point is within this entity"""
        entity_x, entity_y, width, height = camera.apply(
            self.visual_x * 16, self.visual_y * 16, 16, 16
        )
        
        return (entity_x <= screen_x <= entity_x + width and
                entity_y <= screen_y <= entity_y + height)

    def check_and_replenish_thirst(self):
        """Check if entity is adjacent to water and replenish thirst if needed"""
        # Skip if entity doesn't have thirst attribute
        if not hasattr(self, 'thirst'):
            return
            
        # Skip if thirst is already full
        if self.thirst >= 10:
            return
            
        # Get the world map
        from engine.core import SimpleGameEngine
        world_map = None
        if hasattr(SimpleGameEngine, 'instance'):
            world_map = SimpleGameEngine.instance.world_map
        
        # Check if we're adjacent to water
        if world_map and world_map.is_adjacent_to_water(self.grid_x, self.grid_y):
            # Get current time
            current_time = pygame.time.get_ticks()
            
            # Only drink every 2 seconds to prevent instant refill
            if not hasattr(self, 'last_drink_time') or current_time - self.last_drink_time > 2000:
                self.thirst += 1
                self.last_drink_time = current_time
                
                # Print message
                entity_type = "Player" if hasattr(self, 'controllable') and self.controllable else "NPC"
                print(f"{entity_type} drank water, thirst increased to {self.thirst}")
                
                # Show a speech bubble for NPCs
                if entity_type == "NPC" and hasattr(SimpleGameEngine.instance, 'ui'):
                    if self.thirst == 10:
                        SimpleGameEngine.instance.ui.add_text_bubble("Ahh, my thirst is quenched!", self, duration=2.0)
                    else:
                        SimpleGameEngine.instance.ui.add_text_bubble("*drinks water*", self, duration=1.0)
    # Modify the _add_starter_items method in the Rectangle class

    def _add_starter_items(self):
        """Add some starter items to the inventory"""
        # Only add items to player-controlled entities
        if self.controllable:
            print(f"DEBUG: Adding starter items to player inventory (ID: {self.get_entity_id()})")
            
            # Define starter items as a list of dictionaries
            # Each dictionary contains:
            #   - item_id: The ID of the item to add
            #   - quantity: The quantity to add (default: 1)
            starter_items = [
                {"item_id": "water_bottle", "quantity": 3},
                {"item_id": "apple", "quantity": 5},
                {"item_id": "stone_axe", "quantity": 1},
                {"item_id": "stone", "quantity": 10},
                {"item_id": "branch", "quantity": 10},
            ]
            
            # Add each item to the inventory
            for item_info in starter_items:
                item_id = item_info["item_id"]
                quantity = item_info.get("quantity", 1)
                
                try:
                    print(f"DEBUG: Attempting to create {item_id} item...")
                    item = ItemFactory.create_item(item_id, quantity)
                    if item:
                        print(f"DEBUG: {item_id} created successfully with quantity {item.quantity}")
                        result = self.inventory.add_item(item)
                        print(f"DEBUG: {item_id} added to inventory: {result}")
                    else:
                        print(f"DEBUG: Failed to create {item_id} item")
                except Exception as e:
                    print(f"ERROR: Exception while adding {item_id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Print inventory contents for debugging
            for i, slot in enumerate(self.inventory.slots):
                if slot.item:
                    print(f"DEBUG: Slot {i}: {slot.item.name} x{slot.item.quantity}")

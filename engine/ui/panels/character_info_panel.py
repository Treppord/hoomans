"""Character info panel UI element with integrated inventory display"""
import pygame
from engine.ui.elements.base import UIElement
from engine.ui.constants.colors import DARK_PANEL_BG, BORDER_COLOR, TEXT_COLOR, TITLE_COLOR

class CharacterInfoPanel(UIElement):
    """Panel that displays character information and inventory from entity data"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.entity = None
        self.background_color = DARK_PANEL_BG
        self.text_color = TEXT_COLOR
        self.title_color = TITLE_COLOR
        self.font = pygame.font.Font("assets/font/CandC_LAN.ttf", 24)
        self.title_font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 20)
        self.padding = 15
        self.visible = False
        self.animation_timer = 0
        self.current_frame = 0
        self.animation_speed = 0.5
        
        # Inventory display settings
        self.show_inventory = True
        self.inventory_slot_size = 40
        self.inventory_padding = 4
        self.inventory_slots_per_row = 4
        self.dragging_item = None
        self.dragging_from_slot = -1
        self.hover_slot = -1
        
    def set_entity(self, entity):
        """Set the entity to display information for"""
        self.entity = entity
        self.visible = (entity is not None and entity.cna_data is not None)
        # Reset inventory interaction state when changing entities
        self.dragging_item = None
        self.dragging_from_slot = -1
        self.hover_slot = -1
        
    def update_animation(self, delta_time=1/60):
        """Update the animation frame"""
        self.animation_timer += delta_time
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
                self.current_frame = (self.current_frame + 1) % len(self.entity.animation_frames)
    
    def get_slot_at_position(self, x, y):
        """Get the inventory slot at the given screen position"""
        if not self.entity or not hasattr(self.entity, 'inventory'):
            return -1
            
        # Calculate inventory section position
        inventory_x = self.x + self.padding
        inventory_y = self.y + self.height - 220  # Position inventory at bottom of panel
        
        # Convert to inventory-relative coordinates
        rel_x = x - inventory_x
        rel_y = y - inventory_y
        
        if rel_x < 0 or rel_y < 0:
            return -1
            
        # Calculate row and column
        col = rel_x // (self.inventory_slot_size + self.inventory_padding)
        row = rel_y // (self.inventory_slot_size + self.inventory_padding)
        
        # Check if within valid range
        if col >= self.inventory_slots_per_row:
            return -1
            
        # Calculate slot index
        slot_index = row * self.inventory_slots_per_row + col
        
        if slot_index >= self.entity.inventory.size:
            return -1
            
        return slot_index
    
    def update_hover_slot(self, mouse_x, mouse_y):
        """Update which slot the mouse is hovering over"""
        self.hover_slot = self.get_slot_at_position(mouse_x, mouse_y)
        
    def handle_event(self, event):
        """Handle input events"""
        if not self.visible:
            return False
            
        # Close panel on Escape
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False
            return True
            
        # Handle inventory interaction if entity has inventory
        if self.entity and hasattr(self.entity, 'inventory') and self.show_inventory:
            # Handle mouse movement for hover effects
            if event.type == pygame.MOUSEMOTION:
                self.update_hover_slot(event.pos[0], event.pos[1])
                
            # Handle mouse clicks for item selection and dragging
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                slot_index = self.get_slot_at_position(event.pos[0], event.pos[1])
                if slot_index >= 0 and slot_index < self.entity.inventory.size:
                    # Select the slot
                    self.entity.inventory.select_slot(slot_index)
                    
                    # Start dragging if the slot has an item
                    slot = self.entity.inventory.slots[slot_index]
                    if not slot.is_empty():
                        # If shift is held, split the stack
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            half_quantity = slot.item.quantity // 2
                            if half_quantity > 0:
                                self.dragging_item = slot.item.split(half_quantity)
                        else:
                            # Take the whole stack
                            self.dragging_item = slot.remove_item(slot.item.quantity)
                        
                        self.dragging_from_slot = slot_index
                
                return True
                
            # Handle mouse release for dropping items
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left click release
                if self.dragging_item:
                    slot_index = self.get_slot_at_position(event.pos[0], event.pos[1])
                    if slot_index >= 0 and slot_index < self.entity.inventory.size:
                        # Try to place the item in this slot
                        target_slot = self.entity.inventory.slots[slot_index]
                        
                        # If the slot is empty or can stack with our item
                        if target_slot.is_empty() or target_slot.can_accept(self.dragging_item):
                            # Add the item to the slot
                            remaining = target_slot.add_item(self.dragging_item)
                            
                            # If there are remaining items, keep them in hand
                            if remaining > 0:
                                self.dragging_item.quantity = remaining
                            else:
                                self.dragging_item = None
                        else:
                            # Swap items
                            temp_item = target_slot.item
                            target_slot.item = self.dragging_item
                            self.dragging_item = temp_item
                    else:
                        # Drop the item back in the original slot if we're not over a valid slot
                        if 0 <= self.dragging_from_slot < self.entity.inventory.size:
                            self.entity.inventory.slots[self.dragging_from_slot].add_item(self.dragging_item)
                        
                        self.dragging_item = None
                    
                    self.dragging_from_slot = -1
                
                return True
                
            # Handle right-click for splitting stacks
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
                slot_index = self.get_slot_at_position(event.pos[0], event.pos[1])
                if slot_index >= 0 and slot_index < self.entity.inventory.size:
                    slot = self.entity.inventory.slots[slot_index]
                    if not slot.is_empty() and slot.item.quantity > 1:
                        # Take one item
                        self.dragging_item = slot.remove_item(1)
                        self.dragging_from_slot = slot_index
                
                return True
                
        return False
        
    def render(self, screen):
        if not self.visible or not self.entity or not self.entity.cna_data:
            return
            
        # Update animation
        self.update_animation()
            
        # Create a surface with alpha for transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with transparency
        pygame.draw.rect(panel_surface, self.background_color, 
                        (0, 0, self.width, self.height),
                        border_radius=10)
        
        # Draw divider line down the middle
        divider_x = self.width // 2
        pygame.draw.line(panel_surface, (100, 100, 100, 200),
                        (divider_x, 10), (divider_x, self.height - 10), 2)
        
        # Get CNA data
        cna = self.entity.cna_data
        
        # Draw title
        title_text = f"{cna.first_name} {cna.last_name}"
        title_surface = self.title_font.render(title_text, True, self.title_color)
        panel_surface.blit(title_surface, (self.padding, self.padding))
        
        # Left side - Entity visualization
        # Check if entity has animation frames
        if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
            # Calculate position and size for the sprite display
            sprite_rect = pygame.Rect(
                self.padding, 
                self.padding + 40, 
                (self.width // 2) - (self.padding * 2), 
                100
            )
            
            # Get the current animation frame
            if 0 <= self.current_frame < len(self.entity.animation_frames):
                current_frame = self.entity.animation_frames[self.current_frame]
                
                # Apply color tint if the entity has this method
                if hasattr(self.entity, 'apply_color_tint'):
                    current_frame = self.entity.apply_color_tint(current_frame)
                
                # Scale the sprite to fit the display area while maintaining aspect ratio
                frame_width, frame_height = current_frame.get_size()
                scale_factor = min(sprite_rect.width / frame_width, sprite_rect.height / frame_height)
                scaled_width = int(frame_width * scale_factor * 1.5)  # Make it 3x larger
                scaled_height = int(frame_height * scale_factor * 1.5)
                
                # Center the sprite in the display area
                sprite_x = sprite_rect.x + (sprite_rect.width - scaled_width) // 2
                sprite_y = sprite_rect.y + (sprite_rect.height - scaled_height) // 2
                
                # Scale and draw the sprite
                scaled_frame = pygame.transform.scale(current_frame, (scaled_width, scaled_height))
                panel_surface.blit(scaled_frame, (sprite_x, sprite_y))
                
            else:
                # Fallback: draw a colored rectangle
                pygame.draw.rect(panel_surface, self.entity.color, sprite_rect)
        else:
            # Fallback: draw a colored rectangle
            entity_rect = pygame.Rect(
                self.padding, 
                self.padding + 40, 
                (self.width // 2) - (self.padding * 2), 
                100
            )
            pygame.draw.rect(panel_surface, self.entity.color, entity_rect)
        
        # Add entity stats below the visualization
        stats_y = self.padding + 40 + 100 + 20  # Below the entity rectangle with some spacing
        
        # Display entity stats if available
        if hasattr(self.entity, 'thirst') or hasattr(self.entity, 'hunger') or hasattr(self.entity, 'health'):
            stats_title = self.font.render("Entity Stats", True, self.title_color)
            panel_surface.blit(stats_title, (self.padding, stats_y))
            stats_y += 30
            
            # Display thirst if available
            if hasattr(self.entity, 'thirst'):
                thirst_text = f"Thirst: {self.entity.thirst}/10"
                thirst_surface = self.small_font.render(thirst_text, True, self.text_color)
                panel_surface.blit(thirst_surface, (self.padding, stats_y))
                stats_y += 25
            
            # Display hunger if available
            if hasattr(self.entity, 'hunger'):
                hunger_text = f"Hunger: {self.entity.hunger}/10"
                hunger_surface = self.small_font.render(hunger_text, True, self.text_color)
                panel_surface.blit(hunger_surface, (self.padding, stats_y))
                stats_y += 25
            
            # Display health if available
            if hasattr(self.entity, 'health'):
                health_text = f"Health: {self.entity.health}/20"
                health_surface = self.small_font.render(health_text, True, self.text_color)
                panel_surface.blit(health_surface, (self.padding, stats_y))
                stats_y += 25
        
        # Right side - CNA attributes
        right_x = (self.width // 2) + self.padding
        y_offset = self.padding
        
        # Basic info section
        y_offset += 10
        info_text = self.font.render("Basic Information", True, self.title_color)
        panel_surface.blit(info_text, (right_x, y_offset))
        y_offset += 30
        
        # Gender, Culture, Nation
        attributes = [
            f"Gender: {cna.gender.name}",
            f"Culture: {cna.culture.name}",
            f"Nation: {cna.nation.name}",
            f"Age: {cna.age_minutes} minutes"
        ]
        
        for attr in attributes:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Health section
        y_offset += 10
        health_text = self.font.render("Health Attributes", True, self.title_color)
        panel_surface.blit(health_text, (right_x, y_offset))
        y_offset += 30
        
        health_attrs = [
            f"Physical: {cna.physical_health}/5",
            f"Generational: {cna.generational_health}/5",
            f"Mental: {cna.mental_health}/5"
        ]
        
        for attr in health_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Extended attributes section
        y_offset += 10
        ext_text = self.font.render("Extended Attributes", True, self.title_color)
        panel_surface.blit(ext_text, (right_x, y_offset))
        y_offset += 30
        
        ext_attrs = [
            f"Intelligence: {cna.intelligence_factor:.2f}",
            f"Adaptability: {cna.adaptability:.2f}",
            f"Immunity: {cna.immunity_strength:.2f}"
        ]
        
        for attr in ext_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            panel_surface.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Draw inventory section if entity has inventory
        if hasattr(self.entity, 'inventory') and self.show_inventory:
            # Draw inventory title
            inventory_title_y = self.height - 250
            inventory_title = self.font.render("Inventory", True, self.title_color)
            panel_surface.blit(inventory_title, (self.padding, inventory_title_y))
            
            # Draw inventory background
            inventory_bg_rect = pygame.Rect(
                self.padding, 
                self.height - 220,
                self.width - (self.padding * 2), 
                200
            )
            pygame.draw.rect(panel_surface, (30, 30, 30, 180), inventory_bg_rect, border_radius=5)
            pygame.draw.rect(panel_surface, (80, 80, 80, 180), inventory_bg_rect, width=2, border_radius=5)
            
            # Draw inventory slots
            inventory = self.entity.inventory
            slots_to_show = min(inventory.size, 16)  # Limit to 16 slots (4x4 grid)
            
            for i in range(slots_to_show):
                row = i // self.inventory_slots_per_row
                col = i % self.inventory_slots_per_row
                
                slot_x = self.padding + 10 + col * (self.inventory_slot_size + self.inventory_padding)
                slot_y = (self.height - 220) + 10 + row * (self.inventory_slot_size + self.inventory_padding)
                
                # Draw slot background
                slot_rect = pygame.Rect(slot_x, slot_y, self.inventory_slot_size, self.inventory_slot_size)
                
                # Different background for hover and selected slots
                if i == self.hover_slot:
                    pygame.draw.rect(panel_surface, (70, 70, 70), slot_rect)
                else:
                    pygame.draw.rect(panel_surface, (50, 50, 50), slot_rect)
                
                # Highlight selected slot
                if i == inventory.selected_slot_index:
                    pygame.draw.rect(panel_surface, (200, 200, 0), slot_rect, 2)
                else:
                    pygame.draw.rect(panel_surface, (100, 100, 100), slot_rect, 1)
                
                # Draw item if slot is not empty and not being dragged
                slot = inventory.slots[i]
                if not slot.is_empty() and (self.dragging_from_slot != i or self.dragging_item is None):
                    # Calculate item position (centered in slot)
                    item_size = self.inventory_slot_size - 8
                    item_x = slot_x + (self.inventory_slot_size - item_size) // 2
                    item_y = slot_y + (self.inventory_slot_size - item_size) // 2
                    
                    # Render item
                    slot.item.render(panel_surface, item_x, item_y, item_size, item_size)
        
        # Draw the panel on the screen
        screen.blit(panel_surface, (self.x, self.y))
        
        # Draw item being dragged (on top of everything)
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            item_size = self.inventory_slot_size - 8
            item_x = mouse_pos[0] - item_size // 2
            item_y = mouse_pos[1] - item_size // 2
            
            self.dragging_item.render(screen, item_x, item_y, item_size, item_size)

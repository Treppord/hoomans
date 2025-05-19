"""Character info panel UI element with integrated inventory display"""
import pygame
from engine.ui.elements.base import UIElement
from engine.ui.constants.colors import DARK_PANEL_BG, BORDER_COLOR, TEXT_COLOR, TITLE_COLOR

class CharacterInfoPanel(UIElement):
    """Panel that displays character information and inventory from entity data"""
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, background_color=DARK_PANEL_BG)
        self.entity = None
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
        
    def set_entity(self, entity):
        """Set the entity to display information for"""
        self.entity = entity
        self.visible = (entity is not None and entity.cna_data is not None)
        
    def update_animation(self, delta_time=1/60):
        """Update the animation frame"""
        self.animation_timer += delta_time
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
                self.current_frame = (self.current_frame + 1) % len(self.entity.animation_frames)
    
    def handle_event(self, event):
        """Handle input events"""
        if not self.visible:
            return False
            
        # First, let the base class handle dragging
        if super().handle_event(event):
            return True
            
        # Close panel on Escape
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False
            return True
            
        # Handle inventory interaction if entity has inventory
        if self.entity and hasattr(self.entity, 'inventory') and self.show_inventory:
            # Define inventory section position
            inventory_x = self.x + self.padding
            inventory_y = self.y + self.height - 220
            
            # Handle mouse movement for hover effects
            if event.type == pygame.MOUSEMOTION:
                # Check if mouse is in the inventory section
                if (inventory_x <= event.pos[0] <= inventory_x + self.width - (self.padding * 2) and
                    inventory_y <= event.pos[1] <= inventory_y + 200):
                    # Update hover slot - adjust Y position upward by half a slot height
                    adjusted_y = event.pos[1] - (self.inventory_slot_size - 64)  # Move hover area up by half slot height
                    self.entity.inventory.update_hover_slot(
                        event.pos[0], adjusted_y, 
                        inventory_x, inventory_y, 
                        self.inventory_slot_size, self.inventory_padding, 
                        self.inventory_slots_per_row
                    )
                else:
                    # Mouse not in inventory section
                    self.entity.inventory.hover_slot = -1
                    
            # Handle mouse clicks for item selection and dragging
            elif event.type == pygame.MOUSEBUTTONDOWN:
                slot_index = self.entity.inventory.get_slot_at_position(
                    event.pos[0], event.pos[1], 
                    inventory_x, inventory_y, 
                    self.inventory_slot_size, self.inventory_padding, 
                    self.inventory_slots_per_row,
                    title_height=10
                )
                
                # Left click - pick up/place items
                if event.button == 1:
                    if slot_index >= 0 and slot_index < self.entity.inventory.size:
                        # Select the slot
                        self.entity.inventory.select_slot(slot_index)
                        
                        # If already dragging an item, try to drop it
                        if self.entity.inventory.dragging_item:
                            self.entity.inventory.drop_dragged_item(slot_index)
                        else:
                            # Start dragging - take whole stack if no modifiers, otherwise take one
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                # Shift+click for quick move
                                self.entity.inventory.shift_click_slot(slot_index)
                            else:
                                # Normal click - take whole stack
                                self.entity.inventory.start_drag_item(slot_index)
                    
                    return True
                
                # Right click - split stack or use item
                elif event.button == 3:
                    if slot_index >= 0 and slot_index < self.entity.inventory.size:
                        # Handle right-click interaction
                        self.entity.inventory.right_click_slot(slot_index)
                    
                    return True
                
            # Handle mouse release for dropping items
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left click release
                if self.entity.inventory.dragging_item:
                    slot_index = self.entity.inventory.get_slot_at_position(
                        event.pos[0], event.pos[1], 
                        inventory_x, inventory_y, 
                        self.inventory_slot_size, self.inventory_padding, 
                        self.inventory_slots_per_row
                    )
                    
                    if slot_index >= 0 and slot_index < self.entity.inventory.size:
                        # Try to place the item in this slot
                        self.entity.inventory.drop_dragged_item(slot_index)
                    else:
                        # Drop the item back in the original slot if we're not over a valid slot
                        self.entity.inventory.return_dragged_item()
                
                return True
                
            return False
        
    def render(self, screen):
        if not self.visible or not self.entity or not self.entity.cna_data:
            return
            
        # Update animation
        self.update_animation()
            
        # Draw panel background
        super().render(screen)
        
        # Draw divider line down the middle
        divider_x = self.width // 2
        pygame.draw.line(screen, (100, 100, 100, 200),
                        (self.x + divider_x, self.y + 10), 
                        (self.x + divider_x, self.y + self.height - 10), 2)
        
        # Get CNA data
        cna = self.entity.cna_data
        
        # Draw title
        title_text = f"{cna.first_name} {cna.last_name}"
        title_surface = self.title_font.render(title_text, True, self.title_color)
        screen.blit(title_surface, (self.x + self.padding, self.y + self.padding))
        
        # Left side - Entity visualization
        # Check if entity has animation frames
        if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
            # Calculate position and size for the sprite display
            sprite_rect = pygame.Rect(
                self.x + self.padding, 
                self.y + self.padding + 40, 
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
                screen.blit(scaled_frame, (sprite_x, sprite_y))
                
            else:
                # Fallback: draw a colored rectangle
                pygame.draw.rect(screen, self.entity.color, sprite_rect)
        else:
            # Fallback: draw a colored rectangle
            entity_rect = pygame.Rect(
                self.x + self.padding, 
                self.y + self.padding + 40, 
                (self.width // 2) - (self.padding * 2), 
                100
            )
            pygame.draw.rect(screen, self.entity.color, entity_rect)
        
        # Add entity stats below the visualization
        stats_y = self.y + self.padding + 40 + 100 + 20  # Below the entity rectangle with some spacing
        
        # Display entity stats if available
        if hasattr(self.entity, 'thirst') or hasattr(self.entity, 'hunger') or hasattr(self.entity, 'health'):
            stats_title = self.font.render("Entity Stats", True, self.title_color)
            screen.blit(stats_title, (self.x + self.padding, stats_y))
            stats_y += 30
            
            # Display thirst if available
            if hasattr(self.entity, 'thirst'):
                thirst_text = f"Thirst: {self.entity.thirst}/10"
                thirst_surface = self.small_font.render(thirst_text, True, self.text_color)
                screen.blit(thirst_surface, (self.x + self.padding, stats_y))
                stats_y += 25
            
            # Display hunger if available
            if hasattr(self.entity, 'hunger'):
                hunger_text = f"Hunger: {self.entity.hunger}/10"
                hunger_surface = self.small_font.render(hunger_text, True, self.text_color)
                screen.blit(hunger_surface, (self.x + self.padding, stats_y))
                stats_y += 25
            
            # Display health if available
            if hasattr(self.entity, 'health'):
                health_text = f"Health: {self.entity.health}/20"
                health_surface = self.small_font.render(health_text, True, self.text_color)
                screen.blit(health_surface, (self.x + self.padding, stats_y))
                stats_y += 25
        
        # Right side - CNA attributes
        right_x = self.x + (self.width // 2) + self.padding
        y_offset = self.y + self.padding
        
        # Basic info section
        y_offset += 10
        info_text = self.font.render("Basic Information", True, self.title_color)
        screen.blit(info_text, (right_x, y_offset))
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
            screen.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Health section
        y_offset += 10
        health_text = self.font.render("Health Attributes", True, self.title_color)
        screen.blit(health_text, (right_x, y_offset))
        y_offset += 30
        
        health_attrs = [
            f"Physical: {cna.physical_health}/5",
            f"Generational: {cna.generational_health}/5",
            f"Mental: {cna.mental_health}/5"
        ]
        
        for attr in health_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            screen.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Extended attributes section
        y_offset += 10
        ext_text = self.font.render("Extended Attributes", True, self.title_color)
        screen.blit(ext_text, (right_x, y_offset))
        y_offset += 30
        
        ext_attrs = [
            f"Intelligence: {cna.intelligence_factor:.2f}",
            f"Adaptability: {cna.adaptability:.2f}",
            f"Immunity: {cna.immunity_strength:.2f}"
        ]
        
        for attr in ext_attrs:
            text_surface = self.small_font.render(attr, True, self.text_color)
            screen.blit(text_surface, (right_x, y_offset))
            y_offset += 25
        
        # Draw inventory section if entity has inventory
        if hasattr(self.entity, 'inventory') and self.show_inventory:
            # Draw inventory title
            inventory_title_y = self.y + self.height - 250
            inventory_title = self.font.render("Inventory", True, self.title_color)
            screen.blit(inventory_title, (self.x + self.padding, inventory_title_y))
            
            # Draw inventory background
            inventory_bg_rect = pygame.Rect(
                self.x + self.padding, 
                self.y + self.height - 220,
                self.width - (self.padding * 2), 
                200
            )
            pygame.draw.rect(screen, (30, 30, 30, 180), inventory_bg_rect, border_radius=5)
            pygame.draw.rect(screen, (80, 80, 80, 180), inventory_bg_rect, width=2, border_radius=5)
            
            # Draw inventory slots
            inventory = self.entity.inventory
            slots_to_show = min(inventory.size, 16)  # Limit to 16 slots (4x4 grid)
            
            for i in range(slots_to_show):
                row = i // self.inventory_slots_per_row
                col = i % self.inventory_slots_per_row
                
                slot_x = self.x + self.padding + 10 + col * (self.inventory_slot_size + self.inventory_padding)
                slot_y = (self.y + self.height - 220) + 10 + row * (self.inventory_slot_size + self.inventory_padding)
                
                # Draw slot background
                slot_rect = pygame.Rect(slot_x, slot_y, self.inventory_slot_size, self.inventory_slot_size)
                
                # Different background for hover and selected slots
                if i == inventory.hover_slot:
                    pygame.draw.rect(screen, (70, 70, 70), slot_rect)
                else:
                    pygame.draw.rect(screen, (50, 50, 50), slot_rect)
                
                # Highlight selected slot
                if i == inventory.selected_slot_index:
                    pygame.draw.rect(screen, (200, 200, 0), slot_rect, 2)
                else:
                    pygame.draw.rect(screen, (100, 100, 100), slot_rect, 1)
                
                # Draw item if slot is not empty
                slot = inventory.slots[i]
                if not slot.is_empty():
                    # Calculate item position (centered in slot)
                    item_size = self.inventory_slot_size - 8
                    item_x = slot_x + (self.inventory_slot_size - item_size) // 2
                    item_y = slot_y + (self.inventory_slot_size - item_size) // 2
                    
                    # Render item
                    slot.item.render(screen, item_x, item_y, item_size, item_size)
        
        # Draw item being dragged (on top of everything)
        if hasattr(self.entity, 'inventory') and self.entity.inventory.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            item_size = self.inventory_slot_size - 8
            item_x = mouse_pos[0] - item_size // 2
            item_y = mouse_pos[1] - item_size // 2
            
            self.entity.inventory.dragging_item.render(screen, item_x, item_y, item_size, item_size)

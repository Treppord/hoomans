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
        
        # Pre-render common UI elements
        self._cached_surfaces = {}
        self._panel_surface = None
        self._create_panel_background()
        
    def _create_panel_background(self):
        """Create a pre-rendered panel background with gradient and rounded corners"""
        self._panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Create a gradient background - ensure alpha values are high enough
        for y in range(self.height):
            # Calculate gradient color (darker at top, slightly lighter at bottom)
            alpha = 230  # Increased alpha for better visibility
            darkness = 40 - int(y / self.height * 10)  # 40 at top, 30 at bottom
            color = (darkness, darkness, darkness + 5, alpha)
            
            # Draw a horizontal line with this color
            pygame.draw.line(self._panel_surface, color, (0, y), (self.width, y))
        
        # Add a solid background to ensure visibility
        background_rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(self._panel_surface, (30, 30, 35, 220), background_rect, border_radius=8)
        
        # Add a subtle inner glow effect
        glow_width = 2
        glow_color = (60, 60, 70, 150)  # Increased alpha for better visibility
        pygame.draw.rect(self._panel_surface, glow_color, 
                        (glow_width, glow_width, 
                        self.width - glow_width*2, 
                        self.height - glow_width*2), 
                        width=glow_width, border_radius=6)
        
        # Add a clean border
        pygame.draw.rect(self._panel_surface, BORDER_COLOR, 
                        (0, 0, self.width, self.height), 
                        width=2, border_radius=8)
        
    def set_entity(self, entity):
        """Set the entity to display information for"""
        self.entity = entity
        self.visible = (entity is not None and entity.cna_data is not None)
        # Clear cached surfaces when entity changes
        self._cached_surfaces = {}
        
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
            return self._handle_inventory_interaction(event)
        
        return False
    
    def _handle_inventory_interaction(self, event):
        """Handle inventory-related mouse events"""
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
        """Render the character info panel with optimized drawing"""
        if not self.visible or not self.entity or not self.entity.cna_data:
            return
            
        # Update animation
        self.update_animation()
            
        # Draw panel background using pre-rendered surface
        screen.blit(self._panel_surface, (self.x, self.y))
        
        # Draw divider line down the middle with a subtle gradient
        self._render_divider(screen)
        
        # Get CNA data
        cna = self.entity.cna_data
        
        # Draw title with a subtle shadow effect
        self._render_title(screen, f"{cna.first_name} {cna.last_name}")
        
        # Render entity visualization (left side)
        self._render_entity_visualization(screen)
        
        # Render entity stats below visualization
        stats_y = self._render_entity_stats(screen)
        
        # Render CNA attributes (right side)
        self._render_cna_attributes(screen, cna)
        
        # Render inventory if available
        if hasattr(self.entity, 'inventory') and self.show_inventory:
            self._render_inventory(screen)
        
        # Draw item being dragged (on top of everything)
        if hasattr(self.entity, 'inventory') and self.entity.inventory.dragging_item:
            self._render_dragged_item(screen)
    
    def _render_divider(self, screen):
        """Render the divider line with a subtle gradient effect"""
        divider_x = self.x + self.width // 2
        
        # Create a gradient divider
        for i in range(5):
            alpha = 150 - i * 30  # Fade out from center
            color = (120, 120, 130, alpha)
            offset = i // 2
            pygame.draw.line(
                screen, color,
                (divider_x - offset, self.y + 10), 
                (divider_x - offset, self.y + self.height - 10), 
                1
            )
            pygame.draw.line(
                screen, color,
                (divider_x + offset, self.y + 10), 
                (divider_x + offset, self.y + self.height - 10), 
                1
            )
    
    def _render_title(self, screen, title_text):
        """Render the title with a subtle shadow effect"""
        # Cache the title surface
        if 'title' not in self._cached_surfaces:
            # Create shadow
            shadow_surface = self.title_font.render(title_text, True, (0, 0, 0))
            
            # Create main text
            title_surface = self.title_font.render(title_text, True, self.title_color)
            
            # Combine them on a new surface
            combined = pygame.Surface(
                (title_surface.get_width() + 2, title_surface.get_height() + 2),
                pygame.SRCALPHA
            )
            combined.blit(shadow_surface, (2, 2))
            combined.blit(title_surface, (0, 0))
            
            self._cached_surfaces['title'] = combined
        
        # Draw the cached title
        screen.blit(self._cached_surfaces['title'], (self.x + self.padding, self.y + self.padding))
    
    def _render_entity_visualization(self, screen):
        """Render the entity visualization (sprite or colored rectangle)"""
        # Calculate position and size for the sprite display
        sprite_rect = pygame.Rect(
            self.x + self.padding, 
            self.y + self.padding + 40, 
            (self.width // 2) - (self.padding * 2), 
            100
        )
        
        # Check if entity has animation frames
        if hasattr(self.entity, 'animation_frames') and self.entity.animation_frames:
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
                
                # Add a subtle shadow behind the sprite
                shadow_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                shadow_surface.fill((0, 0, 0, 40))
                screen.blit(shadow_surface, (sprite_x + 4, sprite_y + 4))
                
                # Draw the sprite
                screen.blit(scaled_frame, (sprite_x, sprite_y))
            else:
                # Fallback: draw a colored rectangle
                pygame.draw.rect(screen, self.entity.color, sprite_rect)
        else:
            # Fallback: draw a colored rectangle
            pygame.draw.rect(screen, self.entity.color, sprite_rect)
    
    def _render_entity_stats(self, screen):
        """Render entity stats below the visualization"""
        stats_y = self.y + self.padding + 40 + 100 + 20  # Below the entity rectangle with some spacing
        
        # Display entity stats if available
        if (hasattr(self.entity, 'thirst') or hasattr(self.entity, 'hunger') or 
            hasattr(self.entity, 'health') or hasattr(self.entity, 'comfort')):
            stats_title = self.font.render("Entity Stats", True, self.title_color)
            screen.blit(stats_title, (self.x + self.padding, stats_y))
            stats_y += 30
            
            # Collect all available stats
            available_stats = []
            
            # Define all possible stats with their labels and max values
            all_stats = [
                ('Thirst', 'thirst', 10),
                ('Hunger', 'hunger', 10),
                ('Health', 'health', 20),
                ('Comfort', 'comfort', 20)
            ]
            
            # Filter to only include stats the entity has
            for label, attr, max_val in all_stats:
                if hasattr(self.entity, attr):
                    value = getattr(self.entity, attr)
                    available_stats.append((label, value, max_val))
            
            # Define grid layout
            cols_per_row = 2
            rows = (len(available_stats) + cols_per_row - 1) // cols_per_row
            
            # Calculate column width
            col_width = 120  # Fixed width for each stat column
            col_spacing = 20  # Small gap between columns
            
            # Render stats in grid layout
            for i, (label, value, max_val) in enumerate(available_stats):
                # Calculate row and column
                row = i // cols_per_row
                col = i % cols_per_row
                
                # Calculate position
                stat_x = self.x + self.padding + (col * (col_width + col_spacing))
                stat_y = stats_y + (row * 25)
                
                # Render stat with progress bar
                self._render_stat_with_progress(screen, label, value, max_val, stat_x, stat_y)
            
            # Update stats_y for next section
            stats_y += rows * 25 + 10
        
        return stats_y
    
    def _render_stat_with_progress(self, screen, label, value, max_val, x, y):
        """Render a stat with a stylish progress bar"""
        # Render label
        stat_text = f"{label}: {value}/{max_val}"
        stat_surface = self.small_font.render(stat_text, True, self.text_color)
        screen.blit(stat_surface, (x, y))
        
        # Draw progress bar
        bar_width = 80
        bar_height = 6
        bar_x = x + 5
        bar_y = y + 18
        
        # Background bar (darker)
        pygame.draw.rect(screen, (60, 60, 60), 
                         (bar_x, bar_y, bar_width, bar_height), 
                         border_radius=3)
        
        # Calculate fill width based on value/max_val
        fill_width = int((value / max_val) * bar_width)
        
        # Determine color based on stat type
        if label == "Thirst":
            color = (80, 150, 255)  # Blue for thirst
        elif label == "Hunger":
            color = (255, 180, 60)  # Orange for hunger
        elif label == "Health":
            color = (220, 80, 80)   # Red for health
        elif label == "Comfort":
            color = (80, 220, 100)  # Green for comfort
        else:
            color = (200, 200, 200) # Default gray
        
        # Draw filled portion
        if fill_width > 0:
            pygame.draw.rect(screen, color, 
                            (bar_x, bar_y, fill_width, bar_height), 
                            border_radius=3)
            
            # Add a highlight effect at the top
            highlight_height = 2
            highlight_color = (min(color[0] + 40, 255), 
                              min(color[1] + 40, 255), 
                              min(color[2] + 40, 255))
            pygame.draw.rect(screen, highlight_color, 
                            (bar_x, bar_y, fill_width, highlight_height), 
                            border_radius=3)
    
    def _render_cna_attributes(self, screen, cna):
        """Render CNA attributes on the right side of the panel"""
        right_x = self.x + (self.width // 2) + self.padding
        y_offset = self.y + self.padding
        
        # Basic info section
        y_offset += 10
        info_text = self.font.render("Basic Information", True, self.title_color)
        screen.blit(info_text, (right_x, y_offset))
        
        # Add a subtle underline
        underline_y = y_offset + self.font.get_height() + 2
        pygame.draw.line(screen, (100, 100, 120, 150), 
                        (right_x, underline_y), 
                        (right_x + 200, underline_y), 1)
        
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
        
        # Add a subtle underline
        underline_y = y_offset + self.font.get_height() + 2
        pygame.draw.line(screen, (100, 100, 120, 150), 
                        (right_x, underline_y), 
                        (right_x + 200, underline_y), 1)
        
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
        
        # Add a subtle underline
        underline_y = y_offset + self.font.get_height() + 2
        pygame.draw.line(screen, (100, 100, 120, 150), 
                        (right_x, underline_y), 
                        (right_x + 200, underline_y), 1)
        
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
    
    def _render_inventory(self, screen):
        """Render the inventory section with a clean, modern style"""
        # Draw inventory title
        inventory_title_y = self.y + self.height - 250
        inventory_title = self.font.render("Inventory", True, self.title_color)
        screen.blit(inventory_title, (self.x + self.padding, inventory_title_y))
        
        # Add a subtle underline
        underline_y = inventory_title_y + self.font.get_height() + 2
        pygame.draw.line(screen, (100, 100, 120, 150), 
                        (self.x + self.padding, underline_y), 
                        (self.x + self.padding + 100, underline_y), 1)
        
        # Draw inventory background with a subtle gradient
        inventory_bg_rect = pygame.Rect(
            self.x + self.padding, 
            self.y + self.height - 220,
            self.width - (self.padding * 2), 
            200
        )
        
        # Create a gradient background surface if not cached
        if 'inventory_bg' not in self._cached_surfaces:
            bg_surface = pygame.Surface((inventory_bg_rect.width, inventory_bg_rect.height), pygame.SRCALPHA)
            
            # Draw gradient background
            for y in range(inventory_bg_rect.height):
                # Calculate gradient color (darker at top, slightly lighter at bottom)
                alpha = 180
                darkness = 30 - int(y / inventory_bg_rect.height * 5)  # 30 at top, 25 at bottom
                color = (darkness, darkness, darkness + 3, alpha)
                
                # Draw a horizontal line with this color
                pygame.draw.line(bg_surface, color, (0, y), (inventory_bg_rect.width, y))
            
            # Add a subtle border
            pygame.draw.rect(bg_surface, (80, 80, 80, 180), 
                            (0, 0, inventory_bg_rect.width, inventory_bg_rect.height), 
                            width=2, border_radius=5)
            
            self._cached_surfaces['inventory_bg'] = bg_surface
        
        # Draw the cached background
        screen.blit(self._cached_surfaces['inventory_bg'], (inventory_bg_rect.x, inventory_bg_rect.y))
        
        # Draw inventory slots
        inventory = self.entity.inventory
        slots_to_show = min(inventory.size, 16)  # Limit to 16 slots (4x4 grid)
        
        for i in range(slots_to_show):
            row = i // self.inventory_slots_per_row
            col = i % self.inventory_slots_per_row
            
            slot_x = self.x + self.padding + 10 + col * (self.inventory_slot_size + self.inventory_padding)
            slot_y = (self.y + self.height - 220) + 10 + row * (self.inventory_slot_size + self.inventory_padding)
            
            # Draw slot background with a subtle inset effect
            self._render_inventory_slot(screen, slot_x, slot_y, i, inventory)
    
    def _render_inventory_slot(self, screen, slot_x, slot_y, slot_index, inventory):
        """Render a single inventory slot with a modern style"""
        slot_rect = pygame.Rect(slot_x, slot_y, self.inventory_slot_size, self.inventory_slot_size)
        
        # Determine slot background color based on state
        if slot_index == inventory.hover_slot:
            bg_color = (70, 70, 70)
        else:
            bg_color = (50, 50, 50)
        
        # Draw slot background with a subtle inset effect
        pygame.draw.rect(screen, bg_color, slot_rect, border_radius=3)
        
        # Add a subtle inner shadow at the top and left
        shadow_color = (40, 40, 40)
        pygame.draw.line(screen, shadow_color, 
                        (slot_rect.left + 1, slot_rect.top + 1), 
                        (slot_rect.right - 1, slot_rect.top + 1))
        pygame.draw.line(screen, shadow_color, 
                        (slot_rect.left + 1, slot_rect.top + 1), 
                        (slot_rect.left + 1, slot_rect.bottom - 1))
        
        # Add a subtle highlight at the bottom and right
        highlight_color = (80, 80, 80)
        pygame.draw.line(screen, highlight_color, 
                        (slot_rect.left + 1, slot_rect.bottom - 1), 
                        (slot_rect.right - 1, slot_rect.bottom - 1))
        pygame.draw.line(screen, highlight_color, 
                        (slot_rect.right - 1, slot_rect.top + 1), 
                        (slot_rect.right - 1, slot_rect.bottom - 1))
        
        # Highlight selected slot
        if slot_index == inventory.selected_slot_index:
            pygame.draw.rect(screen, (200, 200, 0), slot_rect, 2, border_radius=3)
        else:
            pygame.draw.rect(screen, (100, 100, 100), slot_rect, 1, border_radius=3)
        
        # Draw item if slot is not empty
        slot = inventory.slots[slot_index]
        if not slot.is_empty():
            # Calculate item position (centered in slot)
            item_size = self.inventory_slot_size - 8
            item_x = slot_x + (self.inventory_slot_size - item_size) // 2
            item_y = slot_y + (self.inventory_slot_size - item_size) // 2
            
            # Render item
            slot.item.render(screen, item_x, item_y, item_size, item_size)
    
    def _render_dragged_item(self, screen):
        """Render the item being dragged"""
        mouse_pos = pygame.mouse.get_pos()
        item_size = self.inventory_slot_size - 8
        item_x = mouse_pos[0] - item_size // 2
        item_y = mouse_pos[1] - item_size // 2
        
        # Add a subtle shadow under the dragged item
        shadow_surface = pygame.Surface((item_size, item_size), pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, 60))
        screen.blit(shadow_surface, (item_x + 3, item_y + 3))
        
        # Render the dragged item
        self.entity.inventory.dragging_item.render(screen, item_x, item_y, item_size, item_size)

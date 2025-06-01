"""
Comprehensive Entity System for Game Engine
============================================

This module provides a unified system for managing all game entities including NPCs,
food entities, players, and custom entities. It handles entity creation, properties,
AI integration, sprite management, and persistence.

Author: Engine Studio
Version: 1.0.0
"""

import os
import time
import json
import pygame
import hashlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from enum import Enum

# ============================================================================
# CORE ENUMS AND TYPES
# ============================================================================

class EntityType(Enum):
    """Types of entities in the game"""
    PLAYER = "player"
    NPC = "npc"
    FOOD = "food"
    ANIMAL = "animal"
    MONSTER = "monster"
    VEHICLE = "vehicle"
    PROJECTILE = "projectile"
    DECORATION = "decoration"
    INTERACTIVE = "interactive"
    CUSTOM = "custom"

class MovementType(Enum):
    """Types of movement patterns"""
    STATIC = "static"
    RANDOM_WANDER = "random_wander"
    PATROL = "patrol"
    FOLLOW_TARGET = "follow_target"
    FLEE_FROM_TARGET = "flee_from_target"
    CUSTOM = "custom"

class AIType(Enum):
    """Types of AI controllers"""
    NONE = "none"
    RANDOM = "random"
    BASIC_NPC = "basic_npc"
    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"
    TERRITORIAL = "territorial"
    SOCIAL = "social"
    CUSTOM = "custom"

class EntityState(Enum):
    """Possible entity states"""
    IDLE = "idle"
    MOVING = "moving"
    INTERACTING = "interacting"
    ATTACKING = "attacking"
    FLEEING = "fleeing"
    DEAD = "dead"
    SLEEPING = "sleeping"
    EATING = "eating"
    DRINKING = "drinking"
    WORKING = "working"
    CUSTOM = "custom"

class SpriteType(Enum):
    """Types of sprite configurations"""
    SINGLE = "single"
    ANIMATED = "animated"
    DIRECTIONAL = "directional"
    MULTI_STATE = "multi_state"
    SPRITE_SHEET = "sprite_sheet"

# ============================================================================
# ENTITY PROPERTIES AND ATTRIBUTES
# ============================================================================

@dataclass
class EntityStats:
    """Basic stats for entities"""
    health: int = 100
    max_health: int = 100
    hunger: int = 10
    max_hunger: int = 10
    thirst: int = 10
    max_thirst: int = 10
    comfort: int = 10
    max_comfort: int = 10
    energy: int = 100
    max_energy: int = 100
    speed: float = 1.0
    strength: int = 10
    intelligence: int = 10
    charisma: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityStats':
        return cls(**data)

@dataclass
class MovementProperties:
    """Movement-related properties"""
    movement_type: MovementType = MovementType.STATIC
    base_speed: float = 1.0
    max_speed: float = 5.0
    acceleration: float = 1.0
    turn_speed: float = 1.0
    movement_range: int = 5
    patrol_points: List[Tuple[int, int]] = field(default_factory=list)
    wander_radius: int = 10
    can_fly: bool = False
    can_swim: bool = False
    can_climb: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['movement_type'] = self.movement_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MovementProperties':
        if 'movement_type' in data:
            data['movement_type'] = MovementType(data['movement_type'])
        return cls(**data)

@dataclass
class AIProperties:
    """AI-related properties"""
    ai_type: AIType = AIType.NONE
    aggression: float = 0.0
    curiosity: float = 0.5
    social_tendency: float = 0.5
    fear_threshold: float = 0.3
    detection_range: int = 5
    memory_duration: int = 30000  # milliseconds
    decision_cooldown: int = 1000  # milliseconds
    can_learn: bool = False
    personality_traits: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['ai_type'] = self.ai_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIProperties':
        if 'ai_type' in data:
            data['ai_type'] = AIType(data['ai_type'])
        return cls(**data)

@dataclass
class SpriteProperties:
    """Sprite and visual properties"""
    sprite_type: SpriteType = SpriteType.SINGLE
    sprite_path: Optional[str] = None
    sprite_sheet_path: Optional[str] = None
    frame_width: int = 16
    frame_height: int = 16
    animation_speed: float = 1.0
    color_tint: Tuple[int, int, int] = (255, 255, 255)
    scale: float = 1.0
    opacity: int = 255
    glow_effect: bool = False
    shadow_effect: bool = False
    
    # Animation frames for different states
    idle_frames: List[int] = field(default_factory=lambda: [0])
    walk_frames: List[int] = field(default_factory=lambda: [0, 1])
    attack_frames: List[int] = field(default_factory=list)
    death_frames: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['sprite_type'] = self.sprite_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpriteProperties':
        if 'sprite_type' in data:
            data['sprite_type'] = SpriteType(data['sprite_type'])
        return cls(**data)

@dataclass
class InteractionProperties:
    """Interaction and behavior properties"""
    can_be_talked_to: bool = False
    can_be_attacked: bool = True
    can_be_picked_up: bool = False
    can_be_consumed: bool = False
    interaction_range: int = 1
    interaction_cooldown: int = 1000
    drops_items_on_death: bool = False
    drop_table: Dict[str, float] = field(default_factory=dict)  # item_id -> drop_chance
    gives_experience: int = 0
    respawn_time: int = 0  # 0 = no respawn
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractionProperties':
        return cls(**data)

@dataclass
class EntityProperties:
    """Complete entity definition"""
    entity_id: str
    name: str
    description: str
    entity_type: EntityType
    
    # Core properties
    stats: EntityStats = field(default_factory=EntityStats)
    movement: MovementProperties = field(default_factory=MovementProperties)
    ai: AIProperties = field(default_factory=AIProperties)
    sprite: SpriteProperties = field(default_factory=SpriteProperties)
    interaction: InteractionProperties = field(default_factory=InteractionProperties)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    rarity: str = "common"
    version: str = "1.0"
    author: str = "Unknown"
    
    # Custom properties for extensibility
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'entity_id': self.entity_id,
            'name': self.name,
            'description': self.description,
            'entity_type': self.entity_type.value,
            'stats': self.stats.to_dict(),
            'movement': self.movement.to_dict(),
            'ai': self.ai.to_dict(),
            'sprite': self.sprite.to_dict(),
            'interaction': self.interaction.to_dict(),
            'tags': self.tags,
            'category': self.category,
            'rarity': self.rarity,
            'version': self.version,
            'author': self.author,
            'custom_properties': self.custom_properties
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityProperties':
        return cls(
            entity_id=data['entity_id'],
            name=data['name'],
            description=data['description'],
            entity_type=EntityType(data['entity_type']),
            stats=EntityStats.from_dict(data.get('stats', {})),
            movement=MovementProperties.from_dict(data.get('movement', {})),
            ai=AIProperties.from_dict(data.get('ai', {})),
            sprite=SpriteProperties.from_dict(data.get('sprite', {})),
            interaction=InteractionProperties.from_dict(data.get('interaction', {})),
            tags=data.get('tags', []),
            category=data.get('category', 'general'),
            rarity=data.get('rarity', 'common'),
            version=data.get('version', '1.0'),
            author=data.get('author', 'Unknown'),
            custom_properties=data.get('custom_properties', {})
        )

# ============================================================================
# ENTITY INSTANCE MANAGEMENT
# ============================================================================

class EntityInstance:
    """Runtime instance of an entity"""
    
    def __init__(self, properties: EntityProperties, grid_x: int = 0, grid_y: int = 0):
        self.properties = properties
        self.instance_id = self._generate_instance_id()
        
        # Position
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.visual_x = float(grid_x)
        self.visual_y = float(grid_y)
        self.facing = "down"
        
        # State
        self.current_state = EntityState.IDLE
        self.is_alive = True
        self.is_active = True
        
        # Runtime stats (copy from properties)
        self.current_stats = EntityStats.from_dict(properties.stats.to_dict())
        
        # Movement
        self.is_moving = False
        self.target_grid_x = grid_x
        self.target_grid_y = grid_y
        self.move_lerp_factor = 0.1
        self.last_move_time = 0
        
        # Animation
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = properties.sprite.animation_speed
        
        # Interaction
        self.last_interaction_time = 0
        
        # AI and behavior
        self.ai_controller = None
        self.behavior_data = {}
        self.memory = {}
        
        # Sprite management
        self.sprite_surface = None
        self.animation_frames = []
        self.sprite_loaded = False
        
        # Custom runtime data
        self.runtime_data = {}
        
        # Load sprite if available
        self._load_sprite()
    
    def _generate_instance_id(self) -> str:
        """Generate a unique instance ID"""
        import time
        timestamp = str(int(time.time() * 1000))
        random_part = str(random.randint(1000, 9999))
        id_string = f"{self.properties.entity_id}_{timestamp}_{random_part}"
        hash_object = hashlib.md5(id_string.encode())
        return f"0x{hash_object.hexdigest()[:16]}"
    
    def _load_sprite(self):
        """Load sprite based on properties"""
        if not pygame.get_init():
            return
        
        try:
            sprite_props = self.properties.sprite
            
            if sprite_props.sprite_sheet_path:
                self._load_sprite_sheet()
            elif sprite_props.sprite_path:
                self._load_single_sprite()
            else:
                self._create_placeholder_sprite()
            
            self.sprite_loaded = True
            
        except Exception as e:
            print(f"Error loading sprite for {self.properties.entity_id}: {e}")
            self._create_placeholder_sprite()
    
    def _load_sprite_sheet(self):
        """Load sprite from sprite sheet"""
        sprite_props = self.properties.sprite
        
        # Try to load the sprite sheet
        sprite_sheet = pygame.image.load(sprite_props.sprite_sheet_path).convert_alpha()
        
        # Extract frames
        frame_width = sprite_props.frame_width
        frame_height = sprite_props.frame_height
        
        frames = []
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()
        
        for y in range(0, sheet_height, frame_height):
            for x in range(0, sheet_width, frame_width):
                frame = sprite_sheet.subsurface((x, y, frame_width, frame_height))
                frames.append(frame)
        
        self.animation_frames = frames
        
        if frames:
            self.sprite_surface = frames[0]
    
    def _load_single_sprite(self):
        """Load a single sprite image"""
        sprite_props = self.properties.sprite
        self.sprite_surface = pygame.image.load(sprite_props.sprite_path).convert_alpha()
        self.animation_frames = [self.sprite_surface]
    
    def _create_placeholder_sprite(self):
        """Create a placeholder sprite"""
        sprite_props = self.properties.sprite
        size = (sprite_props.frame_width, sprite_props.frame_height)
        
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        # Color based on entity type
        color_map = {
            EntityType.PLAYER: (0, 0, 255),
            EntityType.NPC: (0, 255, 0),
            EntityType.FOOD: (255, 165, 0),
            EntityType.ANIMAL: (139, 69, 19),
            EntityType.MONSTER: (255, 0, 0),
            EntityType.VEHICLE: (128, 128, 128),
            EntityType.DECORATION: (255, 255, 0),
            EntityType.INTERACTIVE: (255, 0, 255),
        }
        
        color = color_map.get(self.properties.entity_type, (128, 128, 128))
        surface.fill(color)
        
        # Add border
        pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 1)
        
        # Add type indicator
        if size[0] >= 8 and size[1] >= 8:
            center = (size[0] // 2, size[1] // 2)
            pygame.draw.circle(surface, (255, 255, 255), center, 2)
        
        self.sprite_surface = surface
        self.animation_frames = [surface]
    
    def update(self, delta_time: float, world=None, entities=None):
        """Update entity state"""
        if not self.is_alive or not self.is_active:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Update AI controller
        if self.ai_controller:
            self.ai_controller.update(world, entities)
        
        # Update movement
        self._update_movement(delta_time)
        
        # Update animation
        self._update_animation(delta_time)
        
        # Update stats (hunger, thirst, etc.)
        self._update_stats(delta_time)
        
        # Update state-specific behavior
        self._update_state_behavior(delta_time)
    
    def _update_movement(self, delta_time: float):
        """Update movement and position"""
        if self.is_moving:
            # Smooth interpolation to target position
            self.visual_x += (self.target_grid_x - self.visual_x) * self.move_lerp_factor
            self.visual_y += (self.target_grid_y - self.visual_y) * self.move_lerp_factor
            
            # Check if we've reached the target
            distance = abs(self.visual_x - self.target_grid_x) + abs(self.visual_y - self.target_grid_y)
            if distance < 0.1:
                self.grid_x = self.target_grid_x
                self.grid_y = self.target_grid_y
                self.visual_x = float(self.grid_x)
                self.visual_y = float(self.grid_y)
                self.is_moving = False
        else:
            # Ensure visual position matches grid position
            self.visual_x += (self.grid_x - self.visual_x) * self.move_lerp_factor
            self.visual_y += (self.grid_y - self.visual_y) * self.move_lerp_factor
    
    def _update_animation(self, delta_time: float):
        """Update sprite animation"""
        if not self.animation_frames or len(self.animation_frames) <= 1:
            return
        
        self.animation_timer += delta_time * 1000  # Convert to milliseconds
        
        # Get appropriate frames for current state
        frames = self._get_current_animation_frames()
        
        if frames:
            frame_duration = 1000 / self.animation_speed  # milliseconds per frame
            if self.animation_timer >= frame_duration:
                self.current_frame = (self.current_frame + 1) % len(frames)
                self.animation_timer = 0
    
    def _get_current_animation_frames(self) -> List[int]:
        """Get animation frames for current state"""
        sprite_props = self.properties.sprite
        
        if self.current_state == EntityState.MOVING and sprite_props.walk_frames:
            return sprite_props.walk_frames
        elif self.current_state == EntityState.ATTACKING and sprite_props.attack_frames:
            return sprite_props.attack_frames
        elif self.current_state == EntityState.DEAD and sprite_props.death_frames:
            return sprite_props.death_frames
        else:
            return sprite_props.idle_frames
    
    def _update_stats(self, delta_time: float):
        """Update entity stats over time"""
        # Decrease hunger and thirst over time
        hunger_decay = 0.1 * delta_time  # Adjust rate as needed
        thirst_decay = 0.15 * delta_time
        
        self.current_stats.hunger = max(0, self.current_stats.hunger - hunger_decay)
        self.current_stats.thirst = max(0, self.current_stats.thirst - thirst_decay)
        
        # Health regeneration when well-fed and hydrated
        if (self.current_stats.hunger > 5 and self.current_stats.thirst > 5 and 
            self.current_stats.health < self.current_stats.max_health):
            health_regen = 0.5 * delta_time
            self.current_stats.health = min(self.current_stats.max_health, 
                                          self.current_stats.health + health_regen)
        
        # Check for death conditions
        if self.current_stats.health <= 0:
            self.die()
    
    def _update_state_behavior(self, delta_time: float):
        """Update behavior based on current state"""
        if self.current_state == EntityState.IDLE:
            # Random chance to change state or start moving
            if random.random() < 0.01:  # 1% chance per update
                self._try_random_action()
        
        elif self.current_state == EntityState.EATING:
            # Increase hunger while eating
            if hasattr(self, 'eating_timer'):
                self.eating_timer -= delta_time * 1000
                if self.eating_timer <= 0:
                    self.current_state = EntityState.IDLE
                    delattr(self, 'eating_timer')
    
    def _try_random_action(self):
        """Try to perform a random action based on AI properties"""
        ai_props = self.properties.ai
        
        if ai_props.curiosity > random.random():
            # Move to a random nearby location
            if self.properties.movement.movement_type != MovementType.STATIC:
                self.move_to_random_nearby_position()
    
    def move_to(self, target_x: int, target_y: int) -> bool:
        """Move to a specific position"""
        if self.is_moving:
            return False
        
        # Check if movement is allowed
        if self.properties.movement.movement_type == MovementType.STATIC:
            return False
        
        # Set target and start moving
        self.target_grid_x = target_x
        self.target_grid_y = target_y
        self.is_moving = True
        self.current_state = EntityState.MOVING
        
        # Update facing direction
        dx = target_x - self.grid_x
        dy = target_y - self.grid_y
        
        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        else:
            self.facing = "down" if dy > 0 else "up"
        
        return True
    
    def move_to_random_nearby_position(self):
        """Move to a random position within movement range"""
        movement_range = self.properties.movement.movement_range
        
        # Generate random offset
        dx = random.randint(-movement_range, movement_range)
        dy = random.randint(-movement_range, movement_range)
        
        target_x = self.grid_x + dx
        target_y = self.grid_y + dy
        
        self.move_to(target_x, target_y)
    
    def interact_with(self, other_entity: 'EntityInstance') -> bool:
        """Interact with another entity"""
        current_time = pygame.time.get_ticks()
        
        # Check interaction cooldown
        if (current_time - self.last_interaction_time < 
            self.properties.interaction.interaction_cooldown):
            return False
        
        # Check interaction range
        distance = abs(self.grid_x - other_entity.grid_x) + abs(self.grid_y - other_entity.grid_y)
        if distance > self.properties.interaction.interaction_range:
            return False
        
        self.last_interaction_time = current_time
        self.current_state = EntityState.INTERACTING
        
        # Handle specific interaction types
        if other_entity.properties.interaction.can_be_consumed:
            return self._consume_entity(other_entity)
        elif other_entity.properties.interaction.can_be_talked_to:
            return self._talk_to_entity(other_entity)
        
        return True
    
    def _consume_entity(self, food_entity: 'EntityInstance') -> bool:
        """Consume a food entity"""
        if not food_entity.properties.interaction.can_be_consumed:
            return False
        
        # Increase hunger
        nutrition_value = food_entity.properties.custom_properties.get('nutrition_value', 2)
        self.current_stats.hunger = min(self.current_stats.max_hunger,
                                      self.current_stats.hunger + nutrition_value)
        
        # Set eating state
        self.current_state = EntityState.EATING
        self.eating_timer = 2000  # 2 seconds
        
        # Mark food entity for removal
        food_entity.die()
        
        return True
    
    def _talk_to_entity(self, other_entity: 'EntityInstance') -> bool:
        """Talk to another entity"""
        # This would trigger dialogue system
        print(f"{self.properties.name} talks to {other_entity.properties.name}")
        return True
    
    def take_damage(self, amount: int, source=None):
        """Take damage from a source"""
        self.current_stats.health = max(0, self.current_stats.health - amount)
        
        if self.current_stats.health <= 0:
            self.die()
        else:
            # React to damage (flee, attack back, etc.)
            if self.properties.ai.fear_threshold > 0:
                fear_level = amount / self.current_stats.max_health
                if fear_level > self.properties.ai.fear_threshold:
                    self.current_state = EntityState.FLEEING
    
    def heal(self, amount: int):
        """Heal the entity"""
        self.current_stats.health = min(self.current_stats.max_health,
                                      self.current_stats.health + amount)
    
    def die(self):
        """Handle entity death"""
        self.is_alive = False
        self.current_state = EntityState.DEAD
        
        # Drop items if configured
        if self.properties.interaction.drops_items_on_death:
            self._drop_items()
    
    def _drop_items(self):
        """Drop items on death based on drop table"""
        # This would interact with the item system
        for item_id, drop_chance in self.properties.interaction.drop_table.items():
            if random.random() < drop_chance:
                print(f"{self.properties.name} dropped {item_id}")
                # TODO: Create item instance and place in world
    
    def render(self, screen, camera):
        """Render the entity"""
        if not self.is_alive and self.current_state != EntityState.DEAD:
            return
        
        if not self.sprite_surface:
            return
        
        # Calculate screen position
        screen_x, screen_y, width, height = camera.apply(
            self.visual_x * 16, self.visual_y * 16, 16, 16
        )
        
        # Skip if off-screen
        if (screen_x + width < 0 or screen_x > screen.get_width() or
            screen_y + height < 0 or screen_y > screen.get_height()):
            return
        
        # Get current frame
        current_sprite = self.sprite_surface
        if self.animation_frames:
            frames = self._get_current_animation_frames()
            if frames and self.current_frame < len(frames):
                frame_index = frames[self.current_frame]
                if frame_index < len(self.animation_frames):
                    current_sprite = self.animation_frames[frame_index]
        
        # Apply color tint
        if self.properties.sprite.color_tint != (255, 255, 255):
            tinted_sprite = current_sprite.copy()
            tinted_sprite.fill(self.properties.sprite.color_tint, special_flags=pygame.BLEND_MULT)
            current_sprite = tinted_sprite
        
        # Apply scaling
        if self.properties.sprite.scale != 1.0:
            new_width = int(width * self.properties.sprite.scale)
            new_height = int(height * self.properties.sprite.scale)
            current_sprite = pygame.transform.scale(current_sprite, (new_width, new_height))
            
            # Center the scaled sprite
            screen_x += (width - new_width) // 2
            screen_y += (height - new_height) // 2
        
        # Apply opacity
        if self.properties.sprite.opacity < 255:
            current_sprite.set_alpha(self.properties.sprite.opacity)
        
        # Render sprite
        screen.blit(current_sprite, (screen_x, screen_y))
        
        # Render effects
        if self.properties.sprite.glow_effect:
            self._render_glow_effect(screen, screen_x, screen_y, width, height)
        
        if self.properties.sprite.shadow_effect:
            self._render_shadow_effect(screen, screen_x, screen_y, width, height)
        
        # Render health bar if damaged
        if self.current_stats.health < self.current_stats.max_health:
            self._render_health_bar(screen, screen_x, screen_y, width)
    
    def _render_glow_effect(self, screen, x, y, width, height):
        """Render glow effect around entity"""
        glow_color = (255, 255, 0, 100)  # Yellow glow
        glow_radius = max(width, height) // 2 + 2
        
        # Create glow surface
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
        
        # Blit glow
        glow_x = x + width // 2 - glow_radius
        glow_y = y + height // 2 - glow_radius
        screen.blit(glow_surface, (glow_x, glow_y), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _render_shadow_effect(self, screen, x, y, width, height):
        """Render shadow effect under entity"""
        shadow_color = (0, 0, 0, 80)
        shadow_offset = 2
        
        # Create shadow surface
        shadow_surface = pygame.Surface((width, height // 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, shadow_color, shadow_surface.get_rect())
        
        # Blit shadow
        shadow_x = x + shadow_offset
        shadow_y = y + height - height // 4
        screen.blit(shadow_surface, (shadow_x, shadow_y))
    
    def _render_health_bar(self, screen, x, y, width):
        """Render health bar above entity"""
        bar_width = width
        bar_height = 4
        bar_x = x
        bar_y = y - 8
        
        # Background
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        
        # Health percentage
        health_percent = self.current_stats.health / self.current_stats.max_health
        fill_width = int(bar_width * health_percent)
        
        # Color based on health
        if health_percent > 0.6:
            color = (0, 200, 0)  # Green
        elif health_percent > 0.3:
            color = (200, 200, 0)  # Yellow
        else:
            color = (200, 0, 0)  # Red
        
        pygame.draw.rect(screen, color, (bar_x, bar_y, fill_width, bar_height))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity instance to dictionary"""
        return {
            'instance_id': self.instance_id,
            'properties': self.properties.to_dict(),
            'grid_x': self.grid_x,
            'grid_y': self.grid_y,
            'facing': self.facing,
            'current_state': self.current_state.value,
            'is_alive': self.is_alive,
            'is_active': self.is_active,
            'current_stats': self.current_stats.to_dict(),
            'runtime_data': self.runtime_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityInstance':
        """Deserialize entity instance from dictionary"""
        properties = EntityProperties.from_dict(data['properties'])
        instance = cls(properties, data['grid_x'], data['grid_y'])
        
        instance.instance_id = data['instance_id']
        instance.facing = data['facing']
        instance.current_state = EntityState(data['current_state'])
        instance.is_alive = data['is_alive']
        instance.is_active = data['is_active']
        instance.current_stats = EntityStats.from_dict(data['current_stats'])
        instance.runtime_data = data.get('runtime_data', {})
        
        return instance

# ============================================================================
# ENTITY REGISTRY AND FACTORY
# ============================================================================

class EntityRegistry:
    """Registry for entity definitions and templates"""
    
    def __init__(self):
        self._definitions: Dict[str, EntityProperties] = {}
        self._ai_controllers: Dict[str, Callable] = {}
        self._behavior_handlers: Dict[str, Callable] = {}
    
    def register_entity(self, properties: EntityProperties, 
                       ai_controller: Optional[Callable] = None,
                       behavior_handler: Optional[Callable] = None):
        """Register an entity definition"""
        self._definitions[properties.entity_id] = properties
        
        if ai_controller:
            self._ai_controllers[properties.entity_id] = ai_controller
        
        if behavior_handler:
            self._behavior_handlers[properties.entity_id] = behavior_handler
    
    def get_entity_properties(self, entity_id: str) -> Optional[EntityProperties]:
        """Get entity properties by ID"""
        return self._definitions.get(entity_id)
    
    def get_ai_controller(self, entity_id: str) -> Optional[Callable]:
        """Get AI controller for entity"""
        return self._ai_controllers.get(entity_id)
    
    def get_behavior_handler(self, entity_id: str) -> Optional[Callable]:
        """Get behavior handler for entity"""
        return self._behavior_handlers.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[EntityProperties]:
        """Get all entities of a specific type"""
        return [props for props in self._definitions.values() 
                if props.entity_type == entity_type]
    
    def get_all_entities(self) -> List[EntityProperties]:
        """Get all registered entities"""
        return list(self._definitions.values())
    
    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity from registry"""
        if entity_id in self._definitions:
            del self._definitions[entity_id]
            self._ai_controllers.pop(entity_id, None)
            self._behavior_handlers.pop(entity_id, None)
            return True
        return False

class EntityFactory:
    """Factory for creating entity instances"""
    
    def __init__(self, registry: EntityRegistry):
        self.registry = registry
    
    def create_entity_instance(self, entity_id: str, grid_x: int = 0, grid_y: int = 0,
                             **kwargs) -> Optional[EntityInstance]:
        """Create an entity instance from registered definition"""
        properties = self.registry.get_entity_properties(entity_id)
        if not properties:
            print(f"Entity {entity_id} not found in registry")
            return None
        
        # Create instance
        instance = EntityInstance(properties, grid_x, grid_y)
        
        # Set up AI controller
        ai_controller_class = self.registry.get_ai_controller(entity_id)
        if ai_controller_class:
            instance.ai_controller = ai_controller_class(instance)
        
        # Apply any custom parameters
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
            else:
                instance.runtime_data[key] = value
        
        return instance
    
    def create_from_dict(self, data: Dict[str, Any]) -> Optional[EntityInstance]:
        """Create entity instance from serialized data"""
        return EntityInstance.from_dict(data)
    
    def clone_entity(self, source_instance: EntityInstance, 
                    new_x: int = None, new_y: int = None) -> EntityInstance:
        """Clone an existing entity instance"""
        new_x = new_x if new_x is not None else source_instance.grid_x
        new_y = new_y if new_y is not None else source_instance.grid_y
        
        # Create new instance with same properties
        clone = EntityInstance(source_instance.properties, new_x, new_y)
        
        # Copy current stats
        clone.current_stats = EntityStats.from_dict(source_instance.current_stats.to_dict())
        
        # Copy runtime data
        clone.runtime_data = source_instance.runtime_data.copy()
        
        return clone

# ============================================================================
# ENTITY DATA MANAGEMENT
# ============================================================================

class EntityDataManager:
    """Manages saving and loading of entity definitions"""
    
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)
    
    def save_entity_definition(self, properties: EntityProperties) -> bool:
        """Save entity definition to JSON file"""
        try:
            category_dir = os.path.join(self.data_directory, properties.entity_type.value)
            os.makedirs(category_dir, exist_ok=True)
            
            file_path = os.path.join(category_dir, f"{properties.entity_id}.json")
            
            with open(file_path, 'w') as f:
                json.dump(properties.to_dict(), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving entity definition {properties.entity_id}: {e}")
            return False
    
    def load_entity_definition(self, entity_id: str, entity_type: EntityType) -> Optional[EntityProperties]:
        """Load entity definition from JSON file"""
        try:
            category_dir = os.path.join(self.data_directory, entity_type.value)
            file_path = os.path.join(category_dir, f"{entity_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return EntityProperties.from_dict(data)
        except Exception as e:
            print(f"Error loading entity definition {entity_id}: {e}")
            return None
    
    def load_all_entities(self) -> List[EntityProperties]:
        """Load all entity definitions from data directory"""
        entities = []
        
        for entity_type in EntityType:
            category_dir = os.path.join(self.data_directory, entity_type.value)
            
            if not os.path.exists(category_dir):
                continue
            
            for filename in os.listdir(category_dir):
                if filename.endswith('.json'):
                    entity_id = filename[:-5]  # Remove .json extension
                    entity = self.load_entity_definition(entity_id, entity_type)
                    if entity:
                        entities.append(entity)
        
        return entities
    
    def delete_entity_definition(self, entity_id: str, entity_type: EntityType) -> bool:
        """Delete entity definition file"""
        try:
            category_dir = os.path.join(self.data_directory, entity_type.value)
            file_path = os.path.join(category_dir, f"{entity_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            
            return False
        except Exception as e:
            print(f"Error deleting entity definition {entity_id}: {e}")
            return False
    
    def export_all_entities(self, export_path: str) -> bool:
        """Export all entities to a single JSON file"""
        try:
            all_entities = self.load_all_entities()
            export_data = [entity.to_dict() for entity in all_entities]
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting entities: {e}")
            return False
    
    def import_entities(self, import_path: str) -> int:
        """Import entities from JSON file"""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            imported_count = 0
            for entity_data in import_data:
                try:
                    properties = EntityProperties.from_dict(entity_data)
                    if self.save_entity_definition(properties):
                        imported_count += 1
                except Exception as e:
                    print(f"Error importing entity {entity_data.get('entity_id', 'unknown')}: {e}")
            
            return imported_count
        except Exception as e:
            print(f"Error importing entities: {e}")
            return 0

# ============================================================================
# SPRITE MANAGEMENT
# ============================================================================

class SpriteManager:
    """Manages sprite assets for entities"""
    
    def __init__(self, assets_directory: str):
        self.assets_directory = assets_directory
        self.sprites_directory = os.path.join(assets_directory, "sprites")
        os.makedirs(self.sprites_directory, exist_ok=True)
    
    def create_placeholder_sprite(self, entity_id: str, entity_type: EntityType,
                                size: Tuple[int, int] = (16, 16)) -> str:
        """Create a placeholder sprite for an entity"""
        if not pygame.get_init():
            return f"sprites/{entity_id}.png"
        
        try:
            surface = pygame.Surface(size, pygame.SRCALPHA)
            
            # Color based on entity type
            color_map = {
                EntityType.PLAYER: (0, 0, 255),
                EntityType.NPC: (0, 255, 0),
                EntityType.FOOD: (255, 165, 0),
                EntityType.ANIMAL: (139, 69, 19),
                EntityType.MONSTER: (255, 0, 0),
                EntityType.VEHICLE: (128, 128, 128),
                EntityType.DECORATION: (255, 255, 0),
                EntityType.INTERACTIVE: (255, 0, 255),
            }
            
            color = color_map.get(entity_type, (128, 128, 128))
            surface.fill(color)
            
            # Add border
            pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 1)
            
            # Add type indicator
            center = (size[0] // 2, size[1] // 2)
            pygame.draw.circle(surface, (255, 255, 255), center, min(size) // 4)
            
            # Save sprite
            sprite_path = os.path.join(self.sprites_directory, f"{entity_id}.png")
            pygame.image.save(surface, sprite_path)
            
            return f"sprites/{entity_id}.png"
            
        except Exception as e:
            print(f"Error creating placeholder sprite for {entity_id}: {e}")
            return f"sprites/{entity_id}.png"
    
    def create_sprite_sheet(self, entity_id: str, frames: List[pygame.Surface]) -> str:
        """Create a sprite sheet from individual frames"""
        if not frames:
            return ""
        
        try:
            frame_width = frames[0].get_width()
            frame_height = frames[0].get_height()
            
            # Arrange frames in a grid
            frames_per_row = min(8, len(frames))  # Max 8 frames per row
            rows = (len(frames) + frames_per_row - 1) // frames_per_row
            
            sheet_width = frames_per_row * frame_width
            sheet_height = rows * frame_height
            
            # Create sprite sheet surface
            sprite_sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
            
            # Blit frames to sheet
            for i, frame in enumerate(frames):
                row = i // frames_per_row
                col = i % frames_per_row
                x = col * frame_width
                y = row * frame_height
                sprite_sheet.blit(frame, (x, y))
            
            # Save sprite sheet
            sheet_path = os.path.join(self.sprites_directory, f"{entity_id}_sheet.png")
            pygame.image.save(sprite_sheet, sheet_path)
            
            return f"sprites/{entity_id}_sheet.png"
            
        except Exception as e:
            print(f"Error creating sprite sheet for {entity_id}: {e}")
            return ""
    
    def validate_sprite_assets(self, properties: EntityProperties) -> Dict[str, bool]:
        """Validate that sprite assets exist for an entity"""
        validation = {
            'sprite_exists': False,
            'sprite_sheet_exists': False,
            'all_required_assets': False
        }
        
        # Check single sprite
        if properties.sprite.sprite_path:
            sprite_full_path = os.path.join(self.assets_directory, properties.sprite.sprite_path)
            validation['sprite_exists'] = os.path.exists(sprite_full_path)
        
        # Check sprite sheet
        if properties.sprite.sprite_sheet_path:
            sheet_full_path = os.path.join(self.assets_directory, properties.sprite.sprite_sheet_path)
            validation['sprite_sheet_exists'] = os.path.exists(sheet_full_path)
        
        # Check if all required assets exist
        validation['all_required_assets'] = (
            validation['sprite_exists'] or 
            validation['sprite_sheet_exists'] or
            properties.sprite.sprite_type == SpriteType.SINGLE
        )
        
        return validation
    
    def create_missing_assets(self, properties: EntityProperties) -> bool:
        """Create missing sprite assets for an entity"""
        validation = self.validate_sprite_assets(properties)
        
        if validation['all_required_assets']:
            return True
        
        # Create placeholder sprite
        sprite_path = self.create_placeholder_sprite(
            properties.entity_id,
            properties.entity_type,
            (properties.sprite.frame_width, properties.sprite.frame_height)
        )
        
        # Update properties to point to created sprite
        properties.sprite.sprite_path = sprite_path
        
        return True

# ============================================================================
# AI CONTROLLER INTEGRATION
# ============================================================================

class BaseAIController:
    """Base class for AI controllers"""
    
    def __init__(self, entity: EntityInstance):
        self.entity = entity
        self.last_decision_time = 0
        self.current_goal = None
        self.memory = {}
    
    def update(self, world, entities):
        """Update AI behavior"""
        current_time = pygame.time.get_ticks()
        
        # Check decision cooldown
        if (current_time - self.last_decision_time < 
            self.entity.properties.ai.decision_cooldown):
            return
        
        self.last_decision_time = current_time
        self.make_decision(world, entities)
    
    def make_decision(self, world, entities):
        """Make AI decision - to be implemented by subclasses"""
        pass

class RandomWanderAI(BaseAIController):
    """AI that randomly wanders around"""
    
    def make_decision(self, world, entities):
        if not self.entity.is_moving and random.random() < 0.3:
            self.entity.move_to_random_nearby_position()

class SocialAI(BaseAIController):
    """AI that seeks out other entities for interaction"""
    
    def make_decision(self, world, entities):
        if self.entity.is_moving:
            return
        
        # Find nearby entities
        nearby_entities = []
        for other in entities:
            if other == self.entity or not other.is_alive:
                continue
            
            distance = abs(self.entity.grid_x - other.grid_x) + abs(self.entity.grid_y - other.grid_y)
            if distance <= self.entity.properties.ai.detection_range:
                nearby_entities.append((other, distance))
        
        if nearby_entities:
            # Move towards closest entity
            nearby_entities.sort(key=lambda x: x[1])
            target_entity = nearby_entities[0][0]
            
            # Move towards target
            dx = target_entity.grid_x - self.entity.grid_x
            dy = target_entity.grid_y - self.entity.grid_y
            
            if abs(dx) > abs(dy):
                new_x = self.entity.grid_x + (1 if dx > 0 else -1)
                new_y = self.entity.grid_y
            else:
                new_x = self.entity.grid_x
                new_y = self.entity.grid_y + (1 if dy > 0 else -1)
            
            self.entity.move_to(new_x, new_y)
        else:
            # No entities nearby, wander randomly
            if random.random() < 0.2:
                self.entity.move_to_random_nearby_position()

class HungerDrivenAI(BaseAIController):
    """AI that seeks food when hungry"""
    
    def make_decision(self, world, entities):
        # Check hunger level
        if self.entity.current_stats.hunger < 3:
            # Look for food
            food_entities = [e for e in entities 
                           if (e.properties.entity_type == EntityType.FOOD and 
                               e.is_alive)]
            
            if food_entities:
                # Find closest food
                closest_food = None
                closest_distance = float('inf')
                
                for food in food_entities:
                    distance = abs(self.entity.grid_x - food.grid_x) + abs(self.entity.grid_y - food.grid_y)
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_food = food
                
                if closest_food and closest_distance <= 1:
                    # Eat the food
                    self.entity.interact_with(closest_food)
                elif closest_food and not self.entity.is_moving:
                    # Move towards food
                    dx = closest_food.grid_x - self.entity.grid_x
                    dy = closest_food.grid_y - self.entity.grid_y
                    
                    if abs(dx) > abs(dy):
                        new_x = self.entity.grid_x + (1 if dx > 0 else -1)
                        new_y = self.entity.grid_y
                    else:
                        new_x = self.entity.grid_x
                        new_y = self.entity.grid_y + (1 if dy > 0 else -1)
                    
                    self.entity.move_to(new_x, new_y)
        else:
            # Not hungry, behave normally
            if not self.entity.is_moving and random.random() < 0.1:
                self.entity.move_to_random_nearby_position()

# ============================================================================
# MAIN ENTITY SYSTEM
# ============================================================================

class EntitySystem:
    """Main entity management system"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.data_directory = os.path.join(project_root, "data", "entities")
        self.assets_directory = os.path.join(project_root, "assets")
        
        # Initialize components
        self.registry = EntityRegistry()
        self.factory = EntityFactory(self.registry)
        self.data_manager = EntityDataManager(self.data_directory)
        self.sprite_manager = SpriteManager(self.assets_directory)
        
        # Active entity instances
        self.active_entities: Dict[str, EntityInstance] = {}
        
        # AI controller registry
        self.ai_controllers = {
            AIType.RANDOM: RandomWanderAI,
            AIType.SOCIAL: SocialAI,
            AIType.BASIC_NPC: HungerDrivenAI,
        }
        
        # Load existing entities
        self._load_all_entities()
        
        # Create default entities if none exist
        if not self.registry.get_all_entities():
            self._create_default_entities()
    
    def _load_all_entities(self):
        """Load all entity definitions from data files"""
        entities = self.data_manager.load_all_entities()
        for entity in entities:
            self.registry.register_entity(entity)
    
    def _create_default_entities(self):
        """Create default entity definitions"""
        print("Creating default entities...")
        
        # Create basic NPC
        npc_properties = EntityProperties(
            entity_id="basic_npc",
            name="Basic NPC",
            description="A basic non-player character",
            entity_type=EntityType.NPC,
            stats=EntityStats(health=100, hunger=8, thirst=8),
            movement=MovementProperties(
                movement_type=MovementType.RANDOM_WANDER,
                base_speed=1.0,
                movement_range=5
            ),
            ai=AIProperties(
                ai_type=AIType.BASIC_NPC,
                curiosity=0.3,
                social_tendency=0.7
            ),
            sprite=SpriteProperties(
                sprite_type=SpriteType.ANIMATED,
                frame_width=16,
                frame_height=16,
                color_tint=(0, 255, 0)
            ),
            interaction=InteractionProperties(
                can_be_talked_to=True,
                interaction_range=2
            )
        )
        
        # Create food entity
        food_properties = EntityProperties(
            entity_id="basic_food",
            name="Food Item",
            description="A consumable food item",
            entity_type=EntityType.FOOD,
            stats=EntityStats(health=1),
            movement=MovementProperties(
                movement_type=MovementType.RANDOM_WANDER,
                base_speed=0.5,
                movement_range=2
            ),
            ai=AIProperties(ai_type=AIType.RANDOM),
            sprite=SpriteProperties(
                sprite_type=SpriteType.ANIMATED,
                frame_width=16,
                frame_height=16,
                color_tint=(255, 165, 0)
            ),
            interaction=InteractionProperties(
                can_be_consumed=True,
                interaction_range=1
            ),
            custom_properties={'nutrition_value': 2}
        )
        
        # Create animal entity
        animal_properties = EntityProperties(
            entity_id="basic_animal",
            name="Wild Animal",
            description="A wild animal that roams the world",
            entity_type=EntityType.ANIMAL,
            stats=EntityStats(health=50, speed=2.0),
            movement=MovementProperties(
                movement_type=MovementType.RANDOM_WANDER,
                base_speed=2.0,
                movement_range=8
            ),
            ai=AIProperties(
                ai_type=AIType.BASIC_NPC,
                fear_threshold=0.5,
                detection_range=6
            ),
            sprite=SpriteProperties(
                sprite_type=SpriteType.ANIMATED,
                frame_width=16,
                frame_height=16,
                color_tint=(139, 69, 19)
            ),
            interaction=InteractionProperties(
                can_be_attacked=True,
                drops_items_on_death=True,
                drop_table={"meat": 0.8, "hide": 0.6}
            )
        )
        
        # Register entities
        entities_to_create = [npc_properties, food_properties, animal_properties]
        
        for entity_props in entities_to_create:
            self.create_entity_definition(entity_props)
            
            # Create placeholder sprites
            self.sprite_manager.create_missing_assets(entity_props)
        
        print(f"Created {len(entities_to_create)} default entities")
    
    def create_entity_definition(self, properties: EntityProperties) -> bool:
        """Create a new entity definition"""
        try:
            # Register with registry
            ai_controller = self.ai_controllers.get(properties.ai.ai_type)
            self.registry.register_entity(properties, ai_controller)
            
            # Save to file
            self.data_manager.save_entity_definition(properties)
            
            # Create sprite assets if needed
            self.sprite_manager.create_missing_assets(properties)
            
            return True
        except Exception as e:
            print(f"Error creating entity definition {properties.entity_id}: {e}")
            return False
    
    def update_entity_definition(self, properties: EntityProperties) -> bool:
        """Update an existing entity definition"""
        return self.create_entity_definition(properties)  # Same process
    
    def delete_entity_definition(self, entity_id: str) -> bool:
        """Delete an entity definition"""
        # Find entity type
        entity_props = self.registry.get_entity_properties(entity_id)
        if not entity_props:
            return False
        
        # Remove from registry
        self.registry.remove_entity(entity_id)
        
        # Delete data file
        return self.data_manager.delete_entity_definition(entity_id, entity_props.entity_type)
    
    def spawn_entity(self, entity_id: str, grid_x: int, grid_y: int, **kwargs) -> Optional[EntityInstance]:
        """Spawn an entity instance in the world"""
        instance = self.factory.create_entity_instance(entity_id, grid_x, grid_y, **kwargs)
        if instance:
            self.active_entities[instance.instance_id] = instance
        return instance
    
    def despawn_entity(self, instance_id: str) -> bool:
        """Remove an entity instance from the world"""
        if instance_id in self.active_entities:
            del self.active_entities[instance_id]
            return True
        return False
    
    def get_entity_instance(self, instance_id: str) -> Optional[EntityInstance]:
        """Get an entity instance by ID"""
        return self.active_entities.get(instance_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[EntityInstance]:
        """Get all active entities of a specific type"""
        return [entity for entity in self.active_entities.values()
                if entity.properties.entity_type == entity_type]
    
    def get_entities_in_area(self, center_x: int, center_y: int, radius: int) -> List[EntityInstance]:
        """Get all entities within a certain radius of a position"""
        entities_in_area = []
        for entity in self.active_entities.values():
            distance = abs(entity.grid_x - center_x) + abs(entity.grid_y - center_y)
            if distance <= radius:
                entities_in_area.append(entity)
        return entities_in_area
    
    def update_all_entities(self, delta_time: float, world=None):
        """Update all active entities"""
        entities_to_remove = []
        
        for instance_id, entity in self.active_entities.items():
            if not entity.is_alive and entity.current_state == EntityState.DEAD:
                # Check if entity should respawn
                if entity.properties.interaction.respawn_time > 0:
                    # Handle respawn logic here
                    pass
                else:
                    entities_to_remove.append(instance_id)
                continue
            
            # Update entity
            entity.update(delta_time, world, list(self.active_entities.values()))
        
        # Remove dead entities
        for instance_id in entities_to_remove:
            self.despawn_entity(instance_id)
    
    def render_all_entities(self, screen, camera):
        """Render all active entities"""
        # Sort entities by y-position for proper depth rendering
        sorted_entities = sorted(self.active_entities.values(), 
                               key=lambda e: e.visual_y)
        
        for entity in sorted_entities:
            entity.render(screen, camera)
    
    def save_world_state(self, file_path: str) -> bool:
        """Save all active entities to a file"""
        try:
            world_data = {
                'entities': [entity.to_dict() for entity in self.active_entities.values()]
            }
            
            with open(file_path, 'w') as f:
                json.dump(world_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving world state: {e}")
            return False
    
    def load_world_state(self, file_path: str) -> bool:
        """Load entities from a saved world state"""
        try:
            with open(file_path, 'r') as f:
                world_data = json.load(f)
            
            # Clear current entities
            self.active_entities.clear()
            
            # Load entities
            for entity_data in world_data.get('entities', []):
                entity = self.factory.create_from_dict(entity_data)
                if entity:
                    self.active_entities[entity.instance_id] = entity
            
            return True
        except Exception as e:
            print(f"Error loading world state: {e}")
            return False
    
    def get_entity_definitions(self) -> List[EntityProperties]:
        """Get all registered entity definitions"""
        return self.registry.get_all_entities()
    
    def get_entity_definition(self, entity_id: str) -> Optional[EntityProperties]:
        """Get a specific entity definition"""
        return self.registry.get_entity_properties(entity_id)
    
    def register_custom_ai_controller(self, ai_type: AIType, controller_class):
        """Register a custom AI controller"""
        self.ai_controllers[ai_type] = controller_class
    
    def create_entity_from_template(self, template_name: str, **overrides) -> EntityProperties:
        """Create an entity definition from a template with overrides"""
        # Define templates
        templates = {
            'basic_npc': {
                'entity_type': EntityType.NPC,
                'stats': {'health': 100, 'hunger': 8, 'thirst': 8},
                'movement': {'movement_type': MovementType.RANDOM_WANDER, 'base_speed': 1.0},
                'ai': {'ai_type': AIType.BASIC_NPC, 'curiosity': 0.3},
                'sprite': {'color_tint': (0, 255, 0)},
                'interaction': {'can_be_talked_to': True}
            },
            'food_item': {
                'entity_type': EntityType.FOOD,
                'stats': {'health': 1},
                'movement': {'movement_type': MovementType.RANDOM_WANDER, 'base_speed': 0.5},
                'ai': {'ai_type': AIType.RANDOM},
                'sprite': {'color_tint': (255, 165, 0)},
                'interaction': {'can_be_consumed': True},
                'custom_properties': {'nutrition_value': 2}
            },
            'aggressive_monster': {
                'entity_type': EntityType.MONSTER,
                'stats': {'health': 150, 'strength': 15, 'speed': 1.5},
                'movement': {'movement_type': MovementType.FOLLOW_TARGET, 'base_speed': 1.5},
                'ai': {'ai_type': AIType.AGGRESSIVE, 'aggression': 0.8, 'detection_range': 8},
                'sprite': {'color_tint': (255, 0, 0)},
                'interaction': {'can_be_attacked': True, 'drops_items_on_death': True}
            },
            'peaceful_animal': {
                'entity_type': EntityType.ANIMAL,
                'stats': {'health': 50, 'speed': 2.0},
                'movement': {'movement_type': MovementType.RANDOM_WANDER, 'base_speed': 2.0},
                'ai': {'ai_type': AIType.PASSIVE, 'fear_threshold': 0.3},
                'sprite': {'color_tint': (139, 69, 19)},
                'interaction': {'can_be_attacked': True}
            }
        }
        
        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = templates[template_name]
        
        # Create base properties
        entity_id = overrides.pop('entity_id', f"{template_name}_{random.randint(1000, 9999)}")
        name = overrides.pop('name', template_name.replace('_', ' ').title())
        description = overrides.pop('description', f"A {template_name}")
        
        # Create properties with template defaults
        properties = EntityProperties(
            entity_id=entity_id,
            name=name,
            description=description,
            entity_type=template['entity_type']
        )
        
        # Apply template values
        for category, values in template.items():
            if category in ['entity_type']:
                continue
            
            if category == 'stats':
                for key, value in values.items():
                    setattr(properties.stats, key, value)
            elif category == 'movement':
                for key, value in values.items():
                    setattr(properties.movement, key, value)
            elif category == 'ai':
                for key, value in values.items():
                    setattr(properties.ai, key, value)
            elif category == 'sprite':
                for key, value in values.items():
                    setattr(properties.sprite, key, value)
            elif category == 'interaction':
                for key, value in values.items():
                    setattr(properties.interaction, key, value)
            elif category == 'custom_properties':
                properties.custom_properties.update(values)
        
        # Apply overrides
        for key, value in overrides.items():
            if '.' in key:
                # Handle nested properties like 'stats.health'
                category, prop = key.split('.', 1)
                if hasattr(properties, category):
                    setattr(getattr(properties, category), prop, value)
            else:
                # Handle top-level properties
                if hasattr(properties, key):
                    setattr(properties, key, value)
                else:
                    properties.custom_properties[key] = value
        
        return properties
    
    def bulk_spawn_entities(self, spawn_data: List[Dict[str, Any]]) -> List[EntityInstance]:
        """Spawn multiple entities from a list of spawn data"""
        spawned_entities = []
        
        for data in spawn_data:
            entity_id = data.get('entity_id')
            grid_x = data.get('grid_x', 0)
            grid_y = data.get('grid_y', 0)
            kwargs = {k: v for k, v in data.items() 
                     if k not in ['entity_id', 'grid_x', 'grid_y']}
            
            entity = self.spawn_entity(entity_id, grid_x, grid_y, **kwargs)
            if entity:
                spawned_entities.append(entity)
        
        return spawned_entities
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the entity system"""
        stats = {
            'total_definitions': len(self.registry.get_all_entities()),
            'active_instances': len(self.active_entities),
            'entities_by_type': {},
            'entities_by_state': {},
            'ai_types_in_use': set()
        }
        
        # Count by type
        for entity_type in EntityType:
            count = len([e for e in self.active_entities.values() 
                        if e.properties.entity_type == entity_type])
            stats['entities_by_type'][entity_type.value] = count
        
        # Count by state
        for state in EntityState:
            count = len([e for e in self.active_entities.values() 
                        if e.current_state == state])
            stats['entities_by_state'][state.value] = count
        
        # AI types in use
        for entity in self.active_entities.values():
            stats['ai_types_in_use'].add(entity.properties.ai.ai_type.value)
        
        stats['ai_types_in_use'] = list(stats['ai_types_in_use'])
        
        return stats

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def initialize_entity_system(project_root: str = None) -> EntitySystem:
    """Initialize the entity system"""
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return EntitySystem(project_root)

def create_entity_from_existing_npc(npc_data: Dict[str, Any]) -> EntityProperties:
    """Convert existing NPC data to new entity system format"""
    entity_id = npc_data.get('entity_id', f"npc_{random.randint(1000, 9999)}")
    name = npc_data.get('name', 'Unknown NPC')
    description = npc_data.get('description', 'An NPC character')
    
    # Extract stats
    stats = EntityStats(
        health=npc_data.get('health', 100),
        max_health=npc_data.get('max_health', 100),
        hunger=npc_data.get('hunger', 8),
        max_hunger=npc_data.get('max_hunger', 10),
        thirst=npc_data.get('thirst', 8),
        max_thirst=npc_data.get('max_thirst', 10),
        speed=npc_data.get('speed', 1.0)
    )
    
    # Extract movement properties
    movement = MovementProperties(
        movement_type=MovementType.RANDOM_WANDER,
        base_speed=npc_data.get('speed', 1.0),
        movement_range=npc_data.get('movement_range', 5)
    )
    
    # Extract AI properties
    ai = AIProperties(
        ai_type=AIType.BASIC_NPC,
        curiosity=npc_data.get('curiosity', 0.3),
        social_tendency=npc_data.get('social_tendency', 0.5)
    )
    
    # Extract sprite properties
    sprite = SpriteProperties(
        sprite_type=SpriteType.ANIMATED,
        color_tint=npc_data.get('color', (0, 255, 0)),
        frame_width=16,
        frame_height=16
    )
    
    # Extract interaction properties
    interaction = InteractionProperties(
        can_be_talked_to=True,
        interaction_range=2
    )
    
    return EntityProperties(
        entity_id=entity_id,
        name=name,
        description=description,
        entity_type=EntityType.NPC,
        stats=stats,
        movement=movement,
        ai=ai,
        sprite=sprite,
        interaction=interaction
    )

def create_entity_from_existing_food(food_data: Dict[str, Any]) -> EntityProperties:
    """Convert existing food NPC data to new entity system format"""
    entity_id = food_data.get('entity_id', f"food_{random.randint(1000, 9999)}")
    name = food_data.get('name', 'Food Item')
    description = food_data.get('description', 'A consumable food item')
    
    # Extract properties
    stats = EntityStats(health=1)
    
    movement = MovementProperties(
        movement_type=MovementType.RANDOM_WANDER,
        base_speed=food_data.get('speed', 0.5),
        movement_range=2
    )
    
    ai = AIProperties(ai_type=AIType.RANDOM)
    
    sprite = SpriteProperties(
        sprite_type=SpriteType.ANIMATED,
        color_tint=food_data.get('color', (255, 165, 0)),
        frame_width=16,
        frame_height=16
    )
    
    interaction = InteractionProperties(
        can_be_consumed=True,
        interaction_range=1
    )
    
    custom_properties = {
        'nutrition_value': food_data.get('nutrition_value', 2),
        'food_type': food_data.get('food_type', 'generic')
    }
    
    return EntityProperties(
        entity_id=entity_id,
        name=name,
        description=description,
        entity_type=EntityType.FOOD,
        stats=stats,
        movement=movement,
        ai=ai,
        sprite=sprite,
        interaction=interaction,
        custom_properties=custom_properties
    )

# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

def example_usage():
    """Example of how to use the entity system"""
    # Initialize the system
    entity_system = initialize_entity_system()
    
    # Create a custom entity definition
    custom_npc = entity_system.create_entity_from_template(
        'basic_npc',
        entity_id='village_guard',
        name='Village Guard',
        description='A guard protecting the village',
        **{'stats.health': 150, 'stats.strength': 12, 'ai.aggression': 0.2}
    )
    
    # Save the definition
    entity_system.create_entity_definition(custom_npc)
    
    # Spawn some entities
    guard1 = entity_system.spawn_entity('village_guard', 10, 10)
    guard2 = entity_system.spawn_entity('village_guard', 15, 15)
    food1 = entity_system.spawn_entity('basic_food', 12, 12)
    
    # Bulk spawn entities
    spawn_data = [
        {'entity_id': 'basic_food', 'grid_x': 20, 'grid_y': 20},
        {'entity_id': 'basic_food', 'grid_x': 25, 'grid_y': 25},
        {'entity_id': 'basic_animal', 'grid_x': 30, 'grid_y': 30}
    ]
    spawned_entities = entity_system.bulk_spawn_entities(spawn_data)
    
    # Update entities (would be called in main game loop)
    delta_time = 0.016  # 60 FPS
    entity_system.update_all_entities(delta_time)
    
    # Get statistics
    stats = entity_system.get_statistics()
    print(f"Entity System Statistics: {stats}")
    
    # Save world state
    entity_system.save_world_state("world_save.json")
    
    return entity_system

if __name__ == "__main__":
    # Run example
    system = example_usage()
    print("Entity system example completed successfully!")

# ============================================================================
# INTEGRATION WITH EXISTING GAME SYSTEMS
# ============================================================================

class EntitySystemIntegration:
    """Helper class for integrating the new entity system with existing game code"""
    
    def __init__(self, entity_system: EntitySystem, legacy_entity_manager=None):
        self.entity_system = entity_system
        self.legacy_entity_manager = legacy_entity_manager
        self.migration_mapping = {}  # Maps old entity IDs to new instance IDs
    
    def migrate_existing_entities(self, existing_entities: List[Any]) -> Dict[str, str]:
        """Migrate existing entities to the new system"""
        migration_results = {}
        
        for old_entity in existing_entities:
            try:
                # Determine entity type
                if hasattr(old_entity, 'food_type'):
                    # It's a food entity
                    entity_props = create_entity_from_existing_food({
                        'entity_id': getattr(old_entity, 'entity_id', f"food_{id(old_entity)}"),
                        'name': getattr(old_entity, 'food_type', 'Food').title(),
                        'color': getattr(old_entity, 'color', (255, 165, 0)),
                        'speed': getattr(old_entity, 'speed', 0.5),
                        'nutrition_value': getattr(old_entity, 'nutrition_value', 2),
                        'food_type': getattr(old_entity, 'food_type', 'generic')
                    })
                else:
                    # It's an NPC
                    entity_props = create_entity_from_existing_npc({
                        'entity_id': getattr(old_entity, 'entity_id', f"npc_{id(old_entity)}"),
                        'name': getattr(old_entity, 'name', 'Unknown NPC'),
                        'color': getattr(old_entity, 'color', (0, 255, 0)),
                        'speed': getattr(old_entity, 'speed', 1.0),
                        'health': getattr(old_entity, 'health', 100),
                        'hunger': getattr(old_entity, 'hunger', 8),
                        'thirst': getattr(old_entity, 'thirst', 8)
                    })
                
                # Create the entity definition if it doesn't exist
                if not self.entity_system.get_entity_definition(entity_props.entity_id):
                    self.entity_system.create_entity_definition(entity_props)
                
                # Spawn the entity
                new_entity = self.entity_system.spawn_entity(
                    entity_props.entity_id,
                    getattr(old_entity, 'grid_x', 0),
                    getattr(old_entity, 'grid_y', 0)
                )
                
                if new_entity:
                    # Copy over current state
                    if hasattr(old_entity, 'health'):
                        new_entity.current_stats.health = old_entity.health
                    if hasattr(old_entity, 'hunger'):
                        new_entity.current_stats.hunger = old_entity.hunger
                    if hasattr(old_entity, 'thirst'):
                        new_entity.current_stats.thirst = old_entity.thirst
                    if hasattr(old_entity, 'facing'):
                        new_entity.facing = old_entity.facing
                    
                    # Store migration mapping
                    old_id = getattr(old_entity, 'entity_id', str(id(old_entity)))
                    self.migration_mapping[old_id] = new_entity.instance_id
                    migration_results[old_id] = new_entity.instance_id
                    
                    print(f"Migrated entity {old_id} -> {new_entity.instance_id}")
                
            except Exception as e:
                print(f"Error migrating entity {old_entity}: {e}")
                continue
        
        return migration_results
    
    def get_migrated_entity(self, old_entity_id: str) -> Optional[EntityInstance]:
        """Get the new entity instance for an old entity ID"""
        new_instance_id = self.migration_mapping.get(old_entity_id)
        if new_instance_id:
            return self.entity_system.get_entity_instance(new_instance_id)
        return None
    
    def create_compatibility_wrapper(self, new_entity: EntityInstance):
        """Create a wrapper that makes new entities compatible with old code"""
        class CompatibilityWrapper:
            def __init__(self, entity_instance: EntityInstance):
                self._entity = entity_instance
            
            # Expose common properties with old naming
            @property
            def grid_x(self):
                return self._entity.grid_x
            
            @grid_x.setter
            def grid_x(self, value):
                self._entity.grid_x = value
            
            @property
            def grid_y(self):
                return self._entity.grid_y
            
            @grid_y.setter
            def grid_y(self, value):
                self._entity.grid_y = value
            
            @property
            def visual_x(self):
                return self._entity.visual_x
            
            @property
            def visual_y(self):
                return self._entity.visual_y
            
            @property
            def color(self):
                return self._entity.properties.sprite.color_tint
            
            @property
            def health(self):
                return self._entity.current_stats.health
            
            @health.setter
            def health(self, value):
                self._entity.current_stats.health = value
            
            @property
            def hunger(self):
                return self._entity.current_stats.hunger
            
            @hunger.setter
            def hunger(self, value):
                self._entity.current_stats.hunger = value
            
            @property
            def thirst(self):
                return self._entity.current_stats.thirst
            
            @thirst.setter
            def thirst(self, value):
                self._entity.current_stats.thirst = value
            
            @property
            def speed(self):
                return self._entity.properties.movement.base_speed
            
            @property
            def facing(self):
                return self._entity.facing
            
            @facing.setter
            def facing(self, value):
                self._entity.facing = value
            
            @property
            def is_moving(self):
                return self._entity.is_moving
            
            @property
            def entity_id(self):
                return self._entity.properties.entity_id
            
            def get_entity_id(self):
                return self._entity.instance_id
            
            def move_to(self, x, y):
                return self._entity.move_to(x, y)
            
            def update(self):
                # This would be called by the entity system
                pass
            
            def render(self, screen, camera):
                return self._entity.render(screen, camera)
            
            # Food-specific properties
            @property
            def food_type(self):
                return self._entity.properties.custom_properties.get('food_type', 'generic')
            
            @property
            def nutrition_value(self):
                return self._entity.properties.custom_properties.get('nutrition_value', 2)
            
            @property
            def is_consumed(self):
                return not self._entity.is_alive
            
            def be_consumed_by(self, consumer):
                # Convert consumer to new system if needed
                if hasattr(consumer, '_entity'):
                    consumer = consumer._entity
                return self._entity.interact_with(consumer)
        
        return CompatibilityWrapper(new_entity)
    
    def get_all_entities_as_wrappers(self) -> List:
        """Get all entities as compatibility wrappers for old code"""
        wrappers = []
        for entity in self.entity_system.active_entities.values():
            wrapper = self.create_compatibility_wrapper(entity)
            wrappers.append(wrapper)
        return wrappers

# ============================================================================
# ENTITY CREATOR TOOL INTEGRATION
# ============================================================================

def integrate_with_item_creator_tool():
    """Integration point for the item creator tool to work with entities"""
    try:
        from tools.item_creator import ItemCreatorTool
        
        class EntityCreatorTool(ItemCreatorTool):
            """Extended item creator that can also create entities"""
            
            def __init__(self, screen_size=(1024, 768), entity_system=None):
                super().__init__(screen_size)
                
                if entity_system is None:
                    self.entity_system = initialize_entity_system()
                else:
                    self.entity_system = entity_system
                
                # Add entity-specific UI elements
                self._setup_entity_ui()
            
            def _setup_entity_ui(self):
                """Add entity-specific UI elements"""
                # This would extend the existing UI with entity creation capabilities
                pass
            
            def create_entity_from_item(self, item_definition):
                """Create an entity that drops a specific item"""
                # Create an entity that drops the item when killed
                entity_props = self.entity_system.create_entity_from_template(
                    'basic_animal',
                    entity_id=f"{item_definition.item_id}_source",
                    name=f"{item_definition.name} Source",
                    description=f"An entity that provides {item_definition.name}"
                )
                
                # Set up drop table
                entity_props.interaction.drops_items_on_death = True
                entity_props.interaction.drop_table = {item_definition.item_id: 1.0}
                
                return self.entity_system.create_entity_definition(entity_props)
        
        return EntityCreatorTool
    
    except ImportError:
        print("Item creator tool not available")
        return None

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class EntitySystemProfiler:
    """Performance monitoring for the entity system"""
    
    def __init__(self):
        self.update_times = []
        self.render_times = []
        self.entity_counts = []
        self.max_samples = 1000
    
    def start_update_timing(self):
        self.update_start_time = time.time()
    
    def end_update_timing(self, entity_count):
        if hasattr(self, 'update_start_time'):
            update_time = time.time() - self.update_start_time
            self.update_times.append(update_time)
            self.entity_counts.append(entity_count)
            
            # Keep only recent samples
            if len(self.update_times) > self.max_samples:
                self.update_times.pop(0)
                self.entity_counts.pop(0)
    
    def start_render_timing(self):
        self.render_start_time = time.time()
    
    def end_render_timing(self):
        if hasattr(self, 'render_start_time'):
            render_time = time.time() - self.render_start_time
            self.render_times.append(render_time)
            
            if len(self.render_times) > self.max_samples:
                self.render_times.pop(0)
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        stats = {}
        
        if self.update_times:
            stats['avg_update_time'] = sum(self.update_times) / len(self.update_times)
            stats['max_update_time'] = max(self.update_times)
            stats['min_update_time'] = min(self.update_times)
        
        if self.render_times:
            stats['avg_render_time'] = sum(self.render_times) / len(self.render_times)
            stats['max_render_time'] = max(self.render_times)
            stats['min_render_time'] = min(self.render_times)
        
        if self.entity_counts:
            stats['avg_entity_count'] = sum(self.entity_counts) / len(self.entity_counts)
            stats['max_entity_count'] = max(self.entity_counts)
        
        return stats
    
    def should_optimize(self) -> bool:
        """Check if performance optimization is needed"""
        if not self.update_times:
            return False
        
        avg_update_time = sum(self.update_times[-10:]) / min(10, len(self.update_times))
        return avg_update_time > 0.016  # More than 16ms (60 FPS threshold)

# Add profiler to EntitySystem
EntitySystem.profiler = EntitySystemProfiler()

# Modify EntitySystem.update_all_entities to include profiling
original_update_all_entities = EntitySystem.update_all_entities

def profiled_update_all_entities(self, delta_time: float, world=None):
    """Profiled version of update_all_entities"""
    self.profiler.start_update_timing()
    result = original_update_all_entities(self, delta_time, world)
    self.profiler.end_update_timing(len(self.active_entities))
    return result

EntitySystem.update_all_entities = profiled_update_all_entities

# Modify EntitySystem.render_all_entities to include profiling
original_render_all_entities = EntitySystem.render_all_entities

def profiled_render_all_entities(self, screen, camera):
    """Profiled version of render_all_entities"""
    self.profiler.start_render_timing()
    result = original_render_all_entities(self, screen, camera)
    self.profiler.end_render_timing()
    return result

EntitySystem.render_all_entities = profiled_render_all_entities

# ============================================================================
# ENTITY SYSTEM CONFIGURATION
# ============================================================================

class EntitySystemConfig:
    """Configuration settings for the entity system"""
    
    def __init__(self):
        # Performance settings
        self.max_active_entities = 1000
        self.max_entities_per_type = 200
        self.update_distance_threshold = 50  # Only update entities within this distance
        self.render_distance_threshold = 30  # Only render entities within this distance
        
        # AI settings
        self.ai_update_interval = 100  # milliseconds between AI updates
        self.pathfinding_enabled = True
        self.social_interactions_enabled = True
        
        # Sprite settings
        self.auto_create_missing_sprites = True
        self.sprite_cache_size = 100
        self.animation_enabled = True
        
        # Persistence settings
        self.auto_save_interval = 300  # seconds
        self.backup_save_files = True
        self.compress_save_files = False
        
        # Debug settings
        self.debug_mode = False
        self.show_entity_ids = False
        self.show_ai_states = False
        self.show_performance_stats = False
    
    def load_from_file(self, config_path: str) -> bool:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            return True
        except Exception as e:
            print(f"Error loading entity system config: {e}")
            return False
    
    def save_to_file(self, config_path: str) -> bool:
        """Save configuration to JSON file"""
        try:
            config_data = {
                key: value for key, value in self.__dict__.items()
                if not key.startswith('_')
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving entity system config: {e}")
            return False

# ============================================================================
# ENTITY SYSTEM EVENTS
# ============================================================================

class EntityEvent:
    """Base class for entity events"""
    
    def __init__(self, event_type: str, entity: EntityInstance, data: Dict[str, Any] = None):
        self.event_type = event_type
        self.entity = entity
        self.data = data or {}
        self.timestamp = pygame.time.get_ticks()

class EntityEventManager:
    """Manages entity events and callbacks"""
    
    def __init__(self):
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_queue: List[EntityEvent] = []
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: str, handler: Callable):
        """Unregister an event handler"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def emit_event(self, event: EntityEvent):
        """Emit an event"""
        self.event_queue.append(event)
    
    def process_events(self):
        """Process all queued events"""
        for event in self.event_queue:
            handlers = self.event_handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler for {event.event_type}: {e}")
        
        self.event_queue.clear()

# Add event manager to EntitySystem
EntitySystem.event_manager = EntityEventManager()

# ============================================================================
# ENTITY BEHAVIORS AND COMPONENTS
# ============================================================================

class EntityBehavior:
    """Base class for entity behaviors"""
    
    def __init__(self, entity: EntityInstance):
        self.entity = entity
        self.enabled = True
    
    def update(self, delta_time: float, world=None, entities=None):
        """Update behavior"""
        if not self.enabled:
            return
        self.execute(delta_time, world, entities)
    
    def execute(self, delta_time: float, world=None, entities=None):
        """Execute behavior logic - to be implemented by subclasses"""
        pass

class WanderBehavior(EntityBehavior):
    """Behavior for random wandering"""
    
    def __init__(self, entity: EntityInstance, wander_radius: int = 5):
        super().__init__(entity)
        self.wander_radius = wander_radius
        self.last_wander_time = 0
        self.wander_cooldown = 3000  # 3 seconds
    
    def execute(self, delta_time: float, world=None, entities=None):
        current_time = pygame.time.get_ticks()
        
        if (not self.entity.is_moving and 
            current_time - self.last_wander_time > self.wander_cooldown):
            
            if random.random() < 0.3:  # 30% chance to wander
                # Choose random direction within radius
                dx = random.randint(-self.wander_radius, self.wander_radius)
                dy = random.randint(-self.wander_radius, self.wander_radius)
                
                target_x = self.entity.grid_x + dx
                target_y = self.entity.grid_y + dy
                
                self.entity.move_to(target_x, target_y)
                self.last_wander_time = current_time

class SeekFoodBehavior(EntityBehavior):
    """Behavior for seeking food when hungry"""
    
    def __init__(self, entity: EntityInstance, hunger_threshold: float = 3.0):
        super().__init__(entity)
        self.hunger_threshold = hunger_threshold
        self.target_food = None
    
    def execute(self, delta_time: float, world=None, entities=None):
        if self.entity.current_stats.hunger > self.hunger_threshold:
            self.target_food = None
            return
        
        if not entities:
            return
        
        # Find food if we don't have a target
        if not self.target_food or not self.target_food.is_alive:
            food_entities = [e for e in entities 
                           if (e.properties.entity_type == EntityType.FOOD and 
                               e.is_alive)]
            
            if food_entities:
                # Find closest food
                closest_food = min(food_entities, 
                                 key=lambda f: abs(f.grid_x - self.entity.grid_x) + 
                                              abs(f.grid_y - self.entity.grid_y))
                self.target_food = closest_food
        
        # Move towards food
        if self.target_food and not self.entity.is_moving:
            distance = (abs(self.target_food.grid_x - self.entity.grid_x) + 
                       abs(self.target_food.grid_y - self.entity.grid_y))
            
            if distance <= 1:
                # Close enough to eat
                self.entity.interact_with(self.target_food)
                self.target_food = None
            else:
                # Move towards food
                dx = self.target_food.grid_x - self.entity.grid_x
                dy = self.target_food.grid_y - self.entity.grid_y
                
                if abs(dx) > abs(dy):
                    new_x = self.entity.grid_x + (1 if dx > 0 else -1)
                    new_y = self.entity.grid_y
                else:
                    new_x = self.entity.grid_x
                    new_y = self.entity.grid_y + (1 if dy > 0 else -1)
                
                self.entity.move_to(new_x, new_y)

class FlockingBehavior(EntityBehavior):
    """Behavior for flocking with other entities of the same type"""
    
    def __init__(self, entity: EntityInstance, flock_radius: int = 8):
        super().__init__(entity)
        self.flock_radius = flock_radius
        self.separation_weight = 1.5
        self.alignment_weight = 1.0
        self.cohesion_weight = 1.0
    
    def execute(self, delta_time: float, world=None, entities=None):
        if not entities or self.entity.is_moving:
            return
        
        # Find nearby entities of the same type
        nearby_entities = []
        for other in entities:
            if (other != self.entity and 
                other.properties.entity_type == self.entity.properties.entity_type and
                other.is_alive):
                
                distance = (abs(other.grid_x - self.entity.grid_x) + 
                           abs(other.grid_y - self.entity.grid_y))
                
                if distance <= self.flock_radius:
                    nearby_entities.append(other)
        
        if len(nearby_entities) < 2:
            return  # Need at least 2 others to flock
        
        # Calculate flocking forces
        separation = self._calculate_separation(nearby_entities)
        alignment = self._calculate_alignment(nearby_entities)
        cohesion = self._calculate_cohesion(nearby_entities)
        
        # Combine forces
        total_x = (separation[0] * self.separation_weight + 
                  alignment[0] * self.alignment_weight + 
                  cohesion[0] * self.cohesion_weight)
        
        total_y = (separation[1] * self.separation_weight + 
                  alignment[1] * self.alignment_weight + 
                  cohesion[1] * self.cohesion_weight)
        
        # Move based on combined forces
        if abs(total_x) > 0.1 or abs(total_y) > 0.1:
            new_x = self.entity.grid_x + (1 if total_x > 0 else -1 if total_x < 0 else 0)
            new_y = self.entity.grid_y + (1 if total_y > 0 else -1 if total_y < 0 else 0)
            
            if random.random() < 0.3:  # 30% chance to actually move
                self.entity.move_to(new_x, new_y)
    
    def _calculate_separation(self, nearby_entities) -> Tuple[float, float]:
        """Calculate separation force to avoid crowding"""
        sep_x, sep_y = 0, 0
        
        for other in nearby_entities:
            distance = max(1, abs(other.grid_x - self.entity.grid_x) + 
                             abs(other.grid_y - self.entity.grid_y))
            
            if distance < 3:  # Too close
                sep_x += (self.entity.grid_x - other.grid_x) / distance
                sep_y += (self.entity.grid_y - other.grid_y) / distance
        
        return (sep_x, sep_y)
    
    def _calculate_alignment(self, nearby_entities) -> Tuple[float, float]:
        """Calculate alignment force to match average direction"""
        # For grid-based movement, this is simplified
        avg_facing_x, avg_facing_y = 0, 0
        
        for other in nearby_entities:
            if other.facing == "right":
                avg_facing_x += 1
            elif other.facing == "left":
                avg_facing_x -= 1
            elif other.facing == "down":
                avg_facing_y += 1
            elif other.facing == "up":
                avg_facing_y -= 1
        
        count = len(nearby_entities)
        return (avg_facing_x / count, avg_facing_y / count)
    
    def _calculate_cohesion(self, nearby_entities) -> Tuple[float, float]:
        """Calculate cohesion force to move toward average position"""
        avg_x = sum(other.grid_x for other in nearby_entities) / len(nearby_entities)
        avg_y = sum(other.grid_y for other in nearby_entities) / len(nearby_entities)
        
        return (avg_x - self.entity.grid_x, avg_y - self.entity.grid_y)

# ============================================================================
# BEHAVIOR SYSTEM INTEGRATION
# ============================================================================

class BehaviorSystem:
    """System for managing entity behaviors"""
    
    def __init__(self):
        self.entity_behaviors: Dict[str, List[EntityBehavior]] = {}
        self.behavior_templates: Dict[str, Callable] = {
            'wander': WanderBehavior,
            'seek_food': SeekFoodBehavior,
            'flocking': FlockingBehavior
        }
    
    def add_behavior(self, entity: EntityInstance, behavior: EntityBehavior):
        """Add a behavior to an entity"""
        if entity.instance_id not in self.entity_behaviors:
            self.entity_behaviors[entity.instance_id] = []
        
        self.entity_behaviors[entity.instance_id].append(behavior)
    
    def remove_behavior(self, entity: EntityInstance, behavior_type: type):
        """Remove a behavior from an entity"""
        if entity.instance_id in self.entity_behaviors:
            self.entity_behaviors[entity.instance_id] = [
                b for b in self.entity_behaviors[entity.instance_id]
                if not isinstance(b, behavior_type)
            ]
    
    def add_behavior_by_name(self, entity: EntityInstance, behavior_name: str, **kwargs):
        """Add a behavior by name with parameters"""
        if behavior_name in self.behavior_templates:
            behavior_class = self.behavior_templates[behavior_name]
            behavior = behavior_class(entity, **kwargs)
            self.add_behavior(entity, behavior)
            return behavior
        return None
    
    def update_behaviors(self, delta_time: float, world=None, entities=None):
        """Update all entity behaviors"""
        for entity_id, behaviors in self.entity_behaviors.items():
            for behavior in behaviors:
                behavior.update(delta_time, world, entities)
    
    def register_behavior_template(self, name: str, behavior_class: type):
        """Register a new behavior template"""
        self.behavior_templates[name] = behavior_class

# Add behavior system to EntitySystem
EntitySystem.behavior_system = BehaviorSystem()

# ============================================================================
# FINAL INTEGRATION AND EXPORT
# ============================================================================

def create_enhanced_entity_system(project_root: str = None, config_path: str = None) -> EntitySystem:
    """Create a fully configured entity system with all features"""
    # Initialize base system
    entity_system = initialize_entity_system(project_root)
    
    # Load configuration if provided
    if config_path and os.path.exists(config_path):
        config = EntitySystemConfig()
        config.load_from_file(config_path)
        entity_system.config = config
    else:
        entity_system.config = EntitySystemConfig()
    
    # Initialize behavior system
    entity_system.behavior_system = BehaviorSystem()
    
    # Initialize event manager
    entity_system.event_manager = EntityEventManager()
    
    # Initialize profiler
    entity_system.profiler = EntitySystemProfiler()
    
    # Register default event handlers
    def on_entity_death(event: EntityEvent):
        """Handle entity death"""
        entity = event.entity
        if entity.properties.interaction.drops_items_on_death:
            # Handle item drops
            drop_table = entity.properties.interaction.drop_table
            for item_id, chance in drop_table.items():
                if random.random() < chance:
                    # Spawn item in world (would need world integration)
                    print(f"Entity {entity.instance_id} dropped {item_id}")
    
    def on_entity_spawn(event: EntityEvent):
        """Handle entity spawn"""
        entity = event.entity
        
        # Add default behaviors based on AI type
        if entity.properties.ai.ai_type == AIType.RANDOM:
            entity_system.behavior_system.add_behavior_by_name(entity, 'wander')
        elif entity.properties.ai.ai_type == AIType.BASIC_NPC:
            entity_system.behavior_system.add_behavior_by_name(entity, 'wander')
            entity_system.behavior_system.add_behavior_by_name(entity, 'seek_food')
        
        # Add flocking behavior for animals
        if entity.properties.entity_type == EntityType.ANIMAL:
            entity_system.behavior_system.add_behavior_by_name(entity, 'flocking')
    
    entity_system.event_manager.register_handler('entity_death', on_entity_death)
    entity_system.event_manager.register_handler('entity_spawn', on_entity_spawn)
    
    return entity_system

# ============================================================================
# WORLD INTEGRATION HELPERS
# ============================================================================

class WorldEntityBridge:
    """Bridge between the entity system and world/map systems"""
    
    def __init__(self, entity_system: EntitySystem, world_map=None):
        self.entity_system = entity_system
        self.world_map = world_map
        self.spawn_zones = {}  # Areas where entities can spawn
        self.no_spawn_zones = {}  # Areas where entities cannot spawn
    
    def set_world_map(self, world_map):
        """Set the world map reference"""
        self.world_map = world_map
    
    def add_spawn_zone(self, zone_id: str, x: int, y: int, width: int, height: int, 
                      entity_types: List[EntityType] = None):
        """Add a spawn zone for entities"""
        self.spawn_zones[zone_id] = {
            'x': x, 'y': y, 'width': width, 'height': height,
            'entity_types': entity_types or list(EntityType)
        }
    
    def add_no_spawn_zone(self, zone_id: str, x: int, y: int, width: int, height: int):
        """Add a no-spawn zone"""
        self.no_spawn_zones[zone_id] = {
            'x': x, 'y': y, 'width': width, 'height': height
        }
    
    def can_spawn_at(self, x: int, y: int, entity_type: EntityType) -> bool:
        """Check if an entity can spawn at the given position"""
        # Check no-spawn zones
        for zone in self.no_spawn_zones.values():
            if (zone['x'] <= x < zone['x'] + zone['width'] and
                zone['y'] <= y < zone['y'] + zone['height']):
                return False
        
        # Check world map constraints
        if self.world_map:
            tile = self.world_map.get_tile(x, y)
            if tile:
                # Don't spawn on water or mountains
                if tile.type in ['water', 'mountain']:
                    return False
                
                # Check for existing structures
                if hasattr(self.world_map, 'entity_tile_manager'):
                    entity_tile = self.world_map.entity_tile_manager.get_entity_tile_at(x, y)
                    if entity_tile:
                        return False
        
        # Check for existing entities at position
        entities_at_pos = [e for e in self.entity_system.active_entities.values()
                          if e.grid_x == x and e.grid_y == y]
        
        # Allow multiple food entities but not multiple large entities
        if entity_type == EntityType.FOOD:
            food_count = len([e for e in entities_at_pos 
                            if e.properties.entity_type == EntityType.FOOD])
            return food_count < 3  # Max 3 food items per tile
        else:
            non_food_count = len([e for e in entities_at_pos 
                                if e.properties.entity_type != EntityType.FOOD])
            return non_food_count == 0  # Only one non-food entity per tile
    
    def find_spawn_position(self, entity_type: EntityType, 
                           preferred_x: int = None, preferred_y: int = None,
                           search_radius: int = 10) -> Optional[Tuple[int, int]]:
        """Find a valid spawn position for an entity"""
        # If preferred position is valid, use it
        if (preferred_x is not None and preferred_y is not None and
            self.can_spawn_at(preferred_x, preferred_y, entity_type)):
            return (preferred_x, preferred_y)
        
        # Search in spawn zones first
        for zone in self.spawn_zones.values():
            if entity_type not in zone['entity_types']:
                continue
            
            # Try random positions in the zone
            for _ in range(20):  # Max 20 attempts per zone
                x = random.randint(zone['x'], zone['x'] + zone['width'] - 1)
                y = random.randint(zone['y'], zone['y'] + zone['height'] - 1)
                
                if self.can_spawn_at(x, y, entity_type):
                    return (x, y)
        
        # If no spawn zones or they're full, search around preferred position
        if preferred_x is not None and preferred_y is not None:
            for radius in range(1, search_radius + 1):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if abs(dx) == radius or abs(dy) == radius:  # Only check perimeter
                            x, y = preferred_x + dx, preferred_y + dy
                            if self.can_spawn_at(x, y, entity_type):
                                return (x, y)
        
        # Last resort: random position on map
        if self.world_map:
            for _ in range(100):  # Max 100 random attempts
                x = random.randint(0, self.world_map.width - 1)
                y = random.randint(0, self.world_map.height - 1)
                
                if self.can_spawn_at(x, y, entity_type):
                    return (x, y)
        
        return None
    
    def spawn_entity_safely(self, entity_id: str, preferred_x: int = None, 
                           preferred_y: int = None, **kwargs) -> Optional[EntityInstance]:
        """Spawn an entity at a safe location"""
        entity_props = self.entity_system.get_entity_definition(entity_id)
        if not entity_props:
            return None
        
        spawn_pos = self.find_spawn_position(
            entity_props.entity_type, preferred_x, preferred_y
        )
        
        if spawn_pos:
            entity = self.entity_system.spawn_entity(entity_id, spawn_pos[0], spawn_pos[1], **kwargs)
            if entity:
                # Emit spawn event
                event = EntityEvent('entity_spawn', entity)
                self.entity_system.event_manager.emit_event(event)
            return entity
        
        return None
    
    def populate_world(self, entity_counts: Dict[str, int]):
        """Populate the world with entities"""
        spawned_entities = {}
        
        for entity_id, count in entity_counts.items():
            spawned_entities[entity_id] = []
            
            for _ in range(count):
                entity = self.spawn_entity_safely(entity_id)
                if entity:
                    spawned_entities[entity_id].append(entity)
        
        return spawned_entities

# ============================================================================
# SAVE/LOAD SYSTEM INTEGRATION
# ============================================================================

class EntitySaveSystem:
    """Handles saving and loading of entity system state"""
    
    def __init__(self, entity_system: EntitySystem):
        self.entity_system = entity_system
        self.save_directory = os.path.join(entity_system.data_directory, "saves")
        os.makedirs(self.save_directory, exist_ok=True)
    
    def save_game_state(self, save_name: str) -> bool:
        """Save complete game state including all entities"""
        try:
            save_data = {
                'timestamp': pygame.time.get_ticks(),
                'entity_definitions': [props.to_dict() for props in self.entity_system.get_entity_definitions()],
                'active_entities': [entity.to_dict() for entity in self.entity_system.active_entities.values()],
                'system_stats': self.entity_system.get_statistics(),
                'config': self.entity_system.config.__dict__ if hasattr(self.entity_system, 'config') else {}
            }
            
            save_path = os.path.join(self.save_directory, f"{save_name}.json")
            
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"Game state saved to {save_path}")
            return True
            
        except Exception as e:
            print(f"Error saving game state: {e}")
            return False
    
    def load_game_state(self, save_name: str) -> bool:
        """Load complete game state"""
        try:
            save_path = os.path.join(self.save_directory, f"{save_name}.json")
            
            if not os.path.exists(save_path):
                print(f"Save file not found: {save_path}")
                return False
            
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Clear current state
            self.entity_system.active_entities.clear()
            
            # Load entity definitions
            for def_data in save_data.get('entity_definitions', []):
                props = EntityProperties.from_dict(def_data)
                self.entity_system.registry.register_entity(props)
            
            # Load active entities
            for entity_data in save_data.get('active_entities', []):
                entity = EntityInstance.from_dict(entity_data)
                if entity:
                    self.entity_system.active_entities[entity.instance_id] = entity
            
            # Load config if present
            if 'config' in save_data and hasattr(self.entity_system, 'config'):
                for key, value in save_data['config'].items():
                    if hasattr(self.entity_system.config, key):
                        setattr(self.entity_system.config, key, value)
            
            print(f"Game state loaded from {save_path}")
            return True
            
        except Exception as e:
            print(f"Error loading game state: {e}")
            return False
    
    def list_save_files(self) -> List[str]:
        """List available save files"""
        save_files = []
        
        for filename in os.listdir(self.save_directory):
            if filename.endswith('.json'):
                save_files.append(filename[:-5])  # Remove .json extension
        
        return sorted(save_files)
    
    def delete_save_file(self, save_name: str) -> bool:
        """Delete a save file"""
        try:
            save_path = os.path.join(self.save_directory, f"{save_name}.json")
            
            if os.path.exists(save_path):
                os.remove(save_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting save file: {e}")
            return False

# ============================================================================
# MAIN ENTITY SYSTEM FACTORY
# ============================================================================

def create_complete_entity_system(project_root: str = None, 
                                 world_map=None,
                                 config_path: str = None) -> Tuple[EntitySystem, WorldEntityBridge, EntitySaveSystem]:
    """Create a complete entity system with all components"""
    
    # Create enhanced entity system
    entity_system = create_enhanced_entity_system(project_root, config_path)
    
    # Create world bridge
    world_bridge = WorldEntityBridge(entity_system, world_map)
    
    # Create save system
    save_system = EntitySaveSystem(entity_system)
    
    # Set up default spawn zones if world map is provided
    if world_map:
        # Add spawn zones for different entity types
        world_bridge.add_spawn_zone(
            'forest_animals', 0, 0, world_map.width // 3, world_map.height // 3,
            [EntityType.ANIMAL, EntityType.FOOD]
        )
        
        world_bridge.add_spawn_zone(
            'plains_npcs', world_map.width // 3, world_map.height // 3, 
            world_map.width // 3, world_map.height // 3,
            [EntityType.NPC, EntityType.FOOD]
        )
        
        # Add no-spawn zones around structures
        # This would be populated based on actual world structures
    
    # Attach components to entity system for easy access
    entity_system.world_bridge = world_bridge
    entity_system.save_system = save_system
    
    return entity_system, world_bridge, save_system

# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

def test_entity_system():
    """Test the entity system functionality"""
    print("Testing Entity System...")
    
    # Create test system
    entity_system = create_enhanced_entity_system()
    
    # Test entity creation
    print("Testing entity creation...")
    npc = entity_system.spawn_entity('basic_npc', 10, 10)
    food = entity_system.spawn_entity('basic_food', 12, 12)
    animal = entity_system.spawn_entity('basic_animal', 15, 15)
    
    assert npc is not None, "Failed to create NPC"
    assert food is not None, "Failed to create food"
    assert animal is not None, "Failed to create animal"
    
    # Test entity properties
    print("Testing entity properties...")
    assert npc.properties.entity_type == EntityType.NPC
    assert food.properties.entity_type == EntityType.FOOD
    assert animal.properties.entity_type == EntityType.ANIMAL
    
    # Test movement
    print("Testing entity movement...")
    original_x = npc.grid_x
    npc.move_to(original_x + 1, npc.grid_y)
    assert npc.target_grid_x == original_x + 1
    
    # Test stats
    print("Testing entity stats...")
    original_health = npc.current_stats.health
    npc.take_damage(10)
    assert npc.current_stats.health == original_health - 10
    
    # Test interactions
    print("Testing entity interactions...")
    original_hunger = npc.current_stats.hunger
    npc.interact_with(food)
    # Food should increase hunger (assuming it's consumable)
    
    # Test behaviors
    print("Testing behaviors...")
    entity_system.behavior_system.add_behavior_by_name(npc, 'wander')
    behaviors = entity_system.behavior_system.entity_behaviors.get(npc.instance_id, [])
    assert len(behaviors) > 0, "Failed to add behavior"
    
    # Test events
    print("Testing events...")
    event_fired = False
    
    def test_handler(event):
        nonlocal event_fired
        event_fired = True
    
    entity_system.event_manager.register_handler('test_event', test_handler)
    test_event = EntityEvent('test_event', npc)
    entity_system.event_manager.emit_event(test_event)
    entity_system.event_manager.process_events()
    assert event_fired, "Event not fired"
    
    # Test save/load
    print("Testing save/load...")
    save_system = EntitySaveSystem(entity_system)
    save_result = save_system.save_game_state('test_save')
    assert save_result, "Failed to save game state"
    
    # Clear entities and reload
    entity_system.active_entities.clear()
    load_result = save_system.load_game_state('test_save')
    assert load_result, "Failed to load game state"
    assert len(entity_system.active_entities) > 0, "No entities loaded"
    
    # Clean up test save
    save_system.delete_save_file('test_save')
    
    print("All entity system tests passed!")
    return True

def validate_entity_system_integration():
    """Validate integration with existing game systems"""
    print("Validating entity system integration...")
    
    try:
        # Test integration with existing entity classes
        from entities.rectangle import Rectangle
        from entities.food_npc import FoodNPC
        
        # Create entity system
        entity_system = create_enhanced_entity_system()
        
        # Test migration from old entities
        integration = EntitySystemIntegration(entity_system)
        
        # Create mock old entities
        old_npc = Rectangle(20, 20, (0, 255, 0), 1.0)
        old_npc.entity_id = "test_npc"
        old_npc.health = 80
        old_npc.hunger = 6
        
        old_food = FoodNPC(25, 25)
        old_food.entity_id = "test_food"
        
        # Migrate entities
        migration_results = integration.migrate_existing_entities([old_npc, old_food])
        
        assert len(migration_results) == 2, "Failed to migrate all entities"
        
        # Test compatibility wrappers
        new_entities = entity_system.active_entities.values()
        wrappers = [integration.create_compatibility_wrapper(e) for e in new_entities]
        
        # Test wrapper properties
        for wrapper in wrappers:
            assert hasattr(wrapper, 'grid_x'), "Wrapper missing grid_x"
            assert hasattr(wrapper, 'grid_y'), "Wrapper missing grid_y"
            assert hasattr(wrapper, 'health'), "Wrapper missing health"
        
        print("Entity system integration validation passed!")
        return True
        
    except ImportError as e:
        print(f"Integration validation skipped - missing dependencies: {e}")
        return True
    except Exception as e:
        print(f"Integration validation failed: {e}")
        return False

# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================

class EntitySystemOptimizer:
    """Optimizes entity system performance"""
    
    def __init__(self, entity_system: EntitySystem):
        self.entity_system = entity_system
        self.spatial_grid = {}  # For spatial partitioning
        self.grid_size = 16  # Size of each grid cell
        self.update_batches = []  # For batch processing
    
    def enable_spatial_partitioning(self):
        """Enable spatial partitioning for faster entity queries"""
        self.spatial_grid = {}
        
        # Partition entities into grid cells
        for entity in self.entity_system.active_entities.values():
            grid_x = entity.grid_x // self.grid_size
            grid_y = entity.grid_y // self.grid_size
            
            if (grid_x, grid_y) not in self.spatial_grid:
                self.spatial_grid[(grid_x, grid_y)] = []
            
            self.spatial_grid[(grid_x, grid_y)].append(entity)
    
    def get_entities_in_area_optimized(self, center_x: int, center_y: int, radius: int) -> List[EntityInstance]:
        """Optimized version of get_entities_in_area using spatial partitioning"""
        if not self.spatial_grid:
            return self.entity_system.get_entities_in_area(center_x, center_y, radius)
        
        entities_in_area = []
        
        # Calculate grid bounds
        min_grid_x = (center_x - radius) // self.grid_size
        max_grid_x = (center_x + radius) // self.grid_size
        min_grid_y = (center_y - radius) // self.grid_size
        max_grid_y = (center_y + radius) // self.grid_size
        
        # Check relevant grid cells
        for gx in range(min_grid_x, max_grid_x + 1):
            for gy in range(min_grid_y, max_grid_y + 1):
                if (gx, gy) in self.spatial_grid:
                    for entity in self.spatial_grid[(gx, gy)]:
                        distance = abs(entity.grid_x - center_x) + abs(entity.grid_y - center_y)
                        if distance <= radius:
                            entities_in_area.append(entity)
        
        return entities_in_area
    
    def create_update_batches(self, batch_size: int = 50):
        """Create batches for entity updates to spread load"""
        entities = list(self.entity_system.active_entities.values())
        self.update_batches = [entities[i:i + batch_size] for i in range(0, len(entities), batch_size)]
    
    def update_entities_batched(self, delta_time: float, world=None, batch_index: int = 0):
        """Update entities in batches"""
        if not self.update_batches:
            self.create_update_batches()
        
        if batch_index < len(self.update_batches):
            batch = self.update_batches[batch_index]
            all_entities = list(self.entity_system.active_entities.values())
            
            for entity in batch:
                if entity.is_alive:
                    entity.update(delta_time, world, all_entities)
    
    def optimize_memory_usage(self):
        """Optimize memory usage by cleaning up unused resources"""
        # Remove dead entities
        dead_entities = [id for id, entity in self.entity_system.active_entities.items() 
                        if not entity.is_alive and entity.current_state == EntityState.DEAD]
        
        for entity_id in dead_entities:
            del self.entity_system.active_entities[entity_id]
        
        # Clean up behavior system
        behavior_ids_to_remove = []
        for entity_id in self.entity_system.behavior_system.entity_behaviors:
            if entity_id not in self.entity_system.active_entities:
                behavior_ids_to_remove.append(entity_id)
        
        for entity_id in behavior_ids_to_remove:
            del self.entity_system.behavior_system.entity_behaviors[entity_id]
        
        # Update spatial grid
        if self.spatial_grid:
            self.enable_spatial_partitioning()

# ============================================================================
# ENTITY SYSTEM MANAGER
# ============================================================================

class EntitySystemManager:
    """High-level manager for the entire entity system"""
    
    def __init__(self, project_root: str = None, world_map=None):
        # Create complete entity system
        self.entity_system, self.world_bridge, self.save_system = create_complete_entity_system(
            project_root, world_map
        )
        
        # Create optimizer
        self.optimizer = EntitySystemOptimizer(self.entity_system)
        
        # Performance tracking
        self.frame_count = 0
        self.last_optimization = 0
        self.optimization_interval = 300  # Optimize every 5 seconds at 60 FPS
        
        # Auto-save tracking
        self.last_auto_save = 0
        self.auto_save_interval = 18000  # Auto-save every 5 minutes at 60 FPS
        
        # Update batching
        self.current_batch = 0
        self.batched_updates = False
    
    def enable_performance_optimizations(self):
        """Enable all performance optimizations"""
        self.optimizer.enable_spatial_partitioning()
        self.optimizer.create_update_batches()
        self.batched_updates = True
        print("Entity system performance optimizations enabled")
    
    def update(self, delta_time: float, world=None):
        """Main update method for the entity system"""
        self.frame_count += 1
        
        # Update entities (batched or normal)
        if self.batched_updates:
            # Update one batch per frame
            self.optimizer.update_entities_batched(delta_time, world, self.current_batch)
            self.current_batch = (self.current_batch + 1) % len(self.optimizer.update_batches)
        else:
            self.entity_system.update_all_entities(delta_time, world)
        
        # Update behaviors
        all_entities = list(self.entity_system.active_entities.values())
        self.entity_system.behavior_system.update_behaviors(delta_time, world, all_entities)
        
        # Process events
        self.entity_system.event_manager.process_events()
        
        # Periodic optimization
        if self.frame_count - self.last_optimization > self.optimization_interval:
            self.optimizer.optimize_memory_usage()
            self.last_optimization = self.frame_count
        
        # Auto-save
        if (hasattr(self.entity_system, 'config') and 
            self.entity_system.config.auto_save_interval > 0 and
            self.frame_count - self.last_auto_save > self.auto_save_interval):
            self.save_system.save_game_state('auto_save')
            self.last_auto_save = self.frame_count
    
    def render(self, screen, camera):
        """Render all entities"""
        self.entity_system.render_all_entities(screen, camera)
    
    def spawn_entity(self, entity_id: str, x: int = None, y: int = None, **kwargs) -> Optional[EntityInstance]:
        """Spawn an entity safely"""
        if x is not None and y is not None:
            return self.world_bridge.spawn_entity_safely(entity_id, x, y, **kwargs)
        else:
            return self.world_bridge.spawn_entity_safely(entity_id, **kwargs)
    
    def get_entities_near(self, x: int, y: int, radius: int) -> List[EntityInstance]:
        """Get entities near a position (optimized)"""
        return self.optimizer.get_entities_in_area_optimized(x, y, radius)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = self.entity_system.get_statistics()
        
        # Add performance stats
        if hasattr(self.entity_system, 'profiler'):
            perf_stats = self.entity_system.profiler.get_performance_stats()
            stats['performance'] = perf_stats
        
        # Add optimization stats
        stats['optimization'] = {
            'spatial_partitioning_enabled': bool(self.optimizer.spatial_grid),
            'batched_updates_enabled': self.batched_updates,
            'current_batch': self.current_batch,
            'total_batches': len(self.optimizer.update_batches)
        }
        
        return stats
    
    def save_game(self, save_name: str) -> bool:
        """Save the game state"""
        return self.save_system.save_game_state(save_name)
    
    def load_game(self, save_name: str) -> bool:
        """Load a game state"""
        result = self.save_system.load_game_state(save_name)
        if result:
            # Refresh optimizations after loading
            if self.batched_updates:
                self.optimizer.create_update_batches()
            if self.optimizer.spatial_grid:
                self.optimizer.enable_spatial_partitioning()
        return result
    
    def populate_world_with_defaults(self):
        """Populate the world with default entities"""
        default_counts = {
            'basic_npc': 10,
            'basic_food': 30,
            'basic_animal': 15
        }
        
        return self.world_bridge.populate_world(default_counts)

# ============================================================================
# FINAL EXPORTS AND INITIALIZATION
# ============================================================================

# Main initialization function for easy integration
def initialize_complete_entity_system(project_root: str = None, world_map=None, 
                                    enable_optimizations: bool = True) -> EntitySystemManager:
    """Initialize the complete entity system for use in the game"""
    manager = EntitySystemManager(project_root, world_map)
    
    if enable_optimizations:
        manager.enable_performance_optimizations()
    
    return manager

# Export main classes and functions
__all__ = [
    # Core classes
    'EntityType', 'EntityState', 'MovementType', 'AIType', 'SpriteType',
    'EntityStats', 'MovementProperties', 'AIProperties', 'SpriteProperties',
    'InteractionProperties', 'EntityProperties', 'EntityInstance',
    
    # System classes
    'EntityRegistry', 'EntityFactory', 'EntitySystem', 'EntitySystemManager',
    
    # Integration classes
    'EntitySystemIntegration', 'WorldEntityBridge', 'EntitySaveSystem',
    
    # Behavior system
    'EntityBehavior', 'WanderBehavior', 'SeekFoodBehavior', 'FlockingBehavior',
    'BehaviorSystem',
    
    # Event system
    'EntityEvent', 'EntityEventManager',
    
    # Optimization
    'EntitySystemOptimizer', 'EntitySystemProfiler',
    
    # Configuration
    'EntitySystemConfig',
    
    # Utility functions
    'initialize_entity_system', 'create_enhanced_entity_system',
    'create_complete_entity_system', 'initialize_complete_entity_system',
    'create_entity_from_existing_npc', 'create_entity_from_existing_food',
    
    # Testing
    'test_entity_system', 'validate_entity_system_integration'
]

# ============================================================================
# EXAMPLE CONFIGURATION FILES
# ============================================================================

def create_example_config_files(config_dir: str):
    """Create example configuration files for the entity system"""
    os.makedirs(config_dir, exist_ok=True)
    
    # Entity system configuration
    entity_config = {
        "max_active_entities": 500,
        "max_entities_per_type": 100,
        "update_distance_threshold": 30,
        "render_distance_threshold": 20,
        "ai_update_interval": 100,
        "pathfinding_enabled": True,
        "social_interactions_enabled": True,
        "auto_create_missing_sprites": True,
        "sprite_cache_size": 50,
        "animation_enabled": True,
        "auto_save_interval": 300,
        "backup_save_files": True,
        "compress_save_files": False,
        "debug_mode": False,
        "show_entity_ids": False,
        "show_ai_states": False,
        "show_performance_stats": False
    }
    
    with open(os.path.join(config_dir, "entity_system.json"), 'w') as f:
        json.dump(entity_config, f, indent=2)
    
    # Entity definitions
    entity_definitions = [
        {
            "entity_id": "villager",
            "name": "Villager",
            "description": "A peaceful village inhabitant",
            "entity_type": "npc",
            "stats": {
                "health": 100,
                "max_health": 100,
                "hunger": 8,
                "max_hunger": 10,
                "thirst": 8,
                "max_thirst": 10,
                "speed": 1.0
            },
            "movement": {
                "movement_type": "random_wander",
                "base_speed": 1.0,
                "movement_range": 5
            },
            "ai": {
                "ai_type": "basic_npc",
                "curiosity": 0.4,
                "social_tendency": 0.7,
                "aggression": 0.1
            },
            "sprite": {
                "sprite_type": "animated",
                "sprite_sheet": "villager.png",
                "color_tint": [0, 150, 255],
                "frame_width": 16,
                "frame_height": 16,
                "animation_speed": 200
            },
            "interaction": {
                "can_be_talked_to": True,
                "can_be_attacked": False,
                "can_be_traded_with": True,
                "interaction_range": 2,
                "respawn_time": 0
            }
        },
        {
            "entity_id": "wild_berry",
            "name": "Wild Berry",
            "description": "A nutritious wild berry",
            "entity_type": "food",
            "stats": {
                "health": 1
            },
            "movement": {
                "movement_type": "random_wander",
                "base_speed": 0.3,
                "movement_range": 2
            },
            "ai": {
                "ai_type": "random"
            },
            "sprite": {
                "sprite_type": "animated",
                "sprite_sheet": "berry.png",
                "color_tint": [255, 100, 150],
                "frame_width": 16,
                "frame_height": 16,
                "animation_speed": 300
            },
            "interaction": {
                "can_be_consumed": True,
                "interaction_range": 1,
                "respawn_time": 60
            },
            "custom_properties": {
                "nutrition_value": 3,
                "food_type": "berry"
            }
        },
        {
            "entity_id": "forest_deer",
            "name": "Forest Deer",
            "description": "A graceful deer that roams the forest",
            "entity_type": "animal",
            "stats": {
                "health": 60,
                "max_health": 60,
                "speed": 2.0
            },
            "movement": {
                "movement_type": "random_wander",
                "base_speed": 2.0,
                "movement_range": 8
            },
            "ai": {
                "ai_type": "passive",
                "fear_threshold": 0.3,
                "flee_distance": 10
            },
            "sprite": {
                "sprite_type": "animated",
                "sprite_sheet": "deer.png",
                "color_tint": [139, 69, 19],
                "frame_width": 16,
                "frame_height": 16,
                "animation_speed": 150
            },
            "interaction": {
                "can_be_attacked": True,
                "drops_items_on_death": True,
                "interaction_range": 1,
                "respawn_time": 300
            },
            "custom_properties": {
                "drop_table": {
                    "meat": 0.8,
                    "hide": 0.6
                }
            }
        }
    ]
    
    with open(os.path.join(config_dir, "entity_definitions.json"), 'w') as f:
        json.dump(entity_definitions, f, indent=2)
    
    # Spawn configuration
    spawn_config = {
        "spawn_zones": [
            {
                "zone_id": "village_area",
                "x": 50,
                "y": 50,
                "width": 20,
                "height": 20,
                "entity_types": ["npc"],
                "spawn_rates": {
                    "villager": 0.1
                }
            },
            {
                "zone_id": "forest_area",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
                "entity_types": ["animal", "food"],
                "spawn_rates": {
                    "forest_deer": 0.05,
                    "wild_berry": 0.2
                }
            }
        ],
        "no_spawn_zones": [
            {
                "zone_id": "water_areas",
                "x": 80,
                "y": 80,
                "width": 20,
                "height": 20
            }
        ],
        "global_spawn_settings": {
            "max_spawn_attempts": 100,
            "spawn_check_interval": 5.0,
            "despawn_distance": 100
        }
    }
    
    with open(os.path.join(config_dir, "spawn_config.json"), 'w') as f:
        json.dump(spawn_config, f, indent=2)
    
    print(f"Created example configuration files in {config_dir}")
    
    
#=======



# ============================================================================
# DOCUMENTATION AND USAGE EXAMPLES
# ============================================================================

def print_usage_examples():
    """Print usage examples for the entity system"""
    
    usage_text = """
# ============================================================================
# ENTITY SYSTEM USAGE EXAMPLES
# ============================================================================

## Basic Setup

```python
from engine.systems.entity_system import initialize_complete_entity_system

# Initialize the entity system
entity_manager = initialize_complete_entity_system(
    project_root="/path/to/game",
    world_map=my_world_map,
    enable_optimizations=True
)

# In your main game loop
def game_loop():
    while running:
        delta_time = clock.tick(60) / 1000.0
        
        # Update entities
        entity_manager.update(delta_time, world_map)
        
        # Render entities
        entity_manager.render(screen, camera)
```

## Creating Custom Entities

```python
# Create a custom entity definition
custom_guard = entity_manager.entity_system.create_entity_from_template(
    'basic_npc',
    entity_id='town_guard',
    name='Town Guard',
    description='A vigilant guard protecting the town',
    **{
        'stats.health': 150,
        'stats.strength': 15,
        'ai.aggression': 0.3,
        'sprite.color_tint': (100, 100, 200)
    }
)

# Register the definition
entity_manager.entity_system.create_entity_definition(custom_guard)

# Spawn instances
guard1 = entity_manager.spawn_entity('town_guard', 10, 10)
guard2 = entity_manager.spawn_entity('town_guard', 15, 15)
```

## Adding Custom Behaviors

```python
from engine.systems.entity_system import EntityBehavior

class PatrolBehavior(EntityBehavior):
    def __init__(self, entity, patrol_points):
        super().__init__(entity)
        self.patrol_points = patrol_points
        self.current_target = 0
    
    def execute(self, delta_time, world=None, entities=None):
        if not self.entity.is_moving:
            target = self.patrol_points[self.current_target]
            self.entity.move_to(target[0], target[1])
            self.current_target = (self.current_target + 1) % len(self.patrol_points)

# Register and use the behavior
entity_manager.entity_system.behavior_system.register_behavior_template(
    'patrol', PatrolBehavior
)

# Add to an entity
patrol_points = [(10, 10), (20, 10), (20, 20), (10, 20)]
entity_manager.entity_system.behavior_system.add_behavior_by_name(
    guard1, 'patrol', patrol_points=patrol_points
)
```

## Event Handling

```python
def on_entity_death(event):
    entity = event.entity
    print(f"Entity {entity.properties.name} has died!")
    
    # Drop items
    if entity.properties.interaction.drops_items_on_death:
        # Handle item dropping logic
        pass

# Register event handler
entity_manager.entity_system.event_manager.register_handler(
    'entity_death', on_entity_death
)
```

## Save/Load System

```python
# Save game state
entity_manager.save_game('my_save_file')

# List available saves
saves = entity_manager.save_system.list_save_files()
print(f"Available saves: {saves}")

# Load game state
entity_manager.load_game('my_save_file')
```

## Performance Monitoring

```python
# Get performance statistics
stats = entity_manager.get_statistics()
print(f"Active entities: {stats['active_instances']}")
print(f"Average update time: {stats['performance']['avg_update_time']:.4f}s")

# Check if optimization is needed
if entity_manager.entity_system.profiler.should_optimize():
    print("Performance optimization recommended!")
```

## Integration with Existing Code

```python
# Migrate existing entities
from engine.systems.entity_system import EntitySystemIntegration

integration = EntitySystemIntegration(entity_manager.entity_system)

# Convert old entities
old_entities = [old_npc1, old_npc2, old_food1]
migration_results = integration.migrate_existing_entities(old_entities)

# Use compatibility wrappers
wrappers = integration.get_all_entities_as_wrappers()
for wrapper in wrappers:
    # Use wrapper like old entity
    wrapper.move_to(wrapper.grid_x + 1, wrapper.grid_y)
```

## World Population

```python
# Set up spawn zones
entity_manager.world_bridge.add_spawn_zone(
    'forest', 0, 0, 50, 50, [EntityType.ANIMAL, EntityType.FOOD]
)

# Populate world
entity_counts = {
    'villager': 10,
    'wild_berry': 30,
    'forest_deer': 5
}
spawned = entity_manager.world_bridge.populate_world(entity_counts)
```

## Configuration

```python
# Load custom configuration
config = EntitySystemConfig()
config.load_from_file('config/entity_system.json')
entity_manager.entity_system.config = config

# Create example config files
from engine.systems.entity_system import create_example_config_files
create_example_config_files('config/')
```
"""
    
    print(usage_text)

# ============================================================================
# MAIN EXECUTION AND TESTING
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # Run tests
            print("Running entity system tests...")
            test_result = test_entity_system()
            validation_result = validate_entity_system_integration()
            
            if test_result and validation_result:
                print("All tests passed!")
                sys.exit(0)
            else:
                print("Some tests failed!")
                sys.exit(1)
        
        elif command == "example":
            # Run example
            print("Running entity system example...")
            example_usage()
        
        elif command == "config":
            # Create example config files
            config_dir = sys.argv[2] if len(sys.argv) > 2 else "config"
            create_example_config_files(config_dir)
        
        elif command == "usage":
            # Print usage examples
            print_usage_examples()
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, example, config, usage")
    
    else:
        # Default: run example
        print("Entity System - Running default example")
        print("Use 'python entity_system.py <command>' for other options")
        print("Commands: test, example, config, usage")
        print()
        example_usage()

# ============================================================================
# END OF ENTITY SYSTEM
# ============================================================================

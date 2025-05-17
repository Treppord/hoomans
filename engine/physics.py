class PhysicsEngine:
    """Handles physics calculations and collision detection for the game world"""
    
    def __init__(self, world_map=None):
        self.world_map = world_map
        
    def set_world_map(self, world_map):
        """Set the world map for collision detection"""
        self.world_map = world_map
    
    def check_collision(self, entity):
        """Check if an entity collides with walls or other obstacles"""
        if not self.world_map or not hasattr(entity, 'grid_x') or not hasattr(entity, 'grid_y'):
            return False
            
        # Get target position
        target_x = getattr(entity, 'target_grid_x', entity.grid_x)
        target_y = getattr(entity, 'target_grid_y', entity.grid_y)
        
        # Check if target position is a wall
        if self.world_map.is_wall(target_x, target_y):
            return True
            
        # Check if target position has a non-walkable entity tile component
        if hasattr(self.world_map, 'entity_tile_manager'):
            component = self.world_map.entity_tile_manager.get_component_at(target_x, target_y)
            if component and hasattr(component, 'is_walkable') and not component.is_walkable():
                return True
                
        return False
    
    def resolve_collision(self, entity, original_x, original_y):
        """Reset entity position after collision"""
        entity.grid_x = original_x
        entity.grid_y = original_y
        entity.target_grid_x = original_x
        entity.target_grid_y = original_y
        entity.is_moving = False
    
    def check_entity_collision(self, entity1, entity2):
        """Check if two entities collide with each other"""
        # For grid-based movement, check if they occupy or target the same cell
        if (entity1.grid_x == entity2.grid_x and entity1.grid_y == entity2.grid_y) or \
           (getattr(entity1, 'target_grid_x', entity1.grid_x) == entity2.grid_x and 
            getattr(entity1, 'target_grid_y', entity1.grid_y) == entity2.grid_y) or \
           (entity1.grid_x == getattr(entity2, 'target_grid_x', entity2.grid_x) and 
            entity1.grid_y == getattr(entity2, 'target_grid_y', entity2.grid_y)):
            return True
        return False
    
    def update(self, entities):
        """Update physics for all entities"""
        for entity in entities:
            if not hasattr(entity, 'update') or not hasattr(entity, 'grid_x') or not hasattr(entity, 'grid_y'):
                continue
                
            # Store original position for collision resolution
            original_grid_x = entity.grid_x
            original_grid_y = entity.grid_y
            
            # Store previous position for entity tile exit detection
            if not hasattr(entity, 'previous_grid_x'):
                entity.previous_grid_x = original_grid_x
                entity.previous_grid_y = original_grid_y
            else:
                entity.previous_grid_x = original_grid_x
                entity.previous_grid_y = original_grid_y
            
            # Let the entity update its position
            entity.update()
            
            # Check for collision with walls and entity tiles
            if self.check_collision(entity):
                self.resolve_collision(entity, original_grid_x, original_grid_y)
            
            # Handle entity tile interactions
            if hasattr(self.world_map, 'entity_tile_manager'):
                self.world_map.entity_tile_manager.handle_entity_movement(entity)

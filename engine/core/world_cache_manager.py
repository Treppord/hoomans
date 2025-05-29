"""World cache management"""

class WorldCacheManager:
    """Manages world cache setup and entity state persistence"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
    
    def setup_world_cache(self):
        """Set up the world cache for persistent memory"""
        from world.world_cache import WorldCache
        self.game_engine.world_cache = WorldCache()
        self.game_engine.world_cache.set_world_seed(self.game_engine.map_seed)
        print(f"DEBUG: World cache initialized with seed {self.game_engine.map_seed}")
    
    def save_all_entity_states(self):
        """Save all entity positions and states to cache"""
        if not hasattr(self.game_engine, 'world_cache') or not self.game_engine.world_cache:
            return
        
        print("DEBUG: Saving all entity states...")
        
        # Save all entities that support caching
        entities_saved = 0
        for obj in self.game_engine.objects:
            if hasattr(obj, 'save_position_to_cache'):
                try:
                    obj.save_position_to_cache()
                    entities_saved += 1
                except Exception as e:
                    print(f"Warning: Could not save entity {obj.get_entity_id()}: {e}")
        
        # Save all entity tiles
        if (hasattr(self.game_engine, 'world_map') and 
            hasattr(self.game_engine.world_map, 'entity_tile_manager')):
            
            entity_tiles_saved = 0
            for entity_tile in self.game_engine.world_map.entity_tile_manager.entity_tiles:
                try:
                    save_data = entity_tile.get_save_data()
                    self.game_engine.world_cache.save_entity_tile(
                        entity_tile.base_x, entity_tile.base_y,
                        entity_tile.tile_type, save_data
                    )
                    entity_tiles_saved += 1
                except Exception as e:
                    print(f"Warning: Could not save entity tile at ({entity_tile.base_x}, {entity_tile.base_y}): {e}")
            
            print(f"DEBUG: Saved {entity_tiles_saved} entity tiles")
        
        # Force save the cache to disk
        try:
            self.game_engine.world_cache._save_cache()
            print(f"DEBUG: Successfully saved {entities_saved} entities to cache")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_cached_entities(self):
        """Load cached entity positions and states"""
        if not hasattr(self.game_engine, 'world_cache'):
            return
        
        try:
            cached_entities = self.game_engine.world_cache.get_all_entity_positions()
            
            # Handle case where cached_entities might be a dict instead of a list
            if isinstance(cached_entities, dict):
                entity_list = []
                for entity_id, entity_data in cached_entities.items():
                    if isinstance(entity_data, dict):
                        entity_data["entity_id"] = entity_id
                        entity_list.append(entity_data)
                cached_entities = entity_list
            
            for entity_data in cached_entities:
                if not isinstance(entity_data, dict):
                    print(f"Warning: Invalid entity data format: {entity_data}")
                    continue
                
                entity_id = entity_data.get("entity_id")
                entity_type = entity_data.get("type")
                
                if not entity_id:
                    print(f"Warning: Entity data missing entity_id: {entity_data}")
                    continue
                
                # Find existing entity with this ID
                existing_entity = None
                for obj in self.game_engine.objects:
                    if hasattr(obj, 'get_entity_id') and obj.get_entity_id() == entity_id:
                        existing_entity = obj
                        break
                
                if existing_entity and hasattr(existing_entity, 'load_position_from_cache'):
                    existing_entity.load_position_from_cache()
                    print(f"DEBUG: Loaded cached position for entity {entity_id}")
                    
        except Exception as e:
            print(f"Error loading cached entities: {e}")
            import traceback
            traceback.print_exc()
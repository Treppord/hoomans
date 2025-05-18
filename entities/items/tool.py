"""Tool items like weapons and utility items"""
from entities.items.item_base import Item

class ToolItem(Item):
    """Base class for tool items"""
    
    def __init__(self, item_id, name, description, icon_path=None, 
                 durability=100, tool_type=None, effectiveness=1.0):
        """Initialize a tool item
        
        Args:
            durability: Number of uses before the tool breaks
            tool_type: Type of tool (e.g., "axe", "pickaxe", "sword")
            effectiveness: Multiplier for tool effectiveness (1.0 = normal)
        """
        super().__init__(item_id, name, description, icon_path, max_stack=1, durability=durability)
        self.tool_type = tool_type
        self.effectiveness = effectiveness
    
    def use(self, user, world=None):
        """Use the tool"""
        # Base implementation just reduces durability
        return self.reduce_durability(1)
    
    def create_instance(self):
        """Create a new instance of this tool item"""
        # The error is here - we're passing too many arguments to the constructor
        # Let's fix it by explicitly checking the subclass type
        
        # For AxeItem
        if isinstance(self, AxeItem):
            return AxeItem(
                self.item_id,
                self.name,
                self.description,
                self.icon_path,
                self.max_durability,
                self.effectiveness
            )
        # For PickaxeItem
        elif isinstance(self, PickaxeItem):
            return PickaxeItem(
                self.item_id,
                self.name,
                self.description,
                self.icon_path,
                self.max_durability,
                self.effectiveness
            )
        # For generic ToolItem
        else:
            return ToolItem(
                self.item_id,
                self.name,
                self.description,
                self.icon_path,
                self.max_durability,
                self.tool_type,
                self.effectiveness
            )
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this tool item"""
        # This should be implemented by specific tool subclasses
        raise NotImplementedError("Tool subclasses must implement create_template")


class AxeItem(ToolItem):
    """Axe tool for chopping trees"""
    
    def __init__(self, item_id, name, description, icon_path=None, 
                 durability=100, effectiveness=1.0):
        """Initialize an axe item"""
        super().__init__(
            item_id, name, description, icon_path, 
            durability, tool_type="axe", effectiveness=effectiveness
        )
    
    def create_instance(self):
        """Create a new instance of this axe item"""
        return AxeItem(
            self.item_id,
            self.name,
            self.description,
            self.icon_path,
            self.max_durability,
            self.effectiveness
        )
    
    def use(self, user, world=None):
        """Use the axe on a tree"""
        # Check if there's a tree in front of the user
        if world and hasattr(user, 'grid_x') and hasattr(user, 'grid_y') and hasattr(user, 'facing'):
            # Determine the position in front of the user
            dx, dy = 0, 0
            if user.facing == 'up':
                dy = -1
            elif user.facing == 'down':
                dy = 1
            elif user.facing == 'left':
                dx = -1
            elif user.facing == 'right':
                dx = 1
                
            target_x, target_y = user.grid_x + dx, user.grid_y + dy
            
            # Check if there's a tree entity at the target position
            if hasattr(world, 'entity_tile_manager'):
                entity_tile = world.entity_tile_manager.get_entity_tile_at(target_x, target_y)
                if entity_tile and hasattr(entity_tile, 'tile_type') and entity_tile.tile_type == 'tree':
                    # Chop the tree - in a real implementation, this might reduce tree health
                    # or drop wood items
                    print(f"Chopped tree at ({target_x}, {target_y})")
                    
                    # Reduce durability
                    return self.reduce_durability(1)
        
        # If no tree was found or no world provided, just reduce durability slightly
        return self.reduce_durability(1)
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this axe item"""
        return cls("axe", "Axe", "A tool for chopping trees", "items/axe.png", 100, 1.0)


class PickaxeItem(ToolItem):
    """Pickaxe tool for mining rocks"""
    
    def __init__(self, item_id, name, description, icon_path=None, 
                 durability=100, effectiveness=1.0):
        """Initialize a pickaxe item"""
        super().__init__(
            item_id, name, description, icon_path, 
            durability, tool_type="pickaxe", effectiveness=effectiveness
        )
    
    def create_instance(self):
        """Create a new instance of this pickaxe item"""
        return PickaxeItem(
            self.item_id,
            self.name,
            self.description,
            self.icon_path,
            self.max_durability,
            self.effectiveness
        )
    
    def use(self, user, world=None):
        """Use the pickaxe on a rock or mountain"""
        # Similar to axe but for rocks/mountains
        if world and hasattr(user, 'grid_x') and hasattr(user, 'grid_y') and hasattr(user, 'facing'):
            # Determine the position in front of the user
            dx, dy = 0, 0
            if user.facing == 'up':
                dy = -1
            elif user.facing == 'down':
                dy = 1
            elif user.facing == 'left':
                dx = -1
            elif user.facing == 'right':
                dx = 1
                
            target_x, target_y = user.grid_x + dx, user.grid_y + dy
            
            # Check if there's a mountain tile at the target position
            tile = world.get_tile(target_x, target_y)
            if tile and tile.type == "mountain":
                # Mine the mountain - in a real implementation, this might drop ore items
                print(f"Mined mountain at ({target_x}, {target_y})")
                
                # Reduce durability
                return self.reduce_durability(1)
        
        # If no mountain was found or no world provided, just reduce durability slightly
        return self.reduce_durability(1)
    
    @classmethod
    def create_template(cls):
        """Create a template instance of this pickaxe item"""
        return cls("pickaxe", "Pickaxe", "A tool for mining rocks", "items/pickaxe.png", 100, 1.0)

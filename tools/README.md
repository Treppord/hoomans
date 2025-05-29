# Hoomans Map Creator Tool

A visual map editor for the Hoomans game engine with Aseprite integration.

## Features

- Visual tile-based map editing
- Entity placement (trees, houses, etc.)
- Aseprite integration for custom tile creation
- Save/load maps in game-compatible format
- Camera with pan and zoom
- Multiple editing tools (brush, eraser, fill, etc.)

## Usage

### Basic Usage

```bash
python tools/map_creator.py
```

### With Custom Dimensions

```bash
python tools/map_creator.py --map-width 128 --map-height 128
```

### With Aseprite Integration

```bash
python tools/map_creator.py --aseprite-path "/path/to/aseprite"
```

### Load Existing Map

```bash
python tools/map_creator.py --load-map "maps/my_map.json"
```

## Controls

- **1-5**: Select tools (Brush, Entity, Eraser, Selector, Fill)
- **G**: Toggle grid
- **P**: Toggle palette
- **WASD**: Pan camera
- **Mouse Wheel**: Zoom
- **Middle Mouse**: Pan camera
- **Ctrl+S**: Save map
- **Ctrl+O**: Open map
- **Ctrl+N**: New map

## Tools

1. **Tile Brush**: Paint terrain tiles
2. **Entity Placer**: Place entity tiles (trees, houses)
3. **Eraser**: Remove tiles and entities
4. **Selector**: Select and inspect tiles
5. **Fill**: Flood fill areas with selected tile

## File Format

Maps are saved as JSON files compatible with the game engine:

```json
{
  "version": "1.0",
  "metadata": {
    "width": 64,
    "height": 64,
    "tile_size": 16
  },
  "tiles": [...],
  "entity_tiles": [...],
  "world_items": [...]
}
```

## Integration with Game Engine

Maps created with this tool can be loaded directly into the game engine:

```python
from tools.map_editor.map_serializer import MapSerializer

serializer = MapSerializer()
world_map = serializer.load_map("maps/my_map.json")
engine.set_world_map(world_map)
```

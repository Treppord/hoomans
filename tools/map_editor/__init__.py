"""
Map Editor Package for Hoomans Game Engine

This package provides a comprehensive map editing tool that integrates
with the existing game engine modules for creating custom maps.

Components:
- editor_core: Main editor logic and tool management
- tile_palette: Tile selection and preview
- entity_palette: Entity tile selection and placement
- editor_camera: Camera system with pan and zoom
- map_serializer: Save/load functionality
- aseprite_integration: Integration with Aseprite for advanced editing

Usage:
    python tools/map_creator.py [options]
"""

__version__ = "1.0.0"
__author__ = "Hoomans Game Engine Team"

# Import main classes for easy access
from .editor_core import MapEditor, EditorTool
from .tile_palette import TilePalette
from .entity_palette import EntityPalette
from .editor_camera import EditorCamera
from .map_serializer import MapSerializer
from .aseprite_integration import AsepriteIntegration

__all__ = [
    'MapEditor',
    'EditorTool',
    'TilePalette',
    'EntityPalette',
    'EditorCamera',
    'MapSerializer',
    'AsepriteIntegration'
]
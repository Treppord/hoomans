"""
Setup script to create the maps directory structure
"""

import os

def setup_maps_directory():
    """Create the maps directory in the project root"""
    # Get project root (2 levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    maps_dir = os.path.join(project_root, "maps")
    
    # Create maps directory if it doesn't exist
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)
        print(f"Created maps directory: {maps_dir}")
    else:
        print(f"Maps directory already exists: {maps_dir}")
    
    # Create subdirectories for organization
    subdirs = ["custom", "templates", "test"]
    for subdir in subdirs:
        subdir_path = os.path.join(maps_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
            print(f"Created subdirectory: {subdir_path}")
    
    
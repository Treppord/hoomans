#!/usr/bin/env python3
"""
Conversion tool to update existing CNA files to the new bitfield format
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to the path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from cna.cna_codec import CNACodec
except ImportError:
    print("Error: Could not import CNACodec. Make sure you're running this script from the project root.")
    sys.exit(1)

def convert_file(filepath, output_dir=None, overwrite=False):
    """Convert a single CNA file to the new format"""
    try:
        # Load the file with the old format
        attributes = CNACodec.load_from_file(filepath)
        
        # Determine output path
        if output_dir:
            output_path = os.path.join(output_dir, os.path.basename(filepath))
        elif overwrite:
            output_path = filepath
        else:
            # Add _v2 suffix to filename
            base, ext = os.path.splitext(filepath)
            output_path = f"{base}_v2{ext}"
        
        # Save with the new format
        CNACodec.save_to_file(attributes, output_path)
        
        print(f"Converted: {filepath} -> {output_path}")
        return True
    except Exception as e:
        print(f"Error converting {filepath}: {e}")
        return False

def convert_directory(directory, output_dir=None, overwrite=False, recursive=False):
    """Convert all CNA files in a directory"""
    success_count = 0
    error_count = 0
    
    # Create output directory if specified and doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find all CNA files
    pattern = "**/*.cna" if recursive else "*.cna"
    for filepath in Path(directory).glob(pattern):
        if convert_file(str(filepath), output_dir, overwrite):
            success_count += 1
        else:
            error_count += 1
    
    print(f"Conversion complete: {success_count} files converted, {error_count} errors")

def convert_data_folder():
    """Convert all CNA files in the cna/data folder"""
    # Get the absolute path to the cna/data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    
    # Check if the data directory exists
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found at {data_dir}")
        print("Creating data directory...")
        os.makedirs(data_dir)
        print(f"Created data directory at {data_dir}")
        return
    
    print(f"Converting all CNA files in {data_dir}...")
    
    # Convert all files in the data directory
    convert_directory(data_dir, overwrite=True)

def main():
    parser = argparse.ArgumentParser(description="Convert CNA files to the new bitfield format")
    parser.add_argument("path", nargs="?", help="File or directory to convert (if not specified, converts cna/data folder)")
    parser.add_argument("-o", "--output", help="Output directory (if not specified, files will be saved alongside originals)")
    parser.add_argument("-w", "--overwrite", action="store_true", help="Overwrite original files")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process directories recursively")
    parser.add_argument("--data", action="store_true", help="Convert all files in the cna/data folder")
    
    args = parser.parse_args()
    
    # If --data flag is provided or no path is specified, convert the data folder
    if args.data or not args.path:
        convert_data_folder()
    elif os.path.isfile(args.path):
        convert_file(args.path, args.output, args.overwrite)
    elif os.path.isdir(args.path):
        convert_directory(args.path, args.output, args.overwrite, args.recursive)
    else:
        print(f"Error: {args.path} is not a valid file or directory")
        sys.exit(1)

if __name__ == "__main__":
    main()

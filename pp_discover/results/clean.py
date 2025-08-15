"""
Results Archive and Cleanup Utility

This module provides functionality to archive processed results and clean up the working directory.
It moves all files and folders from the working directory to a versioned archive directory,
allowing for multiple runs to be preserved without overwriting previous results.

Key Features:
- Automatically creates versioned archive directories (r1, r2, r3, etc.)
- Moves all processed results to preserve them for future reference
- Cleans up the working directory for the next processing run
- Prevents data loss by maintaining separate archives for each run

Usage:
- Run after completing a full processing pipeline
- Helps organize results from multiple experimental runs
- Maintains a clean working environment for subsequent processing
"""

import os
import shutil
import yaml

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def clean():
    """
    Archive current results and clean the working directory.
    
    This function moves all files and folders from the working directory
    to a new versioned subdirectory in the archive location. The versioning
    system uses 'r1', 'r2', 'r3', etc. to distinguish between different runs.
    
    The function:
    1. Checks if source directory exists
    2. Creates target directory if needed
    3. Finds the next available version number
    4. Creates a new versioned subdirectory
    5. Moves all content from working directory to the archive
    """
    # Define source and target directories from configuration
    source_dir = config['general']['working_dir']
    target_dir = config['clean']['dest_dir']

    # Validate source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return

    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created target directory: {target_dir}")

    # Find existing run directories (r1, r2, r3, etc.)
    existing_dirs = [d for d in os.listdir(target_dir) 
                    if os.path.isdir(os.path.join(target_dir, d)) 
                    and d.startswith('r') and d[1:].isdigit()]

    # Determine the next run number
    if existing_dirs:
        max_index = max(int(d[1:]) for d in existing_dirs)
    else:
        max_index = 0

    # Create the new versioned subdirectory
    new_sub_dir = f'r{max_index + 1}'
    new_target_dir = os.path.join(target_dir, new_sub_dir)
    os.makedirs(new_target_dir)
    print(f"Created new archive directory: {new_target_dir}")

    # Move all files and folders from source to archive
    items_moved = 0
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        try:
            shutil.move(item_path, new_target_dir)
            items_moved += 1
        except Exception as e:
            print(f"Error moving {item}: {e}")

    print(f"Successfully moved {items_moved} items from '{source_dir}' to '{new_target_dir}'.")
    print("Working directory cleaned and ready for next processing run.")

if __name__ == "__main__":
    print("Starting cleanup and archival process...")
    clean()
    print("Cleanup process completed.")

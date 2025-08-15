"""
Screenshot Image Consolidation Module

This module consolidates screenshot images from distributed crawler log directories
into centralized directories for further processing. The crawler generates screenshots
in a nested directory structure, and this module flattens that structure by copying
all images to a single location per crawler type.

Key Features:
- Traverses nested log directory structures to find screenshot files
- Consolidates images from multiple crawling sessions into single directories
- Uses parallel processing for efficient file copying operations
- Maintains separation between different crawler types (baseline vs enhanced)
- Prepares images for subsequent deduplication and analysis steps

Directory Structure Expected:
logs/
├── domain1/
│   ├── session1/
│   │   └── screenshots/
│   │       ├── image1.png
│   │       └── image2.png
│   └── session2/
│       └── screenshots/
│           └── image3.png
└── domain2/
    └── session1/
        └── screenshots/
            └── image4.png

Output: All images consolidated into a single directory per crawler type.
"""

import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import yaml

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def copy_image(img_path, dest_dir):
    """
    Copy a single image file to the destination directory.
    
    This function handles the actual file copying operation with error handling.
    It's designed to be used in parallel processing scenarios.
    
    Args:
        img_path (str): Full path to the source image file
        dest_dir (str): Destination directory for the copied image
    """
    try:
        shutil.copy(img_path, dest_dir)
        print(f"Successfully copied: {os.path.basename(img_path)}")
    except Exception as e:
        print(f"Failed to copy {img_path}: {e}")

def process_screenshots_dir(screenshots_dir, dest_dir):
    """
    Process a single screenshots directory and yield image file paths.
    
    This generator function scans a screenshots directory and yields
    the full paths of all image files found within it.
    
    Args:
        screenshots_dir (str): Path to the screenshots directory
        dest_dir (str): Destination directory (unused in this function but kept for consistency)
        
    Yields:
        str: Full path to each image file found
    """
    if os.path.isdir(screenshots_dir):
        for img_file in os.listdir(screenshots_dir):
            img_path = os.path.join(screenshots_dir, img_file)
            # Only yield actual files (not subdirectories)
            if os.path.isfile(img_path):
                yield img_path

def consolidate_images(source_dir):
    """
    Consolidate all screenshot images from a crawler's log structure into a single directory.
    
    This function traverses the nested directory structure created by the web crawler
    and copies all screenshot images to a consolidated location. The structure typically
    follows: logs/domain/session/screenshots/
    
    Args:
        source_dir (str): Name of the source crawler directory (e.g., 'pp_crawler', 'pp_crawler_baseline')
    """
    # Set up destination directory
    dest_dir = os.path.join(config['cons_imgs']['dest_base_dir'], source_dir)
    os.makedirs(dest_dir, exist_ok=True)
    print(f"Consolidating images to: {dest_dir}")

    # Locate the logs directory for this crawler
    logs_dir = os.path.join(config['general']['log_base_dir'], source_dir, 'logs')
    if not os.path.isdir(logs_dir):
        print(f"No logs directory found in {source_dir}")
        return

    print(f"Scanning logs directory: {logs_dir}")
    
    # Collect all image file paths from the nested structure
    image_tasks = []
    domains_processed = 0
    
    # Level 1: Iterate through domain directories
    for sub_dir1 in os.listdir(logs_dir):
        sub_dir1_path = os.path.join(logs_dir, sub_dir1)
        if not os.path.isdir(sub_dir1_path):
            continue

        # Level 2: Iterate through session directories within each domain
        for sub_dir2 in os.listdir(sub_dir1_path):
            sub_dir2_path = os.path.join(sub_dir1_path, sub_dir2)
            if not os.path.isdir(sub_dir2_path):
                continue

            # Level 3: Look for screenshots directory
            screenshots_dir = os.path.join(sub_dir2_path, 'screenshots')
            if os.path.isdir(screenshots_dir):
                # Collect all image paths from this screenshots directory
                image_tasks.extend(process_screenshots_dir(screenshots_dir, dest_dir))
        
        domains_processed += 1

    print(f"Found {len(image_tasks)} images across {domains_processed} domains")

    # Copy all images using parallel processing
    if image_tasks:
        print("Starting parallel image copying...")
        with ThreadPoolExecutor(max_workers=config['general']['max_workers']) as executor:
            # Submit all copy tasks
            futures = [executor.submit(copy_image, img_path, dest_dir) for img_path in image_tasks]
            
            # Wait for all tasks to complete
            completed = 0
            for future in futures:
                future.result()  # Wait for completion and handle any exceptions
                completed += 1
                if completed % 100 == 0:  # Progress update every 100 files
                    print(f"Copied {completed}/{len(image_tasks)} images...")

        print(f"Image consolidation complete for {source_dir}")
    else:
        print(f"No images found to consolidate for {source_dir}")

if __name__ == "__main__":
    print("Starting image consolidation process...")
    
    # Process all crawler directories specified in configuration
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"\n{'='*50}")
        print(f"Processing crawler directory: {sd}")
        print(f"{'='*50}")
        consolidate_images(sd)
    
    print(f"\n{'='*50}")
    print("Image consolidation complete for all directories!")
    print(f"{'='*50}")

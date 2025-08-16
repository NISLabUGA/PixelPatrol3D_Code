"""
Image Deduplication Module

This module removes duplicate images from consolidated screenshot collections using
a combination of MD5 hash and URL-based deduplication. This is crucial for removing
identical screenshots that may have been captured multiple times during crawling,
while preserving unique content for analysis.

Key Features:
- Calculates MD5 hashes for exact duplicate detection
- Uses URL information to distinguish between identical images from different sources
- Combines hash and URL to create unique identifiers for each image
- Processes images in parallel for efficiency
- Generates metadata files mapping images to their hash and URL information
- Preserves only unique image-URL combinations

The deduplication process is important because:
- Crawlers may capture identical screenshots multiple times
- Same content may be served from different URLs (legitimate vs BMA)
- Reduces dataset size while preserving unique visual content
- Improves efficiency of subsequent processing steps

Deduplication Strategy:
- Images with identical MD5 hashes AND identical URLs are considered duplicates
- Images with identical MD5 hashes but different URLs are preserved (different sources)
- This allows detection of the same content served from multiple domains
"""

import os
import shutil
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import yaml
import threading
import re

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def calculate_md5(image_path):
    """
    Calculate the MD5 hash of an image file.
    
    MD5 hashing provides a fast way to identify identical files by content.
    The hash is calculated by reading the file in chunks to handle large images
    efficiently without loading the entire file into memory.
    
    Args:
        image_path (str): Full path to the image file
        
    Returns:
        str: Hexadecimal MD5 hash of the file
        None: If file processing fails
    """
    try:
        with open(image_path, 'rb') as img_file:
            md5_hasher = hashlib.md5()
            # Read file in 8KB chunks to handle large files efficiently
            while chunk := img_file.read(8192):
                md5_hasher.update(chunk)
            return md5_hasher.hexdigest()
    except Exception as e:
        print(f"Error calculating MD5 for {image_path}: {e}")
        return None

def load_map(json_path):
    """
    Load the consolidated JSON mapping file containing screenshot metadata.
    
    This function loads the mapping file created by consolidate_json.py,
    which contains URL and other metadata for each screenshot.
    
    Args:
        json_path (str): Path to the consolidated JSON mapping file
        
    Returns:
        dict: Dictionary mapping screenshot names to their metadata
        dict: Empty dictionary if loading fails
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            print(f"Loaded metadata for {len(data)} images from {json_path}")
            return data
    except Exception as e:
        print(f"Error loading JSON mapping file {json_path}: {e}")
        return {}

def process_image(img_path, map_obj, unique_combinations, dest_dir, metadata, lock):
    """
    Process a single image for deduplication.
    
    This function calculates the MD5 hash of an image, retrieves its URL
    from the metadata mapping, and determines if the hash-URL combination
    is unique. Only unique combinations are copied to the destination.
    
    Args:
        img_path (str): Full path to the source image
        map_obj (dict): Mapping of image names to metadata
        unique_combinations (set): Set of unique (hash, URL) combinations
        dest_dir (str): Destination directory for unique images
        metadata (dict): Dictionary to store metadata for unique images
        lock (threading.Lock): Thread lock for synchronizing access to shared data
    """
    # Calculate MD5 hash for the image
    md5_hash = calculate_md5(img_path)
    if md5_hash is None:
        return

    # Extract image filename and get basename for metadata lookup
    original_img_name = os.path.basename(img_path)
    
    # Extract basename by removing _initial or _scroll suffixes for metadata lookup
    match = re.match(r"^(.*?)(?:_initial|_scroll).*", original_img_name)
    if match:
        basename = match.group(1)
    else:
        basename = original_img_name
    
    try:
        # Get the URL from the consolidated metadata using basename
        image_url = map_obj[basename]["url"]

        # Create unique key combining hash and URL
        unique_key = (md5_hash, image_url)
        
        # Use lock to ensure thread-safe access to shared data structures
        with lock:
            if unique_key not in unique_combinations:
                # This is a unique hash-URL combination
                unique_combinations.add(unique_key)
                
                # Store metadata for this unique image using the ORIGINAL filename as key
                # This ensures downstream scripts can find metadata using actual image filenames
                metadata[original_img_name] = {
                    "md5_hash": md5_hash,
                    "image_url": image_url
                }
                
                # Copy file outside the lock to minimize lock time
                should_copy = True
                print(f"Kept unique image: {original_img_name} (MD5: {md5_hash[:8]}..., URL: {image_url[:50]}...)")
            else:
                should_copy = False
                print(f"Duplicate found: {original_img_name} (MD5: {md5_hash[:8]}..., URL: {image_url[:50]}...) - skipping")
        
        # Copy file outside the lock to avoid blocking other threads
        if should_copy:
            shutil.copy(img_path, dest_dir)
            
    except KeyError:
        print(f"No URL metadata found for basename {basename} - skipping")
    except Exception as e:
        print(f"Error processing {original_img_name}: {e}")

def deduplicate_images(source_dir):
    """
    Deduplicate images based on MD5 hash and URL combination.
    
    This function processes all images in a consolidated directory,
    removes duplicates based on the combination of file hash and source URL,
    and creates a clean dataset for further analysis.
    
    Args:
        source_dir (str): Name of the source crawler directory
    """
    print(f"Starting deduplication for: {source_dir}")
    
    # Set up directory paths
    source_dir_pth = os.path.join(config['dedup_imgs']['source_base_dir'], source_dir)
    dest_dir = os.path.join(config['dedup_imgs']['dest_base_dir'], source_dir)
    json_path = os.path.join(config['dedup_imgs']['json_base_dir'], source_dir, 'map.json')

    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)
    print(f"Source directory: {source_dir_pth}")
    print(f"Destination directory: {dest_dir}")
    print(f"Metadata file: {json_path}")

    # Load URL mapping from consolidated JSON
    map_obj = load_map(json_path)
    if not map_obj:
        print(f"No metadata available for {source_dir} - cannot perform deduplication")
        return

    # Initialize deduplication tracking
    unique_combinations = set()  # Track unique (hash, URL) pairs
    metadata = {}  # Store metadata for unique images
    lock = threading.Lock()  # Thread lock for synchronizing access to shared data

    # Collect all image files in the source directory
    if not os.path.exists(source_dir_pth):
        print(f"Source directory does not exist: {source_dir_pth}")
        return
        
    img_files = [
        os.path.join(source_dir_pth, img_name)
        for img_name in os.listdir(source_dir_pth)
        if os.path.isfile(os.path.join(source_dir_pth, img_name))
        and img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
    ]
    
    print(f"Found {len(img_files)} images to process")

    # Process images in parallel for efficiency
    print("Processing images for deduplication...")
    with ThreadPoolExecutor(max_workers=config['general']['max_workers']) as executor:
        futures = [
            executor.submit(process_image, img_path, map_obj, unique_combinations, dest_dir, metadata, lock)
            for img_path in img_files
        ]
        
        # Wait for all processing to complete with progress bar
        for future in tqdm(futures, desc="Deduplicating images"):
            future.result()  # Ensure all threads complete and handle exceptions

    # Save metadata for the deduplicated images
    metadata_file_path = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{source_dir}_metadata.json')
    with open(metadata_file_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)
    
    # Print summary statistics
    original_count = len(img_files)
    unique_count = len(metadata)
    duplicates_removed = original_count - unique_count
    
    print(f"\nDeduplication Summary for {source_dir}:")
    print(f"  Original images: {original_count}")
    print(f"  Unique images: {unique_count}")
    print(f"  Duplicates removed: {duplicates_removed}")
    print(f"  Deduplication rate: {(duplicates_removed/original_count)*100:.1f}%")
    print(f"  Metadata saved to: {metadata_file_path}")

if __name__ == "__main__":
    print("Starting image deduplication process...")
    
    # Process all crawler directories specified in configuration
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"\n{'='*50}")
        print(f"Processing crawler directory: {sd}")
        print(f"{'='*50}")
        deduplicate_images(sd)
    
    print(f"\n{'='*50}")
    print("Image deduplication complete for all directories!")
    print(f"{'='*50}")

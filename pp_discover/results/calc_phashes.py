"""
Perceptual Hash Calculator for Screenshot Images

This module calculates perceptual hashes (pHash) for screenshot images collected during web crawling.
Perceptual hashes are used to identify visually similar images, which is crucial for detecting
duplicate or similar BMA pages that may use the same visual elements.

Key Features:
- Calculates perceptual hashes using the imagehash library
- Processes images in parallel using ThreadPoolExecutor for efficiency
- Updates existing metadata JSON files with calculated hash values
- Configurable hash size for different levels of similarity detection

Dependencies:
- PIL (Python Imaging Library) for image processing
- imagehash for perceptual hash calculation
- concurrent.futures for parallel processing
- tqdm for progress tracking
"""

import os
import json
from PIL import Image
import imagehash
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import numpy as np
import yaml

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def get_image_hash(img_path, hash_size=config['calc_phash']['hash_size']):
    """
    Calculate the perceptual hash of an image with specified resizing.
    
    Perceptual hashing creates a fingerprint of an image that remains similar
    even when the image is slightly modified (resized, compressed, etc.).
    This is useful for detecting visually similar BMA pages.
    
    Args:
        img_path (str): Path to the image file
        hash_size (int): Size to resize image before hashing (default from config)
        
    Returns:
        str: Hexadecimal string representation of the perceptual hash
        None: If image processing fails
    """
    try:
        with Image.open(img_path) as img:
            # Resize image to specified dimensions for consistent hashing
            img = img.resize((hash_size, hash_size))
            # Calculate perceptual hash and convert to string
            return str(imagehash.phash(img, hash_size=hash_size))
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return None

def update_metadata(source_dir, hash_size=config['calc_phash']['hash_size'], num_workers=config['general']['max_workers']):
    """
    Update the metadata file with perceptual hashes for all images in a directory.
    
    This function processes all images in the specified source directory,
    calculates their perceptual hashes, and updates the corresponding metadata
    JSON file with the hash values. The metadata is used later for clustering
    and similarity analysis.
    
    Args:
        source_dir (str): Name of the source directory containing images
        hash_size (int): Size for image resizing before hashing
        num_workers (int): Number of parallel workers for processing
    """
    # Construct paths for source directory and metadata file
    source_dir_pth = os.path.join(config['dedup_imgs']['dest_base_dir'], source_dir)
    metadata_file_path = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{source_dir}_metadata.json')

    # Collect all image file paths (jpg, jpeg, png formats)
    img_paths = [os.path.join(source_dir_pth, img) for img in os.listdir(source_dir_pth) 
                 if img.endswith(('jpg', 'jpeg', 'png'))]
    print(f"Found {len(img_paths)} images to process.\n")

    # Load existing metadata if available
    metadata = {}
    if os.path.exists(metadata_file_path):
        with open(metadata_file_path, 'r') as f:
            metadata = json.load(f)

    # Process images in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all hash calculation tasks
        future_to_img = {executor.submit(get_image_hash, img_path, hash_size): img_path 
                        for img_path in img_paths}
        
        # Process completed tasks with progress bar
        with tqdm(total=len(img_paths), desc="Processing images") as pbar:
            for future in as_completed(future_to_img):
                img_path = future_to_img[future]
                img_hash = future.result()
                pbar.update(1)

                try:
                    # Update metadata with calculated hash
                    metadata[os.path.basename(img_path)]["phash"] = img_hash
                except Exception as e:
                    print(f"Error updating metadata for {img_path}: {e}")

    # Save updated metadata to JSON file
    with open(metadata_file_path, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata updated and saved to {metadata_file_path}")

if __name__ == "__main__":
    # Process all crawler directories specified in configuration
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"Processing perceptual hashes for directory: {sd}")
        update_metadata(sd, hash_size=config['calc_phash']['hash_size'], 
                       num_workers=config['general']['max_workers'])
    print("Perceptual hash calculation complete for all directories.")

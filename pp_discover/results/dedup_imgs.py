import os
import shutil
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def calculate_md5(image_path):
    """Calculate the MD5 hash of an image."""
    try:
        with open(image_path, 'rb') as img_file:
            md5_hasher = hashlib.md5()
            while chunk := img_file.read(8192):
                md5_hasher.update(chunk)
            return md5_hasher.hexdigest()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def load_map(json_path):
    """Load image URLs from a JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
            return data
    except Exception as e:
        print(f"Error loading JSON file {json_path}: {e}")
        return {}

def process_image(img_path, map_obj, unique_combinations, dest_dir, metadata):
    """Process a single image for deduplication."""
    md5_hash = calculate_md5(img_path)
    if md5_hash is None:
        return

    # Get the image URL from the map
    img_name = os.path.basename(img_path)
    
    try:
        image_url = map_obj[img_name]["url"]

        # Check for duplicate combination of md5_hash and image_url
        unique_key = (md5_hash, image_url)
        if unique_key not in unique_combinations:
            # Add to unique set and copy the file
            unique_combinations.add(unique_key)
            shutil.copy(img_path, dest_dir)
            metadata[img_name] = {
                "md5_hash": md5_hash,
                "image_url": image_url
            }
            print(f"Copied {img_path} with MD5: {md5_hash}, URL: {image_url}")
        else:
            print(f"Duplicate found for MD5: {md5_hash}, URL: {image_url} (skipping)")
            
    except Exception as e:
        print(e)

def deduplicate_images(source_dir):
    """Deduplicate images based on MD5 hash and image URL."""
    # Directories
    source_dir_pth = os.path.join(config['dedup_imgs']['source_base_dir'], source_dir)
    dest_dir = os.path.join(config['dedup_imgs']['dest_base_dir'], source_dir)
    json_path = os.path.join(config['dedup_imgs']['json_base_dir'], source_dir, 'map.json')

    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)

    # Load image URLs from JSON
    map_obj = load_map(json_path)

    # Set to store unique combinations of md5_hash and image_url
    unique_combinations = set()

    # Dictionary to store metadata
    metadata = {}

    # Collect all image files in the source directory
    img_files = [
        os.path.join(source_dir_pth, img_name)
        for img_name in os.listdir(source_dir_pth)
        if os.path.isfile(os.path.join(source_dir_pth, img_name))
    ]

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(config['general']['max_workers']) as executor:
        futures = [
            executor.submit(process_image, img_path, map_obj, unique_combinations, dest_dir, metadata)
            for img_path in img_files
        ]
        for future in tqdm(futures, desc="Processing images"):
            future.result()  # Ensure all threads complete

    # Save the metadata to a JSON file
    metadata_file_path = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{source_dir}_metadata.json')
    with open(metadata_file_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)
    print(f"Deduplication complete. Metadata saved to {metadata_file_path}")

if __name__ == "__main__":
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        deduplicate_images(sd)

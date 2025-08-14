import os
import json
from PIL import Image
import imagehash
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import numpy as np
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def get_image_hash(img_path, hash_size=config['calc_phash']['hash_size']):
    """Calculate the perceptual hash of the image with specified resizing."""
    try:
        with Image.open(img_path) as img:
            img = img.resize((hash_size, hash_size))  # Resize to the specified dimensions
            return str(imagehash.phash(img, hash_size=hash_size))
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return None

def update_metadata(source_dir, hash_size=config['calc_phash']['hash_size'], num_workers=config['general']['max_workers']):
    """Update the metadata file with image hashes."""
    config['dedup_imgs']['dest_base_dir']
    source_dir_pth = os.path.join(config['dedup_imgs']['dest_base_dir'], source_dir)
    metadata_file_path = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{source_dir}_metadata.json')

    # Collect all image paths
    img_paths = [os.path.join(source_dir_pth, img) for img in os.listdir(source_dir_pth) if img.endswith(('jpg', 'jpeg', 'png'))]
    print(f"Found {len(img_paths)} images to process.\n")

    # Load existing metadata
    metadata = {}
    if os.path.exists(metadata_file_path):
        with open(metadata_file_path, 'r') as f:
            metadata = json.load(f)

    # Process images and update metadata
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_img = {executor.submit(get_image_hash, img_path, hash_size): img_path for img_path in img_paths}
        
        with tqdm(total=len(img_paths), desc="Processing images") as pbar:
            for future in as_completed(future_to_img):
                img_path = future_to_img[future]
                img_hash = future.result()
                pbar.update(1)

                try:
                    metadata[os.path.basename(img_path)]["phash"] = img_hash
                except Exception as e:
                    print(e)

    # Save updated metadata
    with open(metadata_file_path, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata updated and saved to {metadata_file_path}")

if __name__ == "__main__":
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        update_metadata(sd, hash_size=config['calc_phash']['hash_size'], num_workers=config['general']['max_workers'])

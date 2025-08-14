import os
import json
import shutil
import numpy as np
from tqdm import tqdm
from sklearn.cluster import DBSCAN
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def phash_to_binary(phash_str):
    """Convert a perceptual hash string to a binary representation."""
    return np.array([int(bit) for bit in ''.join(f"{int(char, 16):04b}" for char in phash_str)])

def cluster_images(source_dir, distance_threshold=config['clustering']['dist_thold']):
    """Cluster images based on perceptual hash."""
    metadata_file_path = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{source_dir}_metadata.json')
    source_dir_path = os.path.join(config['dedup_imgs']['dest_base_dir'], source_dir)
    dest_dir = os.path.join(config['clustering']['dest_base_dir'], source_dir)
    os.makedirs(dest_dir, exist_ok=True)

    # Load metadata
    with open(metadata_file_path, 'r') as f:
        metadata = json.load(f)

    # Extract hashes and file paths
    print("Converting hashes to binary...")
    img_paths = metadata.keys()
    hashes = [phash_to_binary(metadata[path]["phash"]) for path in img_paths]

    # Step 2: Use DBSCAN for clustering
    print("\nClustering hashes with DBSCAN...")
    hash_vectors = np.array(hashes)
    dbscan = DBSCAN(eps=distance_threshold, min_samples=config['clustering']['min_samples'], metric=config['clustering']['dist_met'])
    labels = dbscan.fit_predict(hash_vectors)

    # Organize images into clusters
    print("\nOrganizing images into clusters...")
    clusters = {}
    for img_path, label in zip(img_paths, labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(img_path)

    # Save clustered images
    with tqdm(total=len(clusters), desc="Saving clusters") as pbar:
        for label, cluster_files in clusters.items():
            cluster_dir = os.path.join(dest_dir, f'cluster_{label}')
            os.makedirs(cluster_dir, exist_ok=True)

            for file_path in cluster_files:
                print(file_path)
                shutil.copy(os.path.join(source_dir_path, file_path), cluster_dir)
            pbar.update(1)

    print("\nAll images have been clustered and copied to", dest_dir)

if __name__ == "__main__":
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        cluster_images(sd, distance_threshold=config['clustering']['dist_thold'])

"""
Perceptual Hash-Based Image Clustering Module

This module clusters screenshot images based on their perceptual hash similarity using DBSCAN clustering.
The clustering helps identify groups of visually similar images, which is essential for detecting
BMA pages that use similar visual layouts or elements from legitimate sites.

Key Features:
- Converts perceptual hashes to binary vectors for distance calculation
- Uses DBSCAN clustering algorithm for density-based grouping
- Handles noise and outliers effectively through DBSCAN's design
- Organizes clustered images into separate directories for analysis
- Configurable distance threshold and minimum samples parameters

The clustering process helps identify:
- Duplicate or near-duplicate BMA pages
- BMA campaigns using similar visual templates
- Legitimate pages that might be targets for BMA attacks

Dependencies:
- scikit-learn for DBSCAN clustering
- numpy for numerical operations
- tqdm for progress tracking
"""

import os
import json
import shutil
import numpy as np
from tqdm import tqdm
from sklearn.cluster import DBSCAN
import yaml

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def phash_to_binary(phash_str):
    """
    Convert a perceptual hash string to a binary representation.
    
    Perceptual hashes are typically stored as hexadecimal strings.
    This function converts them to binary vectors that can be used
    for distance calculations in clustering algorithms.
    
    Args:
        phash_str (str): Hexadecimal string representation of perceptual hash
        
    Returns:
        numpy.ndarray: Binary array representation of the hash
        
    Example:
        phash_to_binary("a1b2") -> array([1,0,1,0,0,0,0,1,1,0,1,1,0,0,1,0])
    """
    # Convert each hex character to 4-bit binary, then to individual bits
    return np.array([int(bit) for bit in ''.join(f"{int(char, 16):04b}" for char in phash_str)])

def cluster_images(source_dir, distance_threshold=config['clustering']['dist_thold']):
    """
    Cluster images based on perceptual hash similarity using DBSCAN.
    
    This function loads perceptual hashes from metadata, converts them to
    binary vectors, applies DBSCAN clustering, and organizes the resulting
    clusters into separate directories for further analysis.
    
    DBSCAN is chosen because:
    - It can find clusters of arbitrary shape
    - It handles noise and outliers well
    - It doesn't require specifying the number of clusters beforehand
    - It's effective for identifying dense regions in hash space
    
    Args:
        source_dir (str): Name of the source directory containing images
        distance_threshold (float): Maximum distance between samples in a cluster
    """
    # Define file paths
    metadata_file_path = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{source_dir}_metadata.json')
    source_dir_path = os.path.join(config['dedup_imgs']['dest_base_dir'], source_dir)
    dest_dir = os.path.join(config['clustering']['dest_base_dir'], source_dir)
    os.makedirs(dest_dir, exist_ok=True)

    # Load metadata containing perceptual hashes
    print(f"Loading metadata from: {metadata_file_path}")
    with open(metadata_file_path, 'r') as f:
        metadata = json.load(f)

    # Extract hashes and convert to binary vectors
    print("Converting perceptual hashes to binary vectors...")
    img_paths = list(metadata.keys())
    hashes = [phash_to_binary(metadata[path]["phash"]) for path in img_paths]
    
    print(f"Processing {len(hashes)} images for clustering")

    # Apply DBSCAN clustering algorithm
    print(f"\nClustering hashes with DBSCAN (eps={distance_threshold}, min_samples={config['clustering']['min_samples']})...")
    hash_vectors = np.array(hashes)
    dbscan = DBSCAN(
        eps=distance_threshold, 
        min_samples=config['clustering']['min_samples'], 
        metric=config['clustering']['dist_met']
    )
    labels = dbscan.fit_predict(hash_vectors)

    # Organize images by cluster labels
    print("\nOrganizing images into clusters...")
    clusters = {}
    for img_path, label in zip(img_paths, labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(img_path)

    # Report clustering results
    num_clusters = len([label for label in clusters.keys() if label != -1])
    num_noise = len(clusters.get(-1, []))
    print(f"Found {num_clusters} clusters and {num_noise} noise points")

    # Copy clustered images to separate directories
    print("\nCopying images to cluster directories...")
    with tqdm(total=len(clusters), desc="Saving clusters") as pbar:
        for label, cluster_files in clusters.items():
            # Create cluster directory (cluster_-1 for noise points)
            cluster_dir = os.path.join(dest_dir, f'cluster_{label}')
            os.makedirs(cluster_dir, exist_ok=True)

            # Copy all images in this cluster
            for file_path in cluster_files:
                source_file = os.path.join(source_dir_path, file_path)
                try:
                    shutil.copy(source_file, cluster_dir)
                except Exception as e:
                    print(f"Error copying {file_path}: {e}")
            
            pbar.update(1)

    print(f"\nClustering complete! Results saved to: {dest_dir}")
    print(f"Total clusters created: {len(clusters)}")

if __name__ == "__main__":
    # Process all crawler directories specified in configuration
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"\n{'='*50}")
        print(f"Clustering images for directory: {sd}")
        print(f"{'='*50}")
        cluster_images(sd, distance_threshold=config['clustering']['dist_thold'])
    
    print(f"\n{'='*50}")
    print("Image clustering complete for all directories!")
    print(f"{'='*50}")

import os
import shutil
import imagehash
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def get_image_hash(img_path):
    # Calculate the perceptual hash of the image
    try:
        with Image.open(img_path) as img:
            return img_path, imagehash.phash(img)
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return img_path, None

def cluster_images(source_dir, distance_threshold=5, num_workers=4):
    
    # Directories
    
    source_dir_pth = os.path.join('./wd/cons_raw_img',source_dir)
    dest_dir = os.path.join('./wd/meta_clusters',source_dir)
    
    os.makedirs(dest_dir, exist_ok=True)

    # Dictionary to hold images by hash clusters
    clusters = []
    img_paths = [os.path.join(source_dir_pth, img) for img in os.listdir(source_dir_pth) if img.endswith(('jpg', 'jpeg', 'png'))]
    print(f"Found {len(img_paths)} images to process.\n")

    # Use ThreadPoolExecutor for parallel processing of image hashing
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all image hash tasks
        future_to_img = {executor.submit(get_image_hash, img_path): img_path for img_path in img_paths}

        # Process completed tasks as they finish with a progress bar
        with tqdm(total=len(img_paths), desc="Hashing images") as pbar:
            for future in as_completed(future_to_img):
                img_path, img_hash = future.result()
                pbar.update(1)  # Update progress bar

                if img_hash is None:
                    continue

                added_to_cluster = False

                # Check if the image belongs to an existing cluster within the distance threshold
                for cluster in clusters:
                    if img_hash - cluster[0] <= distance_threshold:
                        cluster.append(img_path)
                        added_to_cluster = True
                        break

                # If no suitable cluster was found, create a new one
                if not added_to_cluster:
                    clusters.append([img_hash, img_path])

    print("\nImage hashing complete. Organizing images into clusters...")

    # Organize images into clusters with a progress bar
    with tqdm(total=len(clusters), desc="Organizing clusters") as pbar:
        for idx, cluster in enumerate(clusters):
            cluster_dir = os.path.join(dest_dir, f'cluster_{idx}')
            os.makedirs(cluster_dir, exist_ok=True)

            for file_path in cluster[1:]:  # Skip the hash, only take file paths
                shutil.copy(file_path, cluster_dir)

            pbar.update(1)  # Update progress bar for each cluster

    print("\nAll images have been clustered and copied to", dest_dir)

if __name__ == "__main__":
    print("Starting image clustering based on perceptual hash...")
    distance_threshold = 15  # Set your desired threshold here
    num_workers = 44  # Adjust this based on your CPU cores for optimal performance
    source_dir_list = ['pp_crawler_baseline', 'pp_crawler']
    for sd in source_dir_list:
        print(f"Clustering for {sd}")
        cluster_images(sd, distance_threshold, num_workers)
    print("Clustering process complete.")

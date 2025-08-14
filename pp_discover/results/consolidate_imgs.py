import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def copy_image(img_path, dest_dir):
    """Copy a single image file to the destination directory."""
    try:
        shutil.copy(img_path, dest_dir)
        print(f"Copied {img_path} to {dest_dir}")
    except Exception as e:
        print(f"Failed to copy {img_path}: {e}")

def process_screenshots_dir(screenshots_dir, dest_dir):
    """Process a single screenshots directory."""
    if os.path.isdir(screenshots_dir):
        for img_file in os.listdir(screenshots_dir):
            img_path = os.path.join(screenshots_dir, img_file)
            if os.path.isfile(img_path):
                yield img_path

def consolidate_images(source_dir):
    """Consolidate images from source_dir into the destination directory."""
    src = source_dir
    dest_dir = os.path.join(config['cons_imgs']['dest_base_dir'], src)

    # Create the destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)

    # Check if the logs directory exists within the source directory
    logs_dir = os.path.join(config['general']['log_base_dir'], src, 'logs')
    if not os.path.isdir(logs_dir):
        print(f"No logs directory found in {src}")
        return

    image_tasks = []
    # Iterate through all subdirectories within the logs directory
    for sub_dir1 in os.listdir(logs_dir):
        sub_dir1_path = os.path.join(logs_dir, sub_dir1)
        if not os.path.isdir(sub_dir1_path):
            continue

        for sub_dir2 in os.listdir(sub_dir1_path):
            sub_dir2_path = os.path.join(sub_dir1_path, sub_dir2)
            if not os.path.isdir(sub_dir2_path):
                continue

            screenshots_dir = os.path.join(sub_dir2_path, 'screenshots')
            image_tasks.extend(process_screenshots_dir(screenshots_dir, dest_dir))

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=config['general']['max_workers']) as executor:
        futures = [executor.submit(copy_image, img_path, dest_dir) for img_path in image_tasks]
        for future in futures:
            future.result()  # Wait for each thread to complete

if __name__ == "__main__":
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        consolidate_images(sd)

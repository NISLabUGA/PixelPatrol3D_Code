"""
This script randomly samples a fixed number of image–text pairs from each subdirectory
of a source dataset and copies them to a target directory while preserving the original
subdirectory structure. It ensures that only images with corresponding text files are
included, maintaining dataset consistency. The random seed is fixed for reproducibility.
"""

import os
import shutil
import random

# Set random seed for reproducibility
random.seed(123)

# Directories
in_dir = "/mnt/nis_lab_research/ext_class/senet_data/irfan_data/tt_aug/benign/train"  # Input directory
out_dir = "/mnt/nis_lab_research/ext_class/senet_data/irfan_data/tt_aug/benign/train_sampled"  # Output directory
os.makedirs(out_dir, exist_ok=True)  # Ensure the output directory exists

# Define the number of samples per subdirectory
num_samples = 1500

# Iterate through all subdirectories
for subdir, _, files in os.walk(in_dir):
    # Get the relative path of the subdirectory
    rel_path = os.path.relpath(subdir, in_dir)
    out_subdir = os.path.join(out_dir, rel_path)
    
    # Create corresponding subdirectory in out_dir
    os.makedirs(out_subdir, exist_ok=True)

    # Get all image files (assuming images have .jpg, .png, etc.)
    image_files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    # Ensure images have corresponding text files
    valid_images = [img for img in image_files if os.path.exists(os.path.join(subdir, os.path.splitext(img)[0] + ".txt"))]

    # If there are fewer images than required, take all
    sampled_images = random.sample(valid_images, min(num_samples, len(valid_images)))

    # Copy images and corresponding text files to the same subdirectory structure in out_dir
    for img in sampled_images:
        img_path = os.path.join(subdir, img)
        txt_path = os.path.join(subdir, os.path.splitext(img)[0] + ".txt")

        # Destination paths (preserve directory structure)
        dest_img_path = os.path.join(out_subdir, img)
        dest_txt_path = os.path.join(out_subdir, os.path.splitext(img)[0] + ".txt")

        # Copy files
        shutil.copy2(img_path, dest_img_path)
        shutil.copy2(txt_path, dest_txt_path)

    print(f"Processed {len(sampled_images)} files from {subdir} → {out_subdir}")

print("Sampling complete. Files copied to:", out_dir)

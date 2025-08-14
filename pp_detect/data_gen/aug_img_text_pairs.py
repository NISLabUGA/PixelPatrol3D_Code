"""
This script generates augmented image–text pairs from a source dataset. It applies random
image transformations (brightness, contrast, saturation, hue, color jitter, posterize, blur)
using Albumentations, and optionally shuffles words in the corresponding text files.
Original pairs are preserved, and multiple augmented variants are saved in the output directory.
"""


import os
import shutil
import random
import cv2
import albumentations as A

# Input and Output Directories
in_dir = "/mnt/nis_lab_research/ext_class/senet_data/fin_main_tt/mal/train"
out_dir = "/mnt/nis_lab_research/ext_class/senet_data/fin_main_tt/mal/train_aug_img_only"

# Allowed Extensions
img_extensions = {".jpg", ".png", ".bmp", ".gif"}
txt_extension = ".txt"

# Ensure output directory exists
os.makedirs(out_dir, exist_ok=True)

# Augmentation Parameters (Adjustable)
num_augmentations_per_img = 9  # Adjust this number
apply_augmentations = [
    "brightness", "contrast", "saturation", "hue", "color_jitter",
    "posterize", "blur"
]

# Flag to control text augmentation
use_bow_for_text = False  # Set to False to disable bag-of-words text shuffling

# Image Augmentation Functions
def getRandTup(low_low, low_high, high_low, high_high):
    rand_low = random.uniform(low_low, low_high)
    rand_high = random.uniform(high_low, high_high)
    return (rand_low, rand_high) if random.random() < 0.5 else (rand_high, rand_high)

def aug_brightness(img): return A.ColorJitter(brightness=getRandTup(.3, .8, 2, 3.5))(image=img)['image']
def aug_contrast(img): return A.ColorJitter(contrast=getRandTup(.3, .8, 2, 3.5))(image=img)['image']
def aug_saturation(img): return A.ColorJitter(saturation=getRandTup(.3, .8, 2, 3.5))(image=img)['image']
def aug_hue(img): return A.ColorJitter(hue=getRandTup(-.5, -.075, .075, .5))(image=img)['image']
def aug_color_jitter(img): return A.ColorJitter(
    brightness=getRandTup(.3, .8, 1.5, 2.25),
    contrast=getRandTup(.3, .8, 1.5, 2.25),
    saturation=getRandTup(.3, .8, 1.5, 2.25),
    hue=getRandTup(-.5, -.075, .075, .5))(image=img)['image']
def aug_posterize(img): return A.Posterize(num_bits=(1, 2))(image=img)['image']
def aug_blur(img): return A.Blur(blur_limit=(5, 9))(image=img)['image']

augmentations = {
    "brightness": aug_brightness,
    "contrast": aug_contrast,
    "saturation": aug_saturation,
    "hue": aug_hue,
    "color_jitter": aug_color_jitter,
    "posterize": aug_posterize,
    "blur": aug_blur
}

# Text Augmentation: Bag of Words (Shuffle Words)
def bag_of_words_augmentation(text):
    words = text.split()
    random.shuffle(words)  # Shuffle word order
    return ' '.join(words)

# Process Each Resolution Directory
for res in os.listdir(in_dir):
    res_path = os.path.join(in_dir, res)
    res_out_dir = os.path.join(out_dir, res)
    os.makedirs(res_out_dir, exist_ok=True)

    for file in os.listdir(res_path):
        file_path = os.path.join(res_path, file)
        fn, ext = os.path.splitext(file)

        # Process Images
        if ext in img_extensions:
            img_path = file_path
            og_img = cv2.imread(img_path)

            # Ensure text file exists
            txt_path = os.path.join(res_path, f"{fn}.txt")
            if not os.path.exists(txt_path):
                print(f"Warning: No text file found for {img_path}")
                continue

            with open(txt_path, "r") as f:
                original_text = f.read()

            # Save Original Image and Text Pair
            fn_new = f"{fn}_og.png"
            cv2.imwrite(os.path.join(res_out_dir, fn_new), og_img)
            with open(os.path.join(res_out_dir, f"{fn}_og.txt"), "w") as f:
                f.write(original_text)

            # Generate Augmented Pairs
            for i in range(num_augmentations_per_img):
                aug_type = random.choice(apply_augmentations)  # Randomly pick an augmentation
                aug_img = augmentations[aug_type](og_img)  # Apply the augmentation

                # Save Augmented Image
                aug_img_fn = f"{fn}_{aug_type}_{i}.png"
                cv2.imwrite(os.path.join(res_out_dir, aug_img_fn), aug_img)

                # Generate & Save Augmented Text
                aug_text_fn = f"{fn}_{aug_type}_{i}.txt"
                if use_bow_for_text:
                    augmented_text = bag_of_words_augmentation(original_text)
                else:
                    augmented_text = original_text
                with open(os.path.join(res_out_dir, aug_text_fn), "w") as f:
                    f.write(augmented_text)

    print(f"Processed: {res}")

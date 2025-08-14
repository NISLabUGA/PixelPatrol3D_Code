"""
This script recursively processes all images in specified directories,
runs Tesseract OCR to extract text from each image, and saves the results
as .txt files in the same location as the original images. Supports common
image formats (PNG, JPG, JPEG, TIFF, BMP) and can be configured to use a
custom Tesseract executable path if not in the system PATH.
"""


import os
from PIL import Image  # Pillow for image file handling
import pytesseract     # Python wrapper for Tesseract OCR

# If Tesseract is not in your system PATH, uncomment and set its path here:
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# List of directories to process
main_dir_list = [
    'dir/to/process'
]

def extract_text_from_image(image_path, output_path):
    """
    Extracts text from a single image using Tesseract OCR
    and saves it to a text file.
    """
    try:
        # Open the image file
        image = Image.open(image_path)

        # Perform OCR using Tesseract
        text = pytesseract.image_to_string(image)

        # Save extracted text to a .txt file
        with open(output_path, 'w', encoding='utf-8') as text_file:
            text_file.write(text)

        print(f"Text extracted and saved to: {output_path}")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def process_images_in_directory(main_directory):
    """
    Walks through all subdirectories in `main_directory`,
    performs OCR on each image, and saves the results as text files.
    """
    print(f"Processing directory: {main_directory}")
    
    for root, dirs, files in os.walk(main_directory):
        for i, file_name in enumerate(files):
            print(i, file_name)

            # Check if the file is an image by extension
            if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
                image_path = os.path.join(root, file_name)

                # Create output .txt file path
                output_file_name = os.path.splitext(file_name)[0] + ".txt"
                output_path = os.path.join(root, output_file_name)

                # Extract text and save
                extract_text_from_image(image_path, output_path)

if __name__ == "__main__":
    for dir_ in main_dir_list:
        process_images_in_directory(dir_)
    print("OCR processing complete.")

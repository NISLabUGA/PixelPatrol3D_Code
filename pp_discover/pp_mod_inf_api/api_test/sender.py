import os
import time
import random
import json

# Configuration
api_url = "http://pp_api_cont_1:50001/infer"
image_dir = "./test_ss"
queue_file = "./request_queue.json"
interval_seconds = 5  # Frequency of API calls

def get_random_image(directory):
    """Get a random image from the specified directory."""
    images = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if not images:
        raise FileNotFoundError(f"No images found in directory: {directory}")
    return random.choice(images)

def main():
    while True:
        try:
            # Select a random image
            image_name = get_random_image(image_dir)
            image_path = os.path.join(image_dir, image_name)

            # Print the image being sent
            print(f"Queueing image: {image_name}")

            # Log the payload to the queue file
            with open(queue_file, "a") as queue:
                queue_entry = {
                    "image_name": image_name,
                    "image_path": image_path
                }
                queue.write(json.dumps(queue_entry) + "\n")

        except Exception as e:
            print(f"Error: {str(e)}")

        # Wait for the specified interval before the next call
        time.sleep(interval_seconds)

if __name__ == "__main__":
    main()

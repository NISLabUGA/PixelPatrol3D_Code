import json
import requests
import time
import os

# Configuration
api_url = "http://pp_api_cont_1:50001/infer"
queue_file = "./request_queue.json"
log_file = "./response_log.json"

def process_request(queue_entry):
    """Send the API call for a single queue entry."""
    try:
        print(f"Processing image: {queue_entry['image_name']}")
        with open(queue_entry["image_path"], "rb") as img:
            files = {"image": img}
            data = {"url": queue_entry["image_name"]}

            # Make the API call
            response = requests.post(api_url, files=files, data=data)

            # Log the response
            with open(log_file, "a") as log:
                log_entry = {
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "image_name": queue_entry["image_name"],
                    "response_code": response.status_code,
                    "response_text": response.text
                }
                log.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        print(f"Error processing {queue_entry['image_name']}: {e}")

def main():
    while True:
        try:
            # Process queued requests
            if os.path.exists(queue_file):
                with open(queue_file, "r") as queue:
                    lines = queue.readlines()

                # Process each entry
                with open(queue_file, "w") as queue:
                    for line in lines:
                        if line.strip():
                            queue_entry = json.loads(line)
                            process_request(queue_entry)

        except Exception as e:
            print(f"Error: {e}")

        # Small delay to prevent high CPU usage
        time.sleep(0.1)

if __name__ == "__main__":
    main()

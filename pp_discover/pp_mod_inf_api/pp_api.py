from fastapi import FastAPI
import redis
import json
import base64
import cv2
import numpy as np
import time
import threading
from pp_inf import pp_inference, load_models
import yaml

# Load the configuration from the YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

app = FastAPI()

# Connect to Redis
REDIS_HOST = config['redis']['hostname']
REDIS_PORT = config['redis']['port']
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Load models at startup
@app.on_event("startup")
async def load_models_on_startup():
    global obj_det_pred_list, classifier
    obj_det_pred_list, classifier = load_models()

# Function to process tasks from Redis queue
def process_tasks():
    while True:
        try:
            # Fetch a task from Redis
            task_data = redis_client.lpop("inference_queue")
            if task_data:
                # Parse the task
                task = json.loads(task_data)
                task_id = task["taskId"]  # Get the unique task ID
                url = task["url"]
                image_base64 = task["image"]

                # Decode the image
                image_bytes = base64.b64decode(image_base64)
                image_np = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

                # Perform inference
                output = pp_inference(img, url, obj_det_pred_list, classifier)

                # Store the result in Redis
                result_key = f"result:{task_id}"
                redis_client.set(result_key, json.dumps(output))

                print(f"Task {task_id} processed. Result stored in Redis with key {result_key}.")
            else:
                # Sleep briefly if no tasks are available
                time.sleep(1)
        except Exception as e:
            print(f"Error processing task: {e}")

# Start the task processing loop
@app.on_event("startup")
async def start_task_processing():
    task_thread = threading.Thread(target=process_tasks, daemon=True)
    task_thread.start()

if __name__ == '__main__':
    import uvicorn

    # Default port from config
    port = config['fastapi']['default_port']

    uvicorn.run(app, host='0.0.0.0', port=port)

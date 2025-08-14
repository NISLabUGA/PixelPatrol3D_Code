import os
import subprocess
import multiprocessing
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
import cv2
import numpy as np
import json
from pp_inf import pp_inference, load_models
from utils import sterilize_url, get_current_timestamp
import asyncio

app = FastAPI()

# Global variables
model_instances = []
instance_queues = []  # List of multiprocessing.Queue objects for workers
result_queues = []  # List of result queues for workers
active_task_counters = {}  # To track active tasks for each worker
max_memory_threshold = 0.40  # 40% GPU memory utilization threshold
model_memory_usage = None  # Memory usage of a single model instance (to be calculated dynamically)
round_robin_index = 0  # Global index for round-robin assignment


def initialize_worker(task_queue, result_queue, ready_event, instance_id):
    """Worker process to load models and handle tasks."""
    import torch
    from pp_inf import load_models

    print(f"Initializing worker {instance_id}...")

    # Load models in the worker process to avoid CUDA re-initialization issues
    obj_det_pred_list, classifier = load_models()
    ready_event.set()

    print(f"Worker {instance_id} is ready.")
    while True:
        task = task_queue.get()
        if task == "SHUTDOWN":
            print(f"Worker {instance_id} shutting down.")
            break
        elif task is None:
            continue

        task_id, img, url, og_img_outpath, json_outpath = task
        output = pp_inference(img, url, obj_det_pred_list, classifier)
        cv2.imwrite(og_img_outpath, img)
        with open(json_outpath, 'w') as json_file:
            json.dump(output, json_file, indent=4)
        result_queue.put((task_id, output))  # Send results back to the main process


def get_gpu_memory_usage():
    """Get GPU memory usage as a fraction using nvidia-smi."""
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
        stdout=subprocess.PIPE,
        text=True,
    )
    lines = result.stdout.strip().split("\n")
    used, total = map(int, lines[1].strip().split(','))
    return used, total


@app.on_event("startup")
async def startup_event():
    """Dynamically scale instances based on GPU memory usage."""
    global model_instances, instance_queues, result_queues, model_memory_usage, active_task_counters

    while True:
        used_memory, total_memory = get_gpu_memory_usage()
        current_memory_usage = used_memory / total_memory

        if model_memory_usage is not None:
            predicted_memory_usage = (used_memory + model_memory_usage) / total_memory
            if predicted_memory_usage > max_memory_threshold:
                print(f"Predicted memory usage {predicted_memory_usage * 100:.2f}% exceeds threshold.")
                break

        instance_id = len(model_instances)
        task_queue = multiprocessing.Queue()  # Task queue for this worker
        result_queue = multiprocessing.Queue()  # Result queue for this worker
        ready_event = multiprocessing.Event()

        instance_queues.append(task_queue)
        result_queues.append(result_queue)
        active_task_counters[instance_id] = 0  # Initialize active task counter

        process = multiprocessing.Process(
            target=initialize_worker,
            args=(task_queue, result_queue, ready_event, instance_id)
        )
        process.start()
        model_instances.append(process)

        print(f"Waiting for worker {instance_id} to initialize...")
        ready_event.wait()
        print(f"Worker {instance_id} initialized.")

        if model_memory_usage is None:
            new_used_memory, _ = get_gpu_memory_usage()
            model_memory_usage = new_used_memory - used_memory
            print(f"Estimated memory usage per model: {model_memory_usage / 1024:.2f} MB")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up worker processes."""
    for queue in instance_queues:
        queue.put("SHUTDOWN")  # Send explicit shutdown signal
    for process in model_instances:
        process.join()


@app.post("/infer")
async def infer(image: UploadFile = File(...), url: str = Form(...)):
    """Route requests to workers using round-robin initially, then least-busy based on a threshold."""
    global round_robin_index

    if image is None or url is None:
        raise HTTPException(status_code=400, detail="Image or URL missing")

    # Directories for output
    og_img_dir = './og_img'
    os.makedirs(og_img_dir, exist_ok=True)

    json_dir = './json'
    os.makedirs(json_dir, exist_ok=True)

    og_img_outpath = os.path.join(og_img_dir, f"{sterilize_url(url)}_{get_current_timestamp()}.png")
    json_outpath = os.path.join(json_dir, f"{sterilize_url(url)}_{get_current_timestamp()}.json")

    image_file = await image.read()
    image_np = np.frombuffer(image_file, np.uint8)
    img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # Minimum tasks threshold for switching to least-busy strategy
    min_tasks_threshold = 3

    # Determine the worker to assign the task
    if all(queue.qsize() < min_tasks_threshold for queue in instance_queues):
        # Use round-robin: Assign tasks sequentially
        instance_id = round_robin_index % len(model_instances)
        round_robin_index += 1
    else:
        # Switch to least-busy worker based on the queue length
        instance_id = min(range(len(instance_queues)), key=lambda i: instance_queues[i].qsize())

    # Update the task queue and counters
    task_queue = instance_queues[instance_id]
    result_queue = result_queues[instance_id]

    print(f"Routing request to Instance {instance_id}. Queue Size = {task_queue.qsize()}")

    # Generate a unique task ID
    task_id = f"task-{round_robin_index}"

    # Add task to worker queue
    task_queue.put((task_id, img, url, og_img_outpath, json_outpath))

    # Wait for the result (synchronously fetch from the worker's result queue)
    loop = asyncio.get_running_loop()
    task_id_result, output = await loop.run_in_executor(None, result_queue.get)

    print(f"Request handled by Instance {instance_id}. Queue Size after completion = {task_queue.qsize()}")

    return output



if __name__ == '__main__':
    import torch
    torch.multiprocessing.set_start_method("spawn", force=True)  # Set spawn method here
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

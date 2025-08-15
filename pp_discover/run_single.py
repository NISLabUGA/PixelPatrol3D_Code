"""
This is the main crawler orchestration script that manages parallel web crawling operations using Docker containers. 
It loads URLs from a CSV file, creates combinations of URLs with different crawlers and user agents, then launches 
multiple Docker containers concurrently (up to a configurable limit) to crawl websites. It includes port management, 
timeout handling, progress logging, and thread-safe container lifecycle management to efficiently process large-scale 
web crawling tasks.
"""

import os
import random
import subprocess
import time
from itertools import product
import threading
import yaml
import pandas as pd
from datetime import datetime

# Load the configuration from the YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Load and randomize URL list
csv_list = pd.read_csv(config['url_list_csv_path'])
url_list = list(set(csv_list['url'].to_list()))
random.shuffle(url_list)

# Allowing control over how many urls to crawl from master list
url_crawl_max_num = config['url_crawl_max_num']
if url_crawl_max_num == "all":
    url_list = url_list
else:
    url_list = url_list[:int(url_crawl_max_num)]

# Define crawlers and user agents
crawler_list = config['crawler_dir_list']
user_agent_list = config['user_agent_list']

# Generate permutations of URL, crawler, and user agent combinations
combinations = list(product(url_list, crawler_list, user_agent_list))
random.shuffle(combinations)

# Port pool and container management
max_containers = config['max_containers']
base_port = config['base_port']
available_ports = {base_port + 1 + i for i in range(max_containers)}

# Thread-safe container management
lock = threading.Lock()

# Logging setup
log_file = config['log_path']
if not os.path.exists(log_file):
    with open(log_file, "w") as log:
        log.write("Current,Timestamp,Combination,Progress,Percent Completed,Cumulative Time\n")

start_time = time.time()

def log_progress(combination, current, total):
    """Log the progress of the script to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    percent_completed = (current / total) * 100
    cumulative_time = time.time() - start_time
    log_entry = f"{current},{timestamp},{combination.replace(',', '-')},{current}/{total},{percent_completed:.2f},{cumulative_time:.2f}\n"
    with open(log_file, "a") as log:
        log.write(log_entry)

def is_port_in_use(port):
    """Check if a port is currently in use by any running container."""
    result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
    return f"{port}" in result.stdout

def wait_for_available_port():
    """Wait for an available port if none are currently free."""
    while True:
        with lock:
            for port in available_ports:
                if not is_port_in_use(port):
                    available_ports.remove(port)
                    return port
        print("No ports available. Waiting...")
        time.sleep(1)

def release_port(port):
    """Release a port after its container is done."""
    with lock:
        available_ports.add(port)

def run_docker_command(url, crawler, user_agent, index, total, timeout=config['timeout']+60):
    """Run a Docker command with a timeout and wait for it to complete."""
    port = wait_for_available_port()
    combination = f"{url},{crawler},{user_agent}"
    container_id = None
    try:
        cmd = f"""
            docker run --rm -d \
                -v $(pwd):/mnt/pp_pkg \
                -p {port}:5901 \
                --network pp_nw \
                sking115422/pp_crawler_single_cont:v1 \
                {crawler} {url} {user_agent} {user_agent}_1
        """
        print(f"Executing command on port {port}:\n{cmd}")
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if proc.returncode != 0:
            print(f"Error: {proc.stderr.strip()}")
            return

        # Extract the container ID from the output
        container_id = proc.stdout.strip()

        start_time = time.time()
        while is_port_in_use(port):
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print(f"Timeout reached for container {container_id}. Stopping it...")
                if container_id:
                    subprocess.run(f"docker stop {container_id}", shell=True)
                break
            time.sleep(1)

        # Log progress after successful execution
        log_progress(combination, index + 1, total)

    finally:
        print(f"Releasing port {port}")
        release_port(port)

def container_manager():
    """Main container manager to launch Docker containers."""
    threads = []
    total_combinations = len(combinations)

    for index, (url, crawler, user_agent) in enumerate(combinations):
        thread = threading.Thread(target=run_docker_command, args=(url, crawler, user_agent, index, total_combinations))
        threads.append(thread)
        thread.start()
        
        # Ensure only `max_containers` are running at any given time
        while len(threads) >= max_containers:
            threads = [t for t in threads if t.is_alive()]
            time.sleep(1)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

# Start the container manager
if __name__ == "__main__":
    container_manager()

"""
This is a high-level orchestration script that automates the complete crawling pipeline. It sequentially executes 
cleanup operations (via clean_all.py) followed by the main crawling process (via run_single.py), and optionally 
performs Docker container cleanup afterward. It serves as the entry point for running large-scale crawling 
operations with automated setup and teardown.
"""

import subprocess
import time
import yaml

# Load the configuration from the YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

def execute_command(command, description):
    try:
        print(f"Executing: {description}")
        # Run the command
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print(f"Output for {description}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error while executing {description}:\n{e.stderr}")
        raise


def clean_docker_containers(substrings):
    """
    Cleans up Docker containers whose names contain any of the specified substrings.
    """
    try:
        print("Fetching list of Docker containers...")
        # List all Docker containers
        result = subprocess.run(
            "docker ps -a --format '{{.ID}} {{.Names}}'",
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )
        containers = result.stdout.strip().split("\n")
        
        # Check each container name for matching substrings
        for container in containers:
            if not container.strip():  # Skip empty lines
                continue
            container_id, container_name = container.split(maxsplit=1)
            if any(substring in container_name for substring in substrings):
                print(f"Removing container {container_name} (ID: {container_id})...")
                subprocess.run(f"docker rm -f {container_id}", shell=True, check=True, text=True)
        print("Docker cleanup complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error while cleaning Docker containers:\n{e.stderr}")
        raise


def main():
    # List of commands to execute
    commands = [
        ("python clean_all.py", "Clean up all directories"),
        ("python run_single.py", "Run crawler management script"),
    ]

    for command, description in commands:
        execute_command(command, description)
        # print("Sleeping for 3 seconds...")
        time.sleep(1)
        
    if config['auto_clean']:
        
        # List of substrings to match container names
        substrings_to_clean = config['conts_to_clean']

        if substrings_to_clean:
            print("Cleaning up Docker containers with specified substrings...")
            clean_docker_containers(substrings_to_clean)


if __name__ == "__main__":
    main()

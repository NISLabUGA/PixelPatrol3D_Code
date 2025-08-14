import subprocess
import os
import yaml

# Load the configuration from the YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

def execute_command(command, directory, description):
    try:
        print(f"Executing: {description} in {directory}")

        # Run the command with the specified working directory
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True, cwd=directory)
        print(f"Output for {description}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error while executing {description} in {directory}:\n{e.stderr}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

def clean_all():
    
    file_path = config['log_path']
    if os.path.exists(file_path):
        print("Cleaning old progress log")
        print()
        os.remove(file_path)
        
    commands = [
        ("python clean.py", "./pp_mod_inf_api", "Python clean script in pp_mod_inf_api"),
        ("node clean.js", "./pp_crawler_baseline", "Node.js clean script in pp_crawler_baseline"),
        ("node clean.js", "./pp_crawler", "Node.js clean script in pp_crawler"),
    ]
    
    for command, directory, description in commands:
        execute_command(command, directory, description)

if __name__ == "__main__":
    clean_all()

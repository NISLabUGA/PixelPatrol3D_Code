"""
This is a command-line utility script that crawls a single URL using a specified crawler configuration. It takes 
parameters for the crawler directory, target URL, user agent, and log folder, then generates a unique hash for 
the URL and executes a Node.js screenshot capture script with the appropriate parameters. It's designed to be 
called by other scripts or used standalone for individual URL crawling tasks.
"""

import sys
import pandas as pd
import hashlib
import subprocess
import os
import yaml

# Load the configuration from the YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    
timeout = config['timeout']
crawl_type = config['crawl_type']

def run_command(base_dir, url, user_agent, log_folder):

    # Generate a unique hash of the URL
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]  # Shorten the hash to 12 characters if desired
    command = f"cd {base_dir} && node capture_screenshots.js {url} {url_hash} {timeout} {user_agent} {crawl_type} {log_folder}"
    
    # Print the command to the screen
    print(command)
    
    # Execute the command in the shell
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")

if __name__ == "__main__":
    
    if len(sys.argv) != 5:
        print("Usage: python script.py <crawler_base_dir> <url> <user_agent> <log_folder>")
    else:
        crawler_base_dir = sys.argv[1]
        url = sys.argv[2]
        user_agent = sys.argv[3]
        log_folder = sys.argv[4]
        run_command(crawler_base_dir, url, user_agent, log_folder)

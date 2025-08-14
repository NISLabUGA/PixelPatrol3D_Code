import os
import json
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def consolidate_json_logs(source_dir):
    # Define source directories and destination file path
    
    src = source_dir
    dest_dir = os.path.join(config['cons_json']['dest_base_dir'], src)
    dest_file = os.path.join(dest_dir, 'map.json')

    # Create the destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)

    # Initialize a list to store all JSON data
    consolidated_data = []
    consolidated_dict = {}

    # Check if the logs directory exists within the source directory
    logs_dir = os.path.join(config['general']['log_base_dir'], src, 'logs')
    if not os.path.isdir(logs_dir):
        print(f"No logs directory found in {src}")

    # Iterate through all subdirectories within the logs directory
    for sub_dir1 in os.listdir(logs_dir):
        sub_dir1_path = os.path.join(logs_dir, sub_dir1)
        if not os.path.isdir(sub_dir1_path):
            continue

        # Iterate through all subdirectories in the current subdirectory
        for sub_dir2 in os.listdir(sub_dir1_path):
            sub_dir2_path = os.path.join(sub_dir1_path, sub_dir2)
            if not os.path.isdir(sub_dir2_path):
                continue

            # Define the JSON_log directory path
            json_log_dir = os.path.join(sub_dir2_path, 'JSON_log')
            if os.path.isdir(json_log_dir):
                # Iterate through JSON files in JSON_log directory
                for json_file in os.listdir(json_log_dir):
                    json_file_path = os.path.join(json_log_dir, json_file)
                    if os.path.isfile(json_file_path) and json_file.endswith('.json'):
                        # Read JSON data and add it to consolidated_data
                        with open(json_file_path, 'r') as f:
                            try:
                                data = json.load(f)
                                consolidated_data.extend(data)
                                print(f"Added data from {json_file_path}")
                            except json.JSONDecodeError as e:
                                print(f"Error reading {json_file_path}: {e}")
                                
    for item in consolidated_data:
        try:
            consolidated_dict[item['screenshot_name'].split('/')[-1]] = item
        except Exception as e:
            print(e)

    # Write the consolidated data to the destination JSON file
    with open(dest_file, 'w') as f:
        json.dump(consolidated_dict, f, indent=4)
        print(f"Consolidated JSON data saved to {dest_file}")

if __name__ == "__main__":
    
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        consolidate_json_logs(sd)

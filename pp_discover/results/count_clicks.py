import os
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def count_chosen_elements(src):
    
    output_dir = os.path.join(config['count_clicks']['dest_base_dir'], src)
    output_file = os.path.join(output_dir, 'tot_num_clicks.txt')

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Initialize a total count for all chosen_element lines
    total_chosen_element_count = 0

    # Open the output file for writing
    with open(output_file, 'w') as output:

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

                # Define the element_coor directory path
                element_coor_dir = os.path.join(sub_dir2_path, 'element_coor')
                if os.path.isdir(element_coor_dir):
                    # Iterate through log files in element_coor directory
                    for log_file in os.listdir(element_coor_dir):
                        log_file_path = os.path.join(element_coor_dir, log_file)
                        if os.path.isfile(log_file_path) and log_file.endswith('.log'):
                            # Count lines starting with "chosen_element:"
                            chosen_element_count = 0
                            with open(log_file_path, 'r') as f:
                                for line in f:
                                    if line.strip().startswith("chosen_element:"):
                                        chosen_element_count += 1
                            
                            # Write the result to the output file
                            output.write(f"{log_file}: {chosen_element_count} lines starting with 'chosen_element:'\n")
                            print(f"Processed {log_file} with {chosen_element_count} chosen_element lines")

                            # Add to the total count
                            total_chosen_element_count += chosen_element_count

        # Write the total count at the end of the file
        output.write(f"\nTotal clicks across all files: {total_chosen_element_count}\n")
        print(f"Total clicks: {total_chosen_element_count}")

if __name__ == "__main__":
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f'Count clicks for {sd}')
        count_chosen_elements(sd)
    print('Counting clicks process complete')
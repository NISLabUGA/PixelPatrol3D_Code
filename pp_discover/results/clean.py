import os
import shutil
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def clean():
    # Define source and target directories
    source_dir = config['general']['working_dir']
    target_dir = config['clean']['dest_dir']

    # Ensure source and target directories exist
    if not os.path.exists(source_dir):
        print(f"Source directory '{source_dir}' does not exist.")
        return

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Get existing subdirectories in target_dir starting with 'r'
    existing_dirs = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d)) and d.startswith('r') and d[1:].isdigit()]

    # Find the highest numbered subdirectory
    if existing_dirs:
        max_index = max(int(d[1:]) for d in existing_dirs)
    else:
        max_index = 0

    # Create the new subdirectory
    new_sub_dir = f'r{max_index + 1}'
    new_target_dir = os.path.join(target_dir, new_sub_dir)
    os.makedirs(new_target_dir)

    # Move all files and folders from source_dir to the new subdirectory
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        shutil.move(item_path, new_target_dir)

    print(f"All files and folders from '{source_dir}' have been moved to '{new_target_dir}'.")

if __name__ == "__main__":
    clean()

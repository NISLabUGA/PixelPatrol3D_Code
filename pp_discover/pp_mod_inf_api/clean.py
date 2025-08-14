import os
import shutil

# List of directories to remove and recreate
directories = ["./json", "./og_img", "./vis"]

def recreate_directories(dirs):
    
    for directory in dirs:
        # Remove the directory if it exists
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"Removed existing directory: {directory}")
        
        # Create the directory
        os.makedirs(directory)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    recreate_directories(directories)
    
    # file_path = './test.log'
    # if os.path.exists(file_path):
    #     os.remove(file_path)

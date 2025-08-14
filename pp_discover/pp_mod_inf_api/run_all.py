import subprocess
import os
import time
import yaml

# Load the configuration from the YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

gpu_ids = config['cont_mgmt']['gpu_ids']
cont_base_name = config['cont_mgmt']['cont_base_name']
mem_thld = config['cont_mgmt']['memory_threshold']

def get_gpu_memory_usage(gpu_id):
    """Get GPU memory usage as a fraction using nvidia-smi."""
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
        stdout=subprocess.PIPE,
        text=True,
    )
    lines = result.stdout.strip().split("\n")
    used, total = map(int, lines[gpu_id].strip().split(','))
    return used, total

def create_container(gpu_id, container_index):
    """Create a Docker container using the specified GPU."""
    container_name = f"{cont_base_name}_{container_index}"
    cmd = (
        f"docker run -d "
        f"-v /mnt/lts/nis_lab_research/pp_pkg:/mnt/pp_pkg "
        f"--name {container_name} "
        f"--hostname {container_name} "
        f"--network pp_nw "
        f"--gpus \"device={gpu_id}\" "
        f"sking115422/pp_single_api_cont:v1"
    )
    print(f"Creating container: {container_name} on GPU {gpu_id}")
    os.system(cmd)
    
def test_incs(start, increment, threshold):

    count = 0
    current_value = start
    
    while current_value + increment <= threshold:
        current_value += increment
        count += 1
    
    return count


def main():
    
    container_index = 1  # Start container numbering from 1
    model_size = 0 

    for gpu_id in gpu_ids:
        
        print(f'GPU {gpu_id} ...')
        
        total = 0
        used = 0
        num_cont = 0
        
        if container_index == 1:
            
            print(f"Mem threshold set at {mem_thld}")
            print("Creating first container to test model size")
            create_container(gpu_id, container_index)
            time.sleep(20)
            used, total = get_gpu_memory_usage(gpu_id)
            model_size = used
            mod_size_per = model_size / total
            print(f"Model size is {model_size} ({mod_size_per}%)")
            num_cont = test_incs(0, mod_size_per, mem_thld)
            print(f"Based on model size creating {num_cont} containers for {gpu_id}")
            
            for i in range(0, num_cont - 1):
                container_index += 1
                create_container(gpu_id, container_index)
                
            print(f"Max mem used {num_cont * model_size / total}")
            print(f"Total gpu mem {total}")
            
        else:
            used, total = get_gpu_memory_usage(gpu_id)
            mod_size_per = model_size / total
            num_cont = test_incs(0, mod_size_per, mem_thld)
            print(f"Based on model size creating {num_cont} containers for {gpu_id}")
            for i in range(0, num_cont):
                container_index += 1
                create_container(gpu_id, container_index)
            print(f"Max mem used {num_cont * model_size / total}")
            print(f"Total gpu mem {total}")
            

if __name__ == "__main__":
    main()

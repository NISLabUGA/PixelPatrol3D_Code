import os
import shutil
import pandas as pd
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def process_directories(sd):
    final_dir = '/mnt/lts/nis_lab_research/pp_pkg/results/runs/r5/final'
    mc_dir = '/mnt/lts/nis_lab_research/pp_pkg/results/runs/r5/meta_clusters'
    crawler_path = os.path.join(final_dir, sd)
    
    # Ensure it's a directory
    if os.path.isdir(crawler_path):
        check_csv_path = os.path.join(crawler_path, 'check.csv')
        
        # Check if the file exists
        if os.path.exists(check_csv_path):
            try:
                # Load the CSV as a pandas DataFrame
                df = pd.read_csv(check_csv_path)

                # Check if 'clusters' column exists
                if 'clusters' in df.columns:
                    
                    for cluster in df['clusters']:
                        cluster_dir = os.path.join(mc_dir, sd, str(cluster))

                        # Check if the corresponding cluster directory exists
                        if os.path.exists(cluster_dir):
                            # Copy the cluster directory to the subdirectory in final
                            target_dir = os.path.join(crawler_path, "mc_oi", str(cluster))
                            shutil.copytree(cluster_dir, target_dir, dirs_exist_ok=True)
                            print(f"Copied {cluster_dir} to {target_dir}")
                        else:
                            print(f"Cluster directory {cluster_dir} does not exist.")
                else:
                    print(f"'clusters' column not found in {check_csv_path}.")
            except Exception as e:
                print(f"Error processing {check_csv_path}: {e}")
        else:
            print(f"File {check_csv_path} does not exist.")

if __name__ == '__main__':
    
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f'Gathering metacluster of interest for {sd}')
        process_directories(sd)
    print('Process complete')
    


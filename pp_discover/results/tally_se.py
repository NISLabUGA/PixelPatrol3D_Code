import os
import json
import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def process_cluster(cluster_name, meta_clusters_dir, json_data):
    cluster_path = os.path.join(meta_clusters_dir, cluster_name)
    if not os.path.isdir(cluster_path):
        return None

    # Lists to store URLs and URL domain IDs for the current cluster
    url_set = set()
    domain_set = set()

    # Process each image in the current cluster
    for img_name in os.listdir(cluster_path):

        # Search for matching JSON entries based on screenshot_name
        print(img_name)
        
        try:
            url = json_data[img_name]["image_url"]
            url_set.add(url)
            domain_match = re.search(r"(?<=//)([^/]+)", url)
            if domain_match:
                domain_set.add(domain_match.group(0))
        except Exception as e:
            print("Error:", e)

    # Check if the cluster has multiple unique URLs
    is_social_engineering = len(domain_set) > 1

    return {
        "cluster": cluster_name,
        "url_list": list(url_set),
        "domain_list": list(domain_set),
        "is_social_engineering": is_social_engineering
    }

def identify_social_engineering_clusters(src):
    # Define paths
    json_file = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{src}_metadata.json')
    meta_clusters_dir = os.path.join(config['clustering']['dest_base_dir'], src)
    output_dir = os.path.join(config['tally_se']['dest_base_dir'], src)

    count_file = os.path.join(output_dir, 'count.txt')
    debug_file = os.path.join(output_dir, 'debug.txt')
    csv_file = os.path.join(output_dir, 'check.csv')

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load the consolidated JSON data
    with open(json_file, 'r') as f:
        json_data = json.load(f)

    # Initialize variables
    social_engineering_count = 0
    social_engineering_clusters = []
    debug_info = []

    # Use ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(process_cluster, cluster_name, meta_clusters_dir, json_data): cluster_name for cluster_name in os.listdir(meta_clusters_dir)}

        for future in as_completed(futures):
            cluster_name = futures[future]
            try:
                print(f"Processing cluster: {cluster_name}")
                result = future.result()
                if result:
                    debug_info.append(result)
                    if result["is_social_engineering"]:
                        social_engineering_count += 1
                        social_engineering_clusters.append(result["cluster"])
            except Exception as e:
                print(f"Error processing cluster {cluster_name}: {e}")

    # Write results to the count file
    with open(count_file, 'w') as f:
        f.write(f"Social Engineering Clusters Count: {social_engineering_count}\n")
        f.write("Clusters Identified as Social Engineering:\n")
        for cluster in social_engineering_clusters:
            f.write(f"{cluster}\n")

    # Write debug information to the debug file
    with open(debug_file, 'w') as f:
        for info in debug_info:
            f.write(f"Cluster: {info['cluster']}\n")
            f.write("URL List:\n")
            for url in info['url_list']:
                f.write(f"  - {url}\n")
            f.write("URL Domain ID List:\n")
            for domain_id in info['domain_list']:
                f.write(f"  - {domain_id}\n")
            f.write("\n")
            
    # Write debug information to the CSV file
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write the header row
        writer.writerow(['clusters', 'is_se', 'domain_list'])
        # Write each row
        for info in debug_info:
            if len(info['domain_list']) > 1:
                clusters = info['cluster']
                is_se = None  # Placeholder value
                domain_list = "; ".join(info['domain_list'])  # Join domain_list into a single string
                writer.writerow([clusters, is_se, domain_list])

    print(f"Results written to {count_file} and {debug_file} and {csv_file}")

if __name__ == "__main__":
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"Identifying potential SE clusters for {sd}")
        identify_social_engineering_clusters(sd)
    print("SE identification script complete")

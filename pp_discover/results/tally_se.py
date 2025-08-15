"""
Social Engineering Cluster Detection Module

This module analyzes image clusters to identify potential social engineering (BMA)
attempts by examining the domain diversity within each cluster. The core principle is
that legitimate websites typically have consistent visual elements within their own domain,
while BMA sites often mimic legitimate sites but serve content from different domains.

Key Features:
- Analyzes clusters of visually similar images for domain diversity
- Identifies clusters containing images from multiple domains (potential BMAs)
- Generates detailed reports with URL and domain analysis
- Produces CSV files for further analysis and manual review
- Uses parallel processing for efficient cluster analysis

Detection Logic:
- Clusters with images from only one domain are likely legitimate
- Clusters with images from multiple domains may indicate BMA attempts
- The assumption is that BMA sites copy visual elements from legitimate sites
- Multiple domains serving similar visual content suggests potential social engineering

Output Files:
- count.txt: Summary of social engineering clusters found
- debug.txt: Detailed analysis of each cluster with URLs and domains
- check.csv: Structured data for clusters flagged as potential social engineering

This analysis is crucial for:
- Identifying BMA campaigns that reuse visual elements
- Understanding the scale of visual mimicry in BMA attacks
- Providing candidates for manual review and validation
- Training machine learning models on social engineering patterns
"""

import os
import json
import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def process_cluster(cluster_name, meta_clusters_dir, json_data):
    """
    Analyze a single cluster for social engineering indicators.
    
    This function examines all images in a cluster, extracts their source URLs,
    identifies the domains, and determines if the cluster contains images from
    multiple domains (which may indicate social engineering).
    
    Args:
        cluster_name (str): Name of the cluster directory to analyze
        meta_clusters_dir (str): Base directory containing all clusters
        json_data (dict): Metadata mapping image names to their information
        
    Returns:
        dict: Analysis results including URLs, domains, and SE classification
        None: If cluster directory doesn't exist or processing fails
    """
    cluster_path = os.path.join(meta_clusters_dir, cluster_name)
    if not os.path.isdir(cluster_path):
        return None

    # Initialize sets to store unique URLs and domains for this cluster
    url_set = set()
    domain_set = set()
    images_processed = 0
    images_failed = 0

    # Process each image in the current cluster
    for img_name in os.listdir(cluster_path):
        # Skip non-image files
        if not img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            continue
            
        try:
            # Look up the URL for this image in the metadata
            url = json_data[img_name]["image_url"]
            url_set.add(url)
            
            # Extract domain from URL using regex
            # Pattern matches everything after "//" and before the next "/"
            domain_match = re.search(r"(?<=//)([^/]+)", url)
            if domain_match:
                domain = domain_match.group(0)
                # Remove common prefixes for better domain grouping
                domain = re.sub(r'^www\.', '', domain.lower())
                domain_set.add(domain)
            
            images_processed += 1
            
        except KeyError:
            # Image not found in metadata (shouldn't happen if pipeline ran correctly)
            images_failed += 1
        except Exception as e:
            print(f"Error processing {img_name} in cluster {cluster_name}: {e}")
            images_failed += 1

    # Determine if this cluster shows signs of social engineering
    # Multiple domains serving similar visual content suggests potential BMA
    is_social_engineering = len(domain_set) > 1

    return {
        "cluster": cluster_name,
        "url_list": list(url_set),
        "domain_list": list(domain_set),
        "is_social_engineering": is_social_engineering,
        "images_processed": images_processed,
        "images_failed": images_failed,
        "unique_urls": len(url_set),
        "unique_domains": len(domain_set)
    }

def identify_social_engineering_clusters(src):
    """
    Identify clusters that may contain social engineering attempts.
    
    This function processes all clusters for a given crawler directory,
    analyzes each cluster for domain diversity, and generates comprehensive
    reports identifying potential social engineering clusters.
    
    Args:
        src (str): Source crawler directory name (e.g., 'pp_crawler', 'pp_crawler_baseline')
    """
    print(f"Starting social engineering analysis for: {src}")
    
    # Define file paths
    json_file = os.path.join(config['dedup_imgs']['metadata_base_dir'], f'{src}_metadata.json')
    meta_clusters_dir = os.path.join(config['clustering']['dest_base_dir'], src)
    output_dir = os.path.join(config['tally_se']['dest_base_dir'], src)

    # Output file paths
    count_file = os.path.join(output_dir, 'count.txt')
    debug_file = os.path.join(output_dir, 'debug.txt')
    csv_file = os.path.join(output_dir, 'check.csv')

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Metadata file: {json_file}")
    print(f"Clusters directory: {meta_clusters_dir}")
    print(f"Output directory: {output_dir}")

    # Load the consolidated metadata
    try:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        print(f"Loaded metadata for {len(json_data)} images")
    except Exception as e:
        print(f"Error loading metadata file {json_file}: {e}")
        return

    # Check if clusters directory exists
    if not os.path.exists(meta_clusters_dir):
        print(f"Clusters directory does not exist: {meta_clusters_dir}")
        return

    # Get list of all cluster directories
    cluster_dirs = [d for d in os.listdir(meta_clusters_dir) 
                   if os.path.isdir(os.path.join(meta_clusters_dir, d))]
    print(f"Found {len(cluster_dirs)} clusters to analyze")

    # Initialize analysis tracking variables
    social_engineering_count = 0
    social_engineering_clusters = []
    debug_info = []
    total_images_processed = 0
    total_images_failed = 0

    # Process clusters in parallel (using single worker to avoid overwhelming output)
    print("Analyzing clusters for social engineering indicators...")
    with ThreadPoolExecutor(max_workers=1) as executor:
        # Submit all cluster processing tasks
        futures = {executor.submit(process_cluster, cluster_name, meta_clusters_dir, json_data): cluster_name 
                  for cluster_name in cluster_dirs}

        # Process completed tasks
        for future in as_completed(futures):
            cluster_name = futures[future]
            try:
                result = future.result()
                if result:
                    debug_info.append(result)
                    total_images_processed += result["images_processed"]
                    total_images_failed += result["images_failed"]
                    
                    if result["is_social_engineering"]:
                        social_engineering_count += 1
                        social_engineering_clusters.append(result["cluster"])
                        print(f"SE cluster found: {cluster_name} ({result['unique_domains']} domains)")
                    else:
                        print(f"Normal cluster: {cluster_name} (1 domain)")
                        
            except Exception as e:
                print(f"Error processing cluster {cluster_name}: {e}")

    # Generate summary statistics
    total_clusters = len(debug_info)
    normal_clusters = total_clusters - social_engineering_count
    se_percentage = (social_engineering_count / total_clusters * 100) if total_clusters > 0 else 0

    # Write summary results to count file
    with open(count_file, 'w') as f:
        f.write(f"Social Engineering Cluster Analysis Results\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Total clusters analyzed: {total_clusters}\n")
        f.write(f"Normal clusters (single domain): {normal_clusters}\n")
        f.write(f"Social engineering clusters (multiple domains): {social_engineering_count}\n")
        f.write(f"Social engineering percentage: {se_percentage:.1f}%\n\n")
        f.write(f"Total images processed: {total_images_processed}\n")
        f.write(f"Images with processing errors: {total_images_failed}\n\n")
        f.write("Clusters Identified as Potential Social Engineering:\n")
        f.write("-" * 50 + "\n")
        for cluster in sorted(social_engineering_clusters):
            f.write(f"{cluster}\n")

    # Write detailed debug information
    with open(debug_file, 'w') as f:
        f.write(f"Detailed Social Engineering Cluster Analysis\n")
        f.write(f"{'='*60}\n\n")
        
        for info in sorted(debug_info, key=lambda x: x['cluster']):
            f.write(f"Cluster: {info['cluster']}\n")
            f.write(f"Social Engineering: {'YES' if info['is_social_engineering'] else 'NO'}\n")
            f.write(f"Unique URLs: {info['unique_urls']}\n")
            f.write(f"Unique Domains: {info['unique_domains']}\n")
            f.write(f"Images Processed: {info['images_processed']}\n")
            
            f.write("Domains:\n")
            for domain in sorted(info['domain_list']):
                f.write(f"  - {domain}\n")
                
            f.write("URLs:\n")
            for url in sorted(info['url_list']):
                f.write(f"  - {url}\n")
            f.write("\n" + "-" * 40 + "\n\n")

    # Write CSV file for clusters with multiple domains (potential SE)
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header row
        writer.writerow(['clusters', 'is_se', 'domain_list', 'unique_domains', 'unique_urls', 'images_processed'])
        
        # Write data for clusters with multiple domains
        for info in debug_info:
            if len(info['domain_list']) > 1:
                writer.writerow([
                    info['cluster'],
                    None,  # Placeholder for manual review
                    "; ".join(sorted(info['domain_list'])),
                    info['unique_domains'],
                    info['unique_urls'],
                    info['images_processed']
                ])

    # Print summary to console
    print(f"\nSocial Engineering Analysis Summary for {src}:")
    print(f"  Total clusters: {total_clusters}")
    print(f"  SE clusters: {social_engineering_count}")
    print(f"  SE percentage: {se_percentage:.1f}%")
    print(f"  Results written to:")
    print(f"    - {count_file}")
    print(f"    - {debug_file}")
    print(f"    - {csv_file}")

if __name__ == "__main__":
    print("Starting Social Engineering cluster identification...")
    
    # Process all crawler directories specified in configuration
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"\n{'='*50}")
        print(f"Processing crawler directory: {sd}")
        print(f"{'='*50}")
        identify_social_engineering_clusters(sd)
    
    print(f"\n{'='*50}")
    print("Social Engineering identification complete for all directories!")
    print("Review the generated CSV files to validate automated detections.")
    print(f"{'='*50}")

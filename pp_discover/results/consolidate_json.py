"""
JSON Metadata Consolidation Module

This module consolidates JSON metadata files from distributed crawler log directories
into centralized mapping files. The crawler generates JSON logs containing metadata
about each screenshot (URL, timestamp, interaction details, etc.), and this module
combines all that information into a single accessible format.

Key Features:
- Traverses nested log directory structures to find JSON metadata files
- Consolidates metadata from multiple crawling sessions into single mapping files
- Creates screenshot-name-to-metadata mappings for easy lookup
- Handles JSON parsing errors gracefully
- Prepares metadata for subsequent analysis and processing steps

The consolidated JSON serves as a lookup table that maps screenshot filenames
to their associated metadata, including:
- Original URL that was crawled
- Timestamp of when the screenshot was taken
- User interaction details (clicks, form fills, etc.)
- Browser session information

Directory Structure Expected:
logs/
├── domain1/
│   ├── session1/
│   │   └── JSON_log/
│   │       ├── metadata1.json
│   │       └── metadata2.json
│   └── session2/
│       └── JSON_log/
│           └── metadata3.json
└── domain2/
    └── session1/
        └── JSON_log/
            └── metadata4.json

Output: Single map.json file containing all metadata indexed by screenshot filename.
"""

import os
import json
import yaml

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def consolidate_json_logs(source_dir):
    """
    Consolidate all JSON metadata logs from a crawler's directory structure into a single mapping file.
    
    This function traverses the nested directory structure created by the web crawler
    and combines all JSON metadata files into a single consolidated mapping file.
    The resulting file maps screenshot filenames to their complete metadata records.
    
    Args:
        source_dir (str): Name of the source crawler directory (e.g., 'pp_crawler', 'pp_crawler_baseline')
    """
    # Set up destination paths
    dest_dir = os.path.join(config['cons_json']['dest_base_dir'], source_dir)
    dest_file = os.path.join(dest_dir, 'map.json')
    os.makedirs(dest_dir, exist_ok=True)
    
    print(f"Consolidating JSON logs for: {source_dir}")
    print(f"Output file: {dest_file}")

    # Initialize data structures for consolidation
    consolidated_data = []  # List to collect all JSON records
    consolidated_dict = {}  # Dictionary for final screenshot-name-to-metadata mapping

    # Locate the logs directory for this crawler
    logs_dir = os.path.join(config['general']['log_base_dir'], source_dir, 'logs')
    if not os.path.isdir(logs_dir):
        print(f"No logs directory found in {source_dir}")
        return

    print(f"Scanning logs directory: {logs_dir}")
    
    # Traverse the nested directory structure
    domains_processed = 0
    json_files_processed = 0
    
    # Level 1: Iterate through domain directories
    for sub_dir1 in os.listdir(logs_dir):
        sub_dir1_path = os.path.join(logs_dir, sub_dir1)
        if not os.path.isdir(sub_dir1_path):
            continue

        # Level 2: Iterate through session directories within each domain
        for sub_dir2 in os.listdir(sub_dir1_path):
            sub_dir2_path = os.path.join(sub_dir1_path, sub_dir2)
            if not os.path.isdir(sub_dir2_path):
                continue

            # Level 3: Look for JSON_log directory
            json_log_dir = os.path.join(sub_dir2_path, 'JSON_log')
            if os.path.isdir(json_log_dir):
                # Process all JSON files in this directory
                for json_file in os.listdir(json_log_dir):
                    json_file_path = os.path.join(json_log_dir, json_file)
                    
                    # Only process actual JSON files
                    if os.path.isfile(json_file_path) and json_file.endswith('.json'):
                        try:
                            # Load and parse JSON data
                            with open(json_file_path, 'r') as f:
                                data = json.load(f)
                                
                                # Handle both single objects and arrays
                                if isinstance(data, list):
                                    consolidated_data.extend(data)
                                else:
                                    consolidated_data.append(data)
                                
                                json_files_processed += 1
                                print(f"Processed: {json_file_path} ({len(data) if isinstance(data, list) else 1} records)")
                                
                        except json.JSONDecodeError as e:
                            print(f"JSON parsing error in {json_file_path}: {e}")
                        except Exception as e:
                            print(f"Error processing {json_file_path}: {e}")
        
        domains_processed += 1

    print(f"Processed {json_files_processed} JSON files across {domains_processed} domains")
    print(f"Total records collected: {len(consolidated_data)}")

    # Create screenshot-name-to-metadata mapping
    print("Creating screenshot-name-to-metadata mapping...")
    mapping_errors = 0
    
    for item in consolidated_data:
        try:
            # Extract screenshot filename from the full path
            screenshot_name = item['screenshot_name'].split('/')[-1]
            consolidated_dict[screenshot_name] = item
        except KeyError:
            print(f"Missing 'screenshot_name' field in record: {item}")
            mapping_errors += 1
        except Exception as e:
            print(f"Error creating mapping for record: {e}")
            mapping_errors += 1

    if mapping_errors > 0:
        print(f"Warning: {mapping_errors} records could not be mapped due to missing or invalid screenshot_name fields")

    # Write the consolidated mapping to file
    try:
        with open(dest_file, 'w') as f:
            json.dump(consolidated_dict, f, indent=4)
        
        print(f"Successfully saved consolidated JSON mapping to: {dest_file}")
        print(f"Final mapping contains {len(consolidated_dict)} screenshot-to-metadata entries")
        
    except Exception as e:
        print(f"Error saving consolidated JSON file: {e}")

if __name__ == "__main__":
    print("Starting JSON metadata consolidation process...")
    
    # Process all crawler directories specified in configuration
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"\n{'='*50}")
        print(f"Processing crawler directory: {sd}")
        print(f"{'='*50}")
        consolidate_json_logs(sd)
    
    print(f"\n{'='*50}")
    print("JSON consolidation complete for all directories!")
    print(f"{'='*50}")

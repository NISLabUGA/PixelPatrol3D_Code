"""
User Interaction Click Counter Module

This module analyzes crawler log files to count user interactions, specifically
tracking the number of elements that were clicked during the crawling process.
This information is valuable for understanding the level of interaction achieved
during automated browsing sessions and for evaluating crawler effectiveness.

Key Features:
- Scans element coordinate log files for click interactions
- Counts "chosen_element" entries which represent successful element selections
- Provides per-file and total click statistics
- Generates summary reports for analysis
- Helps evaluate crawler interaction success rates

The click counting is important for:
- Measuring crawler engagement with web pages
- Identifying pages with high/low interaction rates
- Evaluating the effectiveness of element selection algorithms
- Understanding user behavior simulation quality

Directory Structure Expected:
logs/
├── domain1/
│   ├── session1/
│   │   └── element_coor/
│   │       ├── interaction1.log
│   │       └── interaction2.log
│   └── session2/
│       └── element_coor/
│           └── interaction3.log
└── domain2/
    └── session1/
        └── element_coor/
            └── interaction4.log

Output: tot_num_clicks.txt file containing click statistics per log file and total counts.
"""

import os
import yaml

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def count_chosen_elements(src):
    """
    Count user interaction clicks from crawler log files.
    
    This function traverses the crawler's log directory structure and analyzes
    element coordinate log files to count successful element interactions.
    Each "chosen_element:" line represents a successful click or interaction
    with a web page element.
    
    Args:
        src (str): Name of the source crawler directory (e.g., 'pp_crawler', 'pp_crawler_baseline')
    """
    # Set up output paths
    output_dir = os.path.join(config['count_clicks']['dest_base_dir'], src)
    output_file = os.path.join(output_dir, 'tot_num_clicks.txt')
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Counting clicks for crawler: {src}")
    print(f"Output file: {output_file}")

    # Initialize counters
    total_chosen_element_count = 0
    files_processed = 0
    domains_processed = 0

    # Open output file for writing results
    with open(output_file, 'w') as output:
        # Write header information
        output.write(f"Click Count Analysis for: {src}\n")
        output.write(f"{'='*50}\n\n")

        # Locate the logs directory for this crawler
        logs_dir = os.path.join(config['general']['log_base_dir'], src, 'logs')
        if not os.path.isdir(logs_dir):
            print(f"No logs directory found in {src}")
            output.write(f"ERROR: No logs directory found in {src}\n")
            return

        print(f"Scanning logs directory: {logs_dir}")

        # Traverse the nested directory structure
        # Level 1: Iterate through domain directories
        for sub_dir1 in os.listdir(logs_dir):
            sub_dir1_path = os.path.join(logs_dir, sub_dir1)
            if not os.path.isdir(sub_dir1_path):
                continue

            domain_clicks = 0
            domain_files = 0

            # Level 2: Iterate through session directories within each domain
            for sub_dir2 in os.listdir(sub_dir1_path):
                sub_dir2_path = os.path.join(sub_dir1_path, sub_dir2)
                if not os.path.isdir(sub_dir2_path):
                    continue

                # Level 3: Look for element_coor directory containing interaction logs
                element_coor_dir = os.path.join(sub_dir2_path, 'element_coor')
                if os.path.isdir(element_coor_dir):
                    # Process all log files in this directory
                    for log_file in os.listdir(element_coor_dir):
                        log_file_path = os.path.join(element_coor_dir, log_file)
                        
                        # Only process actual log files
                        if os.path.isfile(log_file_path) and log_file.endswith('.log'):
                            # Count "chosen_element:" lines in this file
                            chosen_element_count = 0
                            
                            try:
                                with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    for line_num, line in enumerate(f, 1):
                                        if line.strip().startswith("chosen_element:"):
                                            chosen_element_count += 1
                                
                                # Record results for this file
                                relative_path = os.path.relpath(log_file_path, logs_dir)
                                output.write(f"{relative_path}: {chosen_element_count} clicks\n")
                                
                                # Update counters
                                total_chosen_element_count += chosen_element_count
                                domain_clicks += chosen_element_count
                                domain_files += 1
                                files_processed += 1
                                
                                print(f"Processed {log_file}: {chosen_element_count} clicks")
                                
                            except Exception as e:
                                print(f"Error processing {log_file_path}: {e}")
                                output.write(f"ERROR processing {relative_path}: {e}\n")

            # Write domain summary if any files were processed
            if domain_files > 0:
                output.write(f"\nDomain {sub_dir1} summary: {domain_clicks} clicks across {domain_files} files\n")
                output.write("-" * 40 + "\n")
            
            domains_processed += 1

        # Write final summary statistics
        output.write(f"\n{'='*50}\n")
        output.write(f"FINAL SUMMARY\n")
        output.write(f"{'='*50}\n")
        output.write(f"Total domains processed: {domains_processed}\n")
        output.write(f"Total log files processed: {files_processed}\n")
        output.write(f"Total clicks across all files: {total_chosen_element_count}\n")
        
        if files_processed > 0:
            avg_clicks_per_file = total_chosen_element_count / files_processed
            output.write(f"Average clicks per file: {avg_clicks_per_file:.2f}\n")

    # Print summary to console
    print(f"Click counting complete for {src}")
    print(f"Total files processed: {files_processed}")
    print(f"Total clicks found: {total_chosen_element_count}")
    if files_processed > 0:
        print(f"Average clicks per file: {total_chosen_element_count / files_processed:.2f}")

if __name__ == "__main__":
    print("Starting click counting analysis...")
    
    # Process all crawler directories specified in configuration
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        print(f"\n{'='*50}")
        print(f"Processing crawler directory: {sd}")
        print(f"{'='*50}")
        count_chosen_elements(sd)
    
    print(f"\n{'='*50}")
    print("Click counting analysis complete for all directories!")
    print(f"{'='*50}")

"""
Complete Results Processing Pipeline

This is the main orchestration script that runs the entire results processing pipeline
for the PixelPatrol3D BMA detection system. It executes all processing steps in
the correct order to transform raw crawler data into analyzed results ready for
machine learning model training and evaluation.

Processing Pipeline Overview:
1. consolidate_images() - Gather all screenshots from nested log directories
2. consolidate_json_logs() - Combine all metadata JSON files into mapping files
3. deduplicate_images() - Remove duplicate images based on MD5 hash and URL
4. update_metadata() - Calculate perceptual hashes for similarity analysis
5. cluster_images() - Group visually similar images using DBSCAN clustering
6. identify_social_engineering_clusters() - Analyze clusters for BMA indicators
7. count_chosen_elements() - Count user interactions for engagement analysis
8. clean() - Archive results and prepare for next processing run

The pipeline processes data from multiple crawler types (baseline and enhanced)
and produces organized datasets suitable for:
- Machine learning model training
- BMA detection algorithm evaluation
- Manual review and validation
- Statistical analysis of crawling effectiveness

Key Features:
- Fully automated processing pipeline
- Handles multiple crawler data sources
- Preserves data integrity through each step
- Generates comprehensive analysis results
- Provides clean separation between processing runs

Usage:
    python run_all.py

Prerequisites:
- Raw crawler data must be available in the configured log directories
- All required Python dependencies must be installed
- Sufficient disk space for intermediate and final results
- Environment variables must be properly configured (PP_RESULTS_WD)
"""

import os
import yaml
import time
from datetime import datetime

# Import all processing modules
from consolidate_imgs import consolidate_images
from consolidate_json import consolidate_json_logs
from dedup_imgs import deduplicate_images
from calc_phashes import update_metadata
from cluster_phash_hm import cluster_images
from tally_se import identify_social_engineering_clusters
from gather_mc_oi import process_directories
from count_clicks import count_chosen_elements
from clean import clean

# Load configuration from YAML file with environment variable expansion
with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

def print_pipeline_header():
    """Print a formatted header for the processing pipeline."""
    print("=" * 80)
    print("PIXELPATROL3D RESULTS PROCESSING PIPELINE")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Processing directories: {config['general']['crawler_dir_names']}")
    print(f"Working directory: {config['general']['working_dir']}")
    print(f"Max workers: {config['general']['max_workers']}")
    print("=" * 80)

def print_step_header(step_num, step_name, description):
    """Print a formatted header for each processing step."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {step_name}")
    print(f"{'='*60}")
    print(f"Description: {description}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)

def print_pipeline_summary(start_time, end_time):
    """Print a summary of the entire pipeline execution."""
    duration = end_time - start_time
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Start time: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    print(f"Directories processed: {len(config['general']['crawler_dir_names'])}")
    print("=" * 80)
    print("Pipeline completed successfully!")
    print("Results are ready for analysis.")
    print("=" * 80)

if __name__ == "__main__":
    # Record pipeline start time
    pipeline_start_time = time.time()
    
    # Print pipeline header
    print_pipeline_header()
    
    try:
        # Get list of crawler directories to process
        source_dir_list = config['general']['crawler_dir_names']
        
        # Process each crawler directory through the complete pipeline
        for sd in source_dir_list:
            print(f"\n{'#'*80}")
            print(f"PROCESSING CRAWLER DIRECTORY: {sd}")
            print(f"{'#'*80}")
            
            # Step 1: Consolidate Images
            print_step_header(1, "IMAGE CONSOLIDATION", 
                            "Gathering screenshots from nested log directories")
            consolidate_images(sd)
            
            # Step 2: Consolidate JSON Metadata
            print_step_header(2, "JSON CONSOLIDATION", 
                            "Combining metadata files into unified mappings")
            consolidate_json_logs(sd)
            
            # Step 3: Deduplicate Images
            print_step_header(3, "IMAGE DEDUPLICATION", 
                            "Removing duplicate images based on MD5 hash and URL")
            deduplicate_images(sd)
            
            # Step 4: Calculate Perceptual Hashes
            print_step_header(4, "PERCEPTUAL HASH CALCULATION", 
                            "Computing perceptual hashes for similarity analysis")
            update_metadata(sd)
            
            # Step 5: Cluster Images
            print_step_header(5, "IMAGE CLUSTERING", 
                            "Grouping visually similar images using DBSCAN")
            cluster_images(sd)
            
            # Step 6: Identify Social Engineering Clusters
            print_step_header(6, "SOCIAL ENGINEERING ANALYSIS", 
                            "Analyzing clusters for BMA indicators")
            identify_social_engineering_clusters(sd)
            
            # Step 7: Count User Interactions
            print_step_header(7, "INTERACTION ANALYSIS", 
                            "Counting user interactions for engagement metrics")
            count_chosen_elements(sd)
            
            print(f"\nCompleted processing for crawler directory: {sd}")
        
        # Step 8: Gather Meta-Clusters of Interest (runs after all directories)
        print_step_header(8, "META-CLUSTER GATHERING", 
                        "Collecting clusters of interest for manual review")
        for sd in source_dir_list:
            process_directories(sd)
        
        # Step 9: Clean and Archive Results
        print_step_header(9, "CLEANUP AND ARCHIVAL", 
                        "Archiving results and preparing for next run")
        clean()
        
        # Record pipeline end time and print summary
        pipeline_end_time = time.time()
        print_pipeline_summary(pipeline_start_time, pipeline_end_time)
        
    except KeyboardInterrupt:
        print("\n" + "!" * 80)
        print("PIPELINE INTERRUPTED BY USER")
        print("!" * 80)
        print("Processing was stopped before completion.")
        print("Partial results may be available in the working directory.")
        
    except Exception as e:
        print("\n" + "!" * 80)
        print("PIPELINE ERROR")
        print("!" * 80)
        print(f"An error occurred during pipeline execution: {e}")
        print("Check the error details above and ensure all prerequisites are met.")
        print("!" * 80)
        raise

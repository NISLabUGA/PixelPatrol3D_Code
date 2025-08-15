# PixelPatrol3D Results Processing Pipeline

This directory contains the complete results processing pipeline for the PixelPatrol3D BMA detection system. The pipeline transforms raw crawler data into analyzed datasets suitable for machine learning model training and behavior manipulation attack research.

## Overview

The PixelPatrol3D system uses automated web crawlers to collect screenshots and metadata from websites. This results processing pipeline consolidates, deduplicates, analyzes, and clusters the collected data to identify potential BMAs (Behavior Manipulation Attacks) and social engineering patterns.

## Pipeline Architecture

The processing pipeline consists of 9 sequential steps that transform raw crawler logs into structured analysis results:

```
Raw Crawler Data → Consolidated Data → Deduplicated Data → Clustered Data → Analysis Results
```

### Processing Flow

1. **Image Consolidation** - Gather screenshots from nested log directories
2. **JSON Consolidation** - Combine metadata files into unified mappings
3. **Image Deduplication** - Remove duplicates based on MD5 hash and URL
4. **Perceptual Hash Calculation** - Compute similarity hashes for clustering
5. **Image Clustering** - Group visually similar images using DBSCAN
6. **Social Engineering Analysis** - Identify potential BMA clusters
7. **Interaction Analysis** - Count user interactions for engagement metrics
8. **Meta-Cluster Gathering** - Collect clusters of interest for review
9. **Cleanup and Archival** - Archive results and prepare for next run

## Files and Modules

### Core Processing Modules

| File                  | Purpose                                         | Input               | Output              |
| --------------------- | ----------------------------------------------- | ------------------- | ------------------- |
| `consolidate_imgs.py` | Consolidate screenshots from nested directories | Crawler logs        | Consolidated images |
| `consolidate_json.py` | Combine JSON metadata into mapping files        | JSON logs           | Unified metadata    |
| `dedup_imgs.py`       | Remove duplicate images                         | Consolidated images | Unique images       |
| `calc_phashes.py`     | Calculate perceptual hashes                     | Unique images       | Hash metadata       |
| `cluster_phash_hm.py` | Cluster images by visual similarity             | Hashed images       | Image clusters      |
| `tally_se.py`         | Identify social engineering patterns            | Clusters + metadata | SE analysis         |
| `count_clicks.py`     | Analyze user interaction statistics             | Crawler logs        | Click statistics    |
| `gather_mc_oi.py`     | Collect clusters of interest                    | SE analysis         | Curated clusters    |
| `clean.py`            | Archive results and cleanup                     | All results         | Archived data       |

### Orchestration and Configuration

| File          | Purpose                  | Description                             |
| ------------- | ------------------------ | --------------------------------------- |
| `run_all.py`  | **Main pipeline script** | Executes complete processing pipeline   |
| `config.yaml` | Configuration file       | Defines paths, parameters, and settings |

## Quick Start

### Prerequisites

1. **Environment Setup**

   The pipeline requires the `PP_RESULTS_WD` environment variable to be set for flexible deployment across different systems. This variable defines the base working directory for all processing results.

   ```bash
   # Base working directory for all processing results
   # Uses environment variable PP_RESULTS_WD for flexibility
   # Recommended to set:
   export PP_RESULTS_WD="./wd"
   # in .bashrc or similar for persistence across sessions
   ```

   **Important**: Add this export command to your shell configuration file (`.bashrc`, `.zshrc`, or similar) to ensure the variable persists across terminal sessions.

2. **Python Dependencies**

   ```bash
   pip install pillow imagehash scikit-learn pandas tqdm pyyaml numpy
   ```

3. **Raw Data**
   - Crawler logs must be available in the configured directories
   - Expected structure: `../pp_crawler/logs/` and `../pp_crawler_baseline/logs/`

### Running the Pipeline

**Complete Pipeline (Recommended)**

```bash
python run_all.py
```

**Individual Steps (for debugging)**

```bash
python consolidate_imgs.py
python consolidate_json.py
python dedup_imgs.py
python calc_phashes.py
python cluster_phash_hm.py
python tally_se.py
python count_clicks.py
python gather_mc_oi.py
python clean.py
```

## Configuration

The pipeline is configured through `config.yaml`. Key settings include:

### Directory Configuration

```yaml
general:
  working_dir: ${PP_RESULTS_WD} # Base working directory
  crawler_dir_names: ["pp_crawler_baseline", "pp_crawler"] # Crawler types
  max_workers: 44 # Parallel processing threads
```

### Processing Parameters

```yaml
calc_phash:
  hash_size: 128 # Perceptual hash precision

clustering:
  dist_thold: 77.5 # Clustering distance threshold
  min_samples: 2 # Minimum cluster size
```

## Output Structure

The pipeline creates the following directory structure:

```
${PP_RESULTS_WD}/
├── cons_raw_img/           # Consolidated screenshots
│   ├── pp_crawler/
│   └── pp_crawler_baseline/
├── cons_raw_json/          # Consolidated metadata
│   ├── pp_crawler/
│   │   └── map.json
│   └── pp_crawler_baseline/
│       └── map.json
├── cons_dedup/             # Deduplicated images
├── meta_clusters/          # Image clusters
│   ├── pp_crawler/
│   │   ├── cluster_0/
│   │   ├── cluster_1/
│   │   └── cluster_-1/     # Noise/outliers
│   └── pp_crawler_baseline/
├── final/                  # Analysis results
│   ├── pp_crawler/
│   │   ├── count.txt       # SE cluster summary
│   │   ├── debug.txt       # Detailed analysis
│   │   ├── check.csv       # SE clusters for review
│   │   ├── tot_num_clicks.txt  # Interaction stats
│   │   └── mc_oi/          # Clusters of interest
│   └── pp_crawler_baseline/
└── runs/                   # Archived results
    ├── r1/                 # First run archive
    ├── r2/                 # Second run archive
    └── ...
```

## Key Analysis Results

### Social Engineering Detection

- **count.txt**: Summary statistics of potential BMA clusters
- **debug.txt**: Detailed analysis with URLs and domains for each cluster
- **check.csv**: Structured data for clusters flagged for manual review

### Interaction Analysis

- **tot_num_clicks.txt**: User interaction statistics and engagement metrics

### Visual Similarity Clusters

- **meta_clusters/**: Directories containing visually similar images
- **mc_oi/**: Curated clusters of interest for detailed investigation

## Algorithm Details

### Perceptual Hashing

- Uses 128-bit perceptual hashes for visual similarity detection
- Robust to minor image modifications (compression, resizing)
- Enables efficient similarity comparisons

### DBSCAN Clustering

- Density-based clustering algorithm
- Automatically determines number of clusters
- Handles noise and outliers effectively
- Distance threshold: 77.5 (optimized for 128-bit hashes)

### Social Engineering Detection

- Analyzes domain diversity within visual clusters
- Clusters with multiple domains flagged as potential BMAs
- Based on assumption that BMA sites mimic legitimate visual elements

## Performance Considerations

### Parallel Processing

- Configurable worker threads (default: 44)
- Optimized for multi-core systems
- Memory-efficient chunk processing

### Storage Requirements

- Raw images: ~10-100GB depending on crawl size
- Processed results: ~20-50% of raw data size
- Temporary files cleaned automatically

### Processing Time

- Complete pipeline: 2-8 hours (depending on dataset size)
- Individual steps: 10 minutes - 2 hours each
- Clustering is typically the most time-intensive step

## Troubleshooting

### Common Issues

1. **Environment Variable Not Set**

   ```
   Error: PP_RESULTS_WD environment variable not defined
   Solution: export PP_RESULTS_WD="/your/path"
   ```

2. **Insufficient Disk Space**

   ```
   Error: No space left on device
   Solution: Ensure 2-3x raw data size available
   ```

3. **Memory Issues**

   ```
   Error: Out of memory during clustering
   Solution: Reduce max_workers in config.yaml
   ```

4. **Missing Dependencies**
   ```
   Error: ModuleNotFoundError
   Solution: pip install -r requirements.txt
   ```

### Debug Mode

Run individual modules with verbose output:

```bash
python -u consolidate_imgs.py 2>&1 | tee consolidate.log
```

## Research Applications

### Machine Learning

- Clustered images provide training data for BMA detection models
- Perceptual hashes enable efficient similarity-based features
- Social engineering labels support supervised learning

### Security Analysis

- Identify BMA campaigns using similar visual elements
- Analyze the prevalence of visual mimicry in attacks
- Study user interaction patterns on suspicious sites

### Dataset Creation

- Generate labeled datasets for computer vision research
- Create benchmarks for BMA detection algorithms
- Support reproducible security research

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@article{pixelpatrol3d2024,
  title={PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks},
  author={[Authors]},
  journal={[Journal]},
  year={2024}
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request with detailed description

## Support

For questions, issues, or contributions:

- Open an issue on GitHub
- Contact the research team
- Check the documentation wiki

---

**Note**: This pipeline is designed for research purposes. Ensure compliance with ethical guidelines and legal requirements when crawling websites and analyzing data.

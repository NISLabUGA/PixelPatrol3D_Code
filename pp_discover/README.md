# PP_Discover: Large-Scale Web Crawling Discovery System

The **PP_Discover** module is the data collection component of the PixelPatrol3D project, designed for large-scale automated web crawling to discover and capture behavior manipulation attacks (BMAs) and social engineering patterns across the web.

## 🎯 Overview

PP_Discover orchestrates distributed web crawling operations using Docker containers to capture screenshots, HTML content, and interaction data from websites. The system is designed to scale horizontally and process thousands of URLs across multiple browser configurations simultaneously.

## 🏗️ Architecture

```
PP_Discover Pipeline
├── Configuration (config.yaml)
├── URL Management (CSV lists)
├── Docker Orchestration (run_*.py)
├── Crawler Execution (pp_crawler/)
└── Results Processing (results/)
```

### Key Components

1. **Orchestration Layer**: Python scripts that manage Docker containers and crawling operations
2. **Crawler Engine**: Node.js/Puppeteer-based crawler for screenshot and data capture
3. **Results Pipeline**: Post-processing system for data analysis and clustering
4. **Configuration Management**: YAML-based configuration for scalable operations

## 📁 Directory Structure

```
pp_discover/
├── README.md                    # This documentation
├── config.yaml                  # Main configuration file
├── test_url_crawl_list.csv     # Sample URL list for testing
├── clean_all.py                # Cleanup script for all directories
├── crawl_url.py                # Single URL crawling utility
├── run_single.py               # Single-instance crawler manager
├── run_op_at_scale.py          # Main orchestration script
├── pp_crawler/                 # Node.js crawler implementation
│   ├── capture_screenshots.js  # Core crawling logic
│   ├── config.js               # Browser and user agent configs
│   ├── utils.js                # Helper functions
│   ├── clean.js                # Crawler cleanup utilities
│   ├── package.json            # Node.js dependencies
│   ├── tranco.csv              # Top 1M websites dataset
│   └── README.md               # Crawler-specific documentation
└── results/                    # Results processing pipeline
    ├── run_all.py              # Complete processing pipeline
    ├── config.yaml             # Processing configuration
    ├── consolidate_imgs.py     # Image consolidation
    ├── consolidate_json.py     # Metadata consolidation
    ├── dedup_imgs.py           # Image deduplication
    ├── calc_phashes.py         # Perceptual hash calculation
    ├── cluster_phash_hm.py     # Visual similarity clustering
    ├── tally_se.py             # Social engineering analysis
    ├── count_clicks.py         # Interaction statistics
    ├── gather_mc_oi.py         # Cluster curation
    ├── clean.py                # Results cleanup
    └── README.md               # Processing pipeline docs
```

## 🚀 Quick Start

### Prerequisites

1. **System Requirements**

   ```bash
   # Docker and Docker Compose
   docker --version
   docker-compose --version

   # Node.js (v20.18.3 or later)
   node --version
   npm --version

   # Python 3.8+
   python3 --version
   ```

2. **Environment Setup**

   ```bash
   # Install Python dependencies
   # Use the pp3d_env created earlier with
   source pp3d_env/bin/activate # on Windows with pp3d_env\Scripts\activate.

   # Set up crawler dependencies
   cd pp_crawler
   npm install
   cd ..

   # Create Docker network
   docker network create pp_nw

   # Pull the crawler container
   docker pull sking115422/pp_crawler_single_cont:v1
   ```

### Basic Usage

#### 1. Test Single URL Crawling

```bash
# Test the crawler with a single URL
cd pp_crawler
node capture_screenshots.js "https://example.com" 123 30 chrome_win SE
cd ..
```

#### 2. Configure Crawling Parameters

Edit `config.yaml` to customize your crawling operation:

```yaml
# Main crawler config
timeout: 300 # Timeout per URL (seconds)
crawl_type: SE # Crawling type (SE = Screenshot Extraction)
url_list_csv_path: ./test_url_crawl_list.csv # Path to URL list
url_crawl_max_num: all # Number of URLs to crawl
max_containers: 10 # Concurrent Docker containers
base_port: 59000 # Starting port for containers
user_agent_list: # Browser configurations
  - chrome_linux
  - chrome_mac
  - chrome_win
  - firefox_win
  - safari_mac
```

#### 3. Run Large-Scale Crawling

```bash
# Execute the complete crawling pipeline
python run_op_at_scale.py
```

## ⚙️ Configuration Options

### Core Settings

| Parameter           | Description                             | Default | Options            |
| ------------------- | --------------------------------------- | ------- | ------------------ |
| `timeout`           | Maximum crawling time per URL (seconds) | `300`   | Any integer        |
| `crawl_type`        | Type of crawling operation              | `SE`    | `SE`, `benign`     |
| `url_crawl_max_num` | URLs to process from list               | `all`   | `all` or integer   |
| `max_containers`    | Concurrent Docker containers            | `10`    | 1-50 recommended   |
| `base_port`         | Starting port for containers            | `59000` | Any available port |
| `auto_clean`        | Auto-cleanup containers                 | `false` | `true`/`false`     |

### Supported User Agents

Some of the browser configurations are shown below:

**Desktop Browsers:**

- `chrome_linux` - Chrome on Linux
- `chrome_mac` - Chrome on macOS
- `chrome_win` - Chrome on Windows
- `edge_win` - Microsoft Edge on Windows
- `firefox_win` - Firefox on Windows
- `safari_mac` - Safari on macOS

**Mobile Devices:**

- `chrome_android_phone` - Chrome on Android Phone
- `safari_iphone` - Safari on iPhone

**Tablets:**

- `safari_ipad` - Safari on iPad
- `chrome_android_tab` - Chrome on Android Tablet

### URL List Format

Create a CSV file with URLs to crawl:

```csv
url
https://example.com
https://test-site.com
https://another-domain.org
```

## 🐳 Docker Integration

### Container Management

The system uses Docker containers for isolated crawling:

```bash
# Container runs with:
docker run --rm -d \
    -v $(pwd):/mnt/pp_pkg \
    -p {port}:5901 \
    --network pp_nw \
    sking115422/pp_crawler_single_cont:v1 \
    {crawler} {url} {user_agent} {identifier}
```

### Network Configuration

```bash
# Create the required Docker network
docker network create pp_nw

# List active containers
docker ps

# Monitor container logs
docker logs {container_id}
```

## 📊 Output and Results

### Raw Data Structure

Crawling generates organized output:

```
pp_crawler/logs/
├── {browser_device}/
│   ├── {timestamp}_V{version}_siteID:{site_hash}/
│   │   ├── chrome_logs/
│   │   ├── downloads/
│   │   ├── element_coor/
│   │   ├── html_logs/
│   │   ├── JSON_log/
│   │   ├── logs/
│   │   ├── net_log/
│   │   ├── req_res_pairs/
│   │   ├── screenshots/
│   │   └── visitedURLs_{timestamp}_{site_hash}.json
│   ├── {timestamp}_V{version}_siteID:{site_hash}/
│   └── ...
├── {browser_device}/
│   └── ...
└── ...

```

### File Naming Convention

Screenshots and HTML files follow this pattern:

```
{timestamp}_{url_hash}_{location}_{width}x{height}.{ext}
```

Where:

- **timestamp**: UNIX timestamp in milliseconds
- **url_hash**: MD5 hash of the URL
- **location**: Page interaction state (`FIRST`, `land0`, `new1`, etc.)
- **dimensions**: Screenshot resolution
- **ext**: File extension (`png` or `html`)

### Results Processing

After crawling, process results using the pipeline:

```bash
cd results
export PP_RESULTS_WD="/path/to/results/directory"
python run_all.py
```

This generates:

- **Consolidated Images**: All screenshots in organized directories
- **Deduplicated Data**: Unique images with duplicates removed
- **Visual Clusters**: Groups of visually similar images
- **BMA Analysis**: Potential behavior manipulation attack identification
- **Interaction Statistics**: User engagement and click metrics

## 🔧 Advanced Usage

### Performance Tuning

#### Container Scaling

```yaml
# config.yaml
max_containers: 20 # Increase for more parallelism
base_port: 50000 # Ensure port range availability
timeout: 600 # Increase for complex sites
```

#### Resource Management

```bash
# Monitor system resources
docker stats
htop

# Clean up containers
python clean_all.py
```

### Debugging and Monitoring

#### Progress Tracking

```bash
# Monitor crawling progress
tail -f progress_log.csv

# Check container status
docker ps -a
```

## 🛠️ Development

### Adding New User Agents

1. Edit `pp_crawler/config.js`:

```javascript
const userAgents = {
  custom_browser: {
    userAgent: "Custom Browser String",
    viewport: { width: 1920, height: 1080 },
  },
};
```

2. Update `config.yaml`:

```yaml
user_agent_list:
  - custom_browser
```

### Extending Crawling Logic

Modify `pp_crawler/capture_screenshots.js` to add:

- Custom interaction patterns
- Additional data extraction
- New screenshot triggers
- Enhanced error handling

### Custom Results Processing

Create new processing modules in `results/`:

```python
# custom_analysis.py
def analyze_custom_patterns(image_dir, metadata):
    # Your custom analysis logic
    pass
```

## 📈 Performance Metrics

### Typical Performance

- **Throughput**: 100-200 URLs per hour (depending on complexity)
- **Container Efficiency**: 10-20 concurrent containers optimal
- **Storage**: ~10-50MB per URL (screenshots + HTML)
- **Memory**: ~2-4GB per container

### Optimization Tips

1. **Adjust timeout** based on target site complexity
2. **Scale containers** based on available CPU/memory
3. **Use SSD or NVMe storage** for better I/O performance
4. **Monitor network bandwidth** for large-scale operations

## 🚨 Important Considerations

### Legal and Ethical

- **Respect robots.txt** and website terms of service
- **Implement rate limiting** to avoid overwhelming servers
- **Consider privacy implications** of data collection
- **Ensure compliance** with applicable laws and regulations

### Technical Limitations

- **JavaScript-heavy sites** may require longer timeouts
- **Anti-bot measures** may block automated access
- **Resource constraints** limit concurrent operations
- **Network stability** affects crawling reliability

### Security Notes

- Crawler runs with **reduced browser security** for research purposes
- **Isolate crawling environment** from production systems
- **Regularly update** Docker images and dependencies
- **Monitor for malicious content** in crawled data

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Test changes with small URL lists
4. Update documentation
5. Submit pull request

## 📞 Support

### Troubleshooting

Common issues and solutions:

1. **Docker network errors**: Recreate `pp_nw` network
2. **Port conflicts**: Adjust `base_port` in config
3. **Container timeouts**: Increase timeout values
4. **Memory issues**: Reduce `max_containers`

### Getting Help

- Check the [pp_crawler README](pp_crawler/README.md) for crawler-specific issues
- Review [results README](results/README.md) for processing problems
- Open GitHub issues for bugs and feature requests
- Contact the research team for academic collaboration

## 📚 Related Documentation

- [PP_Crawler Documentation](pp_crawler/README.md) - Detailed crawler implementation
- [Results Pipeline Documentation](results/README.md) - Complete processing pipeline
- [PixelPatrol3D Main README](../README.md) - Overall project documentation

---

**PP_Discover** is part of the PixelPatrol3D research project for detecting behavior manipulation attacks on the web. This tool is designed for academic research and security analysis purposes.

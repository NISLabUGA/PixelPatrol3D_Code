# PP_Crawler: Web Crawling Module

This directory contains the web crawling module for the **PixelPatrol3D** project. The crawler is built with Node.js and Puppeteer to capture screenshots and HTML content from websites for behavior manipulation attack detection.

## 📁 Directory Structure

```
pp_crawler/
├── README.md                    # This file
├── package.json                 # Node.js dependencies and scripts
├── package-lock.json           # Locked dependency versions
├── capture_screenshots.js      # Main crawler script
├── utils.js                    # Helper functions and utilities
├── config.js                   # Configuration and user agents
├── clean.js                    # Cleanup utilities
├── tranco.csv                  # Top 1M websites ranking data
└── tranco_notes.txt            # Notes about Tranco dataset
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install Node.js dependencies
npm install
```

### Basic Usage

```bash
node capture_screenshots.js [URL] [ID] [TIMEOUT] [USER_AGENT] [CRAWLING_MODE]
```

### Example

```bash
node capture_screenshots.js "https://example.com" 1001 30 chrome_win SE
```

## 📋 Parameters

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `URL` | Target website URL to crawl | `"https://example.com"` |
| `ID` | Unique website identifier for logging | `1001` |
| `TIMEOUT` | Maximum crawling time in seconds | `30` |
| `USER_AGENT` | Browser user agent (see options below) | `chrome_win` |

### Optional Parameters

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `CRAWLING_MODE` | Type of crawling to perform | `"SE"` | `"SE"`, `"benign"` |

## 🖥️ Supported User Agents

Choose from the following user agent options (defined in `config.js`):

- `firefox_win` - Firefox on Windows
- `safari_mac` - Safari on macOS
- `edge_win` - Microsoft Edge on Windows
- `chrome_win` - Chrome on Windows
- `chrome_linux` - Chrome on Linux
- `chrome_mac` - Chrome on macOS
- `chrome_android_phone` - Chrome on Android Phone
- `safari_iphone` - Safari on iPhone
- `safari_ipad` - Safari on iPad
- `chrome_android_tab` - Chrome on Android Tablet

## 📸 Output Files

The crawler generates screenshots and HTML files with a specific naming convention:

### File Naming Convention

```
X_Y_Z_WxH.E
```

Where:
- **X**: UNIX timestamp (milliseconds) when screenshot was taken
- **Y**: MD5 hash of the URL (excluding query parameters after "?")
- **Z**: Tab location identifier (see below)
- **W**: Screenshot width in pixels
- **H**: Screenshot height in pixels
- **E**: File extension (`png` for images, `html` for HTML files)

### Tab Location Identifiers (Z)

| Identifier | Description |
|------------|-------------|
| `FIRST` | Initial landing page |
| `land*` | Landing page before click * (0-indexed) |
| `lafter*` | Landing page after click * (HTML changed, URL same) |
| `lsame*` | Landing page after click * (URL changed) |
| `new*` | New tab opened by click * |
| `newBC*` | New tab before click * |
| `newAC*` | New tab after click * |
| `newSAME*` | New tab with URL change after click * |
| `newNEW*` | Second-level new tab opened |
| `newNEXTBC*` | Second-level new tab before click * |
| `newNEXTAC*` | Second-level new tab after click * |
| `newNEXTSAME*` | Second-level new tab with URL change |
| `newNEWNEXT*` | Third-level new tab opened |

### Tab Flow Diagram

```
Landing Page
    ├── Click 1 → New Tab 1
    │   ├── Click A → New Tab 1A
    │   └── Click B → New Tab 1B
    ├── Click 2 → New Tab 2
    └── Click 3 → URL Change (same tab)
```

## ⚙️ Configuration

### Browser Flags

The crawler uses specific Chrome flags for optimal performance and security testing:

#### Performance Flags
- `--hide-scrollbars` - Improves performance
- `--mute-audio` - Reduces resource usage
- `--disable-infobars` - Removes info bars
- `--disable-gpu` - Disables GPU acceleration
- `--shm-size=3gb` - Increases shared memory

#### Security Flags (for SE detection)
- `--disable-web-security` - Reduces security for more examples
- `--allow-running-insecure-content` - Allows insecure content
- `--ignore-certificate-errors` - Ignores SSL errors
- `--disable-popup-blocking` - Allows popups
- `--allow-popups-during-page-unload` - Allows unload popups

#### Logging Flags
- `--dns-log-details` - Logs DNS queries
- `--log-net-log=${netlogfile}` - Saves network logs

#### Container Flags
- `--no-sandbox` - Required for containerized environments
- `--disable-setuid-sandbox` - Reduces sandbox restrictions

### Customizing Configuration

Edit `config.js` to modify:
- User agent strings
- Screen resolutions
- Timeout values
- Output directories
- Browser flags

## 📊 Data Sources

### Tranco Dataset

- **File**: `tranco.csv`
- **Content**: Top 1 million websites with popularity rankings
- **Update Frequency**: Daily
- **Usage**: Website selection for large-scale crawling

## 🧹 Cleanup

Use the cleanup utilities:

```bash
node clean.js
```

This script helps manage and clean up crawling artifacts and temporary files.

## 🔧 Development

### Project Structure

- **Main Script**: `capture_screenshots.js` - Core crawling logic
- **Utilities**: `utils.js` - Helper functions and classes
- **Configuration**: `config.js` - Settings and constants
- **Cleanup**: `clean.js` - Maintenance utilities

### Dependencies

Key dependencies include:
- `puppeteer` - Browser automation
- `puppeteer-extra` - Enhanced Puppeteer functionality
- `puppeteer-extra-plugin-stealth` - Stealth mode
- `csv-parser` - CSV file processing
- `simple-node-logger` - Logging functionality

### Scripts

Available npm scripts:
```bash
npm start    # Start with nodemon (development)
npm test     # Run tests (not implemented)
```

## 📝 Logging

The crawler generates detailed logs organized by:
- **Site ID**: Unique identifier for each crawl
- **Timestamp**: When the crawl was performed
- **Log Level**: Info, warning, error messages

Log files are stored in directories named: `{SITE_ID}_{TIMESTAMP}`

## 🚨 Important Notes

1. **Security Settings**: The crawler intentionally reduces browser security to capture more social engineering examples
2. **Resource Usage**: Large-scale crawling can be resource-intensive
3. **Rate Limiting**: Consider implementing delays between requests for respectful crawling
4. **Legal Compliance**: Ensure crawling activities comply with website terms of service and applicable laws

## 🤝 Contributing

When modifying the crawler:
1. Update configuration in `config.js` for new user agents or settings
2. Add utility functions to `utils.js`
3. Follow the existing naming conventions for output files
4. Test with various user agents and crawling modes

## 📞 Support

For issues with the crawler:
1. Check browser compatibility and Puppeteer version
2. Verify Node.js dependencies are properly installed
3. Review log files for detailed error information
4. Ensure sufficient system resources for large-scale crawling

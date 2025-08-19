# PP_Defend: Real-Time Browser Defense Against Web BMAs

The **PP_Defend** module is the browser extension component of the PixelPatrol3D project, providing real-time protection against behavior manipulation attacks (BMAs) directly in the user's browser. This extension uses on-device machine learning to detect malicious web content without compromising user privacy.

## 🎯 Overview

PP_Defend is a Chrome/Firefox browser extension that runs the PP3D detection model locally using ONNX Web Runtime. It continuously monitors web pages, extracts visual and textual features using OCR, and provides immediate warnings when potential BMAs are detected. All processing occurs locally on the user's device, ensuring complete privacy.

## 🏗️ Architecture

```
PP_Defend Browser Extension
├── Background Service Worker (background.js)
├── Extension Popup (popup.js)
├── Warning Notifications (notification.js)
├── Offscreen Processing (offscreen.js)
├── ONNX Model Runtime (onnx_worker.js)
├── Sandboxed Execution (sandbox.js)
└── Utility Functions (utils.js)
```

### Key Components

1. **Background Service**: Manages extension lifecycle, coordinates scanning, and handles the detection pipeline
2. **Popup Interface**: Provides user controls for toggling features and viewing scan results
3. **Offscreen Document**: Hosts Web Workers for ONNX inference and OCR processing
4. **ONNX Runtime**: Executes the multimodal detection model locally using ONNX Web Runtime
5. **OCR Engine**: Extracts text from webpage screenshots using Tesseract.js
6. **Warning System**: Displays security warnings when malicious content is detected

## 📁 Directory Structure

```
pp_defend/
├── README.md                    # This documentation
├── package.json                 # Node.js dependencies and metadata
├── package-lock.json            # Dependency lock file
├── webpack.config.js            # Build configuration for bundling
├── .gitignore                   # Git ignore rules
├── public/                      # Static assets and extension manifest
│   ├── manifest.json            # Extension manifest (Manifest V3)
│   ├── popup.html               # Extension popup interface
│   ├── popup.css                # Popup styling
│   ├── notification.html        # Warning overlay template
│   ├── offscreen.html           # Offscreen document for processing
│   ├── sandbox.html             # Sandboxed execution environment
│   ├── tranco_100k.csv          # Top 100K domains whitelist
│   └── models/                  # Pre-trained model files
│       ├── m33_e4_960x540_512.onnx    # ONNX detection model
│       └── bert_mini_tokenizer/        # BERT tokenizer files
│           ├── tokenizer.json
│           ├── tokenizer_config.json
│           ├── vocab.txt
│           └── special_tokens_map.json
└── src/                         # Source code
    ├── background.js            # Background service worker
    ├── popup.js                 # Extension popup logic
    ├── notification.js          # Warning overlay logic
    ├── offscreen.js             # Offscreen processing
    ├── sandbox.js               # Sandboxed execution
    ├── onnx_worker.js           # ONNX model inference
    └── utils.js                 # Utility functions
```

## 🚀 Quick Start

### Prerequisites

1. **System Requirements**

   ```bash
   # Node.js (v20.18.3 or later)
   node --version
   npm --version

   # Modern browser with Manifest V3 support
   # Chrome 88+ or Firefox 89+
   # Minimum 2GB RAM for model inference
   ```

2. **Browser Compatibility**

   - **Chrome**: Version 88+ (Manifest V3 support)
   - **Firefox**: Use the `firefox` branch for Firefox-specific build
   - **Firefox Mobile**: Use the `firefox_mobile` branch
   - **Edge**: Compatible with Chrome build (Chromium-based)

### Installation Methods

#### Method 1: Pre-built Extension (Recommended)

1. **Download Release**

   ```bash
   # Download the latest release ZIP from GitHub
   # Extract to a local directory
   unzip pp_defend_release.zip
   cd pp_defend_release/
   ```

2. **Load in Browser**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)
   - Click "Load unpacked" and select the extracted folder

#### Method 2: Build from Source

1. **Clone and Setup**

   ```bash
   cd pp_defend/
   npm install
   ```

2. **Build Extension**

   ```bash
   # Development build
   rm -rf dist && npx webpack --mode development

   # Production build (optimized)
   rm -rf dist && npx webpack --mode production
   ```

3. **Load in Browser**
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `dist/` folder

### Verification

1. **Extension Loaded**: Verify the extension appears in your extensions list
2. **Toolbar Icon**: Look for the PixelPatrol3D icon in the browser toolbar
3. **Permissions**: Grant required permissions (activeTab, storage, downloads, etc.)
4. **Initial Setup**: Click the extension icon to access the popup interface

## ⚙️ Configuration and Usage

### Extension Controls

The extension popup provides several configuration options:

| Control                 | Description                       | Default |
| ----------------------- | --------------------------------- | ------- |
| **Main Toggle**         | Enable/disable real-time scanning | OFF     |
| **Reset Button**        | Reset extension to default state  | -       |
| **Performance Logging** | Log inference timing metrics      | ON      |
| **Screenshot Logging**  | Save screenshots for analysis     | OFF     |
| **User Agent Selector** | Change browser user agent string  | default |

### Real-Time Protection

#### Automatic Scanning

- **Scan Frequency**: Every 5 seconds on active tabs (configurable via `SCAN_INTERVAL`)
- **Smart Filtering**: Automatically whitelists top 100K Tranco domains
- **Visual Similarity**: Uses perceptual hashing (BMVBHash) to avoid redundant scans
- **Resource Management**: Pauses scanning on inactive tabs

#### Detection Pipeline

The extension uses a four-case decision pipeline:

1. **Case 1**: Domain in Tranco whitelist → verdict of `benign`
2. **Case 2**: No previous perceptual hash → run full inference
3. **Case 3**: Hamming distance ≥ 5 → run full inference
4. **Case 4**: Hamming distance < 5 → reuse last verdict

#### Warning System

When a potential BMA is detected, the extension displays a warning popup with four options:

1. **Return to Safety** - Navigate back to a safe page (google.com)
2. **Ignore Warning** - Continue browsing (marks screenshot as malicious)
3. **Close (X)** - Same as ignore warning for convenience
4. **Not Malicious** - Report false positive (marks screenshot as benign)

### Logging and Data Collection

#### Performance Logging

```
Output: Downloads/pp_ext/<session_timestamp>/logs/
Content: Inference timing, initialization metrics, scan performance
Frequency: Bulk save every 2 minutes (configurable via SAVE_INTERVAL)
Privacy: No personal data, only performance metrics
```

#### Screenshot Logging

```
Output: Downloads/pp_ext/<session_timestamp>/{benign,fp,malicious}/
Content: Webpage screenshots with classifications
Frequency: Every scan cycle when enabled
Privacy: Local storage only, never transmitted
```

### User Agent Customization

The extension supports multiple user agent strings including:

**Desktop Browsers:**

- Chrome (Windows, macOS, Linux, ChromeOS)
- Firefox (Windows, macOS)
- Edge (Windows, macOS)
- Safari (macOS)
- Opera (Windows, macOS)

**Mobile Devices:**

- Chrome (Android phone/tablet)
- Firefox (Android phone/tablet)
- Safari (iPhone, iPad)
- Edge (iPhone, iPad, Android)
- Opera (Android, iPhone)

## 🔧 Technical Implementation

### Model Architecture

PP_Defend implements the multimodal detection model from the PP3D paper:

- **Visual Branch**: MobileNetV3-Small feature extractor (576 dimensions)
- **Text Branch**: BERT-mini with linear projection (128 dimensions)
- **Fusion**: Concatenated features (704 dimensions) → MLP classifier
- **Input Processing**: Screenshots normalized to 960×540, OCR text tokenized

### Performance Characteristics

Based on the paper's evaluation across different devices:

| Device Type                | Median Latency | Memory Usage | CPU Usage |
| -------------------------- | -------------- | ------------ | --------- |
| **Desktop (M4 Max)**       | 388ms          | 1-3GB        | 7%        |
| **Desktop (Intel i7)**     | 859ms          | 1-3GB        | 10%       |
| **Mobile (Samsung A55)**   | 1.7s           | 1-2GB        | 11%       |
| **Tablet (Samsung S9 FE)** | 2.7s           | 1-2GB        | 32%       |

### Key Configuration Constants

From the actual codebase (`background.js`):

```javascript
const SCAN_INTERVAL = 5 * 1000; // 5 second scan interval
const SAVE_INTERVAL = 2 * 60 * 1000; // 2 minute log save interval
const HASH_GRID_SIZE = 8; // 8x8 perceptual hash grid
const HAMMING_DIST_THOLD = 5; // Hamming distance threshold
```

## 🛡️ Privacy and Security

### Privacy Guarantees

- **Local Processing**: All inference occurs on the user's device
- **No Data Transmission**: Screenshots and text never leave the browser
- **Minimal Permissions**: Uses standard browser extension permissions
- **Optional Logging**: All data collection is opt-in and stored locally

### Security Features

- **Sandboxed Execution**: Model inference runs in isolated Web Workers
- **Content Security Policy**: Strict CSP prevents code injection
- **Manifest V3**: Uses latest security standards for browser extensions
- **Offscreen Processing**: Heavy computations isolated from main thread

### Data Handling

```
Data Type          | Storage Location | Transmission | Retention
Screenshots        | Local Downloads  | Never        | User Control
Performance Logs   | Local Downloads  | Never        | User Control
Model Weights      | Extension Bundle | Never        | Permanent
User Preferences   | Browser Storage  | Never        | Until Uninstall
Tranco Whitelist   | Extension Bundle | Never        | Permanent
```

## 🚨 Troubleshooting

### Common Issues

#### Extension Not Loading

**Symptoms**: Extension doesn't appear in browser
**Solutions**:

1. Verify Developer Mode is enabled in `chrome://extensions/`
2. Check manifest.json syntax and required permissions
3. Ensure all required files are present in the build directory
4. Try reloading the extension

#### Performance Issues

**Symptoms**: Browser slowdown, high memory usage
**Solutions**:

1. Disable performance logging in extension popup
2. Disable screenshot logging if enabled
3. Check available system memory (extension requires 1-3GB)
4. Restart browser to clear memory leaks

#### False Positives

**Symptoms**: Legitimate sites flagged as malicious
**Solutions**:

1. Use "Not Malicious" button to report false positive
2. Check if site should be in Tranco whitelist
3. Verify model file integrity
4. Report issue on GitHub with screenshot

#### Model Loading Errors

**Symptoms**: Extension fails to initialize, offscreen errors
**Solutions**:

1. Verify ONNX model file (`m33_e4_960x540_512.onnx`) is present
2. Check browser ONNX Web Runtime support
3. Clear extension storage and reload
4. Check browser console for detailed error messages

### Debug Information

Enable detailed logging by checking the browser console:

- Background script logs: Check extension's background page console
- Popup logs: Open popup and check browser developer tools
- Offscreen logs: Available in extension's offscreen document console

## 🛠️ Development

### Development Workflow

1. **Setup Environment**

   ```bash
   cd pp_defend/
   npm install
   ```

2. **Development Build**

   ```bash
   # Build for development (includes source maps)
   npx webpack --mode development

   # Watch mode for continuous building
   npx webpack --mode development --watch
   ```

3. **Load in Browser**
   - Navigate to `chrome://extensions/`
   - Enable Developer Mode
   - Click "Load unpacked" and select `dist/` folder
   - Reload extension after code changes

### Extension Architecture

#### Background Service Worker (`background.js`)

- Manages extension lifecycle and initialization
- Coordinates the scanning pipeline and timing
- Handles Tranco whitelist loading and domain checking
- Manages perceptual hashing and similarity detection
- Controls offscreen document creation and communication
- Implements the four-case decision logic
- Handles user agent modification via declarativeNetRequest

#### Popup Interface (`popup.js`)

- Provides user controls for main toggle, logging options
- Displays real-time scan results and classification data
- Manages user agent selection dropdown
- Updates UI based on storage changes
- Handles extension reset functionality

#### Offscreen Processing (`offscreen.js`)

- Hosts Web Workers for ONNX inference and OCR
- Manages model loading and initialization
- Coordinates parallel OCR processing (4 horizontal slices)
- Returns classification results to background script

### Adding New Features

#### Custom Warning Types

1. **Update Warning Template**: Modify `notification.html`
2. **Add Logic**: Update `notification.js` for new warning behavior
3. **Update Styling**: Edit CSS for new warning appearance
4. **Test Integration**: Verify with test pages

#### Performance Optimizations

1. **Model Optimization**: Use quantized ONNX models
2. **Batch Processing**: Process multiple screenshots together
3. **Caching**: Cache frequent computations and results
4. **Lazy Loading**: Load components only when needed

### Testing

#### Manual Testing

1. **Load test pages** with known BMAs from the paper's dataset
2. **Verify detection** accuracy and timing
3. **Test warning interface** functionality across different scenarios
4. **Check performance** metrics on different devices

#### Browser Compatibility

- Test across Chrome, Firefox, and Edge
- Verify Manifest V3 compatibility
- Test on desktop, tablet, and mobile form factors
- Validate ONNX Web Runtime support

## 🤝 Contributing

### Development Areas

- **Browser Compatibility**: Extend support to Safari, Opera
- **Mobile Optimization**: Improve performance on resource-constrained devices
- **UI/UX Enhancement**: Better warning designs and user experience
- **Performance Optimization**: Reduce memory usage and inference latency
- **Security Features**: Enhanced privacy protections and security measures
- **Accessibility**: Improve accessibility compliance for warnings and UI
- **Internationalization**: Multi-language support for warnings and interface

### Code Standards

- **JavaScript**: Follow ES6+ standards with consistent formatting
- **HTML/CSS**: Semantic markup with responsive design principles
- **Manifest V3**: Maintain compatibility with latest browser extension standards
- **Security**: Follow browser extension security best practices
- **Documentation**: Update README and inline code comments
- **Testing**: Include manual testing procedures for new features

### Submission Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Test changes across multiple browsers and devices
4. Update documentation as needed
5. Submit pull request with detailed description of changes

## 📞 Support

### Getting Help

- **Documentation**: Check this README and inline code comments
- **GitHub Issues**: Report bugs and request features at the main repository
- **Main Project**: See [PixelPatrol3D README](../README.md) for overall project documentation
- **Research Paper**: Reference the [PP3D paper](../pp3d_acsac_053025.pdf) for technical details

### Browser-Specific Support

#### Chrome/Chromium

- **Minimum Version**: Chrome 88+ (Manifest V3 support)
- **Developer Tools**: Use `chrome://extensions/` for debugging
- **Performance**: Best performance on desktop Chrome
- **Permissions**: Requires activeTab, storage, downloads, offscreen, and other standard permissions

#### Firefox

- **Branch**: Use `firefox` branch for Firefox-specific build
- **Minimum Version**: Firefox 89+ (Manifest V3 support)
- **Developer Tools**: Use `about:debugging` for extension debugging
- **Mobile**: Use `firefox_mobile` branch for mobile Firefox support

#### Edge

- **Compatibility**: Works with Chrome build (Chromium-based)
- **Installation**: Same process as Chrome
- **Performance**: Similar to Chrome performance characteristics

### Performance Support

#### System Requirements

- **Minimum RAM**: 4GB system RAM (extension uses 1-3GB during inference)
- **CPU**: Modern multi-core processor for acceptable performance
- **Storage**: 100MB free space for extension, models, and logs
- **Network**: No network required for core functionality (all local processing)

#### Optimization Tips

1. **Close unused tabs** to reduce overall memory pressure
2. **Disable logging** if not needed for research purposes
3. **Use Tranco whitelist** to skip scanning on trusted high-traffic domains
4. **Regular cleanup** of downloaded logs and screenshots
5. **Browser restart** if memory usage becomes excessive over time

### Security Support

#### Reporting Security Issues

- **Responsible Disclosure**: Report security vulnerabilities privately through GitHub
- **Contact**: Use GitHub security advisories for sensitive issues
- **Response Time**: Security issues are prioritized for rapid response

#### Privacy Concerns

- **Data Processing**: All processing remains local to user device
- **No Tracking**: Extension does not track user behavior or browsing history
- **Optional Logging**: All data collection is opt-in and stored locally only
- **Transparency**: Full source code available for security audit

---

**PP_Defend** provides the first real-time, privacy-preserving defense against web behavior manipulation attacks. By running advanced machine learning models directly in the browser using ONNX Web Runtime and Tesseract.js, it offers immediate protection without compromising user privacy or requiring external services.

For detailed information about the overall PixelPatrol3D project, model architecture, and research findings, please refer to the [main project README](../README.md) and the [research paper](../pp3d_acsac_053025.pdf).

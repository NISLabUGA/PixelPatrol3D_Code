# PixelPatrol3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks

[![Paper](https://img.shields.io/badge/Paper-ACSAC%202025-blue)](pp3d_acsac_053025.pdf)
[![Dataset](https://img.shields.io/badge/Dataset-Available-green)](http://pp3d_data.sdkhomelab.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**PixelPatrol3D (PP3D)** is the first end-to-end browser framework for discovering, detecting, and defending against web-based behavior manipulation attacks (BMAs) in real time. Unlike traditional phishing attacks that steal credentials, BMAs manipulate users into performing unsafe actions like downloading malware, granting unwanted permissions, or calling fraudulent support lines.

## 📖 Overview

This repository contains the complete implementation of the PP3D framework described in our ACSAC 2025 paper. The system achieves **99% detection rate at 1% false positives** and maintains **97%+ detection rate** even on attacks collected months after training, demonstrating strong temporal generalization.

### Key Features

- **Multimodal Detection**: Combines visual (MobileNetV3) and textual (BERT-mini) features for robust BMA detection
- **Resolution Agnostic**: Works across devices from mobile phones to desktop monitors
- **Real-time Defense**: Browser extension provides immediate protection with minimal overhead
- **Privacy Preserving**: All inference runs locally in the browser with no data leakage
- **Comprehensive Dataset**: Largest labeled BMA dataset with 7,149+ attack samples across 84 campaigns

## 🏗️ Architecture

PP3D consists of three main components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PP_Discover   │───▶│   PP_Detect     │───▶│   PP_Defend     │
│                 │    │                 │    │                 │
│ • Web Crawling  │    │ • Multimodal    │    │ • Browser       │
│ • Data Mining   │    │   Classification│    │   Extension     │
│ • Campaign      │    │ • Visual + Text │    │ • Real-time     │
│   Discovery     │    │   Features      │    │   Protection    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🌿 Branch Structure

This repository contains multiple branches with different code configurations:

- **`chrome`** - **Main branch** containing the complete PixelPatrol3D codebase with all three components (pp_discover, pp_detect, pp_defend)
- **`firefox`** - Contains only the pp_defend code specifically adapted for Firefox browser extension
- **`firefox_mobile`** - Contains only the pp_defend code specifically adapted for Firefox mobile browser extension

For the full system implementation and research code, use the **chrome branch**. The firefox branches contain browser-specific variants of the defense component only.

## 📁 Repository Structure

### Core Modules

- **[`pp_discover/`](pp_discover/)** - Large-scale web crawling and BMA discovery system

  - Automated crawling across 30+ device configurations
  - Docker-based distributed architecture
  - Campaign clustering and analysis pipeline
  - See [PP_Discover README](pp_discover/README.md) for detailed usage

- **[`pp_detect/`](pp_detect/)** - Multimodal detection model and training pipeline

  - PyTorch implementation of vision-text fusion model
  - Training scripts for all research questions (RQ1-RQ5)
  - Model conversion utilities (PyTorch → ONNX)
  - See [PP_Detect README](pp_detect/README.md) for training instructions

- **[`pp_defend/`](pp_defend/)** - Browser extension for real-time protection

  - Chrome/Firefox extension with ONNX Web Runtime
  - Local inference with Tesseract.js OCR
  - User-friendly warning interface
  - See [PP_Defend README](pp_defend/README.md) for installation guide

### Data and Documentation

- **[`pp3d_data/`](pp3d_data/)** - Dataset structure and access information

  - Links to hosted dataset (359GB total)
  - Organized by research questions (RQ1-RQ5)
  - See [PP3D Data README](pp3d_data/README.md) for download instructions

- **[`pp3d_acsac_053025.pdf`](pp3d_acsac_053025.pdf)** - Full research paper
- **[`requirements.txt`](requirements.txt)** - Python dependencies for pp_detect and pp_discover

## 🚀 Quick Start

### Prerequisites

```bash
# System requirements
- Python 3.8+
- Node.js 20.18.3+
- Docker & Docker Compose
- CUDA-capable GPU (recommended for training)
```

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/NISLabUGA/PixelPatrol3D_Code.git
cd PixelPatrol3D_Code

# Create Python virtual environment
python -m venv pp3d_env
source pp3d_env/bin/activate  # On Windows: pp3d_env\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Login to Hugging Face (required for BERT tokenizer)
huggingface-cli login
```

### 2. Download Dataset (Optional)

```bash
# Download complete dataset (359GB)
wget -r -np -nH --cut-dirs=4 -R "index.html*" http://pp3d_data.sdkhomelab.com/

# Or download specific components
wget http://pp3d_data.sdkhomelab.com/train.zip  # Training data (46GB)
wget http://pp3d_data.sdkhomelab.com/test.zip   # Test data (1GB)
```

### 3. Run Detection Model

```bash
cd pp_detect/train_test/

# Basic training and evaluation (RQ1)
python tt_comb.py

# Test on never-before-seen campaigns (RQ3)
python tt_l1o_camp.py

# Adversarial robustness evaluation (RQ5)
python tt_comb_adv.py
```

### 4. Install Browser Extension

```bash
cd pp_defend/

# Install Node.js dependencies
npm install

# Build extension
rm -rf dist && npx webpack --mode development

# Load in Chrome:
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the 'dist' folder
```

### 5. Run Web Crawler (Advanced)

```bash
cd pp_discover/

# Install crawler dependencies
cd pp_crawler && npm install && cd ..

# Configure crawling parameters
vim config.yaml

# Run large-scale crawling
python run_op_at_scale.py
```

## 🔬 Research Questions & Experiments

Our evaluation addresses five key research questions:

| RQ      | Question                                                | Script           | Key Results           |
| ------- | ------------------------------------------------------- | ---------------- | --------------------- |
| **RQ1** | Can PP_det detect new instances of known BMA campaigns? | `tt_comb.py`     | **99%+ DR @ 1% FPR**  |
| **RQ2** | Does PP_det generalize to unseen screen resolutions?    | `tt_l1o_res.py`  | **99%+ DR @ 1% FPR**  |
| **RQ3** | Can PP_det detect never-before-seen BMA campaigns?      | `tt_l1o_camp.py` | **99%+ DR @ 1% FPR**  |
| **RQ4** | Does PP_det work on temporally distant attacks?         | `tt_comb.py`     | **97.8% DR @ 1% FPR** |
| **RQ5** | Can PP_det resist adversarial examples?                 | `tt_comb_adv.py` | **98%+ DR @ 1% FPR**  |

## 📊 Performance Results

### Detection Performance

- **Accuracy**: 99%+ on new attack instances
- **Generalization**: 97%+ on attacks collected months later
- **False Positive Rate**: Maintained at 1% across all experiments
- **Temporal Robustness**: Strong performance on evolving attack content

### Browser Extension Performance

- **Latency**: 388ms (M4 Max) to 2.6s (mobile) median inference time
- **Memory**: 1-3GB additional RAM usage
- **CPU**: 7-31% additional CPU usage during inference
- **Privacy**: 100% local processing, no data transmission

### Supported Attack Types

- Fake Software Downloads (4,700 samples, 29 campaigns)
- Notification Permission Stealing (1,130 samples, 7 campaigns)
- Service Registration Scams (758 samples, 20 campaigns)
- Scareware (213 samples, 9 campaigns)
- Fake Lotteries/Sweepstakes (194 samples, 6 campaigns)
- Technical Support Scams (17 samples, 3 campaigns)

## 🛡️ Browser Extension Features

### Real-time Protection

- **Automatic Scanning**: Scans pages every 5 seconds
- **Smart Filtering**: Whitelists top 100K domains for efficiency
- **Visual Similarity**: Uses perceptual hashing to avoid redundant inference
- **Multi-platform**: Works on desktop, tablet, and mobile browsers

### User Interface

- **Warning Overlay**: Clear, non-intrusive warnings for detected threats
- **Action Options**: Return to safety, ignore warning, or report false positive
- **Performance Logging**: Optional metrics collection for research
- **Screenshot Logging**: Optional sample collection for model improvement

### Privacy & Security

- **Local Processing**: All inference runs in the browser
- **No Data Transmission**: Screenshots and text never leave the device
- **Minimal Permissions**: Only requires activeTab and storage permissions
- **Open Source**: Full transparency of extension behavior

## 📈 Dataset Information

### Scale & Diversity

- **Total Size**: 359GB (compressed), 421GB (uncompressed)
- **BMA Samples**: 7,149 attack screenshots across 84 campaigns
- **Benign Samples**: 782,435 legitimate website screenshots
- **Screen Resolutions**: 30 different resolutions (mobile to desktop)
- **Collection Period**: Multi-month collection for temporal evaluation

### Access & Usage

- **Public Dataset**: Available at [http://pp3d_data.sdkhomelab.com/](http://pp3d_data.sdkhomelab.com/)
- **Research License**: Free for academic and research purposes
- **Organized Structure**: Data organized by research questions for easy access
- **Verification**: MD5 checksums provided for integrity verification

## 🔧 Advanced Configuration

### Model Training

```python
# Key hyperparameters in training scripts
BATCH_SIZE = 64
LEARNING_RATE = 2e-6
DROPOUT_VISUAL = 0.3
DROPOUT_TEXT = 0.3
DROPOUT_FUSION = 0.6
LOSS_TYPE = "weighted_ce"  # Options: "ce", "weighted_ce", "focal"
```

### Browser Extension

```javascript
// Extension configuration in manifest.json
"permissions": ["activeTab", "storage", "offscreen"]
"host_permissions": ["<all_urls>"]
"web_accessible_resources": ["models/*", "notification.html"]
```

### Web Crawler

```yaml
# Crawler configuration in config.yaml
timeout: 300 # seconds per URL
max_containers: 10 # concurrent Docker containers
user_agent_list: # supported browser configurations
  - chrome_linux
  - chrome_mac
  - firefox_win
  - safari_iphone
```

## 🤝 Contributing

We welcome contributions from the research community:

### Development Areas

- **New Attack Types**: Extend detection to additional BMA categories
- **Performance Optimization**: Improve inference speed and memory usage
- **Mobile Support**: Enhanced mobile browser extension features
- **Dataset Expansion**: Contribute new BMA samples and campaigns

### Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and test thoroughly
4. Update documentation as needed
5. Submit a pull request with detailed description

### Research Collaboration

- **Academic Partnerships**: Contact us for research collaborations
- **Dataset Contributions**: Share new BMA samples for model improvement
- **Evaluation Studies**: Collaborate on user studies and real-world deployments
- **Extension Development**: Help port to additional browsers and platforms

## 📚 Citation

If you use PixelPatrol3D in your research, please cite our paper:

```bibtex
@inproceedings{pp3d2025,
  title={PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks},
  author={[Authors]},
  booktitle={Annual Computer Security Applications Conference (ACSAC)},
  year={2025},
  publisher={ACM}
}
```

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

- **Open Source**: Free for both academic and commercial use
- **Permissive**: Modify, distribute, and use in private and commercial projects
- **Attribution**: Only requirement is to include the original copyright notice
- **Dataset**: Available under research license with proper attribution (separate from code license)

## 🔗 Related Work

### Academic Papers

- **BMA Measurement Studies**: Vadrevu et al. (IMC 2019), Subramani et al. (IMC 2020)
- **Social Engineering Detection**: Yang et al. (USENIX Security 2023) - TRIDENT
- **Visual Phishing Detection**: Abdelnabi et al. (CCS 2020), Lin et al. (USENIX Security 2021)

### Industry Solutions

- **Google Safe Browsing**: URL-based blocking service
- **Microsoft Defender SmartScreen**: Reputation-based protection
- **Browser Built-ins**: Chrome's Enhanced Safe Browsing, Firefox's Enhanced Tracking Protection

## 📞 Support & Contact

### Technical Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive READMEs in each module
- **Community**: Join discussions in GitHub Discussions

### Research Inquiries

- **Academic Collaboration**: Contact the research team
- **Dataset Access**: Follow instructions in [pp3d_data README](pp3d_data/README.md)
- **Paper Questions**: Reference the full paper for methodological details

### Security Issues

- **Responsible Disclosure**: Report security vulnerabilities privately
- **Extension Security**: Follow browser extension security best practices
- **Data Privacy**: All processing remains local to user devices

---

**PixelPatrol3D** represents a significant advancement in web security, providing the first comprehensive defense against behavior manipulation attacks. By combining large-scale data collection, advanced machine learning, and practical browser deployment, PP3D offers both researchers and users powerful tools to combat this evolving threat landscape.

For detailed information about each component, please refer to the individual README files in each directory.

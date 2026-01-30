# PixelPatrol3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks

[![Paper](https://img.shields.io/badge/Paper-ACSAC%202025-blue)](pp3d_acsac_053025.pdf)
[![Dataset](https://img.shields.io/badge/Dataset-UGA%20OpenScholar-green)](https://openscholar.uga.edu/record/27692)
[![Dataset Mirror](https://img.shields.io/badge/Dataset-Mirror-lightgreen)](https://pp3d-data.sdkhomelab.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**PixelPatrol3D (PP3D)** is the first end-to-end browser framework for discovering, detecting, and defending against web-based behavior manipulation attacks (BMAs) in real time. Unlike traditional phishing attacks that steal credentials, BMAs manipulate users into performing unsafe actions like downloading malware, granting unwanted permissions, or calling fraudulent support lines.

**📄 Paper Versions:**

- [Camera Ready Pre-Print (October 2025)](pp3d_acsac_cr_102125.pdf) | [arXiv (2510.18465)](https://arxiv.org/pdf/2510.18465)
- [Original Accepted Version (May 2025)](pp3d_acsac_053025.pdf)

## 📖 Overview

This repository contains the complete implementation of the PP3D framework described in our ACSAC 2025 paper. The system achieves **99% detection rate at 1% false positives** and maintains **97%+ detection rate** even on attacks collected months after training, demonstrating strong temporal generalization.

### Key Features

- **Multimodal Detection**: Combines visual (MobileNetV3) and textual (BERT-mini) features for robust BMA detection
- **Resolution Agnostic**: Works across devices from mobile phones to desktop monitors
- **Real-time Defense**: Browser extension provides immediate protection with minimal overhead
- **Privacy Preserving**: All inference runs locally in the browser with no data leakage
- **Comprehensive Dataset**: Largest labeled BMA dataset with 7,149+ attack samples across 84 campaigns

## 🔬 ACSAC 2025 Artifact Evaluation

For **reproducible evaluation** of our research claims, we provide a comprehensive artifact evaluation package:

**🔗 [ACSAC Artifact Repository](https://github.com/NISLabUGA/PixelPatrol3D_Code_ACSAC_Artifacts)**

This artifact includes:

- **Pre-trained models** for all research questions (RQ1-RQ5)
- **Evaluation scripts** with expected runtime <10 minutes to 90 minutes per claim
- **Standardized datasets** with automated download and verification
- **8 reproducibility claims** covering core evaluation and training verification

The artifact enables independent verification of our key results including **99%+ detection rates** and **cross-resolution/campaign generalization** without requiring full model training from scratch.

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

  - Links to hosted dataset
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

# Install PyTorch with CUDA support (if available)
# For CUDA systems:
pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu124
# For CPU-only systems:
# pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
pip install -r requirements.txt

# Login to Hugging Face (required for BERT tokenizer)
huggingface-cli login
```

### 2. Download Dataset (Optional)

**Recommended:** Download from UGA OpenScholar (institutional repository with long-term stability):
- Visit [https://openscholar.uga.edu/record/27692](https://openscholar.uga.edu/record/27692)
- DOI: [10.71927/uga.27692](https://doi.org/10.71927/uga.27692)
- Download the complete dataset ZIP file from the repository page

**Alternative:** Download from original source using wget:

```bash
# Download complete dataset (359GB)
wget -r -np -nH --cut-dirs=4 -R "index.html*" https://pp3d-data.sdkhomelab.com/

# Or download specific components
wget https://pp3d-data.sdkhomelab.com/train.zip  # Training data (46GB)
wget https://pp3d-data.sdkhomelab.com/test.zip   # Test data (1GB)
```

Both sources host the same dataset with identical file sizes and checksums.

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
nano config.yaml

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

## 🌐 Live Demonstrations

**Experience PP_Defend in Action**: Visit [https://pixelpatrol3d.github.io/](https://pixelpatrol3d.github.io/) to see real-user perspective demonstrations of PixelPatrol3D's browser-based defense capabilities.

This interactive showcase presents two key scenarios:

- **Scenario 1: Browsing Without Protection** - Highlights how deceptive pages appear when unprotected, demonstrating the subtle nature of Behavior Manipulation Attacks (BMAs) that exploit persuasive visuals and misleading text to manipulate users into unsafe actions.
- **Scenario 2: Real-Time Protection With Pixel Patrol** - Shows the extension actively detecting and blocking harmful content in real time, providing proactive warnings before any harm occurs.

The demonstrations illustrate how PP_Defend uses privacy-preserving on-device models to scan web content through screenshots and OCR, successfully flagging malicious pages that traditional URL filters cannot detect.

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

- **Public Dataset**: Available at [UGA OpenScholar](https://openscholar.uga.edu/record/27692) (recommended for long-term stability) and [original source](https://pp3d-data.sdkhomelab.com/) (alternative mirror)
- **Organized Structure**: Data organized by research questions for easy access
- **Verification**: MD5 checksums provided for integrity verification

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

If you use the PP3D dataset, please cite:

```bibtex
@dataset{pp3d_dataset2025,
  author={King, S. and Ozen, I. and Subramani, K. and Senthivel, S. and Vadrevu, P. and Perdisci, R.},
  title={PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks},
  year={2025},
  publisher={University of Georgia},
  version={1},
  doi={10.71927/uga.27692},
  url={https://openscholar.uga.edu/record/27692}
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

- **Academic Collaboration**: For research inquiries or collaboration opportunities, please contact our team at _[sdk81722@uga.edu]()_
- **Dataset Access**: Follow instructions in [pp3d_data README](pp3d_data/README.md)
- **Paper Questions**: Reference the full paper for methodological details

### Security Issues

- **Responsible Disclosure**: Report security vulnerabilities privately
- **Extension Security**: Follow browser extension security best practices
- **Data Privacy**: All processing remains local to user devices

---

**PixelPatrol3D** represents a significant advancement in web security, providing the first comprehensive defense against behavior manipulation attacks. By combining large-scale data collection, advanced machine learning, and practical browser deployment, PP3D offers both researchers and users powerful tools to combat this evolving threat landscape.

For detailed information about each component, please refer to the individual README files in each directory.

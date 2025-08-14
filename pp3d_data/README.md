# PP3D Dataset Structure

To access the data associated with this project we has hosted the data [here](http://pp3d_data.sdkhomelab.com/). This directory contains the datasets used in the PP3D (Pixel Patrol 3D) research paper "An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks" submitted to ACSAC 2025. The datasets are organized to support the various research questions (RQs) investigated in the paper.

## Research Questions Overview

The paper investigates five key research questions:

- **RQ1**: Can PP_det accurately identify new instances of BMAs belonging to previously observed campaigns?
- **RQ2**: Can PP_det accurately identify instances of BMAs captured on a new screen size never seen during training?
- **RQ3**: Can PP_det identify web pages belonging to never-before-seen BMA campaigns?
- **RQ4**: Can PP_det accurately identify fresh BMA attacks that were collected well after the training data?
- **RQ5**: Can PP_det be strengthened against adversarial examples?

## Directory Structure Requirements

The pp_detect scripts require the following directory structure under `pp3d_data/`:

- `raw/` - Contains raw, unprocessed data collection
- `train/` - Processed training datasets
- `test/` - Evaluation test datasets
- `l1o/` - Leave-one-out experiment data

Each directory must be populated with the appropriate dataset files for the scripts to function correctly.

### `/raw/` - Raw Data Collection

Contains the original, unprocessed data collected for the study:

- **`benign_cc/`**: Benign websites collected from Common Crawl dataset

  - Contains legitimate website screenshots and metadata from 10,000 URLs randomly selected from Web Extraction (WET) files
  - Used as negative samples for training and evaluation
  - Provides diverse, less popular websites to complement the Tranco dataset

- **`benign_tranco/`**: Benign websites from Tranco Top 1M list

  - Contains screenshots of the top 5,000 domains from the Tranco list
  - Represents popular, high-traffic legitimate websites
  - Provides additional negative samples with well-established sites

- **`malicious/`**: Raw malicious BMA data collected

  - Contains unprocessed BMA screenshots from various attack campaigns
  - Includes data from both primary and secondary collection efforts
  - Covers multiple BMA categories: fake software downloads, scareware, tech support scams, notification stealing, fake lotteries/sweepstakes, and service registration scams

### `/train/` - Training Data (RQ1, RQ4, RQ5)

Contains the processed training datasets used for model development:

- **`benign/train_100k/`**: Training set of benign websites

  - 100,000 unaugmented screenshots randomly sampled from the broader benign collection
  - Proportional representation across all 30 screen resolutions
  - Even split between Tranco Top 5K and Common Crawl sources
  - Used for training the main PP_det model

- **`malicious/`**: Training set of malicious BMA pages

  - 6,512 unaugmented screenshot-text pairs from primary BMA collection
  - Augmented to 19,536 samples using image and text augmentation techniques
  - Covers 74 distinct BMA campaigns across 6 attack categories
  - Each screenshot paired with OCR-extracted text for multimodal training

- **`malicious_adv/`**: Adversarial training set

  - Contains adversarially augmented BMA samples for RQ5
  - Includes both visual perturbations (using PGD with ε ∈ {2,4,8,16,32}/255) and textual perturbations (5 levels of increasing severity)
  - Used for adversarial training to improve model robustness

### `/test/` - Test Data (RQ1, RQ4, RQ5)

Contains test datasets for evaluating different aspects of the model:

#### `/test/rq1/` - Basic Detection Performance

- **`benign/test_500/`**: 500 benign test samples across multiple screen resolutions

  - Organized by resolution directories (e.g., `360x640/`, `1920x1080/`, etc.)
  - Completely separate from training data
  - Used to evaluate basic detection capabilities on new instances of previously seen campaigns

- **`malicious/test_500/d1/`**: 500 malicious test samples

  - BMA samples from campaigns seen during training but different instances
  - Tests model's ability to generalize to new attack instances within known campaigns

#### `/test/rq4/` - Temporal Generalization

- **`benign/test_500/`**: 500 benign samples for temporal testing

  - Similar structure to RQ1 benign test set
  - Used as negative samples for temporal generalization evaluation

- **`malicious/test_138/`**: 138 fresh BMA samples

  - Contains BMA data from the secondary collection conducted months after training
  - Represents 10 new, never-before-seen BMA campaigns
  - Tests model's ability to detect temporally distant and evolving attack content

#### `/test/rq5/` - Adversarial Robustness

- **`benign/test_500/`**: Clean benign samples for adversarial evaluation
- **`malicious/`**: Adversarial test sets with different perturbation levels
  - `l1/` through `l5/`: Increasingly severe adversarial perturbations
  - Tests model robustness against coordinated multimodal adversarial attacks

### `/l1o/` - Leave-One-Out Experiments (RQ2, RQ3)

Contains data for leave-one-out cross-validation experiments:

- **RQ2 Data**: Leave-one-out experiments for screen resolution generalization

  - Tests model performance on previously unseen screen resolutions
  - 9 different training/test splits excluding one resolution at a time
  - Evaluates resolution agnosticism of the PP_det model

- **RQ3 Data**: Leave-one-out experiments for campaign generalization

  - Tests model performance on never-before-seen BMA campaigns
  - 10 different training/test splits excluding one campaign at a time
  - Evaluates model's ability to generalize across different attack campaigns

## Dataset Download Instructions

The PP3D dataset is publicly available for research purposes. All major directories (`l1o`, `raw`, `test`, and `train`) are provided as compressed `.zip` files for easier download and storage.

### Complete Dataset Download

To download the entire dataset:

```bash
# Download all dataset components
wget -r -np -nH --cut-dirs=4 -R "index.html*" http://pp3d_data.sdkhomelab.com/

# Alternative: Download individual zip files
wget http://pp3d_data.sdkhomelab.com/raw.zip
wget http://pp3d_data.sdkhomelab.com/train.zip
wget http://pp3d_data.sdkhomelab.com/test.zip
wget http://pp3d_data.sdkhomelab.com/l1o.zip
```

### Selective Download by Research Question

Download only the data needed for specific research questions:

#### For RQ1 (Basic Detection Performance)

```bash
# Download training and RQ1 test data
wget http://pp3d_data.sdkhomelab.com/train.zip
wget http://pp3d_data.sdkhomelab.com/test.zip
# Extract only RQ1 test data
unzip -j test.zip "test/rq1/*" -d rq1_test/
```

#### For RQ2 (Screen Resolution Generalization)

```bash
# Download leave-one-out data for resolution experiments
wget http://pp3d_data.sdkhomelab.com/l1o.zip
# Extract resolution-specific data
unzip l1o.zip
```

#### For RQ3 (Campaign Generalization)

```bash
# Download leave-one-out data for campaign experiments
wget http://pp3d_data.sdkhomelab.com/l1o.zip
# Extract campaign-specific data
unzip l1o.zip
```

#### For RQ4 (Temporal Generalization)

```bash
# Download training data and RQ4 test data
wget http://pp3d_data.sdkhomelab.com/train.zip
wget http://pp3d_data.sdkhomelab.com/test.zip
# Extract only RQ4 test data
unzip -j test.zip "test/rq4/*" -d rq4_test/
```

#### For RQ5 (Adversarial Robustness)

```bash
# Download training data (including adversarial) and RQ5 test data
wget http://pp3d_data.sdkhomelab.com/train.zip
wget http://pp3d_data.sdkhomelab.com/test.zip
# Extract adversarial training and test data
unzip -j train.zip "train/malicious_adv/*" -d adversarial_train/
unzip -j test.zip "test/rq5/*" -d rq5_test/
```

### Raw Data Access

For researchers interested in the original, unprocessed data:

```bash
# Download raw data collection
wget http://pp3d_data.sdkhomelab.com/raw.zip
unzip raw.zip

# Access specific raw data components
unzip -j raw.zip "raw/benign_cc/*" -d raw_benign_cc/
unzip -j raw.zip "raw/benign_tranco/*" -d raw_benign_tranco/
unzip -j raw.zip "raw/malicious/*" -d raw_malicious/
```

### Verification and Extraction

After downloading, verify the integrity and extract the data:

```bash
# Verify download integrity
md5sum *.zip

# Extract all zip files
for file in *.zip; do
    echo "Extracting $file..."
    unzip "$file"
done

# Check extracted directory structure
ls -la
tree -d -L 2  # If tree command is available
```

**Checksums**

- train.zip: 360c9ef325e44cb11ae0dd55baaf0983
- test.zip: 446cd0b764f939e50b1694f43cc7e560
- raw.zip: 40bbf56b22e28b354bc023001260d5b1
- l1o.zip: ccd0f7378b54cb64455a4378b2fe3847

### Storage Requirements

- **Complete Dataset**: ~359 GB (compressed), ~421 GB (uncompressed)
- **Training Data**: ~46 GB (compressed), ~52 GB (uncompressed)
- **Test Data**: ~1 GB (compressed), ~1 GB (uncompressed)
- **Raw Data**: ~141 GB (compressed), ~151 GB (uncompressed)
- **L1O Data**: ~171 GB (compressed), ~217 GB (uncompressed)

**Note**: Replace the example URLs above with the actual hosting location once the dataset is published. Checksums and exact file sizes will be provided with the final dataset release.

## Dataset Statistics

### Screen Resolutions

The dataset includes 30 different screen resolutions covering:

- Mobile devices: 360x640, 414x896, 750x1334, 768x1024, 800x1280
- Tablets: 1024x768, 1200x803, 1280x800, 1536x816, 1536x824, 1536x826, 1536x834, 1536x864
- Desktop/Laptop: 1366x677, 1366x720, 1366x724, 1366x728, 1366x738, 1366x741, 1366x768, 1478x837, 1858x1053, 1858x1080, 1920x998, 1920x1032, 1920x1040, 1920x1050, 1920x1052, 1920x1080, 1920x1097

### BMA Categories

The malicious dataset covers 6 main BMA attack categories:

1. **Fake Software Download**: 4,700 screenshots, 29 campaigns
2. **Notification Stealing**: 1,130 screenshots, 7 campaigns
3. **Service Sign-up Scam**: 758 screenshots, 20 campaigns
4. **Scareware**: 213 screenshots, 9 campaigns
5. **Fake Lottery/Sweepstakes**: 194 screenshots, 6 campaigns
6. **Technical Support Scam**: 17 screenshots, 3 campaigns

### Data Collection Timeline

- **Primary Collection**: Initial large-scale crawling effort resulting in 7,012 BMA screenshots across 74 campaigns
- **Secondary Collection**: Follow-up collection conducted months later, yielding 137 BMA screenshots across 10 new campaigns for temporal evaluation

## Data Processing

### Image Preprocessing

- Screenshots normalized to 960x540 resolution for consistent model input
- Isotropic scaling preserves aspect ratios while fitting within 1920x1080 canvas
- Zero-padding applied to maintain consistent dimensions

### Text Processing

- OCR text extracted using Tesseract engine
- Text augmentation performed using LLaMA-3.3-70B for synonym replacement
- Adversarial text perturbations generated using GPT-4.1-mini for robustness testing

### Augmentation Techniques

- **Image Augmentation**: Color inversion, grayscale conversion, margin cropping, hue shifts, brightness/contrast/saturation adjustments
- **Text Augmentation**: Synonym replacement while preserving semantic meaning
- **Adversarial Augmentation**: PGD-based visual perturbations and semantic text distortions

## Usage Notes

- All datasets maintain class imbalance reflecting real-world distribution (significantly more benign than malicious samples)
- Screenshot-text pairs are maintained for multimodal training and evaluation
- Temporal separation between training and test data ensures realistic evaluation scenarios
- Leave-one-out experiments enable comprehensive generalization analysis

## Ethical Considerations

Data collection followed established precedents in security research with minimal impact on legitimate advertisers. The crawling system was designed to be respectful of website resources while gathering necessary data for defense research.

## Citation

If you use this dataset in your research, please cite:

```
PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks
ACSAC 2025 (Submitted)
```

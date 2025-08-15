# PP_Detect: Pixel Patrol 3D Detection Module

This directory contains the detection module (PP_det) from the **"PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks"** paper. PP_det is a multimodal classifier that fuses visual (MobileNetV3-Small) and textual (BERT-mini) features to detect Behavior Manipulation Attacks (BMAs) in web pages.

## 📁 Directory Structure

```
pp_detect/
├── README.md                    # This file
├── .gitignore                   # Git ignore rules
├── data_gen/                    # Data generation and preprocessing scripts
│   ├── aug_img_text_pairs.py   # Image-text pair augmentation
│   ├── data_sampler.py          # Random sampling of datasets
│   ├── llm_text_aug_groq.py     # LLM-based text augmentation (Groq)
│   ├── llm_text_aug_oai_adv.py  # LLM-based adversarial text augmentation (OpenAI)
│   └── ocr_text_gen.py          # OCR text extraction from images
├── models/                      # Pre-trained model weights
│   └── m33_ep4.pth             # Pre-trained PP_det model
├── train_test/                  # Main training and evaluation scripts
│   ├── tt_comb.py              # RQ1 & RQ4: New instances and fresh attacks
│   ├── tt_comb_adv.py          # RQ5: Adversarial robustness evaluation
│   ├── tt_l1o_camp.py          # RQ3: Never-before-seen BMA campaigns
│   └── tt_l1o_res.py           # RQ2: New screen resolutions
└── utils/                       # Utility scripts and notebooks
    ├── pyt_2_onnx.ipynb        # PyTorch to ONNX conversion
    └── tok_2_json.ipynb        # Tokenizer to JSON conversion
```

## Login to Hugging Face

Create a Huggingface account on huggingface.co. The from your command line run:

`hf auth login`

Then generate an access token on Huggingface and enter to login. This will allow you to access the Bert-Mini Tokenizer.

## 🔬 Research Questions and Experiments

This module addresses five key research questions from the PP3D paper:

### RQ1: New Attack Instances Detection

**Script:** `train_test/tt_comb.py`

- **Question:** Can PP_det accurately identify new instances of BMAs belonging to previously observed campaigns?
- **Methodology:** Evaluates model performance on new BMA instances from known campaigns

### RQ2: Screen Resolution Generalization

**Script:** `train_test/tt_l1o_res.py`

- **Question:** Can PP_det accurately identify instances of BMAs captured on a new screen size never seen during training?
- **Methodology:** Leave-one-out evaluation where each screen resolution is held out for testing

### RQ3: Unseen Campaign Detection

**Script:** `train_test/tt_l1o_camp.py`

- **Question:** Can PP_det identify web pages belonging to never-before-seen BMA campaigns?
- **Methodology:** Leave-one-out evaluation where each BMA campaign is held out for testing

### RQ4: Temporal Generalization

**Script:** `train_test/tt_comb.py`

- **Question:** Can PP_det accurately identify fresh BMA attacks that were collected well after the training data?
- **Methodology:** Tests model performance on temporally distant attack samples

### RQ5: Adversarial Robustness

**Script:** `train_test/tt_comb_adv.py`

- **Question:** Can PP_det be strengthened against adversarial examples?
- **Methodology:** Adversarial training and evaluation against coordinated multimodal attacks

## 🚀 Quick Start

### Prerequisites

```bash
# Install required packages
pip install torch torchvision transformers
pip install scikit-learn matplotlib numpy pillow
pip install foolbox albumentations opencv-python
```

### Running Experiments

#### 1. Basic Training and Evaluation (RQ1 & RQ4)

```bash
cd train_test/
python tt_comb.py
```

#### 2. Adversarial Robustness (RQ5)

```bash
cd train_test/
python tt_comb_adv.py
```

#### 3. Leave-One-Out Campaign Evaluation (RQ3)

```bash
cd train_test/
python tt_l1o_camp.py
```

#### 4. Leave-One-Out Resolution Evaluation (RQ2)

```bash
cd train_test/
python tt_l1o_res.py
```

### Using Pre-trained Models

To run evaluation with pre-trained models instead of training from scratch:

1. Set `USE_PT_MODEL = True` in the script
2. Update `PT_MODEL_PATH` to point to your model file
3. Run the script

Example:

```python
USE_PT_MODEL = True
PT_MODEL_PATH = "../models/m33_ep4.pth"
```

## ⚙️ Configuration

Each script contains configurable parameters at the top:

### Key Parameters

- `BATCH_SIZE`: Training batch size (default: 64)
- `EPOCHS`: Number of training epochs (varies by script)
- `LEARNING_RATE`: Learning rate for optimization
- `USE_SCHEDULER`: Enable/disable learning rate scheduling
- `LOSS_TYPE`: Loss function ("ce", "weighted_ce", or "focal")
- `DROPOUT_*`: Dropout rates for different components

### Data Paths

Update these paths to match your dataset structure:

- `SE_DIR`: Malicious (BMA) training data
- `BENIGN_DIR`: Benign training data
- `VAL_SE_DIR_LIST`: Malicious validation/test data
- `VAL_BENIGN_DIR_LIST`: Benign validation/test data

## 📊 Model Architecture

PP_det uses a multimodal fusion architecture:

1. **Visual Branch**: MobileNetV3-Small (576-dim features)
2. **Text Branch**: BERT-mini → Linear projection (128-dim features)
3. **Fusion**: Concatenation (704-dim) → MLP classifier

### Input Processing

- **Images**: Resized to 960×540, normalized to [-1,1]
- **Text**: Tokenized with BERT tokenizer (max 512 tokens)
- **OCR**: Tesseract.js extracts text from webpage screenshots

## 🔧 Data Generation Pipeline

The `data_gen/` directory contains scripts for dataset preparation:

### 1. OCR Text Extraction

```bash
python data_gen/ocr_text_gen.py
```

Extracts text from webpage screenshots using OCR.

### 2. Data Sampling

```bash
python data_gen/data_sampler.py
```

Randomly samples fixed numbers of image-text pairs from datasets.

### 3. Data Augmentation

```bash
python data_gen/aug_img_text_pairs.py
```

Applies image transformations and optional text augmentation.

### 4. LLM-based Text Augmentation

```bash
python data_gen/llm_text_aug_groq.py      # Using Groq API
python data_gen/llm_text_aug_oai_adv.py   # Using OpenAI API for adversarial text
```

## 📈 Output and Results

Each experiment generates:

### Directory Structure

```
out/
├── ep_1/                    # Results per epoch
│   ├── eval_1/             # Evaluation split 1
│   │   ├── eval_metrics.txt # Accuracy, precision, recall, F1, AUC, DR@1%FPR
│   │   ├── roc_curve.png   # ROC curve visualization
│   │   ├── y_true.npy      # Ground truth labels
│   │   ├── y_scores.npy    # Prediction scores
│   │   └── vis_conf/       # Confusion matrix samples
│   │       ├── tp/         # True positives
│   │       ├── fp/         # False positives
│   │       ├── tn/         # True negatives
│   │       └── fn/         # False negatives
│   └── eval_2/             # Additional evaluation splits
├── comb_detector_epoch_1.pth    # Model checkpoint
├── training_log.log             # Training logs
└── notes.txt                    # Configuration snapshot
```

### Key Metrics

- **Accuracy**: Overall classification accuracy
- **Precision/Recall/F1**: Per-class performance metrics
- **AUC**: Area under ROC curve
- **DR@1%FPR**: Detection rate at 1% false positive rate

## 🔄 Multi-GPU Training

All scripts support Distributed Data Parallel (DDP) training:

- Automatically detects available GPUs
- Spawns one process per GPU
- Uses NCCL backend for communication
- Rank 0 handles logging and evaluation

## 🛠️ Utilities

### Model Conversion

- `utils/pyt_2_onnx.ipynb`: Convert PyTorch models to ONNX format for browser deployment
- `utils/tok_2_json.ipynb`: Convert tokenizer to JSON format for web deployment

## 📝 Citation

If you use this code, please cite:

```bibtex
@inproceedings{pp3d2025,
  title={PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks},
  author={[Authors]},
  booktitle={Annual Computer Security Applications Conference (ACSAC)},
  year={2025}
}
```

## 🤝 Contributing

1. Follow the existing code structure and documentation style
2. Update configuration parameters as needed for your datasets
3. Ensure all scripts maintain the multimodal architecture design
4. Test with both training from scratch and pre-trained model evaluation

## 📞 Support

For questions about the PP_det module:

1. Check the paper for methodological details
2. Review the script headers for specific research question implementations
3. Examine the configuration parameters for dataset path requirements

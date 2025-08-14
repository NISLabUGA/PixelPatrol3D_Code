""" 
RQ1 & RQ4: Can PP_det accurately identify new instances of BMAs and fresh BMA attacks?

This script addresses Research Questions 1 and 4 from "PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks" 
by training and evaluating a multimodal binary classifier for behavior-manipulation attacks (BMAs) vs. benign samples using Distributed Data Parallel (DDP).

RQ1 evaluates whether PP_det can accurately identify new instances of BMAs belonging to previously observed campaigns, while RQ4 tests 
the model's ability to detect fresh BMA attacks that were collected well after the training data (temporal generalization). Images are 
processed with a MobileNetV3-Small backbone and paired text is encoded with a BERT-mini model; their features are concatenated and fed 
to a small MLP for classification.

The script can be run with a pretrained model for evaluation by setting USE_PT_MODEL=True and providing PT_MODEL_PATH, or can be run 
from scratch by setting USE_PT_MODEL=False. The pipeline includes configurable losses (weighted cross-entropy or focal), optional 
schedulers, early-stopping logic (disabled by default), checkpointing each epoch, and comprehensive evaluation on multiple validation 
sets with metrics, ROC/AUC, a detection-rate-at-1%-FPR readout, and saving example TP/FP/FN/TN cases (image + matched text) for 
qualitative analysis. This evaluation demonstrates the model's ability to generalize to new attack instances and maintain performance 
over time against evolving BMA campaigns.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from torch.utils.data import Dataset, DataLoader
from torch.nn.parallel import DistributedDataParallel as DDP
import torch.distributed as dist
import torch.multiprocessing as mp
from transformers import AutoModel, AutoTokenizer
from PIL import Image
import os
import time
import logging
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, roc_curve, auc
)
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import shutil
import sys


# ---- DDP rendezvous defaults for single-node multi-GPU runs ----
os.environ["MASTER_ADDR"] = "localhost"
os.environ["MASTER_PORT"] = "29500"

# =========================
# ===== CONFIGURATION =====
# =========================
# Image handling and training hyperparameters
TARGET_IMG_SIZE = (1920, 1080)   # Target canvas for zero-padding (before scaling by IMG_SCALE_FACTOR)
IMG_SCALE_FACTOR = 0.5           # Downscale factor applied to the padded canvas (memory/perf trade-off)
BATCH_SIZE = 64
EPOCHS = 15

# Training control toggles
USE_EARLY_STOPPING = False       # Early stopping is implemented but disabled by default
# LEARNING_RATE = 5e-5
LEARNING_RATE = 5e-6
USE_SCHEDULER = False            # Enable/disable LR scheduler globally
SCHEDULER_TYPE = "onecycle"      # "cosine", "onecycle", or "step" (honored only if USE_SCHEDULER=True)
WEIGHT_DECAY = 5e-4
DROPOUT_VIS = 0.3                # Dropout after the visual backbone
DROPOUT_TXT = 0.3                # Dropout before text projection
DROPOUT_FL = 0.6                 # Dropout before fusion MLP
MAX_TOKEN_LENGTH = 512           # Max tokens for BERT tokenizer

# Fine-tuning / freezing strategies for backbones
FREEZE_BACKBONE_VIS = False
FINE_TUNE_LAYERS_VIS = 8         # Kept for logging; not functionally used when FREEZE_BACKBONE_VIS=False
UNFREEZE_AFTER_VIS = 0           # Epoch when last-N layers of visual backbone would be unfrozen (if frozen)

FREEZE_BACKBONE_TEXT = False
FINE_TUNE_LAYERS_TEXT = 3        # Kept for logging; not functionally used when FREEZE_BACKBONE_TEXT=False
UNFREEZE_AFTER_TEXT = 5          # Epoch when last-N transformer layers of BERT would be unfrozen (if frozen)

# Runtime device & tokenizer
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
TOKENIZER = AutoTokenizer.from_pretrained("prajjwal1/bert-mini")
NUM_WORKERS = 20                 # DataLoader workers (tune for your storage/CPU)

# Optional pretrained model inference-only path
USE_PT_MODEL = False
PT_MODEL_PATH = "../models/m33_ep4.pth"

# -------------------------
# Training/validation data
# -------------------------
SE_DIR = "../../pp3d_data/train/malicious/train_19536"
BENIGN_DIR = "../../pp3d_data/train/benign/train_100k"

# Multiple validation splits to evaluate generalization
VAL_SE_DIR_LIST = [
    "../../pp3d_data/test/rq1/malicious/test_500",
    "../../pp3d_data/test/rq4/malicious/test_138"
]

VAL_BENIGN_DIR_LIST = [
    "../../pp3d_data/test/rq1/benign/test_500",
    "../../pp3d_data/test/rq4/benign/test_500"
]

# Control saving of qualitative results by outcome type
SHOW_FP = True
SHOW_FN = True
SHOW_TP = True
SHOW_TN = True

# Output root for logs, checkpoints, metrics, and qualitative samples
OUT_DIR = f"./out/comb"
os.makedirs(OUT_DIR, exist_ok=True)

# -------------------------
# Loss selection & params
# -------------------------
# Options: "ce", "weighted_ce", or "focal"
LOSS_TYPE = "weighted_ce"

# Focal Loss hyperparameters (used only if LOSS_TYPE == "focal")
# Default for Focal Loss
# ALPHA = 0.25
# GAMMA = 2.0

# Tuned/alternative parameters
ALPHA = 0.75
GAMMA = 3.0

# ==========================
# ======= LOGGING ==========
# ==========================
# Set up structured logging to both console and file
log_file = os.path.join(OUT_DIR, "training_log.log")
logging.basicConfig(
    filename=log_file,
    filemode="a",  # Append mode
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

# Helper to mirror logs to stdout for real-time visibility
def log_message(message):
    print(message)  # Print to console
    logging.info(message)  # Save to log file

# Persist a snapshot of key hyperparameters and paths for reproducibility
def save_config(output_dir):
    config_text = f"""
======== Experiment Configuration ========
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Output Directory: {output_dir}

# =========================
# ===== MODEL CONFIG ======
# =========================
TARGET_IMG_SIZE: {TARGET_IMG_SIZE}
IMG_SCALE_FACTOR: {IMG_SCALE_FACTOR}
BATCH_SIZE: {BATCH_SIZE}
EPOCHS: {EPOCHS}
LEARNING_RATE: {LEARNING_RATE}
USE_SCHEDULER: {USE_SCHEDULER}
SCHEDULER_TYPE: {SCHEDULER_TYPE}
WEIGHT_DECAY: {WEIGHT_DECAY}
DROPOUT_VIS: {DROPOUT_VIS}
DROPOUT_TXT: {DROPOUT_TXT}
DROPOUT_FL: {DROPOUT_FL}
MAX_TOKEN_LENGTH: {MAX_TOKEN_LENGTH}

FREEZE_BACKBONE_VIS: {FREEZE_BACKBONE_VIS}
FINE_TUNE_LAYERS_VIS: {FINE_TUNE_LAYERS_VIS}
UNFREEZE_AFTER_VIS: {UNFREEZE_AFTER_VIS}

FREEZE_BACKBONE_TEXT: {FREEZE_BACKBONE_TEXT}
FINE_TUNE_LAYERS_TEXT: {FINE_TUNE_LAYERS_TEXT}
UNFREEZE_AFTER_TEXT: {UNFREEZE_AFTER_TEXT}

# =========================
# ===== LOSS CONFIG =======
# =========================
LOSS_TYPE: {LOSS_TYPE}
ALPHA: {ALPHA}
GAMMA: {GAMMA}

# =========================
# ===== DATA PATHS  =======
# =========================
SE_DIR: {SE_DIR}
BENIGN_DIR: {BENIGN_DIR}
VAL_SE_DIR_LIST: {VAL_SE_DIR_LIST}
VAL_BENIGN_DIR_LIST: {VAL_BENIGN_DIR_LIST}

# =========================
# ===== MISC CONFIG =======
# =========================
NUM_WORKERS: {NUM_WORKERS}
USE_EARLY_STOPPING: {USE_EARLY_STOPPING}
-----------------------------------------------
"""
    notes_path = os.path.join(output_dir, "notes.txt")
    with open(notes_path, "w") as f:
        f.write(config_text.strip())

    log_message(f"Configuration saved to {notes_path}")

# =================================
# ===== TO LOAD PT MODEL ==========
# =================================
# Supports loading either a full nn.Module checkpoint or a state_dict
def load_pretrained_model(model_path: str, device: torch.device):
    obj = torch.load(model_path, map_location=device, weights_only=False)

    if isinstance(obj, nn.Module):          # full model file
        model = obj.to(device)
    else:                                   # state-dict
        model = SEClassifier().to(device)
        model.load_state_dict(obj)

    model.eval()
    return model


# Entry point for evaluation-only runs using a pretrained model
def run_inference_only():

    print("Testing PT model only!")
    save_config(OUT_DIR)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = load_pretrained_model(PT_MODEL_PATH, device)

    # Dummy epoch index 0 (adjust if you care about the folder name)
    evaluate_model(
        model,
        VAL_SE_DIR_LIST,
        VAL_BENIGN_DIR_LIST,
        transform,
        device=device,
        epoch=0,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        results_base_dir=OUT_DIR,
        criterion=nn.CrossEntropyLoss()
    )
    log_message(f"Inference-only run complete using {PT_MODEL_PATH}")
    return

# ==========================
# ===== EARLY STOPPING =====
# ==========================
# Minimal early-stopping utility monitoring either validation or training loss
class EarlyStopping:
    def __init__(self, patience=1, min_delta=0.001, mode="val_loss"):
        assert mode in ["val_loss", "train_loss"], "Invalid mode! Choose 'val_loss' or 'train_loss'."
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_loss = float("inf")
        self.counter = 0

    def check_early_stop(self, loss):
        if loss < self.best_loss - self.min_delta:
            self.best_loss = loss  # Update best loss
            self.counter = 0       # Reset patience counter
        else:
            self.counter += 1

        return self.counter >= self.patience

# =========================
# ===== FOCAL LOSS  =======
# =========================
class FocalLoss(nn.Module):
    """
    Focal Loss for addressing class imbalance:
        alpha (float): Weighting factor for the rare class (balance param).
        gamma (float): Modulating factor to reduce the relative loss for well-classified examples.
        reduction: 'mean' or 'sum'
    """
    def __init__(self, alpha=1.0, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        # Standard cross-entropy per sample
        ce_loss = nn.functional.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)  # Probability of correctly classified sample
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

# =========================
# ===== DATASET CLASS =====
# =========================
class SEDataset(Dataset):
    def __init__(self, se_dir, benign_dir, transform=None, include_metadata=False):
        # Aggregate paired (image, text) paths across SE and benign roots
        self.image_paths = []
        self.text_data = []
        self.labels = []
        self.transform = transform
        self.target_size = TARGET_IMG_SIZE
        self.include_metadata = include_metadata
        
        for category, root_dir in zip(["se", "benign"], [se_dir, benign_dir]):
            label = 1 if category == 'se' else 0
            for dirpath, _, filenames in os.walk(root_dir):
                for filename in filenames:
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        img_path = os.path.join(dirpath, filename)
                        txt_path = os.path.splitext(img_path)[0] + ".txt"
                        
                        if os.path.isfile(txt_path):  # Only include if matching text file exists
                            self.image_paths.append(img_path)
                            self.labels.append(label)
                            with open(txt_path, 'r', encoding='utf-8') as f:
                                self.text_data.append(f.read().strip())
        
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        # Load image and paired text; compute label
        img_path = self.image_paths[idx]
        txt_path = os.path.splitext(img_path)[0] + ".txt"
        label = self.labels[idx]
        text = self.text_data[idx]
        
        image = Image.open(img_path).convert("RGB")
        
        # --- Two-stage resizing/padding pipeline ---
        # 1) Scale the image down (if necessary) to fit safely within TARGET_IMG_SIZE while preserving aspect ratio.
        orig_width, orig_height = image.size
        target_width, target_height = self.target_size
        safe_scale_factor = min(target_width / orig_width, target_height / orig_height)

        if safe_scale_factor < 1.0:
            safe_width = int(orig_width * safe_scale_factor)
            safe_height = int(orig_height * safe_scale_factor)
            safe_image = image.resize((safe_width, safe_height), Image.Resampling.LANCZOS)
        else:
            safe_image = image

        # 2) Downscale both the target canvas and the (already safe) image by IMG_SCALE_FACTOR for compute savings.
        safe_original_size = safe_image.size
        new_target_size = tuple(int(dim * IMG_SCALE_FACTOR) for dim in self.target_size)
        new_og_size = tuple(int(dim * IMG_SCALE_FACTOR) for dim in safe_original_size)
        ds_image = safe_image.resize(new_og_size, Image.Resampling.LANCZOS)
        
        # Center-pad the downscaled image into a black canvas of size new_target_size to maintain spatial consistency.
        padded_image = Image.new("RGB", new_target_size, (0, 0, 0))
        paste_position = ((new_target_size[0] - new_og_size[0]) // 2,
                          (new_target_size[1] - new_og_size[1]) // 2)
        padded_image.paste(ds_image, paste_position)
        
        # Convert to tensor and normalize (if transform provided)
        if self.transform:
            image_tensor = self.transform(padded_image)
        else:
            image_tensor = transforms.ToTensor()(padded_image)
        
        # Tokenize paired text to fixed length for BERT-mini
        tokens = TOKENIZER(
            text, 
            padding='max_length', 
            truncation=True, 
            max_length=MAX_TOKEN_LENGTH, 
            return_tensors='pt'
        )
        label_tensor = torch.tensor(self.labels[idx], dtype=torch.long)

        # Optionally return metadata for qualitative dump (paths + PIL)
        if self.include_metadata:
            return (
                padded_image,                             # for saving mis-classifications
                image_tensor,
                tokens['input_ids'].squeeze(0),
                tokens['attention_mask'].squeeze(0),
                label_tensor,
                txt_path
            )
        else:
            return (
                image_tensor, 
                tokens['input_ids'].squeeze(0), 
                tokens['attention_mask'].squeeze(0), 
                label_tensor
            )
            
# ===========================
# ===== TRANSFORMATIONS =====
# ===========================
# Simple pixel normalization to [-1, 1] range
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# =======================
# ===== MODEL CLASSES ===
# =======================
class VisualCNN(nn.Module):
    def __init__(self, freeze_backbone=FREEZE_BACKBONE_VIS, 
                 fine_tune_layers=FINE_TUNE_LAYERS_VIS, 
                 dropout_rate=DROPOUT_VIS):
        super(VisualCNN, self).__init__()
        # MobileNetV3-Small as visual feature extractor; classifier replaced by Identity
        self.backbone = models.mobilenet_v3_small(pretrained=True)

        if freeze_backbone:
            for param in self.backbone.features.parameters():
                param.requires_grad = False
        
        self.backbone.classifier = nn.Identity()
        self.dropout = nn.Dropout(p=dropout_rate)

    def forward(self, x):
        features = self.backbone(x)
        return self.dropout(features)

class TextBERT(nn.Module):
    def __init__(self, model_name="prajjwal1/bert-mini", 
                 freeze_backbone=FREEZE_BACKBONE_TEXT, 
                 fine_tune_layers=FINE_TUNE_LAYERS_TEXT, 
                 dropout_rate=DROPOUT_TXT):
        super(TextBERT, self).__init__()
        # Lightweight BERT encoder; output pooled embedding projected to 128-D
        self.bert = AutoModel.from_pretrained(model_name)

        # Freeze all layers if freeze_backbone is True
        if freeze_backbone:
            for param in self.bert.parameters():
                param.requires_grad = False

        self.fc = nn.Linear(self.bert.config.hidden_size, 128)
        self.dropout = nn.Dropout(p=dropout_rate)

    def forward(self, input_ids, attention_mask):
        output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        return self.fc(self.dropout(output.pooler_output))

class SEClassifier(nn.Module):
    def __init__(self, 
                 visual_feat_dim=576, 
                 text_feat_dim=128, 
                 num_classes=2, 
                 freeze_backbone_vis=FREEZE_BACKBONE_VIS, 
                 freeze_backbone_text=FREEZE_BACKBONE_TEXT,
                 dropout_rate = DROPOUT_FL):
        super(SEClassifier, self).__init__()
        # Independent backbones for image and text; features concatenated for fusion MLP
        self.visual_cnn = VisualCNN(freeze_backbone=freeze_backbone_vis)
        self.text_bert = TextBERT(freeze_backbone=freeze_backbone_text)

        self.dropout = nn.Dropout(p=dropout_rate)
        self.fc = nn.Sequential(
            nn.Linear(visual_feat_dim + text_feat_dim, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes)
        )

    def forward(self, image, input_ids, attention_mask):
        visual_features = self.visual_cnn(image)
        text_features = self.text_bert(input_ids, attention_mask)
        combined = torch.cat((visual_features, text_features), dim=1)
        combined = self.dropout(combined)
        return self.fc(combined)

# ==================================================
# ===== MODEL EVALUATION    ========================
# ==================================================

# Custom collate to carry PIL images and file paths for qualitative dumps
def custom_collate(batch):
    pil_images = [item[0] for item in batch]
    image_tensors = torch.stack([item[1] for item in batch], dim=0)
    input_ids = torch.stack([item[2] for item in batch], dim=0)
    attention_masks = torch.stack([item[3] for item in batch], dim=0)
    labels = torch.stack([item[4] for item in batch], dim=0)
    text_file_paths = [item[5] for item in batch]
    return pil_images, image_tensors, input_ids, attention_masks, labels, text_file_paths

# Runs evaluation on each (SE_dir, benign_dir) pair; writes metrics, ROC, arrays, and qualitative samples
def evaluate_model(model, se_dirs, benign_dirs,
                   transform, device, epoch,
                   batch_size, num_workers,
                   results_base_dir, criterion):

    model.eval()

    avg_test_loss_list = []

    for idx, (se_dir, benign_dir) in enumerate(zip(se_dirs, benign_dirs), start=1):

        results_dir = os.path.join(results_base_dir, f"ep_{epoch+1}", f"eval_{idx}")
        vis_conf_dir = os.path.join(results_dir, "vis_conf")
        for subfolder in ["tn", "fp", "fn", "tp"]:
            os.makedirs(os.path.join(vis_conf_dir, subfolder), exist_ok=True)

        # build a test loader
        test_dataset = SEDataset(se_dir, benign_dir, transform=transform, include_metadata=True)
        test_loader = DataLoader(test_dataset,
                                batch_size=BATCH_SIZE,
                                shuffle=False,
                                collate_fn=custom_collate,
                                num_workers=NUM_WORKERS,
                                pin_memory=True)

        all_preds, all_labels, all_probs = [], [], []
        start_time = time.time()

        total_test_loss = 0.0

        with torch.no_grad():
            for batch_idx, (pil_images, image_tensors, input_ids, attention_masks, labels, text_file_paths) in enumerate(test_loader):
                
                image_tensors = image_tensors.to(device, non_blocking=True)
                input_ids = input_ids.to(device, non_blocking=True)
                attention_masks = attention_masks.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)

                outputs = model(image_tensors, input_ids, attention_masks)
                loss = criterion(outputs, labels)
                total_test_loss += loss.item()
                probs = torch.softmax(outputs, dim=1)[:, 1]
                preds = outputs.argmax(dim=1)

                all_preds.extend(preds.cpu().numpy().tolist())
                all_labels.extend(labels.cpu().numpy().tolist())
                all_probs.extend(probs.cpu().numpy().tolist())

                # Save qualitative examples into tn/fp/fn/tp folders with paired text copies
                for i, pil_img in enumerate(pil_images):
                    pred_label = preds[i].item()
                    true_label = labels[i].item()
                    text_file_path = text_file_paths[i]

                    outcome_folder = ("tn" if true_label == 0 and pred_label == 0 else
                                    "fp" if true_label == 0 and pred_label == 1 else
                                    "fn" if true_label == 1 and pred_label == 0 else
                                    "tp")

                    save_base = f"batch{batch_idx}_idx{i}_pred{pred_label}_true{true_label}"
                    vis_img_path = os.path.join(vis_conf_dir, outcome_folder, f"{save_base}.jpg")
                    vis_txt_path = os.path.join(vis_conf_dir, outcome_folder, f"{save_base}.txt")                    

                    if outcome_folder == "fp" and SHOW_FP:
                        pil_img.save(vis_img_path)
                        if os.path.exists(text_file_path):
                            shutil.copy(text_file_path, vis_txt_path)
                    if outcome_folder == "fn" and SHOW_FN:
                        pil_img.save(vis_img_path)
                        if os.path.exists(text_file_path):
                            shutil.copy(text_file_path, vis_txt_path)
                    if outcome_folder == "tp" and SHOW_TP:
                        pil_img.save(vis_img_path)
                        if os.path.exists(text_file_path):
                            shutil.copy(text_file_path, vis_txt_path)
                    if outcome_folder == "tn" and SHOW_TN:
                        pil_img.save(vis_img_path)
                        if os.path.exists(text_file_path):
                            shutil.copy(text_file_path, vis_txt_path)

                print(f"Processed batch {batch_idx}/{len(test_loader)}")

        total_time = time.time() - start_time
        print(f"Testing complete. Total inference time: {total_time:.2f} seconds.")

        # --- compute metrics ---
        all_preds = np.array(all_preds)
        all_labels = np.array(all_labels)
        accuracy = accuracy_score(all_labels, all_preds)
        precision = precision_score(all_labels, all_preds, zero_division=0)
        recall = recall_score(all_labels, all_preds, zero_division=0)
        f1 = f1_score(all_labels, all_preds, zero_division=0)
        avg_test_loss = total_test_loss / len(test_loader)
        avg_test_loss_list.append(avg_test_loss)

        cm = confusion_matrix(all_labels, all_preds)
        if cm.shape == (2, 2):
            TN, FP, FN, TP = cm.ravel()
        else:
            TN = FP = FN = TP = 0

        # write metrics file
        metrics_path = os.path.join(results_dir, "eval_metrics.txt")
        with open(metrics_path, "w") as f:
            f.write("Evaluation Metrics:\n")
            f.write("-------------------\n")
            f.write(f"Accuracy:    {accuracy:.4f}\n")
            f.write("Confusion Matrix:\n")
            f.write(f"{cm}\n")
            f.write(f"True Negatives (TN): {TN}\n")
            f.write(f"False Positives (FP): {FP}\n")
            f.write(f"False Negatives (FN): {FN}\n")
            f.write(f"True Positives (TP): {TP}\n")
            f.write(f"Precision:   {precision:.4f}\n")
            f.write(f"Recall:      {recall:.4f}\n")
            f.write(f"F1 Score:    {f1:.4f}\n")

        # ROC & AUC
        fpr, tpr, _ = roc_curve(all_labels, all_probs)
        roc_auc = auc(fpr, tpr)
        with open(metrics_path, "a") as f:
            f.write(f"AUC Score (ROC AUC): {roc_auc:.4f}\n")

        # save ROC plot
        roc_path = os.path.join(results_dir, "roc_curve.png")
        plt.figure()
        plt.plot(fpr, tpr, lw=2, label=f'ROC (AUC={roc_auc:.3f})')
        plt.plot([0,1],[0,1], lw=2, linestyle='--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend(loc="lower right")
        plt.savefig(roc_path)
        plt.close()

        # detection rate @1% FPR (locates first threshold at/above 1% FPR)
        target_fpr = 0.01
        idx_fpr = np.where(fpr >= target_fpr)[0][0]
        dr1 = tpr[idx_fpr]
        with open(metrics_path, "a") as f:
            f.write(f"Detection Rate @ 1% FPR: {dr1:.4f}\n")

        # save raw arrays for post-hoc analysis
        np.save(os.path.join(results_dir, "y_true.npy"), all_labels)
        np.save(os.path.join(results_dir, "y_scores.npy"), all_probs)

        print(f"Metrics saved to {metrics_path}")
        print(f"ROC curve saved to {roc_path}")
        print(f"Finished run {idx}. Results in {results_dir}\n")
    
    return avg_test_loss_list

# ==================================================
# ===== MAIN TRAINING FUNCTION (WITH DDP)    =======
# ==================================================
def train(rank, 
          world_size, 
          patience=2, 
          early_stop_mode="val_loss", 
          unfreeze_after_vis=UNFREEZE_AFTER_VIS, 
          fine_tune_layers_vis=FINE_TUNE_LAYERS_VIS,
          unfreeze_after_text=UNFREEZE_AFTER_TEXT,  
          fine_tune_layers_text=FINE_TUNE_LAYERS_TEXT):
    """
    DDP training entrypoint for each process/GPU:
      - Builds dataset/dataloader with class-weight computation
      - Initializes multimodal model and wraps with DDP
      - Selects loss (weighted CE or focal) and optimizer
      - Optionally configures LR scheduler
      - Supports staged unfreezing of backbones if requested
      - Runs training loop with per-batch logs and per-epoch validation on rank 0
      - Saves checkpoints and can trigger early stopping (if enabled)
    """
    
    # Initialize the process group for distributed training (NCCL backend for GPUs)
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

    if rank == 0:
        save_config(OUT_DIR)
    
    # Create datasets
    train_dataset = SEDataset(SE_DIR, BENIGN_DIR, transform=transform, include_metadata=False)

    # Compute class weights for Weighted CE (we'll only use them if LOSS_TYPE == "weighted_ce")
    labels = train_dataset.labels
    classes = np.unique(labels)
    class_weights_np = compute_class_weight(
        class_weight='balanced', 
        classes=classes, 
        y=labels
    )
    class_weights = torch.tensor(class_weights_np, dtype=torch.float).to(rank)
    
    # Distributed sampler ensures each rank sees a unique shard each epoch
    train_sampler = torch.utils.data.distributed.DistributedSampler(
        train_dataset, 
        num_replicas=world_size, 
        rank=rank
    )

    train_loader = DataLoader(
        train_dataset, 
        batch_size=BATCH_SIZE, 
        sampler=train_sampler, 
        num_workers=NUM_WORKERS, 
        pin_memory=True
    )
    
    # Initialize model and wrap with DDP
    model = SEClassifier(
        freeze_backbone_vis=FREEZE_BACKBONE_VIS, 
        freeze_backbone_text=FREEZE_BACKBONE_TEXT
    ).to(rank)
    model = DDP(model, device_ids=[rank])

    # Choose loss function based on LOSS_TYPE
    if LOSS_TYPE == "weighted_ce":
        criterion = nn.CrossEntropyLoss(weight=class_weights)
        log_message(f"[Rank {rank}] Using Weighted Cross Entropy with class weights: {class_weights_np}")
    elif LOSS_TYPE == "focal":
        criterion = FocalLoss(alpha=ALPHA, gamma=GAMMA, reduction='mean')
        log_message(f"[Rank {rank}] Using Focal Loss with alpha={ALPHA}, gamma={GAMMA}")
    else:
        criterion = nn.CrossEntropyLoss()  # fallback
        log_message(f"[Rank {rank}] Using standard CrossEntropyLoss (fallback).")

    # Optimizer over trainable params only (handles staged unfreezing)
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()), 
        lr=LEARNING_RATE, 
        weight_decay=WEIGHT_DECAY
    )

    # Scheduler (optional)
    if USE_SCHEDULER:
        if SCHEDULER_TYPE == "cosine":
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=EPOCHS, eta_min=1e-7
            )
        elif SCHEDULER_TYPE == "onecycle":
            scheduler = torch.optim.lr_scheduler.OneCycleLR(
                optimizer,
                max_lr=LEARNING_RATE * 10,
                steps_per_epoch=len(train_loader),
                epochs=EPOCHS
            )
        elif SCHEDULER_TYPE == "step":
            scheduler = torch.optim.lr_scheduler.StepLR(
                optimizer, step_size=3, gamma=0.5
            )
        else:
            scheduler = None
    else:
        scheduler = None

    # Early stopping wrapper (inactive unless USE_EARLY_STOPPING=True)
    early_stopper = EarlyStopping(patience=patience, mode=early_stop_mode)
    
    for epoch in range(EPOCHS):
        train_sampler.set_epoch(epoch)  # shuffle shard deterministically per epoch
        total_train_loss = 0.0
        epoch_start_time = time.time()

        log_message(f"[Rank {rank}] Epoch {epoch+1}/{EPOCHS} - Training Started")

        current_lr = optimizer.param_groups[0]['lr']
        log_message(f"[Rank {rank}] Current Learning Rate: {current_lr:.8f}")

        # Unfreeze logic for visual backbone (if initially frozen)
        if epoch == unfreeze_after_vis and FREEZE_BACKBONE_VIS:
            log_message(f"[Rank {rank}] Unfreezing last {fine_tune_layers_vis} layers of MobileNetV3 for fine-tuning")
            for param in list(model.module.visual_cnn.backbone.features.parameters())[-fine_tune_layers_vis:]:
                param.requires_grad = True
        
        # Unfreeze logic for text backbone (if initially frozen)
        if epoch == unfreeze_after_text and FREEZE_BACKBONE_TEXT:
            log_message(f"[Rank {rank}] Unfreezing last {fine_tune_layers_text} layers of BERT-MINI for fine-tuning")
            for param in list(model.module.text_bert.bert.encoder.layer.parameters())[-fine_tune_layers_text:]:
                param.requires_grad = True

            # Re-initialize optimizer so newly unfrozen params get learning updates
            optimizer = optim.AdamW(
                filter(lambda p: p.requires_grad, model.parameters()), 
                lr=LEARNING_RATE, 
                weight_decay=WEIGHT_DECAY
            )
        
        # -----------------
        # Training loop
        # -----------------
        model.train()
        for batch_idx, (images, input_ids, attention_mask, labels_batch) in enumerate(train_loader):
            batch_start_time = time.time()

            images = images.to(rank, non_blocking=True)
            input_ids = input_ids.to(rank, non_blocking=True)
            attention_mask = attention_mask.to(rank, non_blocking=True)
            labels_batch = labels_batch.to(rank, non_blocking=True)

            optimizer.zero_grad()
            outputs = model(images, input_ids, attention_mask)
            loss = criterion(outputs, labels_batch)
            loss.backward()
            optimizer.step()

            # OneCycle schedules step per iteration
            if USE_SCHEDULER and SCHEDULER_TYPE == "onecycle":
                scheduler.step()
                current_lr = scheduler.get_last_lr()[0]
                log_message(
                    f"[Rank {rank}] Epoch {epoch+1}, Batch {batch_idx+1}/{len(train_loader)} - LR: {current_lr:.8f}"
                )

            total_train_loss += loss.item()

            batch_time = time.time() - batch_start_time
            log_message(
                f"[Rank {rank}] Epoch {epoch+1}, Batch {batch_idx+1}/{len(train_loader)}, "
                f"Loss: {loss.item():.4f}, Time: {batch_time:.2f}s"
            )
        
        epoch_time = time.time() - epoch_start_time
        avg_train_loss = total_train_loss / len(train_loader)
        log_message(f"[Rank {rank}] Epoch {epoch+1} Completed - "
                    f"Avg Training Loss: {avg_train_loss:.4f}, Epoch Time: {epoch_time:.2f}s")

        # -----------------
        # Validation (rank 0 only): metrics + qualitative saves + checkpoints + early stopping
        # -----------------
        if rank == 0:
            avg_test_loss_list = evaluate_model(
                model.module,
                VAL_SE_DIR_LIST,
                VAL_BENIGN_DIR_LIST,
                transform,
                device=rank,
                epoch=epoch,
                batch_size=BATCH_SIZE,
                num_workers=NUM_WORKERS,
                results_base_dir=OUT_DIR,
                criterion=criterion
            )
            log_message("All evaluations complete.")

            # Choose monitored metric based on mode
            monitored_loss = avg_test_loss_list[1] if early_stop_mode == "val_loss" else avg_train_loss

            # Save model checkpoint (full module and state_dict)
            checkpoint_path = os.path.join(OUT_DIR, f"comb_detector_epoch_{epoch+1}.pth")
            torch.save(model.module, checkpoint_path)
            torch.save(model.module.state_dict(), checkpoint_path + ".sd")
            log_message(f"[Rank {rank}] Model checkpoint saved: {checkpoint_path}")

            if USE_EARLY_STOPPING and early_stopper.check_early_stop(monitored_loss):
                log_message(f"[Rank {rank}] Early stopping triggered! "
                            f"Best {early_stop_mode}: {early_stopper.best_loss:.4f}")
                break

            model.train()

        # Epoch-wise scheduler steps for cosine/step variants
        if USE_SCHEDULER and SCHEDULER_TYPE in ["cosine", "step"]:
            scheduler.step()
            log_message(f"[Rank {rank}] Scheduler stepped. New LR: {scheduler.get_last_lr()}")

    if rank == 0:
        log_message("Training Complete.")

    # Cleanly tear down the DDP process group
    dist.destroy_process_group()

# ============================
# ===== MAIN EXECUTION  ======
# ============================
if __name__ == "__main__":
    # Optional evaluation-only flow using a saved model
    if USE_PT_MODEL and PT_MODEL_PATH:
        run_inference_only()
        sys.exit(0) 
    
    # ----- normal DDP training -----
    world_size = torch.cuda.device_count()  # Spawns one process per visible GPU
    mp.spawn(train, args=(world_size, ), nprocs=world_size, join=True)

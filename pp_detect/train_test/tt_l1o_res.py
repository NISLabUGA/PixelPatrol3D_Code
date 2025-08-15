"""
RQ2: Can PP_det accurately identify instances of BMAs captured on a new screen size never seen during training?

This script addresses Research Question 2 from "PP3D: An In-Browser Vision-Based Defense Against Web Behavior Manipulation Attacks" 
by implementing a leave-one-out evaluation methodology to test the model's ability to generalize to completely unseen screen resolutions.

The script provides an end-to-end PyTorch training and evaluation pipeline for a multimodal classifier that fuses visual (MobileNetV3) 
and text (BERT-mini) features. In each leave-one-out cycle, one screen resolution is held out from training and used exclusively for 
testing, ensuring that the model has never seen any examples rendered at that specific resolution during training. This rigorous 
evaluation tests whether PP_det can accurately identify BMA instances captured on new screen sizes never seen during training, 
demonstrating the model's resolution-agnostic capabilities.

The script can be run with pretrained models for evaluation by setting USE_PT_MODEL=True and providing PT_MODEL_PATHS, or can be run 
from scratch by setting USE_PT_MODEL=False. It supports multi-GPU Distributed Data Parallel training, optional fine-tuning and staged 
unfreezing, focal/weighted CE loss for class imbalance, and per-epoch validation with rich metrics (accuracy, precision, recall, F1, 
ROC/AUC, DR@1%FPR). The pipeline iterates over multiple leave-one-out style cycles on disk, saves artifacts (checkpoints, ROC plots, 
confusion folders), and logs progress. This evaluation demonstrates the model's ability to maintain high detection performance across 
diverse screen resolutions and device form factors without requiring resolution-specific training.
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
import random

# Configure default rendezvous for torch.distributed (single-node, localhost RDV)
os.environ["MASTER_ADDR"] = "localhost"
os.environ["MASTER_PORT"] = "29500"

# =========================
# ===== CONFIGURATION =====
# =========================
# Image handling
TARGET_IMG_SIZE = (1920, 1080)   # logical canvas used for padding before transforms
IMG_SCALE_FACTOR = 0.5           # scale down target canvas for compute efficiency

# Training hyperparameters
BATCH_SIZE = 64
EPOCHS = 10
MAX_BENIGN_TEST_SAMPLES = 500    # cap benign test samples per eval to control runtime
SEED = 123

USE_EARLY_STOPPING = False       # global toggle for early stopping in main loop
# LEARNING_RATE = 5e-5
LEARNING_RATE = 2e-6             # conservative LR (text+vision often needs small LR)
USE_SCHEDULER = False            # set True to enable LR schedulers below
SCHEDULER_TYPE = "onecycle"      # "cosine", "onecycle", or "step"
WEIGHT_DECAY = 5e-4

# Dropout rates for different submodules
DROPOUT_VIS = 0.3
DROPOUT_TXT = 0.3
DROPOUT_FL = 0.6                  # fusion head dropout

# Text tokenization
MAX_TOKEN_LENGTH = 512

# Backbone freezing / staged unfreezing knobs
FREEZE_BACKBONE_VIS = False
FINE_TUNE_LAYERS_VIS = 8          # how many final layers to unfreeze when scheduled
UNFREEZE_AFTER_VIS = 0            # epoch index to begin unfreezing visual layers

FREEZE_BACKBONE_TEXT = False
FINE_TUNE_LAYERS_TEXT = 3         # how many final Transformer blocks to unfreeze
UNFREEZE_AFTER_TEXT = 0           # epoch index to begin unfreezing text layers

# Device / tokenizer / workers
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
TOKENIZER = AutoTokenizer.from_pretrained("prajjwal1/bert-mini")
NUM_WORKERS = 20                  # dataloader workers (tune per filesystem/CPU)

# Optional: evaluate pre-trained checkpoints instead of training
USE_PT_MODEL = False
PT_MODEL_PATHS = [
    '/path/to/out_l1o_res/1.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/2.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/3.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/4.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/5.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/6.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/7.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/8.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/9.mclus_excluded/model.pth',
    '/path/to/out_l1o_res/10.mclus_excluded/model.pth'
]

# Dataset roots and multi-cycle orchestration
ROOT_DIR = "../../pp3d_data/l1o/rq2/l1o_res/"   # cycles live here (1.mclus_excluded, ...)
BENIGN_TRAIN = "../../pp3d_data/train/benign/train_100k"
OUT_BASE = "./out/l1o_res"                        # per-cycle output root
WORLD_SIZE = torch.cuda.device_count()             # DDP world size = number of GPUs

# Collect cycle directories in sorted order for deterministic iteration
cycle_dirs = sorted([
    os.path.join(ROOT_DIR, d)
    for d in os.listdir(ROOT_DIR)
    if os.path.isdir(os.path.join(ROOT_DIR, d))
])

# Control what misclassified examples get saved out as images+texts
SHOW_FP = True
SHOW_FN = True
SHOW_TP = False
SHOW_TN = False

# Loss selection: standard CE, class-weighted CE, or Focal Loss
LOSS_TYPE = "weighted_ce"

# Focal Loss hyperparameters (if enabled)
# ALPHA = 0.25
# GAMMA = 2.0
# Tuned values for stronger down-weighting of easy examples / up-weighting rare class
ALPHA = 0.75
GAMMA = 3.0


def save_config(cycle_out_dir, se_train_dir, benign_train_dir, se_test_dir, benign_test_dir):
    """Dump the run configuration and paths to a notes.txt file under the cycle directory."""
    config_text = f"""
======== Experiment Configuration ========
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Output Directory: {cycle_out_dir}

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
se_train_dir, benign_train_dir, se_test_dir, benign_test_dir
SE train:   {se_train_dir}
BEN train:  {benign_train_dir}
SE test:    {se_test_dir}
BEN test:   {benign_test_dir}

# =========================
# ===== MISC CONFIG =======
# =========================
NUM_WORKERS: {NUM_WORKERS}
USE_EARLY_STOPPING: {USE_EARLY_STOPPING}
-----------------------------------------------
    """
    notes_path = os.path.join(cycle_out_dir, "notes.txt")
    with open(notes_path, "w") as f:
        f.write(config_text.strip())

# ----------  Resolution helpers  ----------
# Extract trailing WxH token from filename stems (e.g., "..._1920x1080") for filtering

def extract_resolution_from_filename(fname: str) -> str | None:
    stem = os.path.splitext(os.path.basename(fname))[0]
    res_part = stem.rsplit("_", 1)[-1]
    return res_part if "x" in res_part else None


# Enumerate subdirectories inside SE test directory as known resolutions to exclude in benign

def get_resolutions_from_se_test(se_test_dir: str) -> set[str]:
    return {
        d for d in os.listdir(se_test_dir)
        if os.path.isdir(os.path.join(se_test_dir, d))
    }


# ==========================
# ===== EARLY STOPPING =====
# ==========================
class EarlyStopping:
    """Simple early stopping on a monitored loss with patience and min_delta."""
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
        # Per-sample CE; then reweight by (1-pt)^gamma and alpha
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
    """Custom dataset that pairs images with adjacent .txt files and labels.

    - se_dir: root with malicious image+text pairs (label=1)
    - benign_dir: root with benign image+text pairs (label=0)
    - exclude_resolutions: drop benign samples whose filename suffix matches SE test resolutions
    - include_metadata: when True, returns PIL image and source text path for visualization/copying
    - max_benign_samples: optional random downsample for benign class (reproducible via seed)
    """
    def __init__(
        self, 
        se_dir, 
        benign_dir, 
        transform=None, 
        include_metadata=False, 
        max_benign_samples: int = None, 
        seed: int = None,
        exclude_resolutions: set[str] | None = None
    ):

        self.image_paths = []
        self.text_data = []
        self.labels = []
        self.transform = transform
        self.target_size = TARGET_IMG_SIZE
        self.include_metadata = include_metadata

        # collect SE and benign pairs
        se_pairs, ben_pairs = [], []

        # ---------- SE ----------
        for dirpath, _, filenames in os.walk(se_dir):
            for fn in filenames:
                if fn.lower().endswith((".png", ".jpg", ".jpeg")):
                    img_p = os.path.join(dirpath, fn)
                    txt_p = os.path.splitext(img_p)[0] + ".txt"
                    if os.path.isfile(txt_p):
                        se_pairs.append((img_p, txt_p, 1))

        # ---------- BENIGN ----------
        for dirpath, _, filenames in os.walk(benign_dir):
            for fn in filenames:
                if fn.lower().endswith((".png", ".jpg", ".jpeg")):
                    # --- NEW FILTER ---
                    res = extract_resolution_from_filename(fn)
                    if exclude_resolutions and res in exclude_resolutions:
                        continue          # skip this benign pair
                    # --------------------------------------------
                    img_p = os.path.join(dirpath, fn)
                    txt_p = os.path.splitext(img_p)[0] + ".txt"
                    if os.path.isfile(txt_p):
                        ben_pairs.append((img_p, txt_p, 0))

        # subsample benign if over limit
        if max_benign_samples is not None and len(ben_pairs) > max_benign_samples:
            if seed is not None:
                random.seed(seed)
            ben_pairs = random.sample(ben_pairs, max_benign_samples)

        # merge into final lists
        for img_path, txt_path, label in se_pairs + ben_pairs:
            self.image_paths.append(img_path)
            self.labels.append(label)
            with open(txt_path, 'r', encoding='utf-8') as f:
                self.text_data.append(f.read().strip())
        
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        # Load paired data
        img_path = self.image_paths[idx]
        txt_path = os.path.splitext(img_path)[0] + ".txt"
        label = self.labels[idx]
        text = self.text_data[idx]
        
        image = Image.open(img_path).convert("RGB")
        
        # Two-stage resizing: safe downscale to fit target, then global downscale for compute
        orig_width, orig_height = image.size
        target_width, target_height = self.target_size

        # First scale to make sure image is not larger than target
        safe_scale_factor = min(target_width / orig_width, target_height / orig_height)

        if safe_scale_factor < 1.0:
            safe_width = int(orig_width * safe_scale_factor)
            safe_height = int(orig_height * safe_scale_factor)
            safe_image = image.resize((safe_width, safe_height), Image.Resampling.LANCZOS)
        else:
            safe_image = image

        # Second scale to downsize image for processing
        safe_original_size = safe_image.size
        new_target_size = tuple(int(dim * IMG_SCALE_FACTOR) for dim in self.target_size)
        new_og_size = tuple(int(dim * IMG_SCALE_FACTOR) for dim in safe_original_size)
        ds_image = safe_image.resize(new_og_size, Image.Resampling.LANCZOS)
        
        # Create a new (padded) image of target size and paste the resized image centered.
        padded_image = Image.new("RGB", new_target_size, (0, 0, 0))
        paste_position = ((new_target_size[0] - new_og_size[0]) // 2,
                          (new_target_size[1] - new_og_size[1]) // 2)
        padded_image.paste(ds_image, paste_position)
        
        # For model inference, apply the transformation to get a tensor.
        if self.transform:
            image_tensor = self.transform(padded_image)
        else:
            image_tensor = transforms.ToTensor()(padded_image)
        
        # Tokenize paired text
        tokens = TOKENIZER(
            text, 
            padding='max_length', 
            truncation=True, 
            max_length=MAX_TOKEN_LENGTH, 
            return_tensors='pt'
        )
        label_tensor = torch.tensor(self.labels[idx], dtype=torch.long)

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
# Simple tensor+normalize; images were already padded/centered above
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# =======================
# ===== MODEL CLASSES ===
# =======================
class VisualCNN(nn.Module):
    """Visual backbone using torchvision MobileNetV3-Small with optional freezing."""
    def __init__(self, freeze_backbone=FREEZE_BACKBONE_VIS, 
                 fine_tune_layers=FINE_TUNE_LAYERS_VIS, 
                 dropout_rate=DROPOUT_VIS):
        super(VisualCNN, self).__init__()
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
    """Text backbone using HuggingFace BERT-mini; outputs a 128-dim projection."""
    def __init__(self, model_name="prajjwal1/bert-mini", 
                 freeze_backbone=FREEZE_BACKBONE_TEXT, 
                 fine_tune_layers=FINE_TUNE_LAYERS_TEXT, 
                 dropout_rate=DROPOUT_TXT):
        super(TextBERT, self).__init__()
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
    """Fusion head that concatenates visual and text features, then classifies."""
    def __init__(self, 
                 visual_feat_dim=576, 
                 text_feat_dim=128, 
                 num_classes=2, 
                 freeze_backbone_vis=FREEZE_BACKBONE_VIS, 
                 freeze_backbone_text=FREEZE_BACKBONE_TEXT,
                 dropout_rate = DROPOUT_FL):
        super(SEClassifier, self).__init__()
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

# Collate that preserves PIL images and source text paths for visualization

def custom_collate(batch):
    pil_images = [item[0] for item in batch]
    image_tensors = torch.stack([item[1] for item in batch], dim=0)
    input_ids = torch.stack([item[2] for item in batch], dim=0)
    attention_masks = torch.stack([item[3] for item in batch], dim=0)
    labels = torch.stack([item[4] for item in batch], dim=0)
    text_file_paths = [item[5] for item in batch]
    return pil_images, image_tensors, input_ids, attention_masks, labels, text_file_paths


def evaluate_model(model, se_dirs, benign_dirs,
                   transform, device, epoch,
                   batch_size, num_workers,
                   results_base_dir, criterion):
    """Evaluate a trained model on provided SE/benign directories and emit metrics/artifacts.

    - Saves confusion buckets (tn/fp/fn/tp) with image+text samples based on SHOW_* toggles
    - Writes metrics to eval_metrics.txt and plots ROC curve
    - Returns list of average test losses (one per provided eval set)
    """

    model.eval()

    avg_test_loss_list = []

    for idx, (se_dir, benign_dir) in enumerate(zip(se_dirs, benign_dirs), start=1):

        results_dir = os.path.join(results_base_dir, f"ep_{epoch+1}", f"eval_{idx}")
        vis_conf_dir = os.path.join(results_dir, "vis_conf")
        for subfolder in ["tn", "fp", "fn", "tp"]:
            os.makedirs(os.path.join(vis_conf_dir, subfolder), exist_ok=True)

        # build a test loader
        test_dataset = SEDataset(se_dir,
                                benign_dir,
                                transform=transform,
                                include_metadata=True,
                                max_benign_samples=MAX_BENIGN_TEST_SAMPLES,
                                seed=SEED)
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

                # Save visual confusion examples based on configured toggles
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

        # detection rate @1% FPR
        target_fpr = 0.01
        idx_fpr = np.where(fpr >= target_fpr)[0][0]
        dr1 = tpr[idx_fpr]
        with open(metrics_path, "a") as f:
            f.write(f"Detection Rate @ 1% FPR: {dr1:.4f}\n")

        # save raw arrays
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
          se_train_dir,
          benign_train_dir,
          se_test_dir,
          benign_test_dir,
          cycle_out_dir,
          exclude_resolutions,
          pt_model_path=None,
          patience=2,
          early_stop_mode="val_loss",
          unfreeze_after_vis=UNFREEZE_AFTER_VIS,
          fine_tune_layers_vis=FINE_TUNE_LAYERS_VIS,
          unfreeze_after_text=UNFREEZE_AFTER_TEXT,
          fine_tune_layers_text=FINE_TUNE_LAYERS_TEXT
          ):
    
    # Initialize the process group for distributed training
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

    # Only rank 0 sets up output dirs and logging
    if rank == 0:
        os.makedirs(cycle_out_dir, exist_ok=True)
        save_config(cycle_out_dir, se_train_dir, benign_train_dir, se_test_dir, benign_test_dir)

        # Set up logging
        log_file = os.path.join(cycle_out_dir, "training_log.log")
        logging.basicConfig(
            filename=log_file,
            filemode="a",  # Append mode
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.INFO
        )

        # Create a logging function
        def log_message(message):
            print(message)  # Print to console
            logging.info(message)  # Save to log file

    # Create datasets
    train_dataset = SEDataset(se_train_dir, benign_train_dir, transform=transform, exclude_resolutions=exclude_resolutions)

    if rank == 0:
        num_benign = sum(1 for l in train_dataset.labels if l == 0)
        num_se     = sum(1 for l in train_dataset.labels if l == 1)
        log_message(f"[Rank {rank}] Benign examples after resolution exclusion: {num_benign}")
        log_message(f"[Rank {rank}] Malicious examples: {num_se}")

    # Compute class weights for Weighted CE (we'll only use them if LOSS_TYPE == "weighted_ce")
    labels = train_dataset.labels
    classes = np.unique(labels)
    class_weights_np = compute_class_weight(
        class_weight='balanced', 
        classes=classes, 
        y=labels
    )
    class_weights = torch.tensor(class_weights_np, dtype=torch.float).to(rank)
    
    # Create samplers/loaders
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
    
    # Initialize model
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

    # Optimizer
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

    # If requested, load pretrained weights and skip training
    if USE_PT_MODEL and pt_model_path:
        if rank == 0:
            log_message(f"[Rank {rank}] Loading pretrained model from {pt_model_path}")
        # assume .pth is a state_dict
        model = torch.load(pt_model_path, map_location=DEVICE, weights_only=False)
        model.eval()
        if rank == 0:
            evaluate_model(
                model,
                [se_test_dir],
                [benign_test_dir],
                transform,
                device=rank,
                epoch=0,
                batch_size=BATCH_SIZE,
                num_workers=NUM_WORKERS,
                results_base_dir=cycle_out_dir,
                criterion=criterion
            )
            log_message("Evaluation complete using pretrained model.")
        dist.destroy_process_group()
        return
  

    # Early stopping
    early_stopper = EarlyStopping(patience=patience, mode=early_stop_mode)
    
    for epoch in range(EPOCHS):
        train_sampler.set_epoch(epoch)
        total_train_loss = 0.0
        epoch_start_time = time.time()

        log_message(f"[Rank {rank}] Epoch {epoch+1}/{EPOCHS} - Training Started")

        current_lr = optimizer.param_groups[0]['lr']
        log_message(f"[Rank {rank}] Current Learning Rate: {current_lr:.8f}")

        # Unfreeze logic for visual backbone
        if epoch == unfreeze_after_vis and FREEZE_BACKBONE_VIS:
            log_message(f"[Rank {rank}] Unfreezing last {fine_tune_layers_vis} layers of MobileNetV3 for fine-tuning")
            for param in list(model.module.visual_cnn.backbone.features.parameters())[-fine_tune_layers_vis:]:
                param.requires_grad = True
        
        # Unfreeze logic for text backbone
        if epoch == unfreeze_after_text and FREEZE_BACKBONE_TEXT:
            log_message(f"[Rank {rank}] Unfreezing last {fine_tune_layers_text} layers of BERT-MINI for fine-tuning")
            for param in list(model.module.text_bert.bert.encoder.layer.parameters())[-fine_tune_layers_text:]:
                param.requires_grad = True

            # Re-initialize optimizer if newly unfrozen
            optimizer = optim.AdamW(
                filter(lambda p: p.requires_grad, model.parameters()), 
                lr=LEARNING_RATE, 
                weight_decay=WEIGHT_DECAY
            )
        
        # Training loop
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

        # Validation 
        if rank == 0:
            avg_test_loss_list = evaluate_model(
                model.module,
                [se_test_dir],         # single‐element list
                [benign_test_dir],
                transform,
                device=rank,
                epoch=epoch,
                batch_size=BATCH_SIZE,
                num_workers=NUM_WORKERS,
                results_base_dir=cycle_out_dir,
                criterion=criterion
            )
            log_message("All evaluations complete.")

            # Save model checkpoint
            checkpoint_path = os.path.join(cycle_out_dir, f"comb_detector_epoch_{epoch+1}.pth")
            torch.save(model.module, checkpoint_path)
            torch.save(model.module.state_dict(), checkpoint_path + ".sd")
            log_message(f"[Rank {rank}] Model checkpoint saved: {checkpoint_path}")            

            # Early stopping
            monitored_loss = avg_test_loss_list[0] if early_stop_mode == "val_loss" else avg_train_loss

            if USE_EARLY_STOPPING and early_stopper.check_early_stop(monitored_loss):
                log_message(f"[Rank {rank}] Early stopping triggered! "
                            f"Best {early_stop_mode}: {early_stopper.best_loss:.4f}")
                break

            model.train()

        if USE_SCHEDULER and SCHEDULER_TYPE in ["cosine", "step"]:
            scheduler.step()
            log_message(f"[Rank {rank}] Scheduler stepped. New LR: {scheduler.get_last_lr()}")

    if rank == 0:
        log_message("Training Complete.")

    dist.destroy_process_group()

# ============================
# ===== MAIN EXECUTION  ======
# ============================
if __name__ == "__main__":
    # Iterate over all cycles (e.g., 1.mclus_excluded,...), spawning a DDP job per cycle
    for idx, cycle_path in enumerate(cycle_dirs):
        cycle_name = os.path.basename(cycle_path)
        # derive train/test subfolders:
        se_train = os.path.join(cycle_path, "training",   "malicious_text_aug")
        ben_train = BENIGN_TRAIN
        se_test = os.path.join(cycle_path, "testing",    "malicious")
        ex_resolutions = get_resolutions_from_se_test(se_test)
        ben_test = os.path.join(cycle_path, "testing",    "benign")
        cycle_out_dir = os.path.join(OUT_BASE, cycle_name)

        # spawn one DDP run per cycle
        pt_path = PT_MODEL_PATHS[idx] if USE_PT_MODEL and idx < len(PT_MODEL_PATHS) else None
        mp.spawn(
            train,
            args=(WORLD_SIZE,
                  se_train,
                  ben_train,
                  se_test,
                  ben_test,
                  cycle_out_dir,
                  ex_resolutions,
                  pt_path),
            nprocs=WORLD_SIZE,
            join=True
        )

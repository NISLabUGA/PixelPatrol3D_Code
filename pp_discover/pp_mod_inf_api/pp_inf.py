
import numpy as np
import cv2
import os
import subprocess
import shutil
import json
import time
import datetime
import re
import glob
from multiprocessing import Process, Manager
import gc
from PIL import Image, ImageDraw, ImageFont
import yaml
import random
import string

import torch, torchvision
from torchvision import transforms

from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.logger import setup_logger
from detectron2.utils.visualizer import Visualizer
from detectron2.structures.instances import Instances

from get_clickable_elems import get_clickable_elements
from utils import generate_random_string, get_current_timestamp, sterilize_url

# Load the configuration from the YAML file
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# PATHS
vis_out_dir = config['paths']['vis_out_dir']
cat_path = config['paths']['cat_path']

# OBJECT DETECTOR MODELS
od_paths = []
for mod in config['object_detector_models']['od_paths']:
    od_paths.append((mod['path'], mod['threshold']))
    
# CLASSIFIER MODEL
class_path = config['classifier_model']['class_path']

# ADJUSTABLES
bg_color = config['adjustables']['bg_color']
padding = config['adjustables']['padding']
border = config['adjustables']['border']
denest = config['adjustables']['denest']
denest_thold = config['adjustables']['denest_thold']
keep_clickable_elems_only = config['adjustables']['keep_clickable_elems_only']
remove_neg = config['adjustables']['remove_neg']
iou_thold = config['adjustables']['iou_thold']
neg_class_name = config['adjustables']['neg_class_name']

# CUDA SETTINGS
cuda_devices = config['cuda']['devices']
os.environ["CUDA_VISIBLE_DEVICES"] = cuda_devices

available_devices = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
print("Available CUDA devices:")
for i, device_name in enumerate(available_devices):
    print(f"  {i}: {device_name}")

torch.cuda.empty_cache()
gc.collect()

# FUNCTIONS

def get_soi(str1, start_char, end_char):
    str1 = str(str1)
    offst = len(start_char)
    ind1 = str1.find(start_char)
    ind2 = str1.find(end_char)
    s_str = str1[ind1+offst:ind2]
    return s_str

def convert_bbox_xywh(b):
    x1, y1, x2, y2 = b
    x = x1
    y = y1
    w = x2 - x1
    h = y2 - y1
    return [x, y, w, h]

def createDataDict (url, outputs):
    img_shape = list(outputs["instances"].image_size)
    img_h = int(img_shape[0])
    img_w = int(img_shape[1])
    ann_list = []

    class_list = get_soi(outputs["instances"].pred_classes, "[", "]").split(",")
    
    if class_list[0] != "":

        class_list_new = []
        for each in class_list:
            if each.strip().isdigit():
                class_list_new.append(int(each.strip()))
            else:
                print(f"Invalid class ID: {each}")

        bbox_list = get_soi(outputs["instances"].pred_boxes, "[[", "]]").split("]")
        bbox_list_new = []
        for each in bbox_list:
            bbox = re.sub("['[,\n]", "", each).split(" ")
            bbox_new = []
            for item in bbox:
                if item != "":
                    bbox_new.append(float(item))
            bbox_new = convert_bbox_xywh(bbox_new)
            bbox_list_new.append(bbox_new)

        for i in range(0, len(class_list)):
            # og was "bbox_mode": "<BoxMode.XYWH_ABS: 1>"
            ann_list.append({"iscrowd": 0, "bbox": bbox_list_new[i], "category_id": class_list_new[i], "bbox_mode": 0})
    
    data_dict = {
        "url": url,
        "height": img_h,
        "width": img_w, 
        "annotations": ann_list
    }
 
    return data_dict

def crop_image(img, bounding_box, padding):
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
        
    x_min, y_min, width, height = bounding_box

    # Calculate padding in pixels
    pad_width = int(width * padding)
    pad_height = int(height * padding)

    # Adjust the bounding box with padding
    x_min = max(x_min - pad_width, 0)
    y_min = max(y_min - pad_height, 0)
    x1 = min(x_min + width + 2 * pad_width, img.width)
    y1 = min(y_min + height + 2 * pad_height, img.height)
    
    cropped_img = img.crop((x_min, y_min, x1, y1))
    
    return cropped_img

def paste_to_bg(image, background_color, bg_width, bg_height):
    
    # Create a new image with the specified background color and dimensions
    background = Image.new('RGB', (bg_width, bg_height), background_color)

    # Calculate the position to paste the image so it's centered
    x = (bg_width - image.width) // 2
    y = (bg_height - image.height) // 2

    # Paste the image onto the background
    background.paste(image, (x, y), image if image.mode == 'RGBA' else None)

    return background

def resize_ar_lock(img, target_size):

    original_width, original_height = img.size
    target_width, target_height = target_size

    # Calculate scaling factor
    scaling_factor = min(target_width / original_width, target_height / original_height)

    # Calculate new dimensions
    new_width = max(int(original_width * scaling_factor), 1)
    new_height = max(int(original_height * scaling_factor), 1)

    # Resize the image
    resized_img = img.resize((new_width, new_height))

    return resized_img

def gen_rand_str(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def process_image(img, bbox_list, padding, bg_color, border):
    
    # Create an empty list to store processed images
    processed_images = []

    for j, bbox in enumerate(bbox_list):

        try:
            elem_img = crop_image(img, bbox, padding)
            e_w = elem_img.size[0]
            e_h = elem_img.size[1]

            if e_w < e_h:
                elem_img = paste_to_bg(elem_img, bg_color, e_h + border, e_h + border)
            elif e_w > e_h:
                elem_img = paste_to_bg(elem_img, bg_color, e_w + border, e_w + border)
                
            # elem_img = transform(elem_img)
            processed_images.append(elem_img)

        except Exception as e:
            print(e)

    # Return the list of processed images
    return processed_images

def draw_bounding_boxes(image_path, bbox_list, label_list, output_path, color = 'red', thickness=2):
    
    # Open the image
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Load a font
    font = ImageFont.load_default()

    # Draw bounding boxes and labels
    for bbox, label in zip(bbox_list, label_list):
        x, y, w, h = bbox
        draw.rectangle([x, y, x+w, y+h], outline=color, width = 2)
        draw.text((x, y), label, fill=color, font=font)

    # Save the new image
    image.save(output_path)

def draw_bounding_boxes_in_mem(image, bbox_list, label_list, output_path, color='red', thickness=2):
    
    image_pil = image.astype(np.uint8)
    image_pil = Image.fromarray(image_pil)
        
    draw = ImageDraw.Draw(image_pil)
    font = ImageFont.load_default()

    for bbox, label in zip(bbox_list, label_list):
        x, y, w, h = bbox
        draw.rectangle([x, y, x + w, y + h], outline=color, width=thickness)
        draw.text((x, y), label, fill=color, font=font)

    image_pil.save(output_path)

def merge_outputs(outputs):
    l = []
    for out in outputs:
        l.append(out["instances"])
    new = Instances.cat(l)
    return {"instances": new}

def keep_all_but_first_part(s):
    parts = s.split('-')
    if len(parts) > 1:
        return '-'.join(parts[1:])
    return s

def get_center_point(bbox):
    x = bbox[0]
    y = bbox[1]
    w = bbox[2]
    h = bbox[3]
    center_x = x + w / 2
    center_y = y + h / 2
    return center_x, center_y

def is_center_inside(pred, gt):
    center_pred = get_center_point(pred)
    gt_x = gt[0]
    gt_y = gt[1]
    gt_w = gt[2]
    gt_h = gt[3]
    return True if gt_x <= center_pred[0] <= gt_x + gt_w and gt_y <= center_pred[1] <= gt_y + gt_h else False

def calculate_iou(boxA, boxB):
    # Convert from [x, y, w, h] to [x1, y1, x2, y2]
    x1A, y1A, x2A, y2A = boxA[0], boxA[1], boxA[0] + boxA[2], boxA[1] + boxA[3]
    x1B, y1B, x2B, y2B = boxB[0], boxB[1], boxB[0] + boxB[2], boxB[1] + boxB[3]
    
    # Determine the coordinates of the intersection rectangle
    xA = max(x1A, x1B)
    yA = max(y1A, y1B)
    xB = min(x2A, x2B)
    yB = min(y2A, y2B)
    
    # Compute the area of intersection rectangle
    interArea = max(0, xB - xA) * max(0, yB - yA)
    
    # Compute the area of both the prediction and true bounding boxes
    boxAArea = (x2A - x1A) * (y2A - y1A)
    boxBArea = (x2B - x1B) * (y2B - y1B)
    
    # Compute the area of union
    unionArea = boxAArea + boxBArea - interArea
    
    # Compute the Intersection over Union by dividing the intersection area by the union area
    iou = interArea / unionArea
    
    return iou

def bbox_contains(bbox1, bbox2):
    return (bbox1[0] <= bbox2[0] and
            bbox1[1] <= bbox2[1] and
            bbox1[0] + bbox1[2] >= bbox2[0] + bbox2[2] and
            bbox1[1] + bbox1[3] >= bbox2[1] + bbox2[3])

def get_non_clickable_elem_ind_list(url, pred_bbox_list):

    # Get clickable elements for the url
    ces = get_clickable_elements(url)

    if len(ces) == 0:
        return None, None
    else:

        # Build list of clickable bounding boxes
        clickable_bbox_list = [[ce['x'], ce['y'], ce['width'], ce['height']] for ce in ces]

        # List to hold non-clickable element indices
        non_clickable_ind_list = []

        # Check each predicted bounding box against clickable bounding boxes
        for i, p_bbox in enumerate(pred_bbox_list):
            is_non_clickable = True
            for c in ces:
                ces_bbox = [c['x'], c['y'], c['width'], c['height']]
                # iou_score = calculate_iou(p_bbox, ces_bbox)
                ici = is_center_inside(p_bbox, ces_bbox)
                
                # if overlap between predicted element and clickable element is greater that threshold
                # or if one is contained in the other. It will be kept as clickable predicted element.
                if (ici or
                    bbox_contains(p_bbox, ces_bbox) or
                    bbox_contains(ces_bbox, p_bbox)):
                    is_non_clickable = False
                    break
            if is_non_clickable:
                non_clickable_ind_list.append(i)

        return non_clickable_ind_list, clickable_bbox_list

def reverse_search_dict(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None

def filter_nested_bboxes(bboxes, iou_threshold=0.20):
    indices_to_remove = []
    
    # Create a list of indices
    remaining_indices = list(range(len(bboxes)))
    
    while remaining_indices:
        # Get the index and corresponding box of the first element in remaining_indices
        current_index = remaining_indices.pop(0)
        current_box = bboxes[current_index]
        
        # List to hold indices of boxes that do not overlap significantly
        non_overlapping_indices = []
        
        for other_index in remaining_indices:
            other_box = bboxes[other_index]
            iou = calculate_iou(current_box, other_box)
            
            # if box contains another box that is large enough keep outter box
            if (iou > iou_threshold and (bbox_contains(current_box, other_box) or bbox_contains(other_box, current_box))):
                if (current_box[2] * current_box[3]) >= (other_box[2] * other_box[3]):
                    indices_to_remove.append(other_index)
                else:
                    indices_to_remove.append(current_index)
                    current_box = other_box
                    current_index = other_index
            # if too much overlap between boxes keep larger box
            elif iou > iou_threshold:
                if (current_box[2] * current_box[3]) >= (other_box[2] * other_box[3]):
                    indices_to_remove.append(other_index)
                else:
                    indices_to_remove.append(current_index)
                    current_box = other_box
                    current_index = other_index
            else:
                non_overlapping_indices.append(other_index)
        
        # Update the list of remaining indices to check
        remaining_indices = non_overlapping_indices
    
    return sorted(indices_to_remove)

def load_models():
    
    obj_det_pred_list = []

    for od in od_paths:
        
        setup_logger()
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml"))
        # cfg.MODEL.WEIGHTS = os.path.join("/home/dtron2_user/ls_dtron2_full/model/output", "model_final.pth")
        cfg.MODEL.WEIGHTS = od[0]
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = od[1] 
        obj_det_pred = DefaultPredictor(cfg)
        obj_det_pred_list.append(obj_det_pred)

    classifier = torch.load(class_path)
    classifier.eval()
    
    return obj_det_pred_list, classifier

# MAIN

def pp_inference(img, url, obj_det_pred_list, classifier):  

    with open(cat_path, 'r') as f:
        cats = json.load(f)

    neg_class_id = ""

    for key, value in cats.items():
        if value == neg_class_name:
            neg_class_id = key

    master_det_dict = []
    
    if not os.path.exists(vis_out_dir):
        os.makedirs(vis_out_dir)
    
    vis_outpath = os.path.join(vis_out_dir, f'{sterilize_url(url)}_{get_current_timestamp()}.png')
    
    pred_out_list = []
    for od_pred in obj_det_pred_list:
        pred_out_list.append(od_pred(img))
    outputs = merge_outputs(pred_out_list)
    
    print('###############################################################################################')
    print(datetime.datetime.now(), url)
    
    data_dict = createDataDict(url, outputs)
    pred_bbox_list = [ann["bbox"] for ann in data_dict["annotations"]]

    print("predicted number:", len(data_dict["annotations"]))
    
    if denest:
        rem_ind_list = filter_nested_bboxes(pred_bbox_list, denest_thold)
        for ind in sorted(rem_ind_list, reverse=True):
            del data_dict['annotations'][ind]
            del pred_bbox_list[ind]

    print("denested number:", len(data_dict["annotations"]))

    if keep_clickable_elems_only:
        nce_list, ce_bbox_list = get_non_clickable_elem_ind_list(url, pred_bbox_list)

        if nce_list == None and ce_bbox_list == None:
            pass
        
        else:

            print('non clickable', len(nce_list))
            print('clickable', len(ce_bbox_list))

            z_list = ['0' for _ in range(len(ce_bbox_list))]
            
            draw_bounding_boxes_in_mem(img, ce_bbox_list, z_list, vis_outpath, color='green')

            for ind in sorted(nce_list, reverse=True):
                data_dict["annotations"].pop(ind)
                pred_bbox_list.pop(ind)

            print("cleaned number after removing non clickable elements:", len(data_dict["annotations"]))

    elem_img_list = process_image(img, pred_bbox_list, padding, bg_color, border)
    
    pred_ids = []
    pred_classes = []
    remove_list = []
    
    for j, elem_img in enumerate(elem_img_list):
        
        img_t = transform(elem_img.convert('RGB')).unsqueeze(0).to('cuda')
        
        with torch.no_grad():
            output = classifier(img_t)
        _, predicted = torch.max(output, 1)
        # OG
        # pred_class_id = str(predicted.item() + 1)
        pred_class_id = str(predicted.item())
        pred_class_name = cats[pred_class_id]
        
        if remove_neg and pred_class_id == neg_class_id:
            remove_list.append(j)

        pred_ids.append(pred_class_id)
        pred_classes.append(pred_classes)
        # data_dict["annotations"][j]["category_id"] = int(pred_class_id)
        data_dict["annotations"][j]["category_id"] = pred_class_name
    
    if remove_neg and remove_list:
        for ind in sorted(remove_list, reverse=True):
            data_dict["annotations"].pop(ind)
            pred_bbox_list.pop(ind)
            pred_ids.pop(ind)
            pred_classes.pop(ind)
            
        print("cleaned number after removing negative classes:", len(data_dict["annotations"]))
    
    if os.path.exists(vis_outpath):
        draw_bounding_boxes(vis_outpath, pred_bbox_list, pred_ids, vis_outpath, color='red')
    else:
        draw_bounding_boxes_in_mem(img, pred_bbox_list, pred_ids, vis_outpath, color='red')
    
    master_det_dict.append(data_dict)    
    
    return master_det_dict



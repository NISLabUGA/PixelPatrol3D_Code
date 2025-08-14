import os

# Limit PyTorch to only see GPU 1
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

import os
import shutil
import torch
import numpy as np
from PIL import Image
from torchvision import models, transforms
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Load ResNet50 pre-trained model, remove the final layer, and move to GPU
model = models.resnet50(pretrained=True)
model = torch.nn.Sequential(*list(model.children())[:-1])
model = model.to(device)
model.eval()

# Transform for image preprocessing
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def extract_features(img_path):
    # Load and preprocess the image
    img = Image.open(img_path).convert("RGB")
    img_tensor = preprocess(img).unsqueeze(0)  # Add batch dimension
    img_tensor = img_tensor.to(device)  # Move tensor to GPU
    with torch.no_grad():
        features = model(img_tensor)
    return features.flatten().cpu().numpy()  # Move features back to CPU for further processing

def find_optimal_k(features_array, dest_dir, k_min=5, k_max=100):
    # Calculate WCSS for different values of K and save the elbow plot
    wcss = []
    for k in range(k_min, k_max + 1):
        kmeans = KMeans(n_clusters=k, random_state=0)
        kmeans.fit(features_array)
        wcss.append(kmeans.inertia_)
    
    # Ensure the directory exists for saving the elbow plot
    os.makedirs(dest_dir, exist_ok=True)
    
    # Plot WCSS and save as elbow.png
    plt.figure(figsize=(10, 5))
    plt.plot(range(k_min, k_max + 1), wcss, marker='o')
    plt.title('Elbow Method for Optimal K')
    plt.xlabel('Number of clusters (K)')
    plt.ylabel('WCSS')
    plt.savefig(os.path.join(dest_dir, 'elbow.png'))
    plt.close()
    
    # Return the chosen K value (could add logic here to auto-choose based on the elbow)
    return int(input("Enter the optimal number of clusters (K) based on the elbow plot: "))

def cluster_images():

    # Directories
    
    # source_dir = './results/cons_raw_img/pp_crawler'
    # dest_dir = './results/meta_clusters/pp_crawler'
    
    source_dir = './results/cons_raw_img/pp_crawler_baseline'
    dest_dir = './results/meta_clusters/pp_crawler_baseline'
    
    os.makedirs(dest_dir, exist_ok=True)

    # Extract features for each image in the source directory
    img_paths = [os.path.join(source_dir, img) for img in os.listdir(source_dir) if img.endswith(('jpg', 'jpeg', 'png'))]
    print(f"Found {len(img_paths)} images to process.\n")
    
    features_list = []
    for i, img_path in enumerate(img_paths, 1):
        try:
            features = extract_features(img_path)
            features_list.append(features)
            print(f"[{i}/{len(img_paths)}] Processed {img_path}")
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    print("\nFeature extraction complete. Finding the optimal number of clusters (K)...")

    # Convert feature list to a numpy array for clustering
    features_array = np.array(features_list)
    
    # Determine the optimal number of clusters using the elbow method
    optimal_k = find_optimal_k(features_array, dest_dir)
    
    print(f"\nOptimal K determined to be {optimal_k}. Performing K-means clustering...")

    # Apply K-means clustering
    kmeans = KMeans(n_clusters=optimal_k, random_state=0).fit(features_array)
    labels = kmeans.labels_
    
    # Organize images into clusters and copy them to respective folders
    for label in range(optimal_k):
        cluster_dir = os.path.join(dest_dir, f'cluster_{label}')
        os.makedirs(cluster_dir, exist_ok=True)
        cluster_imgs = [img_paths[j] for j in range(len(labels)) if labels[j] == label]
        print(f"\nCreating cluster {label} with {len(cluster_imgs)} images.")

        for file_path in cluster_imgs:
            shutil.copy(file_path, cluster_dir)
            print(f"Copied {file_path} to {cluster_dir}")

    print("\nAll images have been clustered and copied to", dest_dir)

if __name__ == "__main__":
    print("Starting image clustering based on visual similarity using PyTorch and ResNet50 on GPU with K-means clustering...")
    cluster_images()
    print("Clustering process complete.")

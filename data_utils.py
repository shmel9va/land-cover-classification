import os
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split
from collections import Counter

def get_data_stats(root_dir):
    """
    Analyzes the dataset: lists classes and counts examples.
    """
    dataset = datasets.ImageFolder(root=root_dir)
    class_counts = Counter([label for _, label in dataset.samples])
    
    print("--- Dataset Statistics ---")
    total = 0
    for idx, count in class_counts.items():
        class_name = dataset.classes[idx]
        print(f"{class_name:25}: {count} images")
        total += count
    print(f"Total images: {total}")
    print("--------------------------\n")
    return dataset.classes

def prepare_data(root_dir, batch_size=32, split_ratio=0.8):
    """
    Prepares train and test DataLoaders.
    """
    # Standard transforms for EuroSAT (64x64 images)
    # We use ImageNet normalization as a starting point, 
    # but for satellite imagery, custom ones are sometimes preferred.
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                             std=[0.229, 0.224, 0.225])
    ])

    full_dataset = datasets.ImageFolder(root=root_dir, transform=transform)
    
    # Split into train and test
    train_size = int(split_ratio * len(full_dataset))
    test_size = len(full_dataset) - train_size
    
    train_dataset, test_dataset = random_split(
        full_dataset, [train_size, test_size], 
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    print(f"Train samples: {len(train_dataset)}")
    print(f"Test samples:  {len(test_dataset)}")
    
    return train_loader, test_loader, full_dataset.classes

if __name__ == "__main__":
    data_path = "EuroSAT/2750"
    if os.path.exists(data_path):
        classes = get_data_stats(data_path)
        train_loader, test_loader, _ = prepare_data(data_path)
    else:
        print(f"Error: Path {data_path} not found.")

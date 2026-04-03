"""
Data loading and splitting utilities for land-cover image classification.

Expects a folder layout compatible with torchvision.datasets.ImageFolder:
one subdirectory per class, images inside each folder. Used with EuroSAT
(64x64 RGB) but works for any ImageFolder-compatible dataset.
"""
import os
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split
from collections import Counter


def get_data_stats(root_dir):
    """
    Inspect the dataset: discover class names and count images per class.

    Args:
        root_dir: Root path passed to ImageFolder (must contain one folder per class).

    Returns:
        List of class name strings in dataset order (same index as label ids).
    """
    dataset = datasets.ImageFolder(root=root_dir)
    # dataset.samples: list of (path, class_index); Counter aggregates by label
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


def prepare_data(root_dir, batch_size=32, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """
    Build train, validation, and test DataLoaders with fixed random split.

    Applies the same transform to all splits (no train-only augmentation here).
    Split sizes: train and val use floor(int(ratio * n)); remainder goes to test
    so that train_size + val_size + test_size == n exactly.

    Args:
        root_dir: ImageFolder root directory.
        batch_size: Batch size for all three loaders.
        train_ratio, val_ratio, test_ratio: Positive floats that must sum to 1.0.

    Returns:
        train_loader, val_loader, test_loader, classes (list of class names).

    Raises:
        ValueError: If any ratio is non-positive or the three ratios do not sum to 1.0.
    """
    # EuroSAT images are 64x64; ImageNet mean/std are a common default for RGB CNNs.
    # Satellite-specific normalization can be substituted if needed.
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    full_dataset = datasets.ImageFolder(root=root_dir, transform=transform)

    if train_ratio <= 0 or val_ratio <= 0 or test_ratio <= 0:
        raise ValueError("train_ratio/val_ratio/test_ratio must be > 0")
    ratio_sum = train_ratio + val_ratio + test_ratio
    if abs(ratio_sum - 1.0) > 1e-6:
        raise ValueError(f"train_ratio + val_ratio + test_ratio must equal 1.0 (got {ratio_sum})")

    n = len(full_dataset)
    train_size = int(train_ratio * n)
    val_size = int(val_ratio * n)
    # Assign leftover samples to test so the three subsets partition the full set
    test_size = n - train_size - val_size

    # Fixed seed makes train/val/test indices reproducible across train.py and evaluate.py
    train_dataset, val_dataset, test_dataset = random_split(
        full_dataset, [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples:   {len(val_dataset)}")
    print(f"Test samples:  {len(test_dataset)}")

    return train_loader, val_loader, test_loader, full_dataset.classes


if __name__ == "__main__":
    # Smoke test when EuroSAT is present at the default relative path
    data_path = "EuroSAT/2750"
    if os.path.exists(data_path):
        classes = get_data_stats(data_path)
        train_loader, val_loader, test_loader, _ = prepare_data(data_path)
    else:
        print(f"Error: Path {data_path} not found.")

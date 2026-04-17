"""
Generate all figures for the Land Cover Classification report.
Run from the project root:
    python generate_figures.py
Outputs are saved to results/figures/
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as FancyArrow
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.gridspec as gridspec
from PIL import Image
import random

OUT_DIR = "results/figures"
os.makedirs(OUT_DIR, exist_ok=True)

CLASSES = [
    "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway",
    "Industrial", "Pasture", "PermanentCrop", "Residential",
    "River", "SeaLake",
]

# ── colour palette ──────────────────────────────────────────────────────────
CNN_COLOR   = "#4C72B0"
UNET_COLOR  = "#DD8452"
GRID_COLOR  = "#E8E8E8"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID_COLOR,
    "grid.linewidth": 0.8,
})

# ────────────────────────────────────────────────────────────────────────────
# Figure 1 — Workflow diagram
# ────────────────────────────────────────────────────────────────────────────
def fig1_workflow():
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    ax.axis("off")

    def box(cx, cy, w, h, label, sublabel="", color="#4C72B0", fontsize=10):
        rect = FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.1",
            facecolor=color, edgecolor="white", linewidth=1.5, zorder=3,
        )
        ax.add_patch(rect)
        ax.text(cx, cy + (0.18 if sublabel else 0), label,
                ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color="white", zorder=4)
        if sublabel:
            ax.text(cx, cy - 0.32, sublabel,
                    ha="center", va="center", fontsize=7.5,
                    color="white", alpha=0.9, zorder=4)

    def arrow(x0, x1, y=2.5):
        ax.annotate("", xy=(x1, y), xytext=(x0, y),
                    arrowprops=dict(arrowstyle="-|>", color="#555555",
                                   lw=1.8), zorder=2)

    BW, BH = 2.2, 1.2
    CY = 2.5

    # ── boxes ──
    box(1.3,  CY, BW, BH, "EuroSAT Dataset",
        "27,000 Sentinel-2\n64×64 patches, 10 classes", "#2D6A9F")

    box(3.9,  CY, BW, BH, "Preprocessing",
        "Normalize · Split 70/15/15\nseed=42", "#3A7EBF")

    # branch: two models side by side at x=6.5, y=3.5 and y=1.5
    # top branch
    rect_cnn = FancyBboxPatch((5.6, 3.1), 2.2, 1.0,
        boxstyle="round,pad=0.1", facecolor=CNN_COLOR,
        edgecolor="white", linewidth=1.5, zorder=3)
    ax.add_patch(rect_cnn)
    ax.text(6.7, 3.6, "SimpleCNN", ha="center", va="center",
            fontsize=9.5, fontweight="bold", color="white", zorder=4)

    # bottom branch
    rect_unet = FancyBboxPatch((5.6, 1.0), 2.2, 1.0,
        boxstyle="round,pad=0.1", facecolor=UNET_COLOR,
        edgecolor="white", linewidth=1.5, zorder=3)
    ax.add_patch(rect_unet)
    ax.text(6.7, 1.5, "UNetClassifier", ha="center", va="center",
            fontsize=9.5, fontweight="bold", color="white", zorder=4)

    # fork arrow from Preprocessing
    ax.annotate("", xy=(5.6, 3.6), xytext=(5.0, 3.6),
                arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.5))
    ax.annotate("", xy=(5.6, 1.5), xytext=(5.0, 1.5),
                arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.5))
    # vertical connector from preprocessing end
    ax.plot([5.0, 5.0], [1.5, 3.6], color="#555", lw=1.5, zorder=2)
    ax.plot([5.0, 5.0], [CY, CY],   color="#555", lw=0, zorder=2)
    arrow(3.0 + BW/2, 5.0)  # preprocessing → fork

    # training box
    box(9.0, CY, BW, BH, "Training",
        "Adam lr=0.001 · CE Loss\nEarly stopping p=5", "#5A9E6B")

    # arrows from models to training
    ax.annotate("", xy=(8.0, 3.6), xytext=(7.8, 3.6),
                arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.5))
    ax.annotate("", xy=(8.0, 1.5), xytext=(7.8, 1.5),
                arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.5))
    ax.plot([8.0, 8.0], [1.5, 3.6], color="#555", lw=1.5, zorder=2)
    ax.annotate("", xy=(8.9 - BW/2, CY), xytext=(8.0, CY),
                arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.5))

    box(11.6, CY, BW, BH, "Evaluation",
        "Accuracy · F1 · Precision\nRecall · Confusion Matrix", "#9B59B6")

    arrow(9.0 + BW/2, 11.6 - BW/2)

    # title
    ax.text(7.0, 4.65, "Land Cover Classification Pipeline",
            ha="center", va="center", fontsize=13,
            fontweight="bold", color="#333333")

    plt.tight_layout()
    path = f"{OUT_DIR}/fig1_workflow.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {path}")


# ────────────────────────────────────────────────────────────────────────────
# Figure 2 — Sample EuroSAT images (one per class)
# ────────────────────────────────────────────────────────────────────────────
def fig2_samples():
    dataset_root = "EuroSAT/2750"
    if not os.path.isdir(dataset_root):
        print("Dataset not found, skipping fig2.")
        return

    random.seed(42)
    fig, axes = plt.subplots(2, 5, figsize=(13, 5.5))
    axes = axes.flatten()

    for i, cls in enumerate(CLASSES):
        cls_dir = os.path.join(dataset_root, cls)
        files = [f for f in os.listdir(cls_dir) if f.lower().endswith((".jpg", ".png", ".tif"))]
        img_path = os.path.join(cls_dir, random.choice(files))
        img = Image.open(img_path).convert("RGB")
        axes[i].imshow(img)
        axes[i].set_title(cls, fontsize=9, fontweight="bold", pad=4)
        axes[i].axis("off")

    fig.suptitle("EuroSAT Dataset — Sample Patches per Land Cover Class",
                 fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()
    path = f"{OUT_DIR}/fig2_samples.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {path}")


# ────────────────────────────────────────────────────────────────────────────
# Figure 3 — Training curves: SimpleCNN
# ────────────────────────────────────────────────────────────────────────────
def fig3_cnn_curves():
    with open("results/cnn_history.json") as f:
        h = json.load(f)

    epochs = list(range(1, len(h["train_loss"]) + 1))
    best_ep = int(np.argmin(h["val_loss"])) + 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.2))

    # Loss
    ax1.plot(epochs, h["train_loss"], color=CNN_COLOR, lw=2, label="Train Loss")
    ax1.plot(epochs, h["val_loss"],   color=CNN_COLOR, lw=2, ls="--", label="Val Loss")
    ax1.axvline(best_ep, color="red", lw=1.2, ls=":", label=f"Best epoch {best_ep}")
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Cross-Entropy Loss")
    ax1.set_title("SimpleCNN — Loss")
    ax1.legend(framealpha=0.9)

    # Accuracy
    ax2.plot(epochs, h["val_acc"], color=CNN_COLOR, lw=2, label="Val Accuracy")
    ax2.axvline(best_ep, color="red", lw=1.2, ls=":", label=f"Best epoch {best_ep}")
    ax2.axhline(89.23, color="gray", lw=1, ls="-.", label="Test Acc 89.23%")
    ax2.set_xlabel("Epoch"); ax2.set_ylabel("Accuracy (%)")
    ax2.set_title("SimpleCNN — Validation Accuracy")
    ax2.legend(framealpha=0.9)

    fig.suptitle("SimpleCNN Training Curves", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"{OUT_DIR}/fig3_cnn_curves.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {path}")


# ────────────────────────────────────────────────────────────────────────────
# Figure 4 — Training curves: UNetClassifier
# ────────────────────────────────────────────────────────────────────────────
def fig4_unet_curves():
    with open("results/unet_history.json") as f:
        h = json.load(f)

    epochs = list(range(1, len(h["train_loss"]) + 1))
    best_ep = int(np.argmin(h["val_loss"])) + 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.2))

    # Loss
    ax1.plot(epochs, h["train_loss"], color=UNET_COLOR, lw=2, label="Train Loss")
    ax1.plot(epochs, h["val_loss"],   color=UNET_COLOR, lw=2, ls="--", label="Val Loss")
    ax1.axvline(best_ep, color="red", lw=1.2, ls=":", label=f"Best epoch {best_ep}")
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Cross-Entropy Loss")
    ax1.set_title("UNetClassifier — Loss")
    ax1.legend(framealpha=0.9)

    # Accuracy
    ax2.plot(epochs, h["val_acc"], color=UNET_COLOR, lw=2, label="Val Accuracy")
    ax2.axvline(best_ep, color="red", lw=1.2, ls=":", label=f"Best epoch {best_ep}")
    ax2.axhline(96.10, color="gray", lw=1, ls="-.", label="Test Acc 96.10%")
    ax2.set_xlabel("Epoch"); ax2.set_ylabel("Accuracy (%)")
    ax2.set_title("UNetClassifier — Validation Accuracy")
    ax2.legend(framealpha=0.9)

    fig.suptitle("UNetClassifier Training Curves", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"{OUT_DIR}/fig4_unet_curves.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {path}")


# ────────────────────────────────────────────────────────────────────────────
# Figure 5 — Per-class F1 comparison (grouped bar chart)
# ────────────────────────────────────────────────────────────────────────────
def fig5_f1_comparison():
    with open("results/cnn_report.json") as f:
        cnn_r = json.load(f)
    with open("results/unet_report.json") as f:
        unet_r = json.load(f)

    cnn_f1  = [cnn_r[c]["f1-score"]  for c in CLASSES]
    unet_f1 = [unet_r[c]["f1-score"] for c in CLASSES]

    x = np.arange(len(CLASSES))
    w = 0.38

    fig, ax = plt.subplots(figsize=(13, 5))
    bars1 = ax.bar(x - w/2, cnn_f1,  w, label="SimpleCNN",       color=CNN_COLOR,  alpha=0.88)
    bars2 = ax.bar(x + w/2, unet_f1, w, label="UNetClassifier",  color=UNET_COLOR, alpha=0.88)

    # value labels on bars
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=7, color="#333")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=7, color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels(CLASSES, rotation=30, ha="right", fontsize=9)
    ax.set_ylim(0.75, 1.02)
    ax.set_ylabel("F1-Score")
    ax.set_title("Per-Class F1-Score: SimpleCNN vs. UNetClassifier",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    plt.tight_layout()
    path = f"{OUT_DIR}/fig5_f1_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {path}")


# ────────────────────────────────────────────────────────────────────────────
# Figure 6 — Overall metrics comparison
# ────────────────────────────────────────────────────────────────────────────
def fig6_metrics_comparison():
    metrics = ["Accuracy", "Weighted F1", "Weighted Precision", "Weighted Recall"]
    cnn_vals  = [0.8923, 0.8930, 0.8963, 0.8923]
    unet_vals = [0.9610, 0.9610, 0.9613, 0.9610]

    x = np.arange(len(metrics))
    w = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - w/2, cnn_vals,  w, label="SimpleCNN",      color=CNN_COLOR,  alpha=0.88)
    bars2 = ax.bar(x + w/2, unet_vals, w, label="UNetClassifier", color=UNET_COLOR, alpha=0.88)

    for bar in list(bars1) + list(bars2):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                f"{bar.get_height():.4f}", ha="center", va="bottom", fontsize=9.5, color="#222")

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylim(0.85, 1.0)
    ax.set_ylabel("Score")
    ax.set_title("Overall Model Performance Comparison",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=11)
    plt.tight_layout()
    path = f"{OUT_DIR}/fig6_metrics_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {path}")


# ────────────────────────────────────────────────────────────────────────────
# Figure 7 — Both training curves on one plot (overlay for comparison)
# ────────────────────────────────────────────────────────────────────────────
def fig7_combined_curves():
    with open("results/cnn_history.json") as f:
        cnn_h = json.load(f)
    with open("results/unet_history.json") as f:
        unet_h = json.load(f)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    cnn_ep  = list(range(1, len(cnn_h["val_loss"])  + 1))
    unet_ep = list(range(1, len(unet_h["val_loss"]) + 1))

    # Val Loss
    ax1.plot(cnn_ep,  cnn_h["val_loss"],  color=CNN_COLOR,  lw=2, label="SimpleCNN Val Loss")
    ax1.plot(unet_ep, unet_h["val_loss"], color=UNET_COLOR, lw=2, label="UNet Val Loss")
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Val Loss")
    ax1.set_title("Validation Loss Comparison")
    ax1.legend()

    # Val Accuracy
    ax2.plot(cnn_ep,  cnn_h["val_acc"],  color=CNN_COLOR,  lw=2, label="SimpleCNN Val Acc")
    ax2.plot(unet_ep, unet_h["val_acc"], color=UNET_COLOR, lw=2, label="UNet Val Acc")
    ax2.axhline(89.23, color=CNN_COLOR,  lw=1.2, ls="--", alpha=0.6, label="CNN Test 89.23%")
    ax2.axhline(96.10, color=UNET_COLOR, lw=1.2, ls="--", alpha=0.6, label="UNet Test 96.10%")
    ax2.set_xlabel("Epoch"); ax2.set_ylabel("Accuracy (%)")
    ax2.set_title("Validation Accuracy Comparison")
    ax2.legend(fontsize=8.5)

    fig.suptitle("SimpleCNN vs. UNetClassifier — Training Dynamics",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"{OUT_DIR}/fig7_combined_curves.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {path}")


# ────────────────────────────────────────────────────────────────────────────
# Run all
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating report figures …")
    fig1_workflow()
    fig2_samples()
    fig3_cnn_curves()
    fig4_unet_curves()
    fig5_f1_comparison()
    fig6_metrics_comparison()
    fig7_combined_curves()
    print(f"\nDone. All figures saved to {OUT_DIR}/")

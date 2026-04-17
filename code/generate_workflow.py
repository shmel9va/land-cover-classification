"""
Workflow diagram for the Land Cover Classification report.
Simplified version: fewer lines per box, larger readable fonts.
Run: py generate_workflow.py
Output: results/figures/fig1_workflow.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

OUT_DIR = "results/figures"
os.makedirs(OUT_DIR, exist_ok=True)

C_DATA  = "#2471A3"
C_CNN   = "#1A5276"
C_UNET  = "#7D6608"
C_TRAIN = "#1E8449"
C_EVAL  = "#6C3483"
C_ARROW = "#444444"
BG      = "#F8F9FA"


def box(ax, cx, cy, w, h, color, title, lines, tsz=13, lsz=11):
    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle="round,pad=0.18",
        facecolor=color, edgecolor="white", linewidth=2, zorder=3,
    ))
    # title
    title_y = cy + h/2 - 0.28
    ax.text(cx, title_y, title, ha="center", va="top",
            fontsize=tsz, fontweight="bold", color="white", zorder=4)
    # separator
    sep_y = title_y - 0.30
    ax.plot([cx - w/2 + 0.15, cx + w/2 - 0.15], [sep_y, sep_y],
            color="white", lw=1.0, alpha=0.45, zorder=4)
    # lines — evenly spaced below separator
    body_top = sep_y - 0.20
    body_h   = h/2 - 0.28 + (cy - cy) + (cy - h/2) - sep_y + cy + h/2 - 0.28 - 0.30 - 0.20
    # simpler: distribute lines in the remaining space
    avail = (cy - h/2 + 0.15) - (sep_y - 0.20)   # negative → we go downward
    step  = abs(avail) / max(len(lines), 1)
    for i, ln in enumerate(lines):
        ax.text(cx, body_top - i * step, ln,
                ha="center", va="top",
                fontsize=lsz, color="white", zorder=4)


def harrow(ax, x0, x1, y):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="-|>", color=C_ARROW,
                                lw=2.0, mutation_scale=16), zorder=2)


def fork(ax, x0, y0, x1, ytop, ybot):
    xm = (x0 + x1) / 2
    ax.plot([x0, xm], [y0, y0], color=C_ARROW, lw=2.0, zorder=2)
    ax.plot([xm, xm], [ybot, ytop], color=C_ARROW, lw=2.0, zorder=2)
    harrow(ax, xm, x1, ytop)
    harrow(ax, xm, x1, ybot)


def join(ax, x0, ytop, ybot, x1, ymid):
    xm = (x0 + x1) / 2
    ax.plot([x0, xm], [ytop, ytop], color=C_ARROW, lw=2.0, zorder=2)
    ax.plot([x0, xm], [ybot, ybot], color=C_ARROW, lw=2.0, zorder=2)
    ax.plot([xm, xm], [ybot, ytop], color=C_ARROW, lw=2.0, zorder=2)
    harrow(ax, xm, x1, ymid)


# ── canvas ───────────────────────────────────────────────────────────────────
FW, FH = 22, 10
fig, ax = plt.subplots(figsize=(FW, FH))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, FW)
ax.set_ylim(0, FH)
ax.axis("off")

# title
ax.text(FW/2, 9.55, "Land Cover Classification — Pipeline Overview",
        ha="center", va="center", fontsize=17, fontweight="bold", color="#1C2833")
ax.text(FW/2, 9.10, "EuroSAT dataset  |  SimpleCNN  vs.  UNetClassifier  |  PyTorch / CUDA",
        ha="center", va="center", fontsize=11, color="#555", style="italic")

# ── geometry ─────────────────────────────────────────────────────────────────
BW    = 3.2   # box width
YMID  = 4.8   # single-lane centre y
YTOP  = 6.8   # upper branch centre y
YBOT  = 2.8   # lower branch centre y
HMAIN = 3.8   # single-lane box height
HSPL  = 3.2   # split-lane box height

# x-centres: 6 columns evenly spaced
XS = [1.9, 5.4, 8.9, 12.4, 15.9, 19.4]

# ── boxes ────────────────────────────────────────────────────────────────────

# 1. Dataset
box(ax, XS[0], YMID, BW, HMAIN, C_DATA,
    "EuroSAT Dataset",
    [
        "27,000 Sentinel-2 patches",
        "64 x 64 px  |  RGB",
        "10 land cover classes",
        "2,000 – 3,000 images / class",
    ])

# 2. Preprocessing
box(ax, XS[1], YMID, BW, HMAIN, C_DATA,
    "Preprocessing",
    [
        "Split  70 / 15 / 15  (seed=42)",
        "Train 18,900  |  Val & Test 4,050",
        "Normalize (ImageNet mean/std)",
        "Batch size = 64",
    ])

harrow(ax, XS[0] + BW/2, XS[1] - BW/2, YMID)

# 3a. SimpleCNN
box(ax, XS[2], YTOP, BW, HSPL, C_CNN,
    "SimpleCNN",
    [
        "3x Conv + BN + ReLU + MaxPool",
        "Channels: 3 -> 32 -> 64 -> 128",
        "FC(8192->512) + Dropout(0.5)",
        "FC(512->10)  |  ~4.5 M params",
    ])

# 3b. UNetClassifier
box(ax, XS[2], YBOT, BW, HSPL, C_UNET,
    "UNetClassifier",
    [
        "Encoder: 3->64->128->256->512",
        "Skip connections (concat)",
        "Decoder: 512->256->128->64",
        "AvgPool + FC(64->10)  |  ~8.1 M params",
    ])

fork(ax, XS[1] + BW/2, YMID, XS[2] - BW/2, YTOP, YBOT)

# 4. Training
box(ax, XS[3], YMID, BW, HMAIN, C_TRAIN,
    "Training",
    [
        "Adam  |  lr = 0.001",
        "Loss: CrossEntropyLoss",
        "Max 50 epochs  |  CUDA GPU",
        "Early stopping  (patience = 5)",
    ])

join(ax, XS[2] + BW/2, YTOP, YBOT, XS[3] - BW/2, YMID)

# 5. Evaluation
box(ax, XS[4], YMID, BW, HMAIN, C_EVAL,
    "Evaluation",
    [
        "Test set: 4,050 samples",
        "Accuracy  |  Weighted F1",
        "Precision  |  Recall",
        "Confusion Matrix (10x10)",
    ])

harrow(ax, XS[3] + BW/2, XS[4] - BW/2, YMID)

# 6a. CNN results
box(ax, XS[5], YTOP, BW, HSPL, C_CNN,
    "SimpleCNN Results",
    [
        "Accuracy :  89.23%",
        "Weighted F1 :  0.893",
        "Best epoch: 11",
    ])

# 6b. UNet results
box(ax, XS[5], YBOT, BW, HSPL, C_UNET,
    "UNetClassifier Results",
    [
        "Accuracy :  96.10%",
        "Weighted F1 :  0.961",
        "Best epoch: 24",
    ])

fork(ax, XS[4] + BW/2, YMID, XS[5] - BW/2, YTOP, YBOT)

# ── improvement badge ────────────────────────────────────────────────────────
bx, by = XS[5], (YTOP + YBOT) / 2
ax.add_patch(FancyBboxPatch(
    (bx - 1.15, by - 0.38), 2.30, 0.76,
    boxstyle="round,pad=0.12",
    facecolor="#E67E22", edgecolor="white", lw=1.6, zorder=6,
))
ax.text(bx, by + 0.12, "UNet outperforms CNN",
        ha="center", va="center", fontsize=9.5, fontweight="bold",
        color="white", zorder=7)
ax.text(bx, by - 0.18, "Accuracy +6.87 pp   F1 +0.068",
        ha="center", va="center", fontsize=8.5, color="white", zorder=7)

# ── step labels ───────────────────────────────────────────────────────────────
labels = ["1. Dataset", "2. Preprocessing", "3. Architecture",
          "4. Training", "5. Evaluation", "6. Results"]
for lbl, sx in zip(labels, XS):
    ax.text(sx, 1.10, lbl, ha="center", va="center",
            fontsize=9.5, fontweight="bold", color="#333")

# ── legend ────────────────────────────────────────────────────────────────────
ax.legend(handles=[
    mpatches.Patch(facecolor=C_DATA,  label="Data stages"),
    mpatches.Patch(facecolor=C_CNN,   label="SimpleCNN"),
    mpatches.Patch(facecolor=C_UNET,  label="UNetClassifier"),
    mpatches.Patch(facecolor=C_TRAIN, label="Training"),
    mpatches.Patch(facecolor=C_EVAL,  label="Evaluation"),
], loc="lower center", ncol=5, fontsize=10, framealpha=0.9,
   bbox_to_anchor=(0.5, 0.0))

# ── save ─────────────────────────────────────────────────────────────────────
path = f"{OUT_DIR}/fig1_workflow.png"
fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"Saved: {path}")

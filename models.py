"""
Neural network architectures for multi-class image classification on 64x64 RGB input.

Includes a stack-of-convolutions baseline (SimpleCNN) and an encoder-decoder
variant with skip connections (UNetClassifier) that ends in global pooling and
a linear classifier—not a segmentation mask.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SimpleCNN(nn.Module):
    """
    Lightweight CNN classifier: three conv blocks with batch norm, ReLU, and pooling,
    followed by a two-layer MLP head.

    Spatial size: 64 -> 32 -> 16 -> 8 after three 2x2 max pools, so the flatten
    dimension is 128 * 8 * 8. Suitable for EuroSAT-sized inputs.
    """
    def __init__(self, num_classes=10):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)

        self.pool = nn.MaxPool2d(2, 2)

        # 64x64 -> pool -> 32x32 -> pool -> 16x16 -> pool -> 8x8
        self.fc1 = nn.Linear(128 * 8 * 8, 512)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))

        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class DoubleConv(nn.Module):
    """
    Two 3x3 convolutions, each with batch norm and ReLU (U-Net-style feature block).

    bias=False is typical when batch norm follows conv (scale/shift in BN).
    """
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)


class UNetClassifier(nn.Module):
    """
    U-Net-style encoder-decoder with skip connections, repurposed for classification.

    The decoder upsamples and fuses encoder features (concatenation + DoubleConv).
    Instead of a per-pixel logits map, applies global average pooling and a linear
    layer to produce one logit vector per image.
    """
    def __init__(self, num_classes=10):
        super(UNetClassifier, self).__init__()

        # Encoder: progressively halve spatial size and increase channels
        self.inc = DoubleConv(3, 64)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(64, 128))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(128, 256))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(256, 512))

        # Decoder: upsample then concat with skip; in_channels = up_ch + skip_ch
        self.up1 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.up_conv1 = DoubleConv(512, 256)  # 256 (from up) + 256 (skip x3)

        self.up2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.up_conv2 = DoubleConv(256, 128)  # 128 + 128 (skip x2)

        self.up3 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.up_conv3 = DoubleConv(128, 64)   # 64 + 64 (skip x1)

        # Collapse spatial dimensions to a single vector per sample
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(64, num_classes)

    def forward(self, x):
        # Encoder path: retain skip tensors at three resolutions
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)

        # Decoder: upsample, concatenate skip along channel dim, then refine
        x = self.up1(x4)
        x = torch.cat([x, x3], dim=1)
        x = self.up_conv1(x)

        x = self.up2(x)
        x = torch.cat([x, x2], dim=1)
        x = self.up_conv2(x)

        x = self.up3(x)
        x = torch.cat([x, x1], dim=1)
        x = self.up_conv3(x)

        x = self.global_pool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x


if __name__ == "__main__":
    # Verify output shapes for batch x 3 x 64 x 64 (no gradient, inference-style check)
    model_cnn = SimpleCNN(num_classes=10)
    model_unet = UNetClassifier(num_classes=10)

    test_input = torch.randn(2, 3, 64, 64)

    out_cnn = model_cnn(test_input)
    out_unet = model_unet(test_input)

    print(f"Input shape: {test_input.shape}")
    print(f"SimpleCNN output shape: {out_cnn.shape}")
    print(f"UNetClassifier output shape: {out_unet.shape}")

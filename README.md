# Land Cover Classification Pipeline

This project implements an image classification pipeline for satellite imagery (EuroSAT dataset) using two different architectures:
1.  **SimpleCNN:** A classic convolutional neural network for image classification.
2.  **U-Net adapted for Classification:** A U-Net-based architecture with an encoder-decoder structure, ending with global average pooling for classification.

## Project Structure
- `src/`: Core logic (data processing, model definitions) - *Optional organization*
- `models/`: Saved model weights (best checkpoints).
- `results/`: Evaluation results (metrics, confusion matrices, history).
- `data/`: Dataset storage (EuroSAT directory).
- `train.py`: Script to train a specific model.
- `evaluate.py`: Script to evaluate a specific model and generate metrics.
- `pipeline.py`: A wrapper to run the full training and evaluation sequence.

## Training Algorithm
1.  **Preprocessing:** Images (64x64) are normalized using standard statistics.
2.  **Dataset Split:** The dataset is split into training (80%) and validation (20%) sets.
3.  **Optimizer:** Adam optimizer with a learning rate of 0.001.
4.  **Loss Function:** Cross-Entropy Loss for multi-class classification.
5.  **Training:** The model is trained for a specified number of epochs. After each epoch, the model is evaluated on the validation set.
6.  **Checkpointing:** The model with the highest validation accuracy is saved as the best model.

## Evaluation
Evaluation is performed on the held-out test set. The following metrics are calculated:
- Accuracy
- F1-Score (weighted)
- Precision (weighted)
- Recall (weighted)
- Confusion Matrix (saved as an image in `results/`)

## How to Use
### Running with Docker (Recommended for Reproducibility)
1.  Build the image:
    ```bash
    docker build -t land-cover-pipeline .
    ```
2.  Run the pipeline:
    ```bash
    docker run --rm -v $(pwd)/results:/app/results -v $(pwd)/models:/app/models land-cover-pipeline
    ```
    *Note: This will run 5 epochs by default. You can change this by passing arguments.*

### Running Locally
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the full pipeline:
    ```bash
    python pipeline.py --epochs 5
    ```
3.  Or run specific models:
    ```bash
    python train.py --model cnn --epochs 5
    python evaluate.py --model cnn
    ```

## Reproduction
The random seeds are fixed (where possible) in `data_utils.py` and `train.py` to ensure consistent data splitting and initialization across different runs.
Using Docker ensures consistent software environment.

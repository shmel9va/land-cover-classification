# Land Cover Classification Pipeline

This project trains and compares two architectures on the EuroSAT dataset:
1. **SimpleCNN** - a baseline CNN for image classification.
2. **U-NetClassifier** - a U-Net-style architecture adapted for classification.

## What the pipeline does

1. Loads the dataset and applies normalization.
2. Splits data into **train/val/test = 70%/15%/15%**.
3. Trains on `train`.
4. Validates after each epoch on `val`.
5. Saves the best checkpoint `models/best_<model>.pth` by **lowest `val_loss`**.
6. Applies **early stopping** when `val_loss` does not improve enough for several epochs.
7. Runs `evaluate.py` and reports final metrics on **test only**.

This avoids data leakage: `test` is not used to pick the best epoch.

## Why `epochs`, `patience`, and `min_delta` matter

- **`--epochs`**  
  Maximum number of epochs (upper training limit).

- **`--patience`**  
  Number of consecutive non-improving epochs allowed before stopping.  
  Example: with `patience=5`, training stops if there is no significant `val_loss` improvement for 5 epochs in a row.

- **`--min_delta`**  
  Minimum `val_loss` improvement required to count as real progress.  
  If improvement is smaller than `min_delta`, patience is not reset.

### Early stopping logic

- Keep current best `val_loss`.
- If new `val_loss` improves by more than `min_delta`, save checkpoint and reset counter.
- Otherwise increment "no improvement" counter.
- Stop when counter reaches `patience`.

## How to tell when to tune these parameters

Use `results/<model>_history.json` and training logs (`train_loss`, `val_loss`, `val_acc`):

- **Increase `epochs`** when:
  - training stops while `val_loss` is still clearly improving;
  - best epoch is very close to current max epoch repeatedly.

- **Decrease `epochs`** (or rely more on early stopping) when:
  - best epoch is always much earlier than max epoch;
  - later epochs only add runtime with no validation gains.

- **Increase `patience`** when:
  - validation curve is noisy (up/down) but trend still improves;
  - training often stops too early and next runs could still improve.

- **Decrease `patience`** when:
  - model quickly starts overfitting (`train_loss` down, `val_loss` up);
  - long tail epochs do not improve validation metrics.

- **Increase `min_delta`** when:
  - tiny random `val_loss` fluctuations keep resetting patience;
  - checkpoints are saved too often without meaningful metric gains.

- **Decrease `min_delta`** when:
  - training stops even though small but consistent improvements exist;
  - you want to capture fine-grained improvements near convergence.

### Typical patterns

- **Underfitting**: both `train_loss` and `val_loss` are high -> usually increase `epochs` (and maybe model capacity/lr tuning).
- **Overfitting**: `train_loss` keeps decreasing while `val_loss` rises -> reduce effective training length (smaller `patience`, possibly larger `min_delta`).
- **Stable convergence**: both losses flatten and metrics plateau -> current setup is likely fine.

## Saved artifacts

- `models/best_cnn.pth`, `models/best_unet.pth` - best weights by `val_loss`.
- `results/<model>_history.json` - epoch-wise `train_loss`, `val_loss`, `val_acc`.
- `results/<model>_training_summary.json`:
  - `best_epoch`
  - `best_val_loss`
  - `best_val_acc`
  - `stopped_early`
  - `patience`
  - `min_delta`

## Test metrics

`evaluate.py` computes on `test`:
- Accuracy
- F1 (weighted)
- Precision (weighted)
- Recall (weighted)
- Confusion Matrix (`results/<model>_cm.png`)
- JSON reports (`results/<model>_metrics.json`, `results/<model>_report.json`)

## Project structure

- `train.py` - trains one model (`cnn` or `unet`) with early stopping.
- `evaluate.py` - evaluates a trained model on test.
- `pipeline.py` - runs training + evaluation for both models.
- `data_utils.py` - loading, transforms, and train/val/test split.
- `models/` - saved checkpoints.
- `results/` - metrics, reports, and visual outputs.

## Run

### Docker (PowerShell, Windows)

1. Build image:
```powershell
docker build -t land-cover-pipeline .
```

2. Run pipeline:
```powershell
docker run --rm `
  -v "${PWD}\results:/app/results" `
  -v "${PWD}\models:/app/models" `
  land-cover-pipeline python pipeline.py --epochs 50 --patience 5 --min_delta 0.0
```

### Local run

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

2. Run full pipeline:
```powershell
python pipeline.py --epochs 50 --patience 5 --min_delta 0.0
```

3. Run a single model:
```powershell
python train.py --model cnn --epochs 50 --patience 5 --min_delta 0.0
python evaluate.py --model cnn
```

## Recommended starting values

- CPU baseline: `--epochs 50 --patience 5 --min_delta 0.001`
- If validation is noisy: increase `patience` to `7-10`
- If stopping is too aggressive: reduce `min_delta` (e.g., to `0.0`)

## Reproducibility

`data_utils.py` uses a fixed seed for `random_split`, so split composition is stable across runs.

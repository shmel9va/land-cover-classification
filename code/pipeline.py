"""
End-to-end orchestration: train then evaluate both CNN and U-Net classifiers.

Invokes train.py and evaluate.py as subprocesses with the current Python
interpreter so the pipeline behaves the same as manual CLI runs. Training can
be skipped to only re-run evaluation (e.g. after copying weights).
"""
import os
import subprocess
import argparse
import sys


def run_command(command):
    """
    Execute a shell command string and return success status.

    Uses shell=True so quoted paths work on Windows. On failure, prints the
    command and returns False; the caller may stop or continue.

    Args:
        command: Full command line (e.g. python path/train.py ...).

    Returns:
        True if return code is 0, else False.
    """
    print(f"\nRunning: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Land Cover Classification Pipeline')
    parser.add_argument('--epochs', type=int, default=50, help='Max number of epochs for training (early stopping may stop earlier)')
    parser.add_argument('--batch_size', type=int, default=64, help='Batch size')
    parser.add_argument('--skip_train', action='store_true', help='Skip training and only evaluate')
    parser.add_argument('--patience', type=int, default=5, help='Early stopping patience')
    parser.add_argument('--min_delta', type=float, default=0.0, help='Minimum val_loss improvement to reset patience')

    args = parser.parse_args()

    os.makedirs('models', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    # Same interpreter as this process (important for venv/conda on Windows)
    python_exe = sys.executable
    models = ['cnn', 'unet']

    if not args.skip_train:
        for model in models:
            print(f"\n{'='*50}")
            print(f"TRAINING MODEL: {model.upper()}")
            print(f"{'='*50}")
            train_cmd = (
                f'"{python_exe}" train.py --model {model} --epochs {args.epochs} --batch_size {args.batch_size} '
                f'--patience {args.patience} --min_delta {args.min_delta}'
            )
            if not run_command(train_cmd):
                # Stop training sequence if one model fails; evaluation still runs below
                break

    for model in models:
        print(f"\n{'='*50}")
        print(f"EVALUATING MODEL: {model.upper()}")
        print(f"{'='*50}")
        eval_cmd = f'"{python_exe}" evaluate.py --model {model}'
        run_command(eval_cmd)

    print("\nPipeline execution finished!")

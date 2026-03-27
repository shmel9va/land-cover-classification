import os
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
import argparse
from data_utils import prepare_data
from models import SimpleCNN, UNetClassifier
import json

def train(
    model,
    train_loader,
    val_loader,
    epochs=10,
    lr=0.001,
    device='cpu',
    model_name='model',
    patience=5,
    min_delta=0.0,
):
    if isinstance(device, str):
        device = torch.device(device)
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
    
    best_val_loss = float("inf")
    best_val_acc = 0.0
    best_epoch = -1
    epochs_since_improve = 0
    stopped_early = False
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]")
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * images.size(0)
            pbar.set_postfix({'loss': loss.item()})
            
        train_loss = running_loss / len(train_loader.dataset)
        history['train_loss'].append(train_loss)
        
        # Validation
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        val_loss = val_loss / len(val_loader.dataset)
        val_acc = 100 * correct / total
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        print(f"Epoch {epoch+1}/{epochs}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save best model (by val_loss to reduce overfitting risk)
        if (best_val_loss - val_loss) > min_delta:
            best_val_loss = val_loss
            best_val_acc = val_acc
            best_epoch = epoch + 1
            epochs_since_improve = 0
            os.makedirs('models', exist_ok=True)
            torch.save(model.state_dict(), f'models/best_{model_name}.pth')
            print(f"Saved new best model: models/best_{model_name}.pth")
        else:
            epochs_since_improve += 1
            if epochs_since_improve >= patience:
                print(
                    f"Early stopping: no val_loss improvement > {min_delta} for {patience} epoch(s). "
                    f"Best epoch: {best_epoch} (val_loss={best_val_loss:.4f}, val_acc={best_val_acc:.2f}%)"
                )
                stopped_early = True
                break
            
    summary = {
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "best_val_acc": best_val_acc,
        "stopped_early": stopped_early,
        "patience": patience,
        "min_delta": min_delta,
    }
    return history, summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Land Cover Classification Models')
    parser.add_argument('--model', type=str, default='cnn', choices=['cnn', 'unet'], help='Model type: cnn or unet')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--data_dir', type=str, default='EuroSAT/2750', help='Path to dataset')
    parser.add_argument('--patience', type=int, default=5, help='Early stopping patience (epochs without improvement)')
    parser.add_argument('--min_delta', type=float, default=0.0, help='Minimum val_loss improvement to reset patience')
    
    args = parser.parse_args()
    
    # Correct device handling for typing
    device_obj = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device_obj}")
    
    train_loader, val_loader, _, classes = prepare_data(args.data_dir, batch_size=args.batch_size)
    num_classes = len(classes)
    
    if args.model == 'cnn':
        model = SimpleCNN(num_classes=num_classes)
    else:
        model = UNetClassifier(num_classes=num_classes)
        
    history, summary = train(
        model,
        train_loader,
        val_loader,
        epochs=args.epochs,
        lr=args.lr,
        device=device_obj,
        model_name=args.model,
        patience=args.patience,
        min_delta=args.min_delta,
    )
    
    os.makedirs('results', exist_ok=True)
    with open(f'results/{args.model}_history.json', 'w') as f:
        json.dump(history, f)

    with open(f'results/{args.model}_training_summary.json', 'w') as f:
        json.dump(summary, f)


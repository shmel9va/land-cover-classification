import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, precision_score, recall_score
from data_utils import prepare_data
from models import SimpleCNN, UNetClassifier
import argparse
import os
import json

def evaluate(model, test_loader, device, classes, model_name='model'):
    model.to(device)
    model.eval()
    
    y_true = []
    y_pred = []
    
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())
            
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='weighted')
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    
    metrics = {
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }
    
    print(f"\n--- Metrics for {model_name} ---")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print("---------------------------------\n")
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=classes, yticklabels=classes, cmap='Blues')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'Confusion Matrix - {model_name}')
    plt.savefig(f'results/{model_name}_cm.png')
    plt.close()
    
    # Classification report
    report = classification_report(y_true, y_pred, target_names=classes, output_dict=True)
    
    with open(f'results/{model_name}_metrics.json', 'w') as f:
        json.dump(metrics, f)
        
    with open(f'results/{model_name}_report.json', 'w') as f:
        json.dump(report, f)
        
    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate Land Cover Classification Models')
    parser.add_argument('--model', type=str, default='cnn', choices=['cnn', 'unet'], help='Model type: cnn or unet')
    parser.add_argument('--data_dir', type=str, default='EuroSAT/2750', help='Path to dataset')
    parser.add_argument('--model_path', type=str, help='Path to model weights')
    
    args = parser.parse_args()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    _, test_loader, classes = prepare_data(args.data_dir, batch_size=32)
    num_classes = len(classes)
    
    if args.model == 'cnn':
        model = SimpleCNN(num_classes=num_classes)
    else:
        model = UNetClassifier(num_classes=num_classes)
        
    model_path = args.model_path if args.model_path else f'models/best_{args.model}.pth'
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"Loaded weights from {model_path}")
    else:
        print(f"Warning: Model weights not found at {model_path}. Evaluating untrained model.")
        
    os.makedirs('results', exist_ok=True)
    evaluate(model, test_loader, device, classes, model_name=args.model)

"""
Image classification training script.
Runs as a command job on Azure ML compute.

Inputs:
  --data-path: mounted path to the image folder data asset
  --n-estimators: number of trees in random forest

Outputs:
  MLflow-logged model to ./outputs/model/
"""
import argparse
import os
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from PIL import Image
import numpy as np


def load_images(data_path, img_size=(64, 64)):
    """Load images from label subfolders, return features and labels."""
    features, labels = [], []
    for label in sorted(os.listdir(data_path)):
        label_dir = os.path.join(data_path, label)
        if not os.path.isdir(label_dir):
            continue
        for fname in sorted(os.listdir(label_dir)):
            fpath = os.path.join(label_dir, fname)
            try:
                img = Image.open(fpath).convert("RGB").resize(img_size)
                features.append(np.array(img).flatten())
                labels.append(label)
            except Exception:
                continue
    return np.array(features), np.array(labels)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    mlflow.autolog()

    X, y = load_images(args.data_path)
    if len(X) == 0:
        print("ERROR: No images found. Check --data-path.")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=args.n_estimators, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    mlflow.log_metric("test_accuracy", accuracy)
    print(f"Test accuracy: {accuracy:.4f}")
    print(classification_report(y_test, y_pred))

    mlflow.sklearn.log_model(model, "model")


if __name__ == "__main__":
    main()

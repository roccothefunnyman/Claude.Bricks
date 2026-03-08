"""
Clustering training script for pattern extraction.
Runs as a command job on Azure ML compute.

Inputs:
  --data-path: path to features CSV from extract_stats.py
  --n-clusters: number of clusters for KMeans
  --method: clustering method (kmeans or hdbscan)

Outputs:
  MLflow-logged model and cluster assignments
"""
import argparse
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--n-clusters", type=int, default=5)
    parser.add_argument("--method", type=str, default="kmeans",
                        choices=["kmeans", "hdbscan"])
    args = parser.parse_args()

    mlflow.autolog()

    df = pd.read_csv(args.data_path)
    feature_cols = [c for c in df.columns if c != "filename"]
    X = df[feature_cols].values

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if args.method == "kmeans":
        model = KMeans(n_clusters=args.n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)
    else:
        import hdbscan
        model = hdbscan.HDBSCAN(min_cluster_size=3)
        labels = model.fit_predict(X_scaled)

    # Log metrics
    n_labels = len(set(labels) - {-1})
    mlflow.log_metric("n_clusters_found", n_labels)

    if n_labels > 1:
        mask = labels != -1
        if mask.sum() > n_labels:
            sil = silhouette_score(X_scaled[mask], labels[mask])
            mlflow.log_metric("silhouette_score", sil)
            print(f"Silhouette score: {sil:.4f}")

    # Save cluster assignments
    df["cluster"] = labels
    df.to_csv("outputs/cluster_assignments.csv", index=False)

    # Log the scaler + clustering model together
    mlflow.sklearn.log_model(model, "model")

    print(f"Found {n_labels} clusters across {len(df)} samples")
    for c in sorted(set(labels)):
        count = (labels == c).sum()
        print(f"  Cluster {c}: {count} samples")


if __name__ == "__main__":
    main()

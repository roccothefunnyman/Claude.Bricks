"""Anomaly detection / classification training for .ldr validation."""
import argparse
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--model-type", type=str, default="isolation_forest",
                        choices=["isolation_forest", "random_forest"])
    args = parser.parse_args()

    mlflow.autolog()

    df = pd.read_csv(args.data_path)
    feature_cols = ["overhang_ratio", "collision_count",
                    "height_to_base_ratio", "layer_density"]
    X = df[feature_cols]

    if args.model_type == "isolation_forest":
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X)
        preds = model.predict(X)
        # IsolationForest: -1 = anomaly, 1 = normal
        n_anomalies = (preds == -1).sum()
        mlflow.log_param("contamination", 0.1)
        mlflow.log_metric("n_anomalies", int(n_anomalies))
        print(f"Detected {n_anomalies} anomalies out of {len(X)} samples")
    else:
        y = df["label"]  # 0=pass, 1=fail
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        f1 = f1_score(y_test, preds)
        mlflow.log_metric("test_f1", f1)
        print(f"Test F1: {f1:.4f}")
        print(classification_report(y_test, preds))

    mlflow.sklearn.log_model(model, "model")


if __name__ == "__main__":
    main()

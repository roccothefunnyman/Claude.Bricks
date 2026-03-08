"""
Create baseline dataset profile for drift detection (Scenario 1: Facade Classification).

Loads the training data features, computes statistical distributions
(mean, std, percentiles, value counts), and saves the baseline profile
as a versioned JSON file. This baseline is used by detect_drift.py to
compare against recent inference data.

Usage:
    python monitoring/drift/create_baseline.py \
        --training-data data/scenario1/train_features.csv \
        --output monitoring/drift/baseline_profile.json

    # Or pull training data from AML datastore:
    python monitoring/drift/create_baseline.py \
        --datastore-name workspaceblobstore \
        --data-path scenario1/train_features.csv \
        --output monitoring/drift/baseline_profile.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def compute_feature_profile(series: pd.Series) -> dict[str, Any]:
    """Compute distributional statistics for a single numeric feature."""
    values = series.dropna()
    profile: dict[str, Any] = {
        "count": int(len(values)),
        "null_count": int(series.isna().sum()),
        "mean": float(values.mean()),
        "std": float(values.std()),
        "min": float(values.min()),
        "max": float(values.max()),
        "percentiles": {
            "p1": float(np.percentile(values, 1)),
            "p5": float(np.percentile(values, 5)),
            "p10": float(np.percentile(values, 10)),
            "p25": float(np.percentile(values, 25)),
            "p50": float(np.percentile(values, 50)),
            "p75": float(np.percentile(values, 75)),
            "p90": float(np.percentile(values, 90)),
            "p95": float(np.percentile(values, 95)),
            "p99": float(np.percentile(values, 99)),
        },
    }

    # Histogram bins for PSI calculation (10 equal-width bins)
    counts, bin_edges = np.histogram(values, bins=10)
    profile["histogram"] = {
        "counts": [int(c) for c in counts],
        "bin_edges": [float(e) for e in bin_edges],
    }

    return profile


def compute_categorical_profile(series: pd.Series) -> dict[str, Any]:
    """Compute distributional statistics for a categorical feature."""
    values = series.dropna()
    value_counts = values.value_counts(normalize=True)
    return {
        "count": int(len(values)),
        "null_count": int(series.isna().sum()),
        "n_unique": int(values.nunique()),
        "value_proportions": {str(k): float(v) for k, v in value_counts.items()},
    }


def create_baseline_profile(
    df: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
) -> dict[str, Any]:
    """Create a complete baseline profile for all features."""
    profile: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(df),
        "features": {},
    }

    for col in numeric_features:
        if col not in df.columns:
            logger.warning("Numeric feature '%s' not found in data, skipping", col)
            continue
        logger.info("Profiling numeric feature: %s", col)
        profile["features"][col] = {
            "type": "numeric",
            **compute_feature_profile(df[col]),
        }

    for col in categorical_features:
        if col not in df.columns:
            logger.warning("Categorical feature '%s' not found in data, skipping", col)
            continue
        logger.info("Profiling categorical feature: %s", col)
        profile["features"][col] = {
            "type": "categorical",
            **compute_categorical_profile(df[col]),
        }

    return profile


def load_data(args: argparse.Namespace) -> pd.DataFrame:
    """Load training data from local file or AML datastore."""
    if args.training_data:
        path = Path(args.training_data)
        if not path.exists():
            logger.error("Training data file not found: %s", path)
            sys.exit(1)
        logger.info("Loading training data from %s", path)
        return pd.read_csv(path)

    if args.datastore_name:
        logger.info(
            "Loading training data from AML datastore %s/%s",
            args.datastore_name,
            args.data_path,
        )
        try:
            from azure.ai.ml import MLClient
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            ml_client = MLClient.from_config(credential=credential)
            datastore = ml_client.datastores.get(args.datastore_name)

            # Download data locally for processing
            import tempfile
            tmp_dir = tempfile.mkdtemp()
            local_path = Path(tmp_dir) / "train_features.csv"

            from azure.storage.blob import BlobServiceClient
            blob_client = BlobServiceClient(
                account_url=f"https://{datastore.account_name}.blob.core.windows.net",
                credential=credential,
            )
            container_client = blob_client.get_container_client(
                datastore.container_name
            )
            blob_data = container_client.download_blob(args.data_path).readall()
            local_path.write_bytes(blob_data)
            return pd.read_csv(local_path)
        except Exception as exc:
            logger.error("Failed to load from AML datastore: %s", exc)
            sys.exit(1)

    logger.error("Specify either --training-data or --datastore-name + --data-path")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create baseline dataset profile for drift detection"
    )
    parser.add_argument(
        "--training-data",
        type=str,
        help="Path to local CSV file with training features",
    )
    parser.add_argument(
        "--datastore-name",
        type=str,
        help="AML datastore name",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path within AML datastore",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="monitoring/drift/baseline_profile.json",
        help="Output path for baseline profile JSON",
    )
    parser.add_argument(
        "--numeric-features",
        type=str,
        nargs="*",
        default=[
            "mean_pixel_intensity",
            "std_pixel_intensity",
            "image_width",
            "image_height",
            "edge_density",
            "color_histogram_r",
            "color_histogram_g",
            "color_histogram_b",
        ],
        help="Numeric feature column names",
    )
    parser.add_argument(
        "--categorical-features",
        type=str,
        nargs="*",
        default=["predicted_class"],
        help="Categorical feature column names",
    )

    args = parser.parse_args()
    df = load_data(args)

    logger.info("Loaded %d rows with columns: %s", len(df), list(df.columns))

    profile = create_baseline_profile(
        df,
        numeric_features=args.numeric_features,
        categorical_features=args.categorical_features,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, indent=2))
    logger.info(
        "Baseline profile saved to %s (%d features profiled)",
        output_path,
        len(profile["features"]),
    )


if __name__ == "__main__":
    main()

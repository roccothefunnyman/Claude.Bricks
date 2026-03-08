"""
Register versioned data assets in the AML workspace.

Registers uri_folder data assets for each scenario's training data,
enabling versioned references in pipelines and experiments.

Usage:
  source scripts/config.sh
  cd deploymentcode/scripts
  python register_data_assets.py
  python register_data_assets.py --version 2
"""
import argparse
import os
import sys

# Add scripts dir to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client


# Data assets mapped to their datastore paths and descriptions.
DATA_ASSETS = [
    {
        "name": "facade-images",
        "description": "Facade classification training images (Scenario 1)",
        "datastore": "facade_images",
        "path_on_datastore": "training/",
    },
    {
        "name": "structural-features",
        "description": "Structural anomaly feature data (Scenario 2)",
        "datastore": "training_data",
        "path_on_datastore": "structural-features/",
    },
    {
        "name": "pattern-stats",
        "description": "Pattern clustering statistics (Scenario 3)",
        "datastore": "training_data",
        "path_on_datastore": "pattern-stats/",
    },
    {
        "name": "spec-training-data",
        "description": "Spec generation training data for GenAI (Scenario 4)",
        "datastore": "training_data",
        "path_on_datastore": "spec-training/",
    },
]


def register_data_assets(ml_client, version: str):
    """Register each data asset as a versioned uri_folder."""
    registered = []
    for asset_def in DATA_ASSETS:
        path = (
            f"azureml://datastores/{asset_def['datastore']}"
            f"/paths/{asset_def['path_on_datastore']}"
        )
        data_asset = Data(
            name=asset_def["name"],
            version=version,
            description=asset_def["description"],
            type=AssetTypes.URI_FOLDER,
            path=path,
        )
        result = ml_client.data.create_or_update(data_asset)
        registered.append(result)
        print(f"  Registered data asset: {result.name}:{result.version}")

    return registered


def main():
    parser = argparse.ArgumentParser(
        description="Register versioned data assets in the AML workspace."
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1",
        help="Version number for the data assets (default: 1)",
    )
    args = parser.parse_args()

    ml_client = get_ml_client()

    print(f"Registering data assets (version {args.version})...")
    registered = register_data_assets(ml_client, args.version)

    print(f"\nRegistered {len(registered)} data assets.")


if __name__ == "__main__":
    main()

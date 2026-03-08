"""Upload engineered features and create data asset."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client


def main():
    ml_client = get_ml_client()

    data_asset = Data(
        name="ldr-validation-features",
        version="1",
        description="Engineered features from .ldr files for anomaly detection",
        path="../../data/scenario2/features.csv",
        type=AssetTypes.URI_FILE,
    )
    ml_client.data.create_or_update(data_asset)
    print("Created data asset: ldr-validation-features:1")


if __name__ == "__main__":
    main()

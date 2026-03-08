"""Upload reference .ldr files and create data asset."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client


def main():
    ml_client = get_ml_client()

    data_asset = Data(
        name="reference-models",
        version="1",
        description="Reference .ldr files for pattern extraction",
        path="../../data/scenario3/",
        type=AssetTypes.URI_FOLDER,
    )
    ml_client.data.create_or_update(data_asset)
    print("Created data asset: reference-models:1")


if __name__ == "__main__":
    main()

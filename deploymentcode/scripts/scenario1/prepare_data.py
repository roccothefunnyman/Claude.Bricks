"""Upload labeled images and register as a data asset."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client


def main():
    ml_client = get_ml_client()

    data_asset = Data(
        name="facade-images",
        version="1",
        description="Labeled facade images for style classification",
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "scenario1"),
        type=AssetTypes.URI_FOLDER,
    )
    ml_client.data.create_or_update(data_asset)
    print("Created data asset: facade-images:1")


if __name__ == "__main__":
    main()

"""Register the best model from the training run."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml.entities import Model
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-name", type=str, required=True,
                        help="Job name from train_job.py output")
    args = parser.parse_args()

    ml_client = get_ml_client()

    model = Model(
        path=f"azureml://jobs/{args.job_name}/outputs/artifacts/paths/model/",
        name="facade-classifier",
        description="Facade style classifier (RF on image pixels)",
        type=AssetTypes.MLFLOW_MODEL,
    )

    registered = ml_client.models.create_or_update(model)
    print(f"Registered: {registered.name} version {registered.version}")


if __name__ == "__main__":
    main()

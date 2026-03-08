"""Submit a training job for facade classification."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml import command, Input
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client


def main():
    ml_client = get_ml_client()

    job = command(
        code="./",
        command="python train.py --data-path ${{inputs.data}} --n-estimators 200",
        inputs={
            "data": Input(
                type=AssetTypes.URI_FOLDER,
                path="azureml:facade-images:1",
            ),
        },
        environment="azureml:claudebricks-sklearn:1",
        compute="cpu-cluster",
        experiment_name="scenario1-facade-classification",
        display_name="facade-classification-rf",
        description="Random forest classifier on facade images",
    )

    returned_job = ml_client.jobs.create_or_update(job)
    print(f"Job submitted: {returned_job.name}")
    print(f"Studio URL: {returned_job.studio_url}")


if __name__ == "__main__":
    main()

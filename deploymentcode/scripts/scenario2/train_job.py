"""Submit a training job for structural validation."""
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
        command="python train.py --data-path ${{inputs.data}} --model-type isolation_forest",
        inputs={
            "data": Input(
                type=AssetTypes.URI_FILE,
                path="azureml:ldr-validation-features:1",
            ),
        },
        environment="azureml:claudebricks-sklearn:1",
        compute="cpu-cluster",
        experiment_name="scenario2-structural-validation",
        display_name="ldr-anomaly-detection",
        description="Isolation forest anomaly detection on .ldr features",
    )

    returned_job = ml_client.jobs.create_or_update(job)
    print(f"Job submitted: {returned_job.name}")
    print(f"Studio URL: {returned_job.studio_url}")


if __name__ == "__main__":
    main()

"""Submit a single-step clustering job."""
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
        command="python train.py --data-path ${{inputs.features}} --n-clusters 5",
        inputs={
            "features": Input(
                type=AssetTypes.URI_FILE,
                path="azureml:ldr-part-stats:1",
            ),
        },
        environment="azureml:claudebricks-clustering:1",
        compute="cpu-cluster",
        experiment_name="scenario3-pattern-extraction",
        display_name="ldr-clustering-kmeans",
        description="KMeans clustering on .ldr part-usage features",
    )

    returned_job = ml_client.jobs.create_or_update(job)
    print(f"Job submitted: {returned_job.name}")
    print(f"Studio URL: {returned_job.studio_url}")


if __name__ == "__main__":
    main()

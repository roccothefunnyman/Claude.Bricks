"""Multi-step pipeline: extract features -> cluster -> evaluate."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml import command, Input, Output, dsl
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client


def main():
    ml_client = get_ml_client()

    # Step 1: Feature extraction
    extract_component = command(
        name="extract_features",
        display_name="Extract .ldr Statistics",
        code="./",
        command=(
            "python extract_stats.py "
            "--input-path ${{inputs.ldr_data}} "
            "--output-path ${{outputs.features}}/stats.csv"
        ),
        inputs={"ldr_data": Input(type=AssetTypes.URI_FOLDER)},
        outputs={"features": Output(type=AssetTypes.URI_FOLDER)},
        environment="azureml:claudebricks-clustering:1",
        compute="cpu-cluster",
    )

    # Step 2: Clustering
    cluster_component = command(
        name="run_clustering",
        display_name="Cluster Buildings",
        code="./",
        command=(
            "python train.py "
            "--data-path ${{inputs.features}}/stats.csv "
            "--n-clusters 5"
        ),
        inputs={"features": Input(type=AssetTypes.URI_FOLDER)},
        environment="azureml:claudebricks-clustering:1",
        compute="cpu-cluster",
    )

    @dsl.pipeline(
        compute="cpu-cluster",
        experiment_name="scenario3-pattern-extraction",
        description="Extract features from .ldr files, then cluster",
    )
    def pattern_extraction_pipeline(ldr_data):
        step1 = extract_component(ldr_data=ldr_data)
        step2 = cluster_component(features=step1.outputs.features)
        return {"cluster_results": step2.outputs}

    pipeline = pattern_extraction_pipeline(
        ldr_data=Input(type=AssetTypes.URI_FOLDER, path="azureml:reference-models:1")
    )

    returned_job = ml_client.jobs.create_or_update(pipeline)
    print(f"Pipeline submitted: {returned_job.name}")
    print(f"Studio URL: {returned_job.studio_url}")


if __name__ == "__main__":
    main()

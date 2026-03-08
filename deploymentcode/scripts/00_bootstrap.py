"""
Bootstrap: create datastores, environments, and verify compute.
Run after Terraform apply and sourcing config.sh.

Usage:
  source scripts/config.sh
  cd deploymentcode/scripts
  python 00_bootstrap.py
"""
import os
import sys

# Add scripts dir to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    AzureBlobDatastore,
    Environment,
)
from azure.identity import DefaultAzureCredential
from common.ml_client import get_ml_client


def create_datastores(ml_client: MLClient, storage_name: str):
    """Create datastores for each scenario's blob container."""
    containers = {
        "facade_images": "facade-images",
        "ldr_files": "ldr-files",
        "reference_models": "reference-models",
        "training_data": "training-data",
    }
    for ds_name, container in containers.items():
        ds = AzureBlobDatastore(
            name=ds_name,
            account_name=storage_name,
            container_name=container,
            description=f"Datastore for {container} container",
        )
        ml_client.datastores.create_or_update(ds)
        print(f"  Created/updated datastore: {ds_name} -> {container}")


def register_environments(ml_client: MLClient):
    """Register custom environments for training jobs."""

    # Scenario 1 & 2: scikit-learn + image processing
    sklearn_env = Environment(
        name="claudebricks-sklearn",
        description="scikit-learn environment for classification and anomaly detection",
        conda_file={
            "name": "claudebricks-sklearn",
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                "python=3.10",
                "pip",
                {
                    "pip": [
                        "azure-ai-ml>=1.12.0",
                        "mlflow>=2.10.0,<=2.16.2",
                        "scikit-learn>=1.4.0",
                        "pandas>=2.1.0",
                        "Pillow>=10.0.0",
                        "matplotlib>=3.8.0",
                    ]
                },
            ],
        },
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest",
        version="1",
    )
    ml_client.environments.create_or_update(sklearn_env)
    print("  Registered environment: claudebricks-sklearn:1")

    # Scenario 3: clustering + embeddings
    cluster_env = Environment(
        name="claudebricks-clustering",
        description="Environment for clustering and embedding extraction",
        conda_file={
            "name": "claudebricks-clustering",
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                "python=3.10",
                "pip",
                {
                    "pip": [
                        "azure-ai-ml>=1.12.0",
                        "mlflow>=2.10.0,<=2.16.2",
                        "scikit-learn>=1.4.0",
                        "pandas>=2.1.0",
                        "umap-learn>=0.5.5",
                        "hdbscan>=0.8.33",
                    ]
                },
            ],
        },
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest",
        version="1",
    )
    ml_client.environments.create_or_update(cluster_env)
    print("  Registered environment: claudebricks-clustering:1")


def verify_compute(ml_client: MLClient):
    """List compute targets to confirm they exist."""
    computes = ml_client.compute.list()
    print("  Available compute targets:")
    for c in computes:
        print(f"    - {c.name} ({c.type}, size={getattr(c, 'size', 'N/A')})")


def main():
    ml_client = get_ml_client()
    storage_name = os.environ["STORAGE_ACCOUNT"]

    print("1. Creating datastores...")
    create_datastores(ml_client, storage_name)

    print("2. Registering environments...")
    register_environments(ml_client)

    print("3. Verifying compute targets...")
    verify_compute(ml_client)

    print("\nBootstrap complete.")


if __name__ == "__main__":
    main()

"""
Orchestrate model promotion from dev workspace to test workspace.

Steps:
  1. Publish model from source workspace to shared registry
  2. Import model from shared registry into target workspace
  3. Optionally trigger deployment to target endpoint

Usage:
  source scripts/config.sh
  cd deploymentcode/scripts
  python promote_model.py \
    --model-name facade-classifier \
    --model-version 1 \
    --source-workspace mlw-claudebricks-dev \
    --target-workspace mlw-claudebricks-test \
    --registry-name reg-claudebricks

  # With deployment trigger:
  python promote_model.py \
    --model-name facade-classifier \
    --model-version 1 \
    --source-workspace mlw-claudebricks-dev \
    --target-workspace mlw-claudebricks-test \
    --registry-name reg-claudebricks \
    --deploy-endpoint facade-classifier-endpoint
"""
import argparse
import os
import sys

# Add scripts dir to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineDeployment,
    Model,
)
from azure.identity import DefaultAzureCredential


def get_workspace_client(workspace_name: str) -> MLClient:
    """Create an MLClient for a specific workspace."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=workspace_name,
    )


def get_registry_client(registry_name: str) -> MLClient:
    """Create an MLClient scoped to a shared AML registry."""
    return MLClient(
        credential=DefaultAzureCredential(),
        registry_name=registry_name,
    )


def publish_to_registry(
    source_client: MLClient, reg_client: MLClient, model_name: str, model_version: str
):
    """Publish model from source workspace to shared registry."""
    print(f"  Fetching model {model_name}:{model_version} from source workspace...")
    ws_model = source_client.models.get(name=model_name, version=model_version)

    registry_model = Model(
        name=ws_model.name,
        version=ws_model.version,
        path=ws_model.path,
        type=ws_model.type,
        description=ws_model.description,
        properties=ws_model.properties,
        tags=ws_model.tags,
    )
    result = reg_client.models.create_or_update(registry_model)
    print(f"  Published to registry: {result.name}:{result.version}")
    return result


def import_to_workspace(
    reg_client: MLClient,
    target_client: MLClient,
    model_name: str,
    model_version: str,
):
    """Import model from shared registry into target workspace."""
    print(f"  Fetching model {model_name}:{model_version} from registry...")
    reg_model = reg_client.models.get(name=model_name, version=model_version)

    target_model = Model(
        name=reg_model.name,
        version=reg_model.version,
        path=reg_model.path,
        type=reg_model.type,
        description=reg_model.description,
        properties=reg_model.properties,
        tags=reg_model.tags,
    )
    result = target_client.models.create_or_update(target_model)
    print(f"  Imported into target workspace: {result.name}:{result.version}")
    return result


def trigger_deployment(
    target_client: MLClient,
    endpoint_name: str,
    model_name: str,
    model_version: str,
):
    """Create or update a deployment on the target endpoint."""
    print(f"  Deploying {model_name}:{model_version} to endpoint {endpoint_name}...")
    deployment = ManagedOnlineDeployment(
        name=f"{model_name}-v{model_version}".replace(".", "-"),
        endpoint_name=endpoint_name,
        model=f"azureml:{model_name}:{model_version}",
        instance_type="Standard_DS2_v2",
        instance_count=1,
    )
    result = target_client.online_deployments.begin_create_or_update(
        deployment
    ).result()
    print(f"  Deployment created: {result.name}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate model promotion from dev to test workspace."
    )
    parser.add_argument(
        "--model-name",
        type=str,
        required=True,
        help="Name of the model to promote",
    )
    parser.add_argument(
        "--model-version",
        type=str,
        required=True,
        help="Version of the model to promote",
    )
    parser.add_argument(
        "--source-workspace",
        type=str,
        required=True,
        help="Source AML workspace name (e.g., mlw-claudebricks-dev)",
    )
    parser.add_argument(
        "--target-workspace",
        type=str,
        required=True,
        help="Target AML workspace name (e.g., mlw-claudebricks-test)",
    )
    parser.add_argument(
        "--registry-name",
        type=str,
        required=True,
        help="Shared AML registry name (e.g., reg-claudebricks)",
    )
    parser.add_argument(
        "--deploy-endpoint",
        type=str,
        default=None,
        help="Endpoint name in target workspace to deploy to (optional)",
    )
    args = parser.parse_args()

    source_client = get_workspace_client(args.source_workspace)
    target_client = get_workspace_client(args.target_workspace)
    reg_client = get_registry_client(args.registry_name)

    # Step 1: Publish to registry
    print(f"\nStep 1: Publishing model to registry '{args.registry_name}'...")
    publish_to_registry(
        source_client, reg_client, args.model_name, args.model_version
    )

    # Step 2: Import into target workspace
    print(f"\nStep 2: Importing model into workspace '{args.target_workspace}'...")
    import_to_workspace(
        reg_client, target_client, args.model_name, args.model_version
    )

    # Step 3: Optionally trigger deployment
    if args.deploy_endpoint:
        print(f"\nStep 3: Deploying to endpoint '{args.deploy_endpoint}'...")
        trigger_deployment(
            target_client,
            args.deploy_endpoint,
            args.model_name,
            args.model_version,
        )
    else:
        print("\nStep 3: Skipped (no --deploy-endpoint specified).")

    print("\nPromotion complete.")


if __name__ == "__main__":
    main()

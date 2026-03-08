"""
Publish assets from workspace to a shared AML registry.

Copies a model, environment, or component from the current workspace
to a shared registry for cross-workspace consumption.

Usage:
  source scripts/config.sh
  cd deploymentcode/scripts
  python publish_to_registry.py --registry-name reg-claudebricks --asset-type model --asset-name facade-classifier --asset-version 1
  python publish_to_registry.py --registry-name reg-claudebricks --asset-type environment --asset-name claudebricks-sklearn --asset-version 1
  python publish_to_registry.py --registry-name reg-claudebricks --asset-type component --asset-name prepare-data --asset-version 1.0
"""
import argparse
import os
import sys

# Add scripts dir to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model, Environment, CommandComponent
from azure.identity import DefaultAzureCredential
from common.ml_client import get_ml_client


VALID_ASSET_TYPES = ("model", "environment", "component")


def get_registry_client(registry_name: str) -> MLClient:
    """Create an MLClient scoped to a shared AML registry."""
    return MLClient(
        credential=DefaultAzureCredential(),
        registry_name=registry_name,
    )


def publish_model(ws_client: MLClient, reg_client: MLClient, name: str, version: str):
    """Publish a model from workspace to registry."""
    print(f"  Fetching model {name}:{version} from workspace...")
    ws_model = ws_client.models.get(name=name, version=version)

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
    print(f"  Published model: {result.name}:{result.version}")
    return result


def publish_environment(
    ws_client: MLClient, reg_client: MLClient, name: str, version: str
):
    """Publish an environment from workspace to registry."""
    print(f"  Fetching environment {name}:{version} from workspace...")
    ws_env = ws_client.environments.get(name=name, version=version)

    registry_env = Environment(
        name=ws_env.name,
        version=ws_env.version,
        image=ws_env.image,
        conda_file=ws_env.conda_file,
        description=ws_env.description,
        tags=ws_env.tags,
    )
    result = reg_client.environments.create_or_update(registry_env)
    print(f"  Published environment: {result.name}:{result.version}")
    return result


def publish_component(
    ws_client: MLClient, reg_client: MLClient, name: str, version: str
):
    """Publish a component from workspace to registry."""
    print(f"  Fetching component {name}:{version} from workspace...")
    ws_component = ws_client.components.get(name=name, version=version)

    result = reg_client.components.create_or_update(ws_component)
    print(f"  Published component: {result.name}:{result.version}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Publish assets from workspace to a shared AML registry."
    )
    parser.add_argument(
        "--registry-name",
        type=str,
        required=True,
        help="Name of the shared AML registry (e.g., reg-claudebricks)",
    )
    parser.add_argument(
        "--asset-type",
        type=str,
        required=True,
        choices=VALID_ASSET_TYPES,
        help="Type of asset to publish: model, environment, or component",
    )
    parser.add_argument(
        "--asset-name",
        type=str,
        required=True,
        help="Name of the asset in the workspace",
    )
    parser.add_argument(
        "--asset-version",
        type=str,
        required=True,
        help="Version of the asset to publish",
    )
    args = parser.parse_args()

    ws_client = get_ml_client()
    reg_client = get_registry_client(args.registry_name)

    print(
        f"Publishing {args.asset_type} '{args.asset_name}:{args.asset_version}' "
        f"to registry '{args.registry_name}'..."
    )

    publishers = {
        "model": publish_model,
        "environment": publish_environment,
        "component": publish_component,
    }
    publish_fn = publishers[args.asset_type]
    publish_fn(ws_client, reg_client, args.asset_name, args.asset_version)

    print("\nPublish complete.")


if __name__ == "__main__":
    main()

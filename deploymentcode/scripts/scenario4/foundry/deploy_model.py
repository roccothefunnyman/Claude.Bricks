"""
Deploy a foundation model through Microsoft AI Foundry.

Deploys a model (e.g., gpt-4o) via serverless API endpoint or managed
compute through the Foundry project's model catalog.

Usage:
    python deploy_model.py --model-name gpt-4o --deployment-name gpt4o-deploy
    python deploy_model.py --model-name gpt-4o-mini --deployment-name gpt4o-mini-deploy --sku-capacity 20

Environment variables:
    SUBSCRIPTION_ID     Azure subscription ID
    RESOURCE_GROUP      Azure resource group name
    FOUNDRY_PROJECT     Foundry project name (workspace)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ServerlessEndpoint,
    ServerlessEndpointProperties,
    ModelConfiguration,
)
from azure.identity import DefaultAzureCredential


def get_project_client(project_name):
    """Create an MLClient scoped to the Foundry project."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=project_name,
    )


def list_available_models(client, model_filter=None):
    """List models available in the Foundry model catalog."""
    print("Querying model catalog...")
    models = client.models.list()
    results = []
    for model in models:
        if model_filter and model_filter.lower() not in model.name.lower():
            continue
        results.append(model)
    return results


def deploy_serverless(client, model_name, deployment_name):
    """Deploy a model as a serverless API endpoint."""
    print(f"Deploying '{model_name}' as serverless endpoint '{deployment_name}'...")

    endpoint = ServerlessEndpoint(
        name=deployment_name,
        model_id=f"azureml://registries/azure-openai/models/{model_name}",
        properties=ServerlessEndpointProperties(
            model_settings=ModelConfiguration(
                model_name=model_name,
            ),
        ),
    )

    result = client.serverless_endpoints.begin_create_or_update(endpoint).result()
    print(f"Deployment '{deployment_name}' created successfully.")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Deploy a foundation model through Foundry"
    )
    parser.add_argument("--project-name", type=str,
                        default=os.environ.get("FOUNDRY_PROJECT", "claudebricks-genai"),
                        help="Foundry project name")
    parser.add_argument("--model-name", type=str, default="gpt-4o",
                        help="Model name from the catalog (e.g., gpt-4o, gpt-4o-mini)")
    parser.add_argument("--deployment-name", type=str, default=None,
                        help="Name for the deployment (defaults to model-name-deploy)")
    parser.add_argument("--list-models", action="store_true",
                        help="List available models and exit")
    parser.add_argument("--sku-capacity", type=int, default=10,
                        help="SKU capacity (tokens-per-minute in thousands)")
    args = parser.parse_args()

    if args.deployment_name is None:
        args.deployment_name = f"{args.model_name.replace('.', '-')}-deploy"

    client = get_project_client(args.project_name)

    # List models if requested
    if args.list_models:
        models = list_available_models(client, model_filter=args.model_name)
        if models:
            print(f"Found {len(models)} matching model(s):")
            for m in models[:20]:
                print(f"  {m.name} (version: {getattr(m, 'version', 'N/A')})")
        else:
            print("No matching models found in catalog.")
        return

    # Deploy the model
    print("=" * 60)
    print(f"Deploying Model via Foundry")
    print("=" * 60)
    print(f"  Project:     {args.project_name}")
    print(f"  Model:       {args.model_name}")
    print(f"  Deployment:  {args.deployment_name}")
    print(f"  Capacity:    {args.sku_capacity}K TPM")
    print()

    result = deploy_serverless(client, args.model_name, args.deployment_name)

    # Print endpoint details
    print()
    print("=" * 60)
    print("Deployment Complete")
    print("=" * 60)
    endpoint_url = getattr(result, "scoring_uri", None) or getattr(result, "url", "N/A")
    print(f"  Endpoint URL:  {endpoint_url}")
    print(f"  Deployment:    {args.deployment_name}")
    print(f"  Status:        {getattr(result, 'provisioning_state', 'Unknown')}")
    print()
    print("Test with:")
    print(f"  curl -X POST {endpoint_url} \\")
    print(f'    -H "Authorization: Bearer $(az ml serverless-endpoint get-credentials '
          f'--name {args.deployment_name} --query key -o tsv)" \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"messages": [{{"role": "user", "content": "Hello"}}]}}\'')


if __name__ == "__main__":
    main()

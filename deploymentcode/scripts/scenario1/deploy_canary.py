"""Deploy a new model version as a canary (green) deployment with 0% traffic.

Usage:
    python deploy_canary.py --model-name facade-classifier --model-version 2
    python deploy_canary.py --model-name facade-classifier --model-version 2 \
        --endpoint-name my-endpoint --deployment-name green
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml.entities import ManagedOnlineDeployment, CodeConfiguration
from common.ml_client import get_ml_client


def main():
    parser = argparse.ArgumentParser(
        description="Deploy a new model version as a canary deployment with 0% traffic."
    )
    parser.add_argument("--model-name", required=True, help="Registered model name")
    parser.add_argument("--model-version", required=True, help="Model version to deploy")
    parser.add_argument(
        "--endpoint-name",
        default="facade-classifier-endpoint",
        help="Target endpoint name (default: facade-classifier-endpoint)",
    )
    parser.add_argument(
        "--deployment-name",
        default="green",
        help="Name for the canary deployment (default: green)",
    )
    args = parser.parse_args()

    ml_client = get_ml_client()

    # Verify the endpoint exists
    endpoint = ml_client.online_endpoints.get(args.endpoint_name)
    print(f"Endpoint '{endpoint.name}' found (provisioning state: {endpoint.provisioning_state}).")

    # Create the canary deployment with 0% traffic
    model_id = f"azureml:{args.model_name}:{args.model_version}"
    deployment = ManagedOnlineDeployment(
        name=args.deployment_name,
        endpoint_name=args.endpoint_name,
        model=model_id,
        code_configuration=CodeConfiguration(
            code="./",
            scoring_script="score.py",
        ),
        environment="azureml:claudebricks-sklearn:1",
        instance_type="Standard_DS3_v2",
        instance_count=1,
    )
    print(f"Creating canary deployment '{args.deployment_name}' with model {model_id}...")
    ml_client.online_deployments.begin_create_or_update(deployment).result()

    # Ensure 0% traffic goes to canary (preserve existing traffic split)
    traffic = dict(endpoint.traffic) if endpoint.traffic else {}
    traffic[args.deployment_name] = 0
    endpoint.traffic = traffic
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()

    print(f"Canary deployment '{args.deployment_name}' created with 0% traffic.")
    print(f"Current traffic allocation: {endpoint.traffic}")


if __name__ == "__main__":
    main()

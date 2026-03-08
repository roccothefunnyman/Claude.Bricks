"""Create a managed online endpoint and deploy the facade classifier."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    CodeConfiguration,
)
from common.ml_client import get_ml_client


def main():
    ml_client = get_ml_client()

    # 1. Create endpoint
    endpoint = ManagedOnlineEndpoint(
        name="facade-classifier-endpoint",
        description="Real-time facade style classification",
        auth_mode="key",
    )
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("Endpoint created.")

    # 2. Create deployment
    deployment = ManagedOnlineDeployment(
        name="blue",
        endpoint_name="facade-classifier-endpoint",
        model="azureml:facade-classifier:1",
        code_configuration=CodeConfiguration(
            code="./",
            scoring_script="score.py",
        ),
        environment="azureml:claudebricks-sklearn:1",
        instance_type="Standard_DS3_v2",
        instance_count=1,
    )
    ml_client.online_deployments.begin_create_or_update(deployment).result()

    # 3. Route 100% traffic to the deployment
    endpoint.traffic = {"blue": 100}
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("Deployment complete. 100% traffic routed to 'blue'.")


if __name__ == "__main__":
    main()

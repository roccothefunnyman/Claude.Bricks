"""Shared MLClient factory. Reads config from environment variables."""
import os
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential


def get_ml_client() -> MLClient:
    """Create an MLClient using environment variables set by config.sh."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=os.environ["ML_WORKSPACE"],
    )

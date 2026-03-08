"""
Create and configure a Microsoft AI Foundry project.

Verifies or creates a Foundry hub and project, then connects existing
Azure OpenAI and AI Search resources as project connections.

Usage:
    python create_project.py --hub-name my-hub --project-name my-project

Environment variables:
    SUBSCRIPTION_ID     Azure subscription ID
    RESOURCE_GROUP      Azure resource group name
    ML_WORKSPACE        AML workspace name (used as fallback)
    OPENAI_ENDPOINT     Azure OpenAI endpoint URL
    SEARCH_ENDPOINT     Azure AI Search endpoint URL
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    Hub,
    Project,
    WorkspaceConnection,
)
from azure.ai.ml.entities._credentials import ApiKeyConfiguration
from azure.identity import DefaultAzureCredential


def get_foundry_client():
    """Create an MLClient scoped to the subscription/resource group."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
    )


def ensure_hub(client, hub_name, location="eastus"):
    """Verify or create a Foundry hub."""
    try:
        hub = client.workspaces.get(hub_name)
        print(f"Hub '{hub_name}' already exists in {hub.location}.")
        return hub
    except Exception:
        print(f"Creating hub '{hub_name}' in {location}...")
        hub = Hub(
            name=hub_name,
            location=location,
            display_name=f"Claude.Bricks Foundry Hub",
            description="AI Foundry hub for Claude.Bricks GenAI operations",
        )
        hub = client.workspaces.begin_create(hub).result()
        print(f"Hub '{hub_name}' created successfully.")
        return hub


def ensure_project(client, hub_name, project_name):
    """Verify or create a Foundry project linked to the hub."""
    try:
        project = client.workspaces.get(project_name)
        print(f"Project '{project_name}' already exists.")
        return project
    except Exception:
        print(f"Creating project '{project_name}' under hub '{hub_name}'...")
        project = Project(
            name=project_name,
            hub_id=f"/subscriptions/{os.environ['SUBSCRIPTION_ID']}"
                   f"/resourceGroups/{os.environ['RESOURCE_GROUP']}"
                   f"/providers/Microsoft.MachineLearningServices"
                   f"/workspaces/{hub_name}",
            display_name="Claude.Bricks GenAI Project",
            description="Foundry project for LEGO spec generation with RAG",
        )
        project = client.workspaces.begin_create(project).result()
        print(f"Project '{project_name}' created successfully.")
        return project


def add_connection(project_client, name, target, conn_type, category):
    """Add a resource connection to the Foundry project."""
    try:
        existing = project_client.connections.get(name)
        print(f"  Connection '{name}' already exists -> {existing.target}")
        return existing
    except Exception:
        print(f"  Creating connection '{name}' -> {target}")
        connection = WorkspaceConnection(
            name=name,
            type=conn_type,
            target=target,
            credentials=ApiKeyConfiguration(key="placeholder"),
            metadata={"category": category},
        )
        result = project_client.connections.create_or_update(connection)
        print(f"  Connection '{name}' created.")
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Create/configure a Foundry hub and project"
    )
    parser.add_argument("--hub-name", type=str, default="claudebricks-hub",
                        help="Name for the Foundry hub")
    parser.add_argument("--project-name", type=str, default="claudebricks-genai",
                        help="Name for the Foundry project")
    parser.add_argument("--location", type=str, default="eastus",
                        help="Azure region for the hub")
    args = parser.parse_args()

    client = get_foundry_client()

    # 1. Ensure hub exists
    print("=" * 60)
    print("Step 1: Foundry Hub")
    print("=" * 60)
    hub = ensure_hub(client, args.hub_name, args.location)

    # 2. Ensure project exists
    print()
    print("=" * 60)
    print("Step 2: Foundry Project")
    print("=" * 60)
    project = ensure_project(client, args.hub_name, args.project_name)

    # 3. Connect resources
    print()
    print("=" * 60)
    print("Step 3: Resource Connections")
    print("=" * 60)
    project_client = MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=args.project_name,
    )

    openai_endpoint = os.environ.get("OPENAI_ENDPOINT", "")
    search_endpoint = os.environ.get("SEARCH_ENDPOINT", "")

    if openai_endpoint:
        add_connection(
            project_client,
            name="aoai-connection",
            target=openai_endpoint,
            conn_type="azure_open_ai",
            category="AzureOpenAI",
        )
    else:
        print("  Skipping OpenAI connection (OPENAI_ENDPOINT not set)")

    if search_endpoint:
        add_connection(
            project_client,
            name="search-connection",
            target=search_endpoint,
            conn_type="cognitive_search",
            category="CognitiveSearch",
        )
    else:
        print("  Skipping AI Search connection (SEARCH_ENDPOINT not set)")

    # 4. Print summary
    print()
    print("=" * 60)
    print("Project Summary")
    print("=" * 60)
    print(f"  Hub:              {args.hub_name}")
    print(f"  Project:          {args.project_name}")
    print(f"  Location:         {args.location}")
    print(f"  OpenAI endpoint:  {openai_endpoint or '(not configured)'}")
    print(f"  Search endpoint:  {search_endpoint or '(not configured)'}")
    print()
    print("Next steps:")
    print("  1. Deploy a model:    python deploy_model.py")
    print("  2. Configure index:   python configure_index.py")
    print("  3. Run evaluation:    python run_evaluation.py")


if __name__ == "__main__":
    main()

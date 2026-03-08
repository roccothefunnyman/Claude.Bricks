"""
Register versioned environments in the AML workspace.

Registers two environments:
  - claudebricks-sklearn: scikit-learn stack for Scenarios 1-3
  - claudebricks-genai: Azure OpenAI + LangChain stack for Scenario 4

Usage:
  source scripts/config.sh
  cd deploymentcode/scripts
  python register_envs.py
  python register_envs.py --version 2
"""
import argparse
import os
import sys

# Add scripts dir to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure.ai.ml.entities import Environment
from common.ml_client import get_ml_client


def register_environments(ml_client, version: str):
    """Register sklearn and genai environments."""
    registered = []

    # Scenario 1-3: scikit-learn environment
    sklearn_env = Environment(
        name="claudebricks-sklearn",
        version=version,
        description=(
            "scikit-learn environment for classification, anomaly detection, "
            "and clustering (Scenarios 1-3)."
        ),
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
                        "umap-learn>=0.5.5",
                        "hdbscan>=0.8.33",
                    ]
                },
            ],
        },
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest",
    )
    result = ml_client.environments.create_or_update(sklearn_env)
    registered.append(result)
    print(f"  Registered environment: {result.name}:{result.version}")

    # Scenario 4: GenAI environment
    genai_env = Environment(
        name="claudebricks-genai",
        version=version,
        description=(
            "GenAI environment for spec generation with Azure OpenAI "
            "and LangChain (Scenario 4)."
        ),
        conda_file={
            "name": "claudebricks-genai",
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                "python=3.10",
                "pip",
                {
                    "pip": [
                        "azure-ai-ml>=1.12.0",
                        "mlflow>=2.10.0,<=2.16.2",
                        "openai>=1.10.0",
                        "langchain>=0.1.0",
                        "langchain-openai>=0.0.5",
                        "azure-search-documents>=11.4.0",
                        "tiktoken>=0.5.0",
                        "promptflow>=1.5.0",
                    ]
                },
            ],
        },
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest",
    )
    result = ml_client.environments.create_or_update(genai_env)
    registered.append(result)
    print(f"  Registered environment: {result.name}:{result.version}")

    return registered


def main():
    parser = argparse.ArgumentParser(
        description="Register versioned environments in the AML workspace."
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1",
        help="Version for the environments (default: 1)",
    )
    args = parser.parse_args()

    ml_client = get_ml_client()

    print(f"Registering environments (version {args.version})...")
    registered = register_environments(ml_client, args.version)

    print(f"\nRegistered {len(registered)} environments.")


if __name__ == "__main__":
    main()

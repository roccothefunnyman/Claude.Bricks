"""
Register reusable pipeline components in the AML workspace.

Registers CommandComponents for data preparation, model training,
and model evaluation, enabling reuse across pipelines and scenarios.

Usage:
  source scripts/config.sh
  cd deploymentcode/scripts
  python register_components.py
  python register_components.py --version 1.1
"""
import argparse
import os
import sys

# Add scripts dir to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from azure.ai.ml.entities import CommandComponent
from common.ml_client import get_ml_client


def build_component_definitions(version: str):
    """Build the list of component definitions to register."""
    return [
        CommandComponent(
            name="prepare-data",
            version=version,
            display_name="Prepare Data",
            description=(
                "Data preparation component: validates inputs, splits "
                "train/test sets, applies feature engineering."
            ),
            inputs={
                "input_data": {"type": "uri_folder"},
                "test_split_ratio": {"type": "number", "default": 0.2},
            },
            outputs={
                "train_data": {"type": "uri_folder"},
                "test_data": {"type": "uri_folder"},
            },
            code="./components/prepare_data/",
            environment="azureml:claudebricks-sklearn:1",
            command=(
                "python prepare.py "
                "--input_data ${{inputs.input_data}} "
                "--test_split_ratio ${{inputs.test_split_ratio}} "
                "--train_data ${{outputs.train_data}} "
                "--test_data ${{outputs.test_data}}"
            ),
        ),
        CommandComponent(
            name="train-model",
            version=version,
            display_name="Train Model",
            description=(
                "Model training component: trains a scikit-learn model, "
                "logs metrics and artifacts via MLflow."
            ),
            inputs={
                "train_data": {"type": "uri_folder"},
                "model_type": {"type": "string", "default": "random_forest"},
                "n_estimators": {"type": "integer", "default": 100},
            },
            outputs={
                "model_output": {"type": "mlflow_model"},
            },
            code="./components/train_model/",
            environment="azureml:claudebricks-sklearn:1",
            command=(
                "python train.py "
                "--train_data ${{inputs.train_data}} "
                "--model_type ${{inputs.model_type}} "
                "--n_estimators ${{inputs.n_estimators}} "
                "--model_output ${{outputs.model_output}}"
            ),
        ),
        CommandComponent(
            name="evaluate-model",
            version=version,
            display_name="Evaluate Model",
            description=(
                "Model evaluation component: computes accuracy, precision, "
                "recall, F1 on the test set and logs results via MLflow."
            ),
            inputs={
                "model_input": {"type": "mlflow_model"},
                "test_data": {"type": "uri_folder"},
            },
            outputs={
                "evaluation_results": {"type": "uri_folder"},
            },
            code="./components/evaluate_model/",
            environment="azureml:claudebricks-sklearn:1",
            command=(
                "python evaluate.py "
                "--model_input ${{inputs.model_input}} "
                "--test_data ${{inputs.test_data}} "
                "--evaluation_results ${{outputs.evaluation_results}}"
            ),
        ),
    ]


def register_components(ml_client, version: str):
    """Register each component in the workspace."""
    components = build_component_definitions(version)
    registered = []
    for component in components:
        result = ml_client.components.create_or_update(component)
        registered.append(result)
        print(f"  Registered component: {result.name}:{result.version}")

    return registered


def main():
    parser = argparse.ArgumentParser(
        description="Register reusable pipeline components in the AML workspace."
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.0",
        help="Version for the components (default: 1.0)",
    )
    args = parser.parse_args()

    ml_client = get_ml_client()

    print(f"Registering pipeline components (version {args.version})...")
    registered = register_components(ml_client, args.version)

    print(f"\nRegistered {len(registered)} components.")


if __name__ == "__main__":
    main()

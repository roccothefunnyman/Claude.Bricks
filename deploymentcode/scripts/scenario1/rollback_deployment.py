"""Revert all traffic to a known-good deployment and optionally delete the failed one.

Usage:
    python rollback_deployment.py --endpoint-name facade-classifier-endpoint
    python rollback_deployment.py --endpoint-name facade-classifier-endpoint \
        --target-deployment blue --delete-failed
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from common.ml_client import get_ml_client


def main():
    parser = argparse.ArgumentParser(
        description="Revert traffic to a target deployment and optionally delete the failed one."
    )
    parser.add_argument(
        "--endpoint-name",
        required=True,
        help="Name of the managed online endpoint",
    )
    parser.add_argument(
        "--target-deployment",
        default="blue",
        help="Deployment to rollback TO (receives 100%% traffic, default: blue)",
    )
    parser.add_argument(
        "--delete-failed",
        action="store_true",
        help="Delete all non-target deployments after rollback",
    )
    args = parser.parse_args()

    ml_client = get_ml_client()

    endpoint = ml_client.online_endpoints.get(args.endpoint_name)
    current_traffic = dict(endpoint.traffic) if endpoint.traffic else {}
    print(f"Current traffic allocation: {current_traffic}")

    # Set 100% traffic to the target deployment, 0% to all others
    new_traffic = {}
    other_deployments = []
    for deployment_name in current_traffic:
        if deployment_name == args.target_deployment:
            new_traffic[deployment_name] = 100
        else:
            new_traffic[deployment_name] = 0
            other_deployments.append(deployment_name)

    if args.target_deployment not in new_traffic:
        new_traffic[args.target_deployment] = 100

    endpoint.traffic = new_traffic
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print(f"Rollback complete. Traffic: {new_traffic}")

    # Optionally delete the failed deployments
    if args.delete_failed and other_deployments:
        for dep_name in other_deployments:
            print(f"Deleting deployment '{dep_name}'...")
            ml_client.online_deployments.begin_delete(
                name=dep_name,
                endpoint_name=args.endpoint_name,
            ).result()
            print(f"Deployment '{dep_name}' deleted.")

    print(f"Rollback to '{args.target_deployment}' finished.")


if __name__ == "__main__":
    main()

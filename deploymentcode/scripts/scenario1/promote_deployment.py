"""Shift traffic to a deployment on a managed online endpoint.

Usage:
    python promote_deployment.py --endpoint-name facade-classifier-endpoint \
        --deployment-name green --traffic 10
    python promote_deployment.py --endpoint-name facade-classifier-endpoint \
        --deployment-name green --traffic 100
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from common.ml_client import get_ml_client


def main():
    parser = argparse.ArgumentParser(
        description="Shift traffic to a specific deployment on an endpoint."
    )
    parser.add_argument(
        "--endpoint-name",
        required=True,
        help="Name of the managed online endpoint",
    )
    parser.add_argument(
        "--deployment-name",
        required=True,
        help="Deployment to promote (receives the specified traffic percentage)",
    )
    parser.add_argument(
        "--traffic",
        type=int,
        required=True,
        help="Traffic percentage to assign to this deployment (0-100)",
    )
    args = parser.parse_args()

    if not 0 <= args.traffic <= 100:
        print(f"Error: --traffic must be between 0 and 100, got {args.traffic}")
        sys.exit(1)

    ml_client = get_ml_client()

    endpoint = ml_client.online_endpoints.get(args.endpoint_name)
    current_traffic = dict(endpoint.traffic) if endpoint.traffic else {}
    print(f"Current traffic allocation: {current_traffic}")

    if args.deployment_name not in current_traffic:
        print(f"Warning: deployment '{args.deployment_name}' not in current traffic map. Adding it.")

    # Calculate remaining traffic to distribute among other deployments
    remaining = 100 - args.traffic
    other_deployments = [d for d in current_traffic if d != args.deployment_name]

    new_traffic = {args.deployment_name: args.traffic}

    if other_deployments:
        # Distribute remaining traffic proportionally, or evenly if only one other
        if len(other_deployments) == 1:
            new_traffic[other_deployments[0]] = remaining
        else:
            # Proportional split among others based on their current share
            other_total = sum(current_traffic.get(d, 0) for d in other_deployments)
            allocated = 0
            for i, d in enumerate(other_deployments):
                if other_total > 0:
                    share = int(remaining * current_traffic.get(d, 0) / other_total)
                else:
                    share = remaining // len(other_deployments)
                # Give rounding remainder to last deployment
                if i == len(other_deployments) - 1:
                    share = remaining - allocated
                new_traffic[d] = share
                allocated += share

    endpoint.traffic = new_traffic
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()

    print(f"Traffic updated: {new_traffic}")


if __name__ == "__main__":
    main()

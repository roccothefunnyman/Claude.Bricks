"""
Configure Foundry continuous monitoring for deployed GenAI application.

Sets up monitoring for the Foundry-deployed model endpoint, including
alerts for latency, error rate, and token consumption thresholds.

Usage:
    python configure_monitoring.py --deployment-name gpt4o-deploy
    python configure_monitoring.py --latency-threshold-ms 5000 --error-rate-threshold 0.05

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
    MonitorDefinition,
    MonitoringTarget,
    AlertNotification,
    ServerlessEndpoint,
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


def configure_genai_monitor(client, deployment_name, monitor_name,
                             latency_threshold_ms, error_rate_threshold,
                             token_threshold, alert_emails):
    """Configure continuous monitoring for a GenAI deployment."""
    print(f"Configuring monitor '{monitor_name}' for deployment '{deployment_name}'...")

    # Define monitoring target
    monitoring_target = MonitoringTarget(
        ml_task="generative_ai",
        endpoint_deployment_id=deployment_name,
    )

    # Define alert configuration
    alert_config = None
    if alert_emails:
        alert_config = AlertNotification(
            emails=alert_emails,
        )

    # Build monitor definition with GenAI-specific signals
    monitor_config = {
        "name": monitor_name,
        "target": monitoring_target,
        "signals": {
            "latency": {
                "type": "performance",
                "metric": "request_latency_ms",
                "threshold": latency_threshold_ms,
                "aggregation": "p95",
                "alert_on": "greater_than",
            },
            "error_rate": {
                "type": "performance",
                "metric": "error_rate",
                "threshold": error_rate_threshold,
                "aggregation": "average",
                "alert_on": "greater_than",
            },
            "token_usage": {
                "type": "usage",
                "metric": "total_tokens_per_request",
                "threshold": token_threshold,
                "aggregation": "p95",
                "alert_on": "greater_than",
            },
            "groundedness": {
                "type": "generation_quality",
                "metric": "groundedness_score",
                "threshold": 0.70,
                "aggregation": "average",
                "alert_on": "less_than",
            },
        },
        "schedule": {
            "frequency": "hour",
            "interval": 1,
        },
    }

    # Create the monitor definition
    monitor = MonitorDefinition(
        name=monitor_name,
        monitoring_target=monitoring_target,
        alert_notification=alert_config,
        properties=monitor_config,
    )

    result = client.schedules.begin_create_or_update(monitor).result()
    print(f"Monitor '{monitor_name}' configured successfully.")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Configure Foundry continuous monitoring for GenAI deployment"
    )
    parser.add_argument("--project-name", type=str,
                        default=os.environ.get("FOUNDRY_PROJECT", "claudebricks-genai"),
                        help="Foundry project name")
    parser.add_argument("--deployment-name", type=str, default="gpt4o-deploy",
                        help="Name of the deployed model endpoint")
    parser.add_argument("--monitor-name", type=str, default="genai-monitor",
                        help="Name for the monitoring configuration")
    parser.add_argument("--latency-threshold-ms", type=int, default=5000,
                        help="P95 latency threshold in milliseconds")
    parser.add_argument("--error-rate-threshold", type=float, default=0.05,
                        help="Error rate threshold (0.0-1.0)")
    parser.add_argument("--token-threshold", type=int, default=4000,
                        help="P95 token consumption threshold per request")
    parser.add_argument("--alert-emails", type=str, nargs="*", default=None,
                        help="Email addresses for alert notifications")
    args = parser.parse_args()

    client = get_project_client(args.project_name)

    print("=" * 60)
    print("Foundry GenAI Monitoring Configuration")
    print("=" * 60)
    print()

    configure_genai_monitor(
        client=client,
        deployment_name=args.deployment_name,
        monitor_name=args.monitor_name,
        latency_threshold_ms=args.latency_threshold_ms,
        error_rate_threshold=args.error_rate_threshold,
        token_threshold=args.token_threshold,
        alert_emails=args.alert_emails or [],
    )

    # Print summary
    print()
    print("=" * 60)
    print("Monitoring Configuration Summary")
    print("=" * 60)
    print(f"  Project:           {args.project_name}")
    print(f"  Deployment:        {args.deployment_name}")
    print(f"  Monitor name:      {args.monitor_name}")
    print(f"  Schedule:          Hourly")
    print()
    print("  Alert thresholds:")
    print(f"    Latency (P95):   {args.latency_threshold_ms} ms")
    print(f"    Error rate:      {args.error_rate_threshold:.1%}")
    print(f"    Tokens (P95):    {args.token_threshold} per request")
    print(f"    Groundedness:    0.70 (average)")
    print()
    if args.alert_emails:
        print(f"  Alert emails:      {', '.join(args.alert_emails)}")
    else:
        print("  Alert emails:      (none configured)")
    print()
    print("Monitor will check deployed endpoint metrics on the configured")
    print("schedule and trigger alerts when thresholds are breached.")


if __name__ == "__main__":
    main()

"""
Analyze traces from Foundry tracing for the GenAI application.

Queries recent traces from the Foundry project, calculates aggregate
metrics (average latency, token usage, error rate), and identifies
top failure modes.

Usage:
    python trace_analysis.py
    python trace_analysis.py --hours 24 --top-errors 10
    python trace_analysis.py --export-path ./trace_report.json

Environment variables:
    SUBSCRIPTION_ID     Azure subscription ID
    RESOURCE_GROUP      Azure resource group name
    FOUNDRY_PROJECT     Foundry project name (workspace)
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential


def get_project_client(project_name):
    """Create an MLClient scoped to the Foundry project."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=project_name,
    )


def query_traces(client, hours_back):
    """Query recent traces from the Foundry project.

    Uses the MLClient to retrieve trace data from the project's
    Application Insights / tracing backend.
    """
    print(f"Querying traces from the last {hours_back} hours...")

    start_time = datetime.utcnow() - timedelta(hours=hours_back)

    # Query traces via the Foundry SDK trace API
    try:
        traces = client.traces.list(
            filter=f"start_time ge '{start_time.isoformat()}Z'",
            order_by="start_time desc",
        )
        trace_list = list(traces)
        print(f"Retrieved {len(trace_list)} traces.")
        return trace_list
    except AttributeError:
        # Fallback: use the REST-based approach if traces API is not available
        print("Traces API not available via SDK. Attempting REST query...")
        return query_traces_rest(client, start_time)
    except Exception as e:
        print(f"Error querying traces: {e}")
        print("Ensure tracing is enabled for the Foundry project.")
        return []


def query_traces_rest(client, start_time):
    """Fallback trace query using workspace telemetry data."""
    try:
        # Attempt to get traces from the workspace telemetry
        workspace = client.workspaces.get(client.workspace_name)
        app_insights_id = getattr(workspace, "application_insights", None)
        if not app_insights_id:
            print("No Application Insights linked to workspace.")
            return []

        print(f"Application Insights: {app_insights_id}")
        print("Use Azure Portal or KQL to query detailed trace data:")
        print(f"  az monitor app-insights query \\")
        print(f"    --app {app_insights_id.split('/')[-1]} \\")
        print(f"    --analytics-query 'requests | where timestamp > ago({int((datetime.utcnow() - start_time).total_seconds() / 3600)}h)'")
        return []
    except Exception as e:
        print(f"REST fallback also failed: {e}")
        return []


def calculate_metrics(traces):
    """Calculate aggregate metrics from trace data."""
    if not traces:
        return {
            "total_requests": 0,
            "avg_latency_ms": 0,
            "p50_latency_ms": 0,
            "p95_latency_ms": 0,
            "p99_latency_ms": 0,
            "avg_prompt_tokens": 0,
            "avg_completion_tokens": 0,
            "avg_total_tokens": 0,
            "error_count": 0,
            "error_rate": 0.0,
            "success_count": 0,
        }

    latencies = []
    prompt_tokens = []
    completion_tokens = []
    total_tokens = []
    error_count = 0

    for trace in traces:
        # Extract latency
        duration = getattr(trace, "duration_ms", None) or getattr(trace, "duration", 0)
        if isinstance(duration, (int, float)):
            latencies.append(duration)

        # Extract token usage from trace attributes/properties
        props = getattr(trace, "properties", {}) or {}
        if "prompt_tokens" in props:
            prompt_tokens.append(int(props["prompt_tokens"]))
        if "completion_tokens" in props:
            completion_tokens.append(int(props["completion_tokens"]))
        if "total_tokens" in props:
            total_tokens.append(int(props["total_tokens"]))

        # Check for errors
        status = getattr(trace, "status", "") or getattr(trace, "result_code", "")
        if str(status).startswith(("4", "5")) or str(status).lower() in ("error", "failed"):
            error_count += 1

    total = len(traces)
    latencies.sort()

    def percentile(sorted_list, pct):
        if not sorted_list:
            return 0
        idx = int(len(sorted_list) * pct / 100)
        return sorted_list[min(idx, len(sorted_list) - 1)]

    return {
        "total_requests": total,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "p99_latency_ms": percentile(latencies, 99),
        "avg_prompt_tokens": sum(prompt_tokens) / len(prompt_tokens) if prompt_tokens else 0,
        "avg_completion_tokens": sum(completion_tokens) / len(completion_tokens) if completion_tokens else 0,
        "avg_total_tokens": sum(total_tokens) / len(total_tokens) if total_tokens else 0,
        "error_count": error_count,
        "error_rate": error_count / total if total > 0 else 0.0,
        "success_count": total - error_count,
    }


def identify_failure_modes(traces, top_n):
    """Identify top failure modes from error traces."""
    error_messages = Counter()

    for trace in traces:
        status = getattr(trace, "status", "") or getattr(trace, "result_code", "")
        if str(status).startswith(("4", "5")) or str(status).lower() in ("error", "failed"):
            props = getattr(trace, "properties", {}) or {}
            error_msg = (
                props.get("error_message", "")
                or props.get("error", "")
                or getattr(trace, "error_message", "Unknown error")
            )
            # Truncate long error messages for grouping
            error_key = str(error_msg)[:200]
            error_messages[error_key] += 1

    return error_messages.most_common(top_n)


def print_report(metrics, failure_modes, hours_back):
    """Print the trace analysis report."""
    print()
    print("=" * 60)
    print(f"Trace Analysis Report (last {hours_back} hours)")
    print("=" * 60)

    print()
    print("Request Volume")
    print("-" * 40)
    print(f"  Total requests:    {metrics['total_requests']}")
    print(f"  Successful:        {metrics['success_count']}")
    print(f"  Errors:            {metrics['error_count']}")
    print(f"  Error rate:        {metrics['error_rate']:.2%}")

    print()
    print("Latency (ms)")
    print("-" * 40)
    print(f"  Average:           {metrics['avg_latency_ms']:.0f}")
    print(f"  P50:               {metrics['p50_latency_ms']:.0f}")
    print(f"  P95:               {metrics['p95_latency_ms']:.0f}")
    print(f"  P99:               {metrics['p99_latency_ms']:.0f}")

    print()
    print("Token Usage (per request)")
    print("-" * 40)
    print(f"  Avg prompt:        {metrics['avg_prompt_tokens']:.0f}")
    print(f"  Avg completion:    {metrics['avg_completion_tokens']:.0f}")
    print(f"  Avg total:         {metrics['avg_total_tokens']:.0f}")

    if failure_modes:
        print()
        print("Top Failure Modes")
        print("-" * 40)
        for error_msg, count in failure_modes:
            print(f"  [{count:>4}x] {error_msg[:80]}")
    elif metrics["error_count"] == 0:
        print()
        print("No errors detected in the analyzed period.")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze traces from Foundry tracing"
    )
    parser.add_argument("--project-name", type=str,
                        default=os.environ.get("FOUNDRY_PROJECT", "claudebricks-genai"),
                        help="Foundry project name")
    parser.add_argument("--hours", type=int, default=24,
                        help="Number of hours to look back for traces")
    parser.add_argument("--top-errors", type=int, default=5,
                        help="Number of top failure modes to display")
    parser.add_argument("--export-path", type=str, default=None,
                        help="Export analysis report to JSON file")
    args = parser.parse_args()

    client = get_project_client(args.project_name)

    # 1. Query traces
    print("=" * 60)
    print("Foundry Trace Analysis")
    print("=" * 60)
    traces = query_traces(client, args.hours)

    # 2. Calculate metrics
    metrics = calculate_metrics(traces)

    # 3. Identify failure modes
    failure_modes = identify_failure_modes(traces, args.top_errors)

    # 4. Print report
    print_report(metrics, failure_modes, args.hours)

    # 5. Export if requested
    if args.export_path:
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "project": args.project_name,
            "hours_analyzed": args.hours,
            "metrics": metrics,
            "failure_modes": [
                {"error": msg, "count": count}
                for msg, count in failure_modes
            ],
        }
        os.makedirs(os.path.dirname(args.export_path) or ".", exist_ok=True)
        with open(args.export_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport exported to {args.export_path}")


if __name__ == "__main__":
    main()

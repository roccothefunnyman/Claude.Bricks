"""Health check against a managed online endpoint.

Sends test requests and validates response latency, success rate, and schema.
Exits with code 0 on pass, 1 on fail.

Usage:
    python smoke_test.py --endpoint-name facade-classifier-endpoint
    python smoke_test.py --endpoint-name facade-classifier-endpoint \
        --deployment-name green --num-requests 10
"""
import argparse
import json
import os
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from common.ml_client import get_ml_client

# Smoke test thresholds
SUCCESS_RATE_THRESHOLD = 0.99
P95_LATENCY_THRESHOLD = 2.0  # seconds
EXPECTED_RESPONSE_FIELDS = {"prediction"}


def build_sample_payload():
    """Build a sample scoring request with synthetic feature data."""
    # 64x64 RGB image flattened = 12288 features
    features = [0.5] * (64 * 64 * 3)
    return json.dumps({"features": features})


def main():
    parser = argparse.ArgumentParser(
        description="Run smoke tests against a managed online endpoint."
    )
    parser.add_argument(
        "--endpoint-name",
        required=True,
        help="Name of the managed online endpoint",
    )
    parser.add_argument(
        "--deployment-name",
        default=None,
        help="Target a specific deployment (optional, default: endpoint-level routing)",
    )
    parser.add_argument(
        "--num-requests",
        type=int,
        default=5,
        help="Number of test requests to send (default: 5)",
    )
    args = parser.parse_args()

    ml_client = get_ml_client()
    payload = build_sample_payload()

    # Write payload to temp file (SDK invoke requires a file path)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    )
    tmp.write(payload)
    tmp.close()
    request_file = tmp.name

    successes = 0
    failures = 0
    latencies = []
    schema_errors = []

    print(f"Running {args.num_requests} smoke test requests against '{args.endpoint_name}'...")
    if args.deployment_name:
        print(f"Targeting deployment: {args.deployment_name}")

    for i in range(args.num_requests):
        start = time.time()
        try:
            invoke_kwargs = {
                "endpoint_name": args.endpoint_name,
                "request_file": request_file,
            }
            if args.deployment_name:
                invoke_kwargs["deployment_name"] = args.deployment_name
            response = ml_client.online_endpoints.invoke(**invoke_kwargs)
            elapsed = time.time() - start
            latencies.append(elapsed)

            # Validate response schema (response may be double-serialized)
            result = json.loads(response)
            if isinstance(result, str):
                result = json.loads(result)
            missing = EXPECTED_RESPONSE_FIELDS - set(result.keys())
            if missing:
                schema_errors.append(f"Request {i + 1}: missing fields {missing}")
                failures += 1
            else:
                successes += 1

            print(f"  Request {i + 1}: {elapsed:.3f}s - prediction={result.get('prediction', 'N/A')}")

        except Exception as e:
            elapsed = time.time() - start
            latencies.append(elapsed)
            failures += 1
            print(f"  Request {i + 1}: FAILED ({elapsed:.3f}s) - {e}")

    # Calculate results
    total = successes + failures
    success_rate = successes / total if total > 0 else 0.0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else float("inf")
    avg_latency = statistics.mean(latencies) if latencies else float("inf")

    # Report
    print("\n--- Smoke Test Results ---")
    print(f"Total requests:  {total}")
    print(f"Successes:       {successes}")
    print(f"Failures:        {failures}")
    print(f"Success rate:    {success_rate:.1%} (threshold: {SUCCESS_RATE_THRESHOLD:.0%})")
    print(f"Avg latency:     {avg_latency:.3f}s")
    print(f"P95 latency:     {p95_latency:.3f}s (threshold: {P95_LATENCY_THRESHOLD}s)")

    if schema_errors:
        print("\nSchema errors:")
        for err in schema_errors:
            print(f"  {err}")

    # Pass/fail determination
    passed = True
    reasons = []

    if success_rate < SUCCESS_RATE_THRESHOLD:
        passed = False
        reasons.append(f"Success rate {success_rate:.1%} below {SUCCESS_RATE_THRESHOLD:.0%}")

    if p95_latency > P95_LATENCY_THRESHOLD:
        passed = False
        reasons.append(f"P95 latency {p95_latency:.3f}s exceeds {P95_LATENCY_THRESHOLD}s")

    os.unlink(request_file)

    if passed:
        print("\nResult: PASS")
        sys.exit(0)
    else:
        print(f"\nResult: FAIL")
        for reason in reasons:
            print(f"  - {reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()

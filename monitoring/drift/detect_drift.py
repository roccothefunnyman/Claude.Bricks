"""
Drift detection for Scenario 1: Facade Classification.

Compares recent inference data feature distributions against the baseline
profile created by create_baseline.py. Calculates PSI (Population Stability
Index), KS statistic, and Jensen-Shannon divergence per feature.

Results are logged to MLflow and posted to Application Insights. Exit code
reflects severity: 0 = no drift, 1 = warning-level drift, 2 = critical drift.

Usage:
    python monitoring/drift/detect_drift.py \
        --baseline monitoring/drift/baseline_profile.json \
        --inference-data data/scenario1/recent_inference.csv \
        --experiment drift-monitoring-scenario1

    # With explicit thresholds:
    python monitoring/drift/detect_drift.py \
        --baseline monitoring/drift/baseline_profile.json \
        --inference-data data/scenario1/recent_inference.csv \
        --psi-warning 0.2 --psi-critical 0.4
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Small constant to avoid log(0) in divergence calculations
EPSILON = 1e-10


def calculate_psi(
    baseline_counts: list[int],
    inference_counts: list[int],
) -> float:
    """
    Calculate Population Stability Index between two histograms.

    PSI < 0.1: no significant drift
    PSI 0.1 - 0.2: moderate drift (warning)
    PSI > 0.2: significant drift (action required)
    """
    baseline_proportions = np.array(baseline_counts, dtype=float)
    inference_proportions = np.array(inference_counts, dtype=float)

    # Normalize to proportions
    baseline_proportions = baseline_proportions / (baseline_proportions.sum() + EPSILON)
    inference_proportions = inference_proportions / (inference_proportions.sum() + EPSILON)

    # Replace zeros with epsilon
    baseline_proportions = np.clip(baseline_proportions, EPSILON, None)
    inference_proportions = np.clip(inference_proportions, EPSILON, None)

    psi = np.sum(
        (inference_proportions - baseline_proportions)
        * np.log(inference_proportions / baseline_proportions)
    )
    return float(psi)


def calculate_ks_statistic(
    baseline_values: np.ndarray,
    inference_values: np.ndarray,
) -> tuple[float, float]:
    """Calculate KS statistic and p-value."""
    statistic, p_value = stats.ks_2samp(baseline_values, inference_values)
    return float(statistic), float(p_value)


def calculate_js_divergence(
    baseline_counts: list[int],
    inference_counts: list[int],
) -> float:
    """Calculate Jensen-Shannon divergence between two distributions."""
    p = np.array(baseline_counts, dtype=float)
    q = np.array(inference_counts, dtype=float)

    p = p / (p.sum() + EPSILON)
    q = q / (q.sum() + EPSILON)

    p = np.clip(p, EPSILON, None)
    q = np.clip(q, EPSILON, None)

    m = 0.5 * (p + q)

    js = 0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m))
    return float(js)


def compute_inference_histogram(
    values: np.ndarray,
    bin_edges: list[float],
) -> list[int]:
    """Compute histogram counts for inference data using baseline bin edges."""
    counts, _ = np.histogram(values, bins=bin_edges)
    return [int(c) for c in counts]


def detect_drift_for_feature(
    feature_name: str,
    baseline_profile: dict[str, Any],
    inference_values: pd.Series,
) -> dict[str, Any]:
    """Run all drift metrics for a single numeric feature."""
    values = inference_values.dropna().values

    if len(values) < 10:
        logger.warning(
            "Feature '%s' has only %d non-null values, skipping", feature_name, len(values)
        )
        return {"skipped": True, "reason": "insufficient_data"}

    bin_edges = baseline_profile["histogram"]["bin_edges"]
    baseline_counts = baseline_profile["histogram"]["counts"]
    inference_counts = compute_inference_histogram(values, bin_edges)

    psi = calculate_psi(baseline_counts, inference_counts)
    ks_stat, ks_pvalue = calculate_ks_statistic(
        np.random.choice(
            np.linspace(baseline_profile["min"], baseline_profile["max"], 1000),
            size=1000,
        ),
        values,
    )
    js_div = calculate_js_divergence(baseline_counts, inference_counts)

    return {
        "skipped": False,
        "psi": psi,
        "ks_statistic": ks_stat,
        "ks_pvalue": ks_pvalue,
        "js_divergence": js_div,
        "inference_mean": float(values.mean()),
        "inference_std": float(values.std()),
        "baseline_mean": baseline_profile["mean"],
        "baseline_std": baseline_profile["std"],
        "inference_count": len(values),
    }


def log_to_mlflow(
    results: dict[str, Any],
    experiment_name: str,
) -> None:
    """Log drift metrics to MLflow."""
    try:
        import mlflow

        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(run_name=f"drift-check-{results['timestamp']}"):
            for feature_name, metrics in results["features"].items():
                if metrics.get("skipped"):
                    continue
                mlflow.log_metric(f"{feature_name}_psi", metrics["psi"])
                mlflow.log_metric(f"{feature_name}_ks_stat", metrics["ks_statistic"])
                mlflow.log_metric(f"{feature_name}_js_div", metrics["js_divergence"])

            mlflow.log_metric("max_psi", results["max_psi"])
            mlflow.log_metric("drifted_feature_count", results["drifted_feature_count"])
            mlflow.log_param("severity", results["severity"])

        logger.info("Drift metrics logged to MLflow experiment '%s'", experiment_name)
    except Exception as exc:
        logger.warning("Failed to log to MLflow: %s", exc)


def post_to_app_insights(
    results: dict[str, Any],
) -> None:
    """Post drift metrics to Application Insights via telemetry client."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "deploymentcode" / "scripts"))
        from common.telemetry import TelemetryClient

        tc = TelemetryClient()
        tc.track_metric("drift_max_psi", results["max_psi"])
        tc.track_metric("drift_drifted_features", results["drifted_feature_count"])

        for feature_name, metrics in results["features"].items():
            if metrics.get("skipped"):
                continue
            tc.track_metric(
                f"drift_psi_{feature_name}",
                metrics["psi"],
                properties={"feature": feature_name},
            )

        if results["severity"] in ("warning", "critical"):
            tc.track_metric(
                "drift_alert",
                1.0,
                properties={
                    "severity": results["severity"],
                    "drifted_features": json.dumps(results["drifted_features"]),
                },
            )

        tc.flush()
        logger.info("Drift metrics posted to Application Insights")
    except Exception as exc:
        logger.warning("Failed to post to App Insights: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect data drift against baseline")
    parser.add_argument("--baseline", required=True, help="Path to baseline profile JSON")
    parser.add_argument("--inference-data", required=True, help="Path to recent inference CSV")
    parser.add_argument("--experiment", default="drift-monitoring-scenario1", help="MLflow experiment name")
    parser.add_argument("--psi-warning", type=float, default=0.2, help="PSI warning threshold")
    parser.add_argument("--psi-critical", type=float, default=0.4, help="PSI critical threshold")
    parser.add_argument("--output", type=str, default=None, help="Output path for drift report JSON")

    args = parser.parse_args()

    # Load baseline
    baseline_path = Path(args.baseline)
    if not baseline_path.exists():
        logger.error("Baseline profile not found: %s", baseline_path)
        sys.exit(2)
    baseline = json.loads(baseline_path.read_text())

    # Load inference data
    inference_path = Path(args.inference_data)
    if not inference_path.exists():
        logger.error("Inference data not found: %s", inference_path)
        sys.exit(2)
    inference_df = pd.read_csv(inference_path)
    logger.info("Loaded %d inference records", len(inference_df))

    # Run drift detection per feature
    results: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "baseline_created": baseline.get("created_at", "unknown"),
        "inference_row_count": len(inference_df),
        "features": {},
        "drifted_features": [],
        "max_psi": 0.0,
        "drifted_feature_count": 0,
        "severity": "none",
    }

    for feature_name, feature_profile in baseline["features"].items():
        if feature_profile["type"] != "numeric":
            continue
        if feature_name not in inference_df.columns:
            logger.warning("Feature '%s' not in inference data, skipping", feature_name)
            continue

        drift_metrics = detect_drift_for_feature(
            feature_name, feature_profile, inference_df[feature_name]
        )
        results["features"][feature_name] = drift_metrics

        if not drift_metrics.get("skipped") and drift_metrics["psi"] > results["max_psi"]:
            results["max_psi"] = drift_metrics["psi"]

        if not drift_metrics.get("skipped") and drift_metrics["psi"] > args.psi_warning:
            results["drifted_features"].append(feature_name)
            results["drifted_feature_count"] += 1

    # Determine severity
    if results["max_psi"] > args.psi_critical:
        results["severity"] = "critical"
    elif results["max_psi"] > args.psi_warning:
        results["severity"] = "warning"
    else:
        results["severity"] = "none"

    # Log results
    logger.info(
        "Drift detection complete: severity=%s, max_psi=%.4f, drifted_features=%d",
        results["severity"],
        results["max_psi"],
        results["drifted_feature_count"],
    )

    if results["drifted_features"]:
        logger.info("Drifted features: %s", ", ".join(results["drifted_features"]))

    # Save report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2))
        logger.info("Drift report saved to %s", output_path)

    # Post to MLflow and App Insights
    log_to_mlflow(results, args.experiment)
    post_to_app_insights(results)

    # Exit with status based on severity
    if results["severity"] == "critical":
        logger.error("CRITICAL drift detected - retraining recommended")
        sys.exit(2)
    elif results["severity"] == "warning":
        logger.warning("WARNING-level drift detected - monitor closely")
        sys.exit(1)
    else:
        logger.info("No significant drift detected")
        sys.exit(0)


if __name__ == "__main__":
    main()

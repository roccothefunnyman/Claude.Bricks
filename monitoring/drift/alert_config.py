"""
Drift alert configuration and action triggers.

Defines warning/critical thresholds for drift metrics and provides
functions to trigger retraining workflows via GitHub Actions
repository_dispatch events when critical drift is detected.

Usage:
    # As a module (imported by detect_drift.py or scheduled jobs):
    from monitoring.drift.alert_config import DriftAlertConfig, trigger_retraining

    config = DriftAlertConfig()
    if max_psi > config.psi_critical:
        trigger_retraining(config, drifted_features=["mean_pixel_intensity"])

    # Standalone to verify configuration:
    python monitoring/drift/alert_config.py

Environment variables:
    GITHUB_TOKEN         - PAT or GITHUB_TOKEN for repository_dispatch
    GITHUB_REPOSITORY    - owner/repo (e.g., "Rocco/Claude.Bricks")
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class DriftAlertConfig:
    """Drift detection thresholds and alert configuration."""

    # PSI thresholds (per feature)
    psi_warning: float = 0.2
    psi_critical: float = 0.4

    # KS statistic thresholds
    ks_warning: float = 0.15
    ks_critical: float = 0.30

    # JS divergence thresholds
    js_warning: float = 0.1
    js_critical: float = 0.25

    # Accuracy degradation thresholds (if labeled holdout available)
    accuracy_warning: float = 0.85
    accuracy_critical: float = 0.80

    # Minimum inference samples before drift check is meaningful
    min_inference_samples: int = 50

    # GitHub Actions retraining trigger
    github_repository: str = field(
        default_factory=lambda: os.environ.get("GITHUB_REPOSITORY", "Rocco/Claude.Bricks")
    )
    github_token: str = field(
        default_factory=lambda: os.environ.get("GITHUB_TOKEN", "")
    )
    retraining_workflow: str = "train.yml"
    retraining_event_type: str = "drift-retrain-trigger"

    # Scenario configuration
    scenario: str = "scenario1"
    model_name: str = "facade-classifier"

    def classify_severity(
        self, psi: float, ks_stat: float = 0.0, js_div: float = 0.0
    ) -> str:
        """Classify drift severity based on metrics."""
        if psi > self.psi_critical or ks_stat > self.ks_critical or js_div > self.js_critical:
            return "critical"
        if psi > self.psi_warning or ks_stat > self.ks_warning or js_div > self.js_warning:
            return "warning"
        return "none"

    def to_dict(self) -> dict[str, Any]:
        """Export configuration as dictionary (excludes secrets)."""
        return {
            "psi_warning": self.psi_warning,
            "psi_critical": self.psi_critical,
            "ks_warning": self.ks_warning,
            "ks_critical": self.ks_critical,
            "js_warning": self.js_warning,
            "js_critical": self.js_critical,
            "accuracy_warning": self.accuracy_warning,
            "accuracy_critical": self.accuracy_critical,
            "min_inference_samples": self.min_inference_samples,
            "github_repository": self.github_repository,
            "retraining_workflow": self.retraining_workflow,
            "retraining_event_type": self.retraining_event_type,
            "scenario": self.scenario,
            "model_name": self.model_name,
        }


def trigger_retraining(
    config: DriftAlertConfig,
    drifted_features: list[str],
    max_psi: float = 0.0,
    drift_report_path: Optional[str] = None,
) -> bool:
    """
    Trigger a retraining workflow via GitHub Actions repository_dispatch.

    Returns True if the dispatch was sent successfully.
    """
    if not config.github_token:
        logger.error(
            "Cannot trigger retraining: GITHUB_TOKEN not set. "
            "Set the environment variable or pass it in DriftAlertConfig."
        )
        return False

    payload = {
        "event_type": config.retraining_event_type,
        "client_payload": {
            "scenario": config.scenario,
            "model_name": config.model_name,
            "trigger_reason": "data_drift",
            "max_psi": max_psi,
            "drifted_features": drifted_features,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "drift_report_path": drift_report_path or "",
        },
    }

    try:
        import requests

        url = f"https://api.github.com/repos/{config.github_repository}/dispatches"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {config.github_token}",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 204:
            logger.info(
                "Retraining triggered via repository_dispatch (repo=%s, event=%s)",
                config.github_repository,
                config.retraining_event_type,
            )
            return True
        else:
            logger.error(
                "Failed to trigger retraining: HTTP %d - %s",
                response.status_code,
                response.text,
            )
            return False

    except ImportError:
        logger.error("requests library not installed. pip install requests")
        return False
    except Exception as exc:
        logger.error("Failed to trigger retraining: %s", exc)
        return False


def post_alert_to_app_insights(
    severity: str,
    drifted_features: list[str],
    max_psi: float,
) -> None:
    """Post a drift alert to Application Insights."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "deploymentcode" / "scripts"))
        from common.telemetry import TelemetryClient

        tc = TelemetryClient()
        tc.track_metric(
            "drift_alert_fired",
            1.0,
            properties={
                "severity": severity,
                "max_psi": str(max_psi),
                "drifted_features": json.dumps(drifted_features),
                "feature_count": str(len(drifted_features)),
            },
        )
        tc.flush()
        logger.info("Drift alert posted to Application Insights (severity=%s)", severity)
    except Exception as exc:
        logger.warning("Failed to post alert to App Insights: %s", exc)


# -----------------------------------------------------------------------
# Standalone: print current configuration for verification
# -----------------------------------------------------------------------

if __name__ == "__main__":
    config = DriftAlertConfig()
    print("Drift Alert Configuration")
    print("=" * 50)
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
    print()
    print("GitHub token configured:", "Yes" if config.github_token else "No")

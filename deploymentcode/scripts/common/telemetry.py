"""
Telemetry client for Claude.Bricks GenAI observability.

Wraps the Application Insights SDK to provide standardized tracking
for requests, dependencies, metrics, and exceptions. Automatically
attaches prompt_version, model_version, and trace_id as custom
dimensions on all telemetry items.

Usage:
    from common.telemetry import TelemetryClient

    tc = TelemetryClient(prompt_version="v2", model_version="gpt-4o-2024-05")
    tc.track_request("generate_spec", duration_ms=1200, success=True,
                     properties={"building_type": "commercial"})
    tc.track_dependency("ai_search", "retrieve", duration_ms=350, success=True)
    tc.track_metric("input_tokens", 1500)
    tc.track_metric("output_tokens", 800)
    tc.track_metric("estimated_cost_usd", 0.023)
    tc.flush()

Environment variables:
    APPLICATIONINSIGHTS_CONNECTION_STRING  - App Insights connection string
    PROMPT_VERSION                         - Active prompt version (fallback)
    MODEL_VERSION                          - Active model version (fallback)
"""

import os
import uuid
import logging
from typing import Any, Optional

from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from applicationinsights import TelemetryClient as AppInsightsTelemetryClient

logger = logging.getLogger(__name__)


class TelemetryClient:
    """Wrapper around Application Insights SDK with auto-attached dimensions."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        prompt_version: Optional[str] = None,
        model_version: Optional[str] = None,
        trace_id: Optional[str] = None,
    ):
        self._connection_string = (
            connection_string
            or os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
        )
        self._prompt_version = (
            prompt_version or os.environ.get("PROMPT_VERSION", "unknown")
        )
        self._model_version = (
            model_version or os.environ.get("MODEL_VERSION", "unknown")
        )
        self._trace_id = trace_id or str(uuid.uuid4())

        self._client: Optional[AppInsightsTelemetryClient] = None
        self._enabled = bool(self._connection_string)

        if self._enabled:
            try:
                # Extract instrumentation key from connection string
                ikey = self._extract_ikey(self._connection_string)
                self._client = AppInsightsTelemetryClient(ikey)
                self._client.context.properties.update(self._base_properties())
                logger.info("Telemetry client initialized (trace_id=%s)", self._trace_id)
            except Exception as exc:
                logger.warning("Failed to initialize telemetry client: %s", exc)
                self._enabled = False
        else:
            logger.info("Telemetry disabled (no connection string)")

    @staticmethod
    def _extract_ikey(connection_string: str) -> str:
        """Extract InstrumentationKey from an App Insights connection string."""
        for part in connection_string.split(";"):
            if part.strip().startswith("InstrumentationKey="):
                return part.strip().split("=", 1)[1]
        raise ValueError("No InstrumentationKey found in connection string")

    def _base_properties(self) -> dict[str, str]:
        """Properties attached to every telemetry item."""
        return {
            "prompt_version": self._prompt_version,
            "model_version": self._model_version,
            "trace_id": self._trace_id,
            "service": "claude-bricks-genai",
        }

    def _merged_properties(
        self, properties: Optional[dict[str, Any]] = None
    ) -> dict[str, str]:
        """Merge caller-supplied properties with base properties."""
        merged = self._base_properties()
        if properties:
            merged.update({k: str(v) for k, v in properties.items()})
        return merged

    # -----------------------------------------------------------------
    # Public tracking methods
    # -----------------------------------------------------------------

    def track_request(
        self,
        name: str,
        duration_ms: float,
        success: bool = True,
        response_code: str = "200",
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        """Track an end-to-end request (e.g., full spec generation)."""
        if not self._enabled or not self._client:
            logger.debug("track_request(%s) skipped - telemetry disabled", name)
            return

        self._client.track_request(
            name=name,
            url=f"/api/{name}",
            success=success,
            duration=duration_ms,
            response_code=response_code,
            properties=self._merged_properties(properties),
        )

    def track_dependency(
        self,
        dependency_type: str,
        name: str,
        duration_ms: float,
        success: bool = True,
        data: Optional[str] = None,
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        """Track an external dependency call (e.g., AI Search, LLM)."""
        if not self._enabled or not self._client:
            logger.debug("track_dependency(%s/%s) skipped", dependency_type, name)
            return

        self._client.track_dependency(
            name=name,
            data=data or "",
            type=dependency_type,
            duration=duration_ms,
            success=success,
            properties=self._merged_properties(properties),
        )

    def track_metric(
        self,
        name: str,
        value: float,
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        """Track a custom metric (e.g., token count, cost, eval score)."""
        if not self._enabled or not self._client:
            logger.debug("track_metric(%s=%.4f) skipped", name, value)
            return

        self._client.track_metric(
            name=name,
            value=value,
            properties=self._merged_properties(properties),
        )

    def track_exception(
        self,
        exception: Optional[Exception] = None,
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        """Track an exception."""
        if not self._enabled or not self._client:
            logger.debug("track_exception skipped")
            return

        self._client.track_exception(
            type=type(exception).__name__ if exception else "UnknownError",
            value=str(exception) if exception else "",
            properties=self._merged_properties(properties),
        )

    def flush(self) -> None:
        """Flush pending telemetry to Application Insights."""
        if self._enabled and self._client:
            self._client.flush()
            logger.debug("Telemetry flushed")

    @property
    def trace_id(self) -> str:
        return self._trace_id

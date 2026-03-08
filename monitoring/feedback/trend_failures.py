"""
Aggregate failure causes from evaluation logs and produce trend reports.

Reads evaluation result files (JSON) from eval/results/, categorizes
failures by a defined taxonomy, and outputs a summary report showing
failure trends over time.

Usage:
    python monitoring/feedback/trend_failures.py \
        --results-dir eval/results \
        --output monitoring/feedback/failure_trends.json

    # Filter to recent results only:
    python monitoring/feedback/trend_failures.py \
        --results-dir eval/results \
        --days 30 \
        --output monitoring/feedback/failure_trends.json
"""

import argparse
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# Failure taxonomy for LEGO spec generation
FAILURE_CATEGORIES = {
    "missing_dimensions": {
        "description": "Output lacks width, depth, or height dimensions",
        "keywords": ["dimension", "width", "depth", "height", "size", "missing_dimensions"],
    },
    "invalid_parts": {
        "description": "References LDraw part numbers that do not exist",
        "keywords": ["invalid_part", "unknown_part", "part_not_found", "bad_part"],
    },
    "invalid_colors": {
        "description": "Uses color codes not in the LDraw color palette",
        "keywords": ["invalid_color", "unknown_color", "bad_color"],
    },
    "structural_issues": {
        "description": "Floating elements, impossible cantilevers, or unsupported structures",
        "keywords": ["structural", "floating", "cantilever", "unsupported", "impossible"],
    },
    "missing_color_palette": {
        "description": "Output does not specify a color palette",
        "keywords": ["missing_color", "no_palette", "missing_palette"],
    },
    "format_error": {
        "description": "Output does not follow expected section structure",
        "keywords": ["format", "missing_section", "parse_error", "malformed"],
    },
    "grounding_failure": {
        "description": "Output not grounded in provided reference context",
        "keywords": ["ungrounded", "hallucination", "groundedness", "not_grounded"],
    },
    "relevance_failure": {
        "description": "Output does not address the user prompt",
        "keywords": ["irrelevant", "off_topic", "relevance", "not_relevant"],
    },
    "coherence_failure": {
        "description": "Output is internally inconsistent or contradictory",
        "keywords": ["incoherent", "contradictory", "inconsistent", "coherence"],
    },
    "safety_failure": {
        "description": "Output contains harmful or inappropriate content",
        "keywords": ["safety", "harmful", "inappropriate", "unsafe"],
    },
    "timeout": {
        "description": "Generation exceeded time limit",
        "keywords": ["timeout", "timed_out", "deadline"],
    },
    "api_error": {
        "description": "Upstream API returned an error",
        "keywords": ["api_error", "http_error", "service_unavailable", "rate_limit"],
    },
    "other": {
        "description": "Failure that does not fit other categories",
        "keywords": [],
    },
}


def categorize_failure(failure_reason: str) -> str:
    """Map a failure reason string to a taxonomy category."""
    reason_lower = failure_reason.lower()
    for category, info in FAILURE_CATEGORIES.items():
        if category == "other":
            continue
        for keyword in info["keywords"]:
            if keyword in reason_lower:
                return category
    return "other"


def load_evaluation_results(
    results_dir: Path,
    days: int | None = None,
) -> list[dict[str, Any]]:
    """Load evaluation result JSON files from the results directory."""
    results = []
    cutoff = None
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for json_file in sorted(results_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text())

            # Handle both single-result and batch-result formats
            if isinstance(data, list):
                entries = data
            elif "results" in data:
                entries = data["results"]
            else:
                entries = [data]

            for entry in entries:
                # Apply date filter if specified
                if cutoff and "timestamp" in entry:
                    try:
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time < cutoff:
                            continue
                    except (ValueError, TypeError):
                        pass

                entry["_source_file"] = json_file.name
                results.append(entry)

        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Skipping invalid result file %s: %s", json_file, exc)

    logger.info("Loaded %d evaluation entries from %s", len(results), results_dir)
    return results


def extract_failures(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract failed evaluations from results."""
    failures = []
    for entry in results:
        # Check various indicators of failure
        is_failure = False
        failure_reasons: list[str] = []

        # Explicit pass/fail field
        if entry.get("passed") is False or entry.get("success") is False:
            is_failure = True

        # Metric-based failures
        for metric in ["groundedness", "relevance", "coherence", "fluency", "buildability"]:
            score = entry.get(metric)
            threshold = entry.get(f"{metric}_threshold")
            if score is not None and threshold is not None and score < threshold:
                is_failure = True
                failure_reasons.append(f"{metric}_failure")

        # Explicit failure reasons
        if "failure_reason" in entry:
            is_failure = True
            failure_reasons.append(entry["failure_reason"])
        if "failure_reasons" in entry:
            is_failure = True
            failure_reasons.extend(entry["failure_reasons"])
        if "errors" in entry:
            is_failure = True
            failure_reasons.extend(entry["errors"])

        if is_failure:
            failures.append({
                "id": entry.get("id", "unknown"),
                "timestamp": entry.get("timestamp", ""),
                "prompt_version": entry.get("prompt_version", "unknown"),
                "failure_reasons": failure_reasons if failure_reasons else ["unspecified"],
                "source_file": entry.get("_source_file", ""),
                "metrics": {
                    k: entry.get(k)
                    for k in ["groundedness", "relevance", "coherence", "fluency", "buildability"]
                    if entry.get(k) is not None
                },
            })

    logger.info("Found %d failures out of %d total entries", len(failures), len(results))
    return failures


def build_trend_report(
    failures: list[dict[str, Any]],
    total_count: int,
) -> dict[str, Any]:
    """Build aggregated failure trend report."""
    # Categorize all failure reasons
    category_counter: Counter = Counter()
    category_examples: defaultdict[str, list[str]] = defaultdict(list)
    per_version: defaultdict[str, Counter] = defaultdict(Counter)

    for failure in failures:
        for reason in failure["failure_reasons"]:
            category = categorize_failure(reason)
            category_counter[category] += 1

            if len(category_examples[category]) < 3:
                category_examples[category].append(reason)

            version = failure.get("prompt_version", "unknown")
            per_version[version][category] += 1

    # Build report
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_evaluations": total_count,
            "total_failures": len(failures),
            "failure_rate": len(failures) / max(total_count, 1),
            "unique_categories": len(category_counter),
        },
        "categories": [],
        "by_prompt_version": {},
    }

    # Top failure categories
    for category, count in category_counter.most_common():
        report["categories"].append({
            "category": category,
            "description": FAILURE_CATEGORIES.get(category, {}).get("description", ""),
            "count": count,
            "percentage": count / max(sum(category_counter.values()), 1) * 100,
            "examples": category_examples.get(category, []),
        })

    # Per-version breakdown
    for version, counts in sorted(per_version.items()):
        report["by_prompt_version"][version] = {
            cat: cnt for cat, cnt in counts.most_common()
        }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate failure causes from evaluation logs"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="eval/results",
        help="Directory containing evaluation result JSON files",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Only include results from the last N days",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="monitoring/feedback/failure_trends.json",
        help="Output path for trend report",
    )

    args = parser.parse_args()
    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        logger.error("Results directory not found: %s", results_dir)
        logger.info("No evaluation results to analyze. Run evaluations first.")
        return

    results = load_evaluation_results(results_dir, days=args.days)
    if not results:
        logger.info("No evaluation results found")
        return

    failures = extract_failures(results)
    report = build_trend_report(failures, total_count=len(results))

    # Print summary to stdout
    print("\nFailure Trend Report")
    print("=" * 60)
    print(f"Total evaluations: {report['summary']['total_evaluations']}")
    print(f"Total failures:    {report['summary']['total_failures']}")
    print(f"Failure rate:      {report['summary']['failure_rate']:.1%}")
    print()

    if report["categories"]:
        print("Top Failure Categories:")
        print("-" * 60)
        for cat in report["categories"]:
            print(f"  {cat['category']:30s}  {cat['count']:4d}  ({cat['percentage']:.1f}%)")
        print()

    if report["by_prompt_version"]:
        print("Failures by Prompt Version:")
        print("-" * 60)
        for version, counts in report["by_prompt_version"].items():
            total = sum(counts.values())
            print(f"  {version}: {total} failures")
            for cat, cnt in counts.items():
                print(f"    {cat}: {cnt}")

    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2))
    logger.info("Failure trend report saved to %s", output_path)


if __name__ == "__main__":
    main()

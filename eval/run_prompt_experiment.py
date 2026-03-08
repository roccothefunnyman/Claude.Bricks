"""Prompt experiment runner for Claude.Bricks.

Runs a matrix of system prompt versions x RAG template versions against
the evaluation dataset, scores each combination, and identifies the best
performing configuration.

Usage:
    python eval/run_prompt_experiment.py \
        --system-prompts v1,v2,v3 \
        --rag-templates v1,v2 \
        --dataset eval/datasets/lego-spec-generator.jsonl \
        --output eval/results/experiment-2026-03-10.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

from azure.identity import DefaultAzureCredential

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluators.buildability import evaluate as evaluate_buildability
from run_evaluation import (
    generate_response,
    load_dataset,
    load_thresholds,
    retrieve_context,
    score_builtin_metrics,
    score_safety,
)


def load_system_prompt(version: str) -> str:
    """Load a system prompt by version identifier.

    Args:
        version: Version string (e.g., "v1", "v2").

    Returns:
        System prompt text.
    """
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "system" / f"{version}.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return (
        f"[System prompt {version} not found at {prompt_path}. "
        "Using default.] You are a LEGO building specification generator. "
        "Produce detailed specifications with dimensions, color palette, "
        "part references, and construction notes."
    )


def load_rag_template(version: str) -> str:
    """Load a RAG prompt template by version identifier.

    Args:
        version: Version string (e.g., "v1", "v2").

    Returns:
        RAG template text (Jinja2 format).
    """
    template_path = Path(__file__).resolve().parent.parent / "prompts" / "rag" / f"{version}.jinja2"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return (
        "Context:\n{{ context }}\n\n---\n\nRequest:\n{{ prompt }}"
    )


def format_rag_prompt(template: str, context: str, prompt: str) -> str:
    """Render a RAG template with context and prompt.

    Performs simple placeholder substitution. For production use,
    replace with Jinja2 rendering.

    Args:
        template: RAG template with {{ context }} and {{ prompt }} placeholders.
        context: Retrieved context text.
        prompt: User prompt.

    Returns:
        Formatted prompt string.
    """
    result = template.replace("{{ context }}", context)
    result = result.replace("{{ prompt }}", prompt)
    result = result.replace("{{context}}", context)
    result = result.replace("{{prompt}}", prompt)
    return result


def evaluate_combination(
    system_prompt: str,
    rag_template: str,
    dataset: list[dict],
    model_deployment: str,
) -> dict:
    """Evaluate a single system-prompt + RAG-template combination.

    Args:
        system_prompt: The system prompt text.
        rag_template: The RAG template text.
        dataset: List of evaluation test cases.
        model_deployment: Azure OpenAI deployment name.

    Returns:
        Dict with aggregated scores, per-case details, and usage stats.
    """
    per_case = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_latency_ms = 0.0

    for test_case in dataset:
        prompt = test_case["prompt"]
        context_docs = test_case.get("context_docs", [])
        context = retrieve_context(context_docs)

        # Format user message using RAG template.
        user_message = format_rag_prompt(rag_template, context, prompt)

        gen_result = generate_response(
            prompt=user_message,
            system_prompt=system_prompt,
            context="",  # Context already embedded in user_message via template.
            model_deployment=model_deployment,
        )
        response = gen_result["response"]

        builtin_scores = score_builtin_metrics(response, prompt, context)
        safety = score_safety(response)
        buildability = evaluate_buildability(response)

        scores = {
            **builtin_scores,
            "safety_pass_rate": safety,
            "buildability": buildability["score"],
        }

        total_input_tokens += gen_result["input_tokens"]
        total_output_tokens += gen_result["output_tokens"]
        total_latency_ms += gen_result["latency_ms"]

        per_case.append({
            "id": test_case.get("id", ""),
            "scores": scores,
        })

    # Aggregate scores.
    metric_keys = ["groundedness", "relevance", "coherence", "fluency", "safety_pass_rate", "buildability"]
    aggregated = {}
    for key in metric_keys:
        values = [c["scores"].get(key, 0.0) for c in per_case]
        aggregated[key] = round(sum(values) / len(values), 4) if values else 0.0

    n = len(dataset)
    return {
        "aggregated_scores": aggregated,
        "avg_input_tokens": round(total_input_tokens / n, 1) if n else 0,
        "avg_output_tokens": round(total_output_tokens / n, 1) if n else 0,
        "avg_latency_ms": round(total_latency_ms / n, 1) if n else 0,
        "estimated_cost_per_request": _estimate_cost(
            total_input_tokens / n if n else 0,
            total_output_tokens / n if n else 0,
        ),
        "per_case": per_case,
    }


def _estimate_cost(input_tokens: float, output_tokens: float) -> float:
    """Estimate per-request cost based on GPT-4 pricing.

    Uses approximate pricing. Adjust rates for your deployment.

    Args:
        input_tokens: Average input tokens per request.
        output_tokens: Average output tokens per request.

    Returns:
        Estimated cost in USD.
    """
    input_rate = 0.03 / 1000   # $0.03 per 1K input tokens (GPT-4 approximate)
    output_rate = 0.06 / 1000  # $0.06 per 1K output tokens
    return round(input_tokens * input_rate + output_tokens * output_rate, 6)


def format_comparison_table(results: list[dict]) -> str:
    """Format a comparison table of all tested combinations.

    Args:
        results: List of combination result dicts.

    Returns:
        Formatted table string.
    """
    lines = []
    lines.append("=" * 110)
    lines.append("PROMPT EXPERIMENT COMPARISON")
    lines.append("=" * 110)
    lines.append("")

    # Header row.
    header = (
        f"{'Combo':<18s} {'Ground':>8s} {'Relev':>8s} {'Coher':>8s} "
        f"{'Fluency':>8s} {'Build':>8s} {'Safety':>8s} "
        f"{'Tokens':>8s} {'Lat(ms)':>8s} {'Cost($)':>8s}"
    )
    lines.append(header)
    lines.append("-" * 110)

    for r in results:
        combo = f"{r['system_prompt']}+{r['rag_template']}"
        s = r["aggregated_scores"]
        lines.append(
            f"{combo:<18s} "
            f"{s.get('groundedness', 0):.4f}   "
            f"{s.get('relevance', 0):.4f}   "
            f"{s.get('coherence', 0):.4f}   "
            f"{s.get('fluency', 0):.4f}   "
            f"{s.get('buildability', 0):.4f}   "
            f"{s.get('safety_pass_rate', 0):.4f}   "
            f"{r.get('avg_input_tokens', 0) + r.get('avg_output_tokens', 0):>7.0f}   "
            f"{r.get('avg_latency_ms', 0):>7.1f}   "
            f"{r.get('estimated_cost_per_request', 0):>7.5f}"
        )

    lines.append("")

    # Identify winner by composite score (simple weighted average).
    def composite(r):
        s = r["aggregated_scores"]
        return (
            s.get("groundedness", 0) * 0.2
            + s.get("relevance", 0) * 0.25
            + s.get("coherence", 0) * 0.2
            + s.get("fluency", 0) * 0.15
            + s.get("buildability", 0) * 0.2
        )

    best = max(results, key=composite)
    lines.append(
        f"RECOMMENDED: {best['system_prompt']}+{best['rag_template']} "
        f"(composite={composite(best):.4f})"
    )
    lines.append("=" * 110)

    return "\n".join(lines)


def run_experiment(args: argparse.Namespace) -> None:
    """Execute the prompt experiment matrix.

    Args:
        args: Parsed command-line arguments.
    """
    system_versions = [v.strip() for v in args.system_prompts.split(",")]
    rag_versions = [v.strip() for v in args.rag_templates.split(",")]

    print(f"System prompt versions: {system_versions}")
    print(f"RAG template versions:  {rag_versions}")
    print(f"Matrix size: {len(system_versions)} x {len(rag_versions)} = {len(system_versions) * len(rag_versions)} combinations")
    print()

    dataset = load_dataset(args.dataset)
    print(f"Loaded {len(dataset)} test cases from {args.dataset}")
    print()

    all_results = []

    for sys_ver, rag_ver in product(system_versions, rag_versions):
        combo_label = f"{sys_ver}+{rag_ver}"
        print(f"Evaluating combination: {combo_label}...")

        system_prompt = load_system_prompt(sys_ver)
        rag_template = load_rag_template(rag_ver)

        combo_result = evaluate_combination(
            system_prompt=system_prompt,
            rag_template=rag_template,
            dataset=dataset,
            model_deployment=args.model_deployment,
        )
        combo_result["system_prompt"] = sys_ver
        combo_result["rag_template"] = rag_ver

        all_results.append(combo_result)
        print(f"  Scores: {combo_result['aggregated_scores']}")
        print()

    # Print comparison table.
    table = format_comparison_table(all_results)
    print(table)

    # Save results.
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_payload = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset": args.dataset,
            "model_deployment": args.model_deployment,
            "system_prompt_versions": system_versions,
            "rag_template_versions": rag_versions,
        },
        "combinations": [
            {
                "system_prompt": r["system_prompt"],
                "rag_template": r["rag_template"],
                "aggregated_scores": r["aggregated_scores"],
                "avg_input_tokens": r["avg_input_tokens"],
                "avg_output_tokens": r["avg_output_tokens"],
                "avg_latency_ms": r["avg_latency_ms"],
                "estimated_cost_per_request": r["estimated_cost_per_request"],
            }
            for r in all_results
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


def main():
    """Parse arguments and run prompt experiment."""
    parser = argparse.ArgumentParser(
        description="Run prompt version experiments for Claude.Bricks."
    )
    parser.add_argument(
        "--system-prompts",
        required=True,
        help="Comma-separated system prompt versions (e.g., v1,v2,v3).",
    )
    parser.add_argument(
        "--rag-templates",
        required=True,
        help="Comma-separated RAG template versions (e.g., v1,v2).",
    )
    parser.add_argument(
        "--dataset",
        default="eval/datasets/lego-spec-generator.jsonl",
        help="Path to evaluation dataset (JSONL).",
    )
    parser.add_argument(
        "--model-deployment",
        default="lego-spec-gpt4",
        help="Azure OpenAI deployment name.",
    )
    parser.add_argument(
        "--output",
        default="eval/results/experiment.json",
        help="Output path for experiment results JSON.",
    )
    args = parser.parse_args()

    run_experiment(args)


if __name__ == "__main__":
    main()

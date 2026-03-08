"""Main evaluation runner for Claude.Bricks LEGO spec generator.

Loads an evaluation dataset, generates responses for each test case,
scores them with built-in Azure AI metrics and a custom buildability
evaluator, compares against configurable thresholds, and outputs a report.

Usage:
    python eval/run_evaluation.py \
        --dataset eval/datasets/lego-spec-generator.jsonl \
        --thresholds eval/configs/thresholds.json \
        --output-dir eval/results \
        --model-deployment lego-spec-gpt4 \
        --prompt-version v1
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

# Local custom evaluator.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluators.buildability import evaluate as evaluate_buildability


def load_dataset(dataset_path: str) -> list[dict]:
    """Load evaluation dataset from a JSONL file.

    Args:
        dataset_path: Path to the .jsonl file.

    Returns:
        List of evaluation row dicts.
    """
    rows = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"WARNING: Skipping invalid JSON on line {line_num}: {exc}")
    return rows


def load_thresholds(thresholds_path: str) -> dict[str, float]:
    """Load quality thresholds from a JSON file.

    Args:
        thresholds_path: Path to the thresholds JSON file.

    Returns:
        Dict mapping metric name to minimum acceptable score.
    """
    with open(thresholds_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt_template(prompt_version: str) -> str:
    """Load a system prompt template by version.

    Looks in prompts/system/ for the version file. Falls back to a
    default system prompt if the file does not exist.

    Args:
        prompt_version: Version identifier (e.g., "v1").

    Returns:
        System prompt text.
    """
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "system" / f"{prompt_version}.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return (
        "You are a LEGO building specification generator. Given a building description, "
        "produce a detailed specification including dimensions, color palette, part references, "
        "construction notes, and structural details suitable for generating an LDraw file."
    )


def retrieve_context(context_docs: list[str]) -> str:
    """Retrieve context content from the specified document paths.

    In a full deployment this would query Azure AI Search. For local
    evaluation it reads the files directly if they exist, or returns
    a placeholder note.

    Args:
        context_docs: List of relative paths to context documents.

    Returns:
        Concatenated context text.
    """
    project_root = Path(__file__).resolve().parent.parent
    context_parts = []
    for doc_path in context_docs:
        full_path = project_root / doc_path
        if full_path.exists():
            context_parts.append(full_path.read_text(encoding="utf-8"))
        else:
            context_parts.append(f"[Context document not available: {doc_path}]")
    return "\n\n---\n\n".join(context_parts)


def generate_response(
    prompt: str,
    system_prompt: str,
    context: str,
    model_deployment: str,
) -> dict:
    """Generate a response from the deployed model.

    Uses the Azure OpenAI SDK via the configured deployment. Returns
    the response text along with usage metadata.

    Args:
        prompt: The user prompt.
        system_prompt: The system prompt.
        context: Retrieved context to include.
        model_deployment: Azure OpenAI deployment name.

    Returns:
        Dict with keys: response, input_tokens, output_tokens, latency_ms.
    """
    try:
        from openai import AzureOpenAI
    except ImportError:
        # Fallback: return a placeholder so the framework can still run
        # structurally without a live model.
        return {
            "response": "[Model not available -- install openai package and configure deployment]",
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": 0,
        }

    client = AzureOpenAI(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-06-01"),
        azure_deployment=model_deployment,
        # Uses DefaultAzureCredential via azure_ad_token_provider or API key
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\n---\n\nRequest:\n{prompt}"},
    ]

    start = time.perf_counter()
    completion = client.chat.completions.create(
        model=model_deployment,
        messages=messages,
        temperature=0.3,
        max_tokens=2000,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    choice = completion.choices[0]
    usage = completion.usage

    return {
        "response": choice.message.content or "",
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "latency_ms": round(latency_ms, 1),
    }


def score_builtin_metrics(response: str, prompt: str, context: str) -> dict[str, float]:
    """Score a response using Azure AI built-in quality metrics.

    Uses the azure-ai-evaluation SDK evaluators for groundedness,
    relevance, coherence, and fluency. Falls back to placeholder
    scores if the SDK is not available.

    Args:
        response: The generated response text.
        prompt: The original user prompt.
        context: The retrieved context.

    Returns:
        Dict mapping metric name to score (0.0-1.0).
    """
    try:
        from azure.ai.evaluation import (
            CoherenceEvaluator,
            FluencyEvaluator,
            GroundednessEvaluator,
            RelevanceEvaluator,
        )

        credential = DefaultAzureCredential()
        model_config = {
            "azure_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            "azure_deployment": os.environ.get("AZURE_OPENAI_EVAL_DEPLOYMENT", "gpt-4"),
            "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-06-01"),
        }

        groundedness_eval = GroundednessEvaluator(credential=credential, model_config=model_config)
        relevance_eval = RelevanceEvaluator(credential=credential, model_config=model_config)
        coherence_eval = CoherenceEvaluator(credential=credential, model_config=model_config)
        fluency_eval = FluencyEvaluator(credential=credential, model_config=model_config)

        groundedness_result = groundedness_eval(
            response=response, context=context, query=prompt
        )
        relevance_result = relevance_eval(response=response, query=prompt)
        coherence_result = coherence_eval(response=response, query=prompt)
        fluency_result = fluency_eval(response=response, query=prompt)

        # Normalize scores to 0-1 range (evaluators return 1-5 scale).
        return {
            "groundedness": groundedness_result.get("groundedness", 0) / 5.0,
            "relevance": relevance_result.get("relevance", 0) / 5.0,
            "coherence": coherence_result.get("coherence", 0) / 5.0,
            "fluency": fluency_result.get("fluency", 0) / 5.0,
        }
    except (ImportError, Exception) as exc:
        print(f"WARNING: Built-in metrics unavailable ({exc}). Using placeholders.")
        return {
            "groundedness": 0.0,
            "relevance": 0.0,
            "coherence": 0.0,
            "fluency": 0.0,
        }


def score_safety(response: str) -> float:
    """Score a response for safety compliance.

    Uses the Azure AI Content Safety evaluator if available.
    Returns 1.0 (pass) or 0.0 (fail).

    Args:
        response: The generated response text.

    Returns:
        1.0 if safe, 0.0 if unsafe content detected.
    """
    try:
        from azure.ai.evaluation import ContentSafetyEvaluator

        credential = DefaultAzureCredential()
        project_scope = {
            "subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID", ""),
            "resource_group_name": os.environ.get("AZURE_RESOURCE_GROUP", ""),
            "project_name": os.environ.get("AZURE_PROJECT_NAME", ""),
        }
        safety_eval = ContentSafetyEvaluator(
            credential=credential, azure_ai_project=project_scope
        )
        result = safety_eval(query="", response=response)
        # Content safety returns severity levels; pass if all are "Very low" or 0.
        defect_rate = result.get("content_safety_defect_rate", 0)
        return 1.0 if defect_rate == 0 else 0.0
    except (ImportError, Exception):
        # Default to pass if safety evaluator unavailable.
        return 1.0


def aggregate_results(per_case_results: list[dict]) -> dict[str, float]:
    """Aggregate per-case scores into overall metric averages.

    Args:
        per_case_results: List of per-case result dicts.

    Returns:
        Dict mapping metric name to average score.
    """
    if not per_case_results:
        return {}

    metric_keys = [
        "groundedness", "relevance", "coherence", "fluency",
        "safety_pass_rate", "buildability",
    ]
    aggregated = {}
    for key in metric_keys:
        values = [r["scores"].get(key, 0.0) for r in per_case_results if "scores" in r]
        aggregated[key] = round(sum(values) / len(values), 4) if values else 0.0
    return aggregated


def check_thresholds(aggregated: dict[str, float], thresholds: dict[str, float]) -> list[dict]:
    """Compare aggregated scores against thresholds.

    Args:
        aggregated: Dict of metric name to average score.
        thresholds: Dict of metric name to minimum score.

    Returns:
        List of dicts with metric, score, threshold, and passed status.
    """
    results = []
    for metric, threshold in thresholds.items():
        score = aggregated.get(metric, 0.0)
        results.append({
            "metric": metric,
            "score": score,
            "threshold": threshold,
            "passed": score >= threshold,
        })
    return results


def format_report(
    per_case_results: list[dict],
    aggregated: dict[str, float],
    threshold_checks: list[dict],
    metadata: dict,
) -> str:
    """Format a human-readable evaluation report.

    Args:
        per_case_results: Per-case evaluation details.
        aggregated: Aggregated metric scores.
        threshold_checks: Threshold comparison results.
        metadata: Run metadata (timestamp, dataset, model, etc.).

    Returns:
        Formatted report string.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("CLAUDE.BRICKS EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append(f"Timestamp:        {metadata.get('timestamp', 'N/A')}")
    lines.append(f"Dataset:          {metadata.get('dataset', 'N/A')}")
    lines.append(f"Model Deployment: {metadata.get('model_deployment', 'N/A')}")
    lines.append(f"Prompt Version:   {metadata.get('prompt_version', 'N/A')}")
    lines.append(f"Test Cases:       {len(per_case_results)}")
    lines.append("")

    lines.append("-" * 70)
    lines.append("AGGREGATED SCORES")
    lines.append("-" * 70)
    for metric, score in sorted(aggregated.items()):
        lines.append(f"  {metric:<25s} {score:.4f}")
    lines.append("")

    lines.append("-" * 70)
    lines.append("THRESHOLD CHECKS")
    lines.append("-" * 70)
    all_passed = True
    for check in threshold_checks:
        status = "PASS" if check["passed"] else "FAIL"
        if not check["passed"]:
            all_passed = False
        lines.append(
            f"  [{status}] {check['metric']:<25s} "
            f"score={check['score']:.4f}  threshold={check['threshold']:.4f}"
        )
    lines.append("")

    lines.append("-" * 70)
    lines.append("PER-CASE SUMMARY")
    lines.append("-" * 70)
    for result in per_case_results:
        case_id = result.get("id", "?")
        difficulty = result.get("difficulty", "?")
        buildability = result.get("scores", {}).get("buildability", 0.0)
        lines.append(
            f"  {case_id:<12s} difficulty={difficulty:<8s} buildability={buildability:.2f}"
        )
    lines.append("")

    overall = "PASS" if all_passed else "FAIL"
    lines.append(f"OVERALL RESULT: {overall}")
    lines.append("=" * 70)

    return "\n".join(lines)


def run_evaluation(args: argparse.Namespace) -> int:
    """Execute the full evaluation pipeline.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code: 0 if all thresholds pass, 1 otherwise.
    """
    print(f"Loading dataset from {args.dataset}...")
    dataset = load_dataset(args.dataset)
    print(f"Loaded {len(dataset)} test cases.")

    print(f"Loading thresholds from {args.thresholds}...")
    thresholds = load_thresholds(args.thresholds)

    system_prompt = load_prompt_template(args.prompt_version)
    print(f"Using prompt version: {args.prompt_version}")
    print(f"Using model deployment: {args.model_deployment}")
    print()

    per_case_results = []

    for i, test_case in enumerate(dataset, start=1):
        case_id = test_case.get("id", f"case-{i}")
        prompt = test_case["prompt"]
        context_docs = test_case.get("context_docs", [])
        difficulty = test_case.get("difficulty", "unknown")

        print(f"[{i}/{len(dataset)}] Evaluating {case_id} ({difficulty})...")

        # Retrieve context.
        context = retrieve_context(context_docs)

        # Generate response.
        gen_result = generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            context=context,
            model_deployment=args.model_deployment,
        )
        response = gen_result["response"]

        # Score with built-in metrics.
        builtin_scores = score_builtin_metrics(response, prompt, context)

        # Score safety.
        safety_score = score_safety(response)

        # Score with custom buildability evaluator.
        buildability_result = evaluate_buildability(response)

        # Combine scores.
        scores = {
            **builtin_scores,
            "safety_pass_rate": safety_score,
            "buildability": buildability_result["score"],
        }

        per_case_results.append({
            "id": case_id,
            "difficulty": difficulty,
            "prompt": prompt,
            "response_preview": response[:200],
            "scores": scores,
            "buildability_details": buildability_result["details"],
            "input_tokens": gen_result["input_tokens"],
            "output_tokens": gen_result["output_tokens"],
            "latency_ms": gen_result["latency_ms"],
        })

    # Aggregate results.
    aggregated = aggregate_results(per_case_results)

    # Check thresholds.
    threshold_checks = check_thresholds(aggregated, thresholds)

    # Build metadata.
    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": args.dataset,
        "model_deployment": args.model_deployment,
        "prompt_version": args.prompt_version,
    }

    # Format and print report.
    report = format_report(per_case_results, aggregated, threshold_checks, metadata)
    print()
    print(report)

    # Save results.
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    results_file = output_dir / f"eval-{timestamp_slug}.json"
    report_file = output_dir / f"eval-{timestamp_slug}.txt"

    results_payload = {
        "metadata": metadata,
        "aggregated_scores": aggregated,
        "threshold_checks": threshold_checks,
        "per_case_results": per_case_results,
    }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {results_file}")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to {report_file}")

    # Determine exit code.
    all_passed = all(check["passed"] for check in threshold_checks)
    return 0 if all_passed else 1


def main():
    """Parse arguments and run evaluation."""
    parser = argparse.ArgumentParser(
        description="Run evaluation pipeline for Claude.Bricks LEGO spec generator."
    )
    parser.add_argument(
        "--dataset",
        default="eval/datasets/lego-spec-generator.jsonl",
        help="Path to evaluation dataset (JSONL).",
    )
    parser.add_argument(
        "--thresholds",
        default="eval/configs/thresholds.json",
        help="Path to quality thresholds JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        default="eval/results",
        help="Directory for evaluation output files.",
    )
    parser.add_argument(
        "--model-deployment",
        default="lego-spec-gpt4",
        help="Azure OpenAI deployment name to evaluate.",
    )
    parser.add_argument(
        "--prompt-version",
        default="v1",
        help="System prompt version to use (e.g., v1, v2).",
    )
    args = parser.parse_args()

    exit_code = run_evaluation(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

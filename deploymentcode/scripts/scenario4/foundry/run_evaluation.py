"""
Run Foundry evaluation pipeline for the LEGO spec generator.

Loads evaluation dataset from eval/datasets/, runs Foundry built-in
evaluators (groundedness, relevance, coherence, fluency) and safety
evaluation, then outputs results summary and saves to eval/results/.

Exit code is non-zero if any metric falls below its threshold.

Usage:
    python run_evaluation.py
    python run_evaluation.py --dataset ../../eval/datasets/lego-spec-generator.jsonl
    python run_evaluation.py --groundedness-threshold 0.8 --relevance-threshold 0.8

Environment variables:
    SUBSCRIPTION_ID     Azure subscription ID
    RESOURCE_GROUP      Azure resource group name
    FOUNDRY_PROJECT     Foundry project name (workspace)
    OPENAI_ENDPOINT     Azure OpenAI endpoint (for judge model)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from azure.ai.evaluation import (
    GroundednessEvaluator,
    RelevanceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
    ContentSafetyEvaluator,
    evaluate,
)
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential


# Default thresholds matching ai300transformation.md quality gates
THRESHOLDS = {
    "groundedness": 0.70,
    "relevance": 0.75,
    "coherence": 0.80,
    "fluency": 0.85,
}


def get_project_client(project_name):
    """Create an MLClient scoped to the Foundry project."""
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=project_name,
    )


def load_dataset(dataset_path):
    """Load evaluation dataset from JSONL file."""
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        print("Creating sample evaluation dataset...")
        os.makedirs(os.path.dirname(dataset_path) or ".", exist_ok=True)
        samples = [
            {
                "query": "Generate a building spec for a 2-story corner bakery with Art Deco styling",
                "context": (
                    "Art Deco buildings feature geometric patterns, stepped facades, "
                    "and decorative cornices. Corner buildings typically have angled "
                    "entrances and wrap-around windows."
                ),
                "response": (
                    "2-story corner bakery: 32x32 stud footprint, dark tan primary "
                    "with sand green accents. Ground floor: storefront with large "
                    "windows, angled corner entrance with arch. Upper floor: geometric "
                    "window pattern with stepped cornice. Flat roof with decorative "
                    "parapet featuring Art Deco zigzag motif."
                ),
            },
            {
                "query": "Design a 3-story historic European townhouse with shop",
                "context": (
                    "European townhouses feature masonry facades, peaked roofs, "
                    "ground floor commercial space, and residential upper floors. "
                    "Common details: dentil cornice, window sills, decorative bands."
                ),
                "response": (
                    "3-story townhouse: 32x16 stud footprint, dark tan masonry "
                    "with white trim. Ground floor: shop with large 1x4x3 windows "
                    "and central door. Floors 2-3: residential with paired windows. "
                    "Peaked roof with dark bluish gray slopes. Dentil cornice "
                    "between each floor. Sand green awning over shop."
                ),
            },
            {
                "query": "Create a modern 2-story office building with glass facade",
                "context": (
                    "Modern office buildings use curtain wall glass facades, flat "
                    "roofs, and minimalist detailing. Common features: rooftop "
                    "terrace, lobby entrance, modular window grid."
                ),
                "response": (
                    "2-story office: 32x32 stud footprint, light bluish gray with "
                    "white frame. Full glass curtain wall on front facade using "
                    "trans-clear 1x4x3 windows in grid pattern. Flat roof with "
                    "tile border and rooftop terrace. Ground floor lobby with "
                    "double door entrance."
                ),
            },
        ]
        with open(dataset_path, "w") as f:
            for sample in samples:
                f.write(json.dumps(sample) + "\n")
        print(f"Created sample dataset at {dataset_path}")

    data = []
    with open(dataset_path) as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    print(f"Loaded {len(data)} evaluation samples.")
    return data


def run_quality_evaluation(project_client, azure_ai_project, dataset):
    """Run quality evaluators (groundedness, relevance, coherence, fluency)."""
    print("Running quality evaluation...")

    evaluators = {
        "groundedness": GroundednessEvaluator(model_config=azure_ai_project),
        "relevance": RelevanceEvaluator(model_config=azure_ai_project),
        "coherence": CoherenceEvaluator(model_config=azure_ai_project),
        "fluency": FluencyEvaluator(model_config=azure_ai_project),
    }

    results = evaluate(
        data=dataset,
        evaluators=evaluators,
        azure_ai_project=azure_ai_project,
    )

    return results


def run_safety_evaluation(project_client, azure_ai_project, dataset):
    """Run safety evaluator on the dataset."""
    print("Running safety evaluation...")

    evaluators = {
        "content_safety": ContentSafetyEvaluator(
            azure_ai_project=azure_ai_project,
        ),
    }

    results = evaluate(
        data=dataset,
        evaluators=evaluators,
        azure_ai_project=azure_ai_project,
    )

    return results


def save_results(results, output_dir):
    """Save evaluation results to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"eval_results_{timestamp}.json")

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results saved to {output_path}")
    return output_path


def check_thresholds(metrics, thresholds):
    """Check if metrics meet thresholds. Returns list of failures."""
    failures = []
    for metric_name, threshold in thresholds.items():
        value = metrics.get(metric_name, 0.0)
        if value < threshold:
            failures.append({
                "metric": metric_name,
                "value": value,
                "threshold": threshold,
            })
    return failures


def main():
    parser = argparse.ArgumentParser(
        description="Run Foundry evaluation pipeline for spec generator"
    )
    parser.add_argument("--project-name", type=str,
                        default=os.environ.get("FOUNDRY_PROJECT", "claudebricks-genai"),
                        help="Foundry project name")
    parser.add_argument("--dataset", type=str,
                        default="../../../../eval/datasets/lego-spec-generator.jsonl",
                        help="Path to evaluation dataset (JSONL)")
    parser.add_argument("--output-dir", type=str,
                        default="../../../../eval/results",
                        help="Directory for evaluation results")
    parser.add_argument("--groundedness-threshold", type=float,
                        default=THRESHOLDS["groundedness"],
                        help="Minimum groundedness score")
    parser.add_argument("--relevance-threshold", type=float,
                        default=THRESHOLDS["relevance"],
                        help="Minimum relevance score")
    parser.add_argument("--coherence-threshold", type=float,
                        default=THRESHOLDS["coherence"],
                        help="Minimum coherence score")
    parser.add_argument("--fluency-threshold", type=float,
                        default=THRESHOLDS["fluency"],
                        help="Minimum fluency score")
    parser.add_argument("--skip-safety", action="store_true",
                        help="Skip safety evaluation")
    args = parser.parse_args()

    thresholds = {
        "groundedness": args.groundedness_threshold,
        "relevance": args.relevance_threshold,
        "coherence": args.coherence_threshold,
        "fluency": args.fluency_threshold,
    }

    azure_ai_project = {
        "subscription_id": os.environ["SUBSCRIPTION_ID"],
        "resource_group_name": os.environ["RESOURCE_GROUP"],
        "project_name": args.project_name,
    }

    project_client = get_project_client(args.project_name)

    # 1. Load dataset
    print("=" * 60)
    print("Step 1: Load Evaluation Dataset")
    print("=" * 60)
    dataset = load_dataset(args.dataset)

    # 2. Run quality evaluation
    print()
    print("=" * 60)
    print("Step 2: Quality Evaluation")
    print("=" * 60)
    quality_results = run_quality_evaluation(
        project_client, azure_ai_project, dataset
    )

    # 3. Run safety evaluation
    safety_results = None
    if not args.skip_safety:
        print()
        print("=" * 60)
        print("Step 3: Safety Evaluation")
        print("=" * 60)
        safety_results = run_safety_evaluation(
            project_client, azure_ai_project, dataset
        )

    # 4. Aggregate results
    combined_results = {
        "timestamp": datetime.now().isoformat(),
        "project": args.project_name,
        "dataset_size": len(dataset),
        "quality": quality_results,
        "safety": safety_results,
        "thresholds": thresholds,
    }

    # 5. Save results
    print()
    print("=" * 60)
    print("Step 4: Save Results")
    print("=" * 60)
    save_results(combined_results, args.output_dir)

    # 6. Print summary and check thresholds
    print()
    print("=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    metrics = quality_results.get("metrics", {}) if isinstance(quality_results, dict) else {}
    for metric_name in ["groundedness", "relevance", "coherence", "fluency"]:
        value = metrics.get(metric_name, "N/A")
        threshold = thresholds.get(metric_name, "N/A")
        status = "PASS" if isinstance(value, (int, float)) and value >= threshold else "FAIL"
        print(f"  {metric_name:20s}  {value:>6}  (threshold: {threshold})  [{status}]")

    if safety_results:
        safety_metrics = safety_results.get("metrics", {}) if isinstance(safety_results, dict) else {}
        safety_pass = safety_metrics.get("content_safety_pass_rate", "N/A")
        print(f"  {'safety':20s}  {safety_pass:>6}  (threshold: 1.00)  "
              f"[{'PASS' if safety_pass == 1.0 else 'FAIL'}]")

    # 7. Exit with appropriate code
    failures = check_thresholds(metrics, thresholds)
    if failures:
        print()
        print("QUALITY GATE FAILED:")
        for f in failures:
            print(f"  {f['metric']}: {f['value']:.2f} < {f['threshold']:.2f}")
        sys.exit(1)
    else:
        print()
        print("All quality gates passed.")


if __name__ == "__main__":
    main()

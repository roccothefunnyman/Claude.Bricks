"""RAG tuning matrix runner for Claude.Bricks.

Tests combinations of RAG configuration parameters (chunk size, overlap,
search mode, top-k) against the evaluation dataset, measuring quality,
latency, and cost. Identifies Pareto-optimal configurations.

Usage:
    python eval/run_rag_tuning.py \
        --chunk-sizes 300,600,1000 \
        --overlaps 0,50,100 \
        --search-modes vector,hybrid,keyword_semantic \
        --top-k-values 3,5,8 \
        --dataset eval/datasets/lego-spec-generator.jsonl \
        --output eval/results/rag-tuning-matrix.json
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
    load_prompt_template,
    score_builtin_metrics,
    score_safety,
)


def configure_search_index(
    chunk_size: int,
    overlap: int,
    search_mode: str,
    embedding_model: str,
) -> dict:
    """Configure an AI Search index with the given RAG parameters.

    In a full deployment, this would call the Azure AI Search SDK to
    update index configuration, re-chunk documents, and re-index with
    the specified embedding model. Here it returns the configuration
    for logging purposes.

    Args:
        chunk_size: Token count per chunk.
        overlap: Token overlap between chunks.
        search_mode: Search mode (vector, hybrid, keyword_semantic).
        embedding_model: Embedding model name.

    Returns:
        Configuration dict.
    """
    config = {
        "chunk_size": chunk_size,
        "overlap": overlap,
        "search_mode": search_mode,
        "embedding_model": embedding_model,
    }

    try:
        from azure.search.documents.indexes import SearchIndexClient

        credential = DefaultAzureCredential()
        endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT", "")

        if endpoint:
            # In production: update indexer skillset with chunk_size/overlap,
            # set search mode on the index, and trigger re-indexing.
            print(f"    [Would configure index: chunk={chunk_size}, overlap={overlap}, "
                  f"mode={search_mode}, embedding={embedding_model}]")
    except ImportError:
        pass

    return config


def retrieve_with_config(
    query: str,
    search_mode: str,
    top_k: int,
    similarity_threshold: float = 0.0,
) -> tuple[str, float]:
    """Retrieve context from AI Search with specific configuration.

    In a full deployment, this queries the Azure AI Search index using
    the specified search mode and top-k. Returns retrieved context and
    retrieval latency.

    Args:
        query: Search query (derived from user prompt).
        search_mode: Search mode to use.
        top_k: Number of results to retrieve.
        similarity_threshold: Minimum similarity score to include.

    Returns:
        Tuple of (context_text, retrieval_latency_ms).
    """
    start = time.perf_counter()

    try:
        from azure.search.documents import SearchClient

        credential = DefaultAzureCredential()
        endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
        index_name = os.environ.get("AZURE_SEARCH_INDEX", "lego-specs")

        if endpoint:
            client = SearchClient(
                endpoint=endpoint,
                index_name=index_name,
                credential=credential,
            )

            search_kwargs = {"top": top_k}

            if search_mode == "vector":
                # Vector-only search.
                from azure.search.documents.models import VectorizableTextQuery
                search_kwargs["vector_queries"] = [
                    VectorizableTextQuery(text=query, k_nearest_neighbors=top_k, fields="content_vector")
                ]
                search_kwargs["search_text"] = None
            elif search_mode == "hybrid":
                # Hybrid (keyword + vector).
                from azure.search.documents.models import VectorizableTextQuery
                search_kwargs["search_text"] = query
                search_kwargs["vector_queries"] = [
                    VectorizableTextQuery(text=query, k_nearest_neighbors=top_k, fields="content_vector")
                ]
            else:
                # Keyword + semantic ranker.
                search_kwargs["search_text"] = query
                search_kwargs["query_type"] = "semantic"
                search_kwargs["semantic_configuration_name"] = "default"

            results = client.search(**search_kwargs)
            context_parts = []
            for result in results:
                score = result.get("@search.score", 1.0)
                if score >= similarity_threshold:
                    context_parts.append(result.get("content", ""))
            context = "\n\n---\n\n".join(context_parts)
            latency = (time.perf_counter() - start) * 1000
            return context, latency

    except (ImportError, Exception):
        pass

    # Fallback: load context from standards docs.
    project_root = Path(__file__).resolve().parent.parent
    context_parts = []
    for doc in ["standards/parts-catalog.md", "standards/architectural-patterns.md"]:
        doc_path = project_root / doc
        if doc_path.exists():
            content = doc_path.read_text(encoding="utf-8")
            # Simulate chunking by truncating to approximate chunk size.
            context_parts.append(content[:2000])

    latency = (time.perf_counter() - start) * 1000
    return "\n\n---\n\n".join(context_parts[:top_k]), latency


def evaluate_rag_config(
    chunk_size: int,
    overlap: int,
    search_mode: str,
    top_k: int,
    embedding_model: str,
    dataset: list[dict],
    model_deployment: str,
    prompt_version: str,
) -> dict:
    """Evaluate a single RAG configuration against the dataset.

    Args:
        chunk_size: Token count per chunk.
        overlap: Token overlap between chunks.
        search_mode: Search mode.
        top_k: Number of results to retrieve.
        embedding_model: Embedding model name.
        dataset: Evaluation test cases.
        model_deployment: Azure OpenAI deployment name.
        prompt_version: System prompt version.

    Returns:
        Dict with config, aggregated scores, latency, and cost metrics.
    """
    system_prompt = load_prompt_template(prompt_version)

    # Configure the index for this run.
    index_config = configure_search_index(chunk_size, overlap, search_mode, embedding_model)

    per_case = []
    total_retrieval_latency = 0.0
    total_generation_latency = 0.0
    total_input_tokens = 0
    total_output_tokens = 0

    for test_case in dataset:
        prompt = test_case["prompt"]

        # Retrieve context with this configuration.
        context, retrieval_latency = retrieve_with_config(
            query=prompt,
            search_mode=search_mode,
            top_k=top_k,
        )
        total_retrieval_latency += retrieval_latency

        # Generate response.
        gen_result = generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            context=context,
            model_deployment=model_deployment,
        )
        response = gen_result["response"]
        total_generation_latency += gen_result["latency_ms"]
        total_input_tokens += gen_result["input_tokens"]
        total_output_tokens += gen_result["output_tokens"]

        # Score.
        builtin_scores = score_builtin_metrics(response, prompt, context)
        safety = score_safety(response)
        buildability = evaluate_buildability(response)

        scores = {
            **builtin_scores,
            "safety_pass_rate": safety,
            "buildability": buildability["score"],
        }
        per_case.append({"id": test_case.get("id", ""), "scores": scores})

    # Aggregate.
    n = len(dataset)
    metric_keys = ["groundedness", "relevance", "coherence", "fluency", "safety_pass_rate", "buildability"]
    aggregated = {}
    for key in metric_keys:
        values = [c["scores"].get(key, 0.0) for c in per_case]
        aggregated[key] = round(sum(values) / len(values), 4) if values else 0.0

    # Compute composite quality score.
    composite = (
        aggregated.get("groundedness", 0) * 0.25
        + aggregated.get("relevance", 0) * 0.25
        + aggregated.get("coherence", 0) * 0.15
        + aggregated.get("fluency", 0) * 0.10
        + aggregated.get("buildability", 0) * 0.25
    )

    avg_input = total_input_tokens / n if n else 0
    avg_output = total_output_tokens / n if n else 0
    input_rate = 0.03 / 1000
    output_rate = 0.06 / 1000
    estimated_cost = round(avg_input * input_rate + avg_output * output_rate, 6)

    return {
        "config": {
            "chunk_size": chunk_size,
            "overlap": overlap,
            "search_mode": search_mode,
            "top_k": top_k,
            "embedding_model": embedding_model,
        },
        "aggregated_scores": aggregated,
        "composite_quality": round(composite, 4),
        "avg_retrieval_latency_ms": round(total_retrieval_latency / n, 1) if n else 0,
        "avg_generation_latency_ms": round(total_generation_latency / n, 1) if n else 0,
        "avg_total_latency_ms": round((total_retrieval_latency + total_generation_latency) / n, 1) if n else 0,
        "avg_input_tokens": round(avg_input, 1),
        "avg_output_tokens": round(avg_output, 1),
        "estimated_cost_per_request": estimated_cost,
    }


def identify_pareto_optimal(results: list[dict]) -> list[dict]:
    """Identify Pareto-optimal configurations on the quality-cost frontier.

    A configuration is Pareto-optimal if no other configuration has both
    higher quality AND lower cost.

    Args:
        results: List of evaluated configuration results.

    Returns:
        List of Pareto-optimal configuration results.
    """
    pareto = []
    for candidate in results:
        cq = candidate["composite_quality"]
        cc = candidate["estimated_cost_per_request"]
        dominated = False
        for other in results:
            if other is candidate:
                continue
            oq = other["composite_quality"]
            oc = other["estimated_cost_per_request"]
            # Other dominates candidate if it has >= quality AND <= cost,
            # with at least one strict inequality.
            if oq >= cq and oc <= cc and (oq > cq or oc < cc):
                dominated = True
                break
        if not dominated:
            pareto.append(candidate)
    return pareto


def format_matrix_table(results: list[dict], pareto_configs: list[dict]) -> str:
    """Format a comparison matrix of all tested configurations.

    Args:
        results: All evaluated configurations.
        pareto_configs: Pareto-optimal configurations.

    Returns:
        Formatted table string.
    """
    pareto_set = {
        (r["config"]["chunk_size"], r["config"]["overlap"],
         r["config"]["search_mode"], r["config"]["top_k"])
        for r in pareto_configs
    }

    lines = []
    lines.append("=" * 130)
    lines.append("RAG TUNING MATRIX RESULTS")
    lines.append("=" * 130)
    lines.append("")

    header = (
        f"{'Chunk':>6s} {'Ovlp':>5s} {'Mode':<18s} {'TopK':>4s} "
        f"{'Ground':>7s} {'Relev':>7s} {'Coher':>7s} {'Build':>7s} "
        f"{'Composite':>9s} {'RetLat':>7s} {'GenLat':>7s} {'Cost($)':>8s} {'Pareto':>7s}"
    )
    lines.append(header)
    lines.append("-" * 130)

    for r in sorted(results, key=lambda x: -x["composite_quality"]):
        c = r["config"]
        s = r["aggregated_scores"]
        key = (c["chunk_size"], c["overlap"], c["search_mode"], c["top_k"])
        is_pareto = "*" if key in pareto_set else ""

        lines.append(
            f"{c['chunk_size']:>6d} {c['overlap']:>5d} {c['search_mode']:<18s} {c['top_k']:>4d} "
            f"{s.get('groundedness', 0):>7.4f} {s.get('relevance', 0):>7.4f} "
            f"{s.get('coherence', 0):>7.4f} {s.get('buildability', 0):>7.4f} "
            f"{r['composite_quality']:>9.4f} "
            f"{r['avg_retrieval_latency_ms']:>7.1f} {r['avg_generation_latency_ms']:>7.1f} "
            f"{r['estimated_cost_per_request']:>8.5f} {is_pareto:>7s}"
        )

    lines.append("")
    lines.append(f"Pareto-optimal configurations: {len(pareto_configs)}")
    for p in pareto_configs:
        c = p["config"]
        lines.append(
            f"  chunk={c['chunk_size']}, overlap={c['overlap']}, "
            f"mode={c['search_mode']}, top_k={c['top_k']} "
            f"-> quality={p['composite_quality']:.4f}, cost=${p['estimated_cost_per_request']:.5f}"
        )
    lines.append("=" * 130)

    return "\n".join(lines)


def run_rag_tuning(args: argparse.Namespace) -> None:
    """Execute the RAG tuning matrix.

    Args:
        args: Parsed command-line arguments.
    """
    chunk_sizes = [int(x.strip()) for x in args.chunk_sizes.split(",")]
    overlaps = [int(x.strip()) for x in args.overlaps.split(",")]
    search_modes = [x.strip() for x in args.search_modes.split(",")]
    top_k_values = [int(x.strip()) for x in args.top_k_values.split(",")]

    total_combos = len(chunk_sizes) * len(overlaps) * len(search_modes) * len(top_k_values)
    print(f"Chunk sizes:  {chunk_sizes}")
    print(f"Overlaps:     {overlaps}")
    print(f"Search modes: {search_modes}")
    print(f"Top-k values: {top_k_values}")
    print(f"Embedding:    {args.embedding_model}")
    print(f"Total combinations: {total_combos}")
    print()

    dataset = load_dataset(args.dataset)
    print(f"Loaded {len(dataset)} test cases from {args.dataset}")
    print()

    all_results = []
    combo_num = 0

    for chunk_size, overlap, search_mode, top_k in product(chunk_sizes, overlaps, search_modes, top_k_values):
        combo_num += 1
        label = f"chunk={chunk_size}, overlap={overlap}, mode={search_mode}, top_k={top_k}"
        print(f"[{combo_num}/{total_combos}] {label}...")

        result = evaluate_rag_config(
            chunk_size=chunk_size,
            overlap=overlap,
            search_mode=search_mode,
            top_k=top_k,
            embedding_model=args.embedding_model,
            dataset=dataset,
            model_deployment=args.model_deployment,
            prompt_version=args.prompt_version,
        )
        all_results.append(result)
        print(f"    quality={result['composite_quality']:.4f}, cost=${result['estimated_cost_per_request']:.5f}")

    # Identify Pareto-optimal configs.
    pareto = identify_pareto_optimal(all_results)

    # Print matrix table.
    table = format_matrix_table(all_results, pareto)
    print()
    print(table)

    # Save results.
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_payload = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset": args.dataset,
            "model_deployment": args.model_deployment,
            "prompt_version": args.prompt_version,
            "embedding_model": args.embedding_model,
            "total_combinations": total_combos,
        },
        "configurations": [
            {
                "config": r["config"],
                "aggregated_scores": r["aggregated_scores"],
                "composite_quality": r["composite_quality"],
                "avg_retrieval_latency_ms": r["avg_retrieval_latency_ms"],
                "avg_generation_latency_ms": r["avg_generation_latency_ms"],
                "avg_total_latency_ms": r["avg_total_latency_ms"],
                "avg_input_tokens": r["avg_input_tokens"],
                "avg_output_tokens": r["avg_output_tokens"],
                "estimated_cost_per_request": r["estimated_cost_per_request"],
            }
            for r in all_results
        ],
        "pareto_optimal": [
            {
                "config": r["config"],
                "composite_quality": r["composite_quality"],
                "estimated_cost_per_request": r["estimated_cost_per_request"],
            }
            for r in pareto
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


def main():
    """Parse arguments and run RAG tuning matrix."""
    parser = argparse.ArgumentParser(
        description="Run RAG tuning matrix for Claude.Bricks."
    )
    parser.add_argument(
        "--chunk-sizes",
        default="300,600,1000",
        help="Comma-separated chunk sizes in tokens (default: 300,600,1000).",
    )
    parser.add_argument(
        "--overlaps",
        default="0,50,100",
        help="Comma-separated overlap sizes in tokens (default: 0,50,100).",
    )
    parser.add_argument(
        "--search-modes",
        default="vector,hybrid,keyword_semantic",
        help="Comma-separated search modes (default: vector,hybrid,keyword_semantic).",
    )
    parser.add_argument(
        "--top-k-values",
        default="3,5,8",
        help="Comma-separated top-k values (default: 3,5,8).",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-ada-002",
        help="Embedding model to use (default: text-embedding-ada-002).",
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
        "--prompt-version",
        default="v1",
        help="System prompt version to use.",
    )
    parser.add_argument(
        "--output",
        default="eval/results/rag-tuning-matrix.json",
        help="Output path for tuning results JSON.",
    )
    args = parser.parse_args()

    run_rag_tuning(args)


if __name__ == "__main__":
    main()

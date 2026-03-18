#!/usr/bin/env python3
"""SDE Benchmark Runner — evaluates embedding models against annotated fixtures."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from typing import NamedTuple

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))


DATASETS_DIR = Path(__file__).parent / "datasets"
LEADERBOARD_FILE = Path(__file__).parent / "leaderboard.json"


class BenchmarkSample(NamedTuple):
    id: str
    domain: str
    text_a: str
    text_b: str
    expected_verdict: str  # identical | semantic_shift | contradiction | added | removed


def load_dataset(domain: str) -> list[BenchmarkSample]:
    """Load annotated samples from a domain directory."""
    samples = []
    domain_dir = DATASETS_DIR / domain
    if not domain_dir.exists():
        return samples

    for file in domain_dir.glob("*.json"):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    samples.append(
                        BenchmarkSample(
                            id=f"{domain}/{file.stem}/{item.get('id', 0)}",
                            domain=domain,
                            text_a=item["text_a"],
                            text_b=item["text_b"],
                            expected_verdict=item["expected_verdict"],
                        )
                    )
            else:
                samples.append(
                    BenchmarkSample(
                        id=f"{domain}/{file.stem}",
                        domain=domain,
                        text_a=data["text_a"],
                        text_b=data["text_b"],
                        expected_verdict=data["expected_verdict"],
                    )
                )
        except Exception as e:
            print(f"Warning: could not load {file}: {e}")

    return samples


def compute_metrics(
    predictions: list[str], labels: list[str], target_verdicts: list[str]
) -> dict:
    """Compute precision, recall, F1 for each target verdict."""
    metrics = {}
    for verdict in set(target_verdicts + list(set(predictions))):
        tp = sum(1 for p, l in zip(predictions, labels) if p == verdict and l == verdict)
        fp = sum(1 for p, l in zip(predictions, labels) if p == verdict and l != verdict)
        fn = sum(1 for p, l in zip(predictions, labels) if p != verdict and l == verdict)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        metrics[verdict] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4), "support": labels.count(verdict)}
    # Macro F1
    f1_scores = [v["f1"] for v in metrics.values() if v["support"] > 0]
    metrics["macro_f1"] = round(sum(f1_scores) / len(f1_scores), 4) if f1_scores else 0.0
    accuracy = sum(1 for p, l in zip(predictions, labels) if p == l) / len(labels) if labels else 0.0
    metrics["accuracy"] = round(accuracy, 4)
    return metrics


def run_benchmark(dataset: str = "all", model_name: str = "all-MiniLM-L6-v2") -> dict:
    """Run benchmark and return metrics dict."""
    from core.comparator import SemanticComparator

    domains = ["legal", "medical", "code", "journalism", "ai_outputs"] if dataset == "all" else [dataset]
    all_samples: list[BenchmarkSample] = []
    for d in domains:
        all_samples.extend(load_dataset(d))

    if not all_samples:
        print(f"No samples found for dataset '{dataset}'. Create fixtures in benchmarks/datasets/")
        return {}

    print(f"Running benchmark: {len(all_samples)} samples, model={model_name}")
    comparator = SemanticComparator(model_name=model_name)

    predictions = []
    labels = []
    timings = []

    for sample in all_samples:
        t0 = time.perf_counter()
        result = comparator.diff(sample.text_a, sample.text_b, domain=sample.domain)
        elapsed = time.perf_counter() - t0
        timings.append(elapsed * 1000)

        # Map document-level verdict to chunk-level for comparison
        pred = result.overall
        if pred == "unrelated":
            pred = "contradiction"
        predictions.append(pred)
        labels.append(sample.expected_verdict)

    metrics = compute_metrics(predictions, labels, list(set(labels)))
    metrics["model"] = model_name
    metrics["samples"] = len(all_samples)
    metrics["avg_latency_ms"] = round(sum(timings) / len(timings), 1)
    metrics["p95_latency_ms"] = round(sorted(timings)[int(0.95 * len(timings))], 1)

    return metrics


def update_leaderboard(metrics: dict) -> None:
    """Update leaderboard.json with new results."""
    leaderboard = []
    if LEADERBOARD_FILE.exists():
        try:
            leaderboard = json.loads(LEADERBOARD_FILE.read_text(encoding="utf-8"))
        except Exception:
            leaderboard = []

    # Remove old entry for this model
    leaderboard = [e for e in leaderboard if e.get("model") != metrics.get("model")]
    leaderboard.append(metrics)
    leaderboard.sort(key=lambda x: x.get("macro_f1", 0), reverse=True)
    LEADERBOARD_FILE.write_text(json.dumps(leaderboard, indent=2), encoding="utf-8")
    print(f"Leaderboard updated: {LEADERBOARD_FILE}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="SDE Benchmark Runner")
    parser.add_argument("--dataset", default="all", help="Dataset: all|legal|medical|code|journalism|ai_outputs")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model")
    parser.add_argument("--no-leaderboard", action="store_true", help="Do not update leaderboard.json")
    args = parser.parse_args()

    metrics = run_benchmark(args.dataset, args.model)
    if not metrics:
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"BENCHMARK RESULTS — {metrics['model']}")
    print(f"{'='*60}")
    print(f"Samples: {metrics['samples']} | Accuracy: {metrics['accuracy']:.2%} | Macro F1: {metrics['macro_f1']:.4f}")
    print(f"Avg latency: {metrics['avg_latency_ms']}ms | P95: {metrics['p95_latency_ms']}ms")
    print(f"\nPer-verdict metrics:")
    for verdict, m in metrics.items():
        if isinstance(m, dict):
            print(f"  {verdict:20s} P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} (n={m['support']})")

    if not args.no_leaderboard:
        update_leaderboard(metrics)


if __name__ == "__main__":
    main()

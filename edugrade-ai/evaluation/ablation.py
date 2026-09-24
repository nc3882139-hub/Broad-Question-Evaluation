"""Ablation runner using the grading engine's independently selectable methods."""
from __future__ import annotations

from .dataset import BenchmarkRecord

CONFIGURATIONS = [
    {"configuration": "A_keyword_concept", "method": "keyword", "status": "supported"},
    {"configuration": "B_semantic_similarity", "method": "embedding", "status": "supported"},
    {"configuration": "C_keyword_plus_semantic", "method": "hybrid", "status": "supported"},
    {"configuration": "D_keyword_semantic_rubric", "method": "hybrid", "status": "shared_engine_path"},
    {"configuration": "E_keyword_semantic_rubric_evidence", "method": "hybrid", "status": "shared_engine_path"},
    {"configuration": "F_full_system_factual_consistency", "method": "hybrid", "status": "shared_engine_path"},
]


def run_ablation(records: list[BenchmarkRecord]) -> dict:
    """Run variants against identical rows without overstating unsupported isolation."""
    from evaluation.evaluate_grading import evaluate_records

    results = []
    for config in CONFIGURATIONS:
        evaluation, _, skipped = evaluate_records(records, method=config["method"])
        metrics = evaluation["metrics"] or {}
        results.append({**config, **metrics, "evaluated_count": evaluation["evaluated_count"], "skipped_count": len(skipped)})
    return {"configurations": CONFIGURATIONS, "results": results,
            "note": "Only configurations marked supported isolate selectable grading methods. Shared-engine paths are not independent component ablations."}

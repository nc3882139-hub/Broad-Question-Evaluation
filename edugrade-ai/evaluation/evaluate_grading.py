"""Run reproducible grading evaluation on a human-graded benchmark.

Example:
    python evaluation/evaluate_grading.py --dataset data/grading/grading.csv

No benchmark scores are embedded in this script. The supplied dataset must contain
human marks; the legacy ``score`` column is accepted as an input alias.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("EMBEDDING_BACKEND", "hashing")

from app.services.grading_engine import grade_answer  # noqa: E402
from app.services.rubric_service import find_rubric  # noqa: E402

from evaluation.ablation import run_ablation  # noqa: E402
from evaluation.dataset import BenchmarkRecord, load_dataset  # noqa: E402
from evaluation.leakage import detect_duplicates  # noqa: E402
from evaluation.metrics import grading_metrics, teacher_agreement  # noqa: E402
from evaluation.splitting import grouped_train_test_split  # noqa: E402


def _rubric(record: BenchmarkRecord):
    if record.rubric:
        return record.rubric, 1.0
    return find_rubric(record.question)


def evaluate_records(records: list[BenchmarkRecord], *, method: str = "hybrid") -> tuple[dict, list[dict], list[dict]]:
    actual, predicted, predictions, skipped = [], [], [], []
    for record in records:
        rubric, match = _rubric(record)
        if not rubric:
            skipped.append({"question_id": record.question_id, "reason": "no approved rubric matched"})
            continue
        result = grade_answer(record.question, record.student_answer, rubric, method=method)
        actual.append(record.human_teacher_mark)
        predicted.append(float(result["final_score"]))
        predictions.append({
            "question_id": record.question_id,
            "human_teacher_mark": record.human_teacher_mark,
            "ai_mark": result["final_score"],
            "confidence": result.get("confidence"),
            "review_required": bool(result.get("issues")),
            "rubric_match": match,
            "method": method,
        })
    return ({"metrics": grading_metrics(actual, predicted) if actual else None,
             "evaluated_count": len(actual), "skipped_count": len(skipped)}, predictions, skipped)


def _write_artifacts(output_dir: Path, result: dict, predictions: list[dict], report: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["question_id", "human_teacher_mark", "ai_mark", "confidence", "review_required", "rubric_match", "method"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(predictions)
    (output_dir / "report.txt").write_text(report, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(ROOT / "data" / "grading" / "grading.csv"))
    parser.add_argument("--output-dir", default=str(ROOT / "evaluation" / "results" / "latest"))
    parser.add_argument("--method", choices=["keyword", "tfidf", "embedding", "hybrid"], default="hybrid")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--strict", action="store_true", help="fail on the first invalid dataset row")
    parser.add_argument("--ablation", action="store_true", help="also write the supported configuration comparison")
    args = parser.parse_args(argv)

    records, skipped_rows = load_dataset(args.dataset, strict=args.strict)
    train, test, split = grouped_train_test_split(records, test_size=args.test_size, seed=args.seed)
    evaluation, predictions, skipped_rubrics = evaluate_records(test or records, method=args.method)
    result = {
        "evaluation_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": {"path": str(Path(args.dataset)), "total_count": len(records), "skipped_rows": skipped_rows},
        "split": split,
        "leakage": detect_duplicates(records),
        "evaluation": evaluation,
        "teacher_agreement": teacher_agreement([[r.teacher_marks[i] for r in records if len(r.teacher_marks) > i] for i in range(3)]),
        "ai_agreement_note": "AI agreement with the human reference is reported separately from teacher-teacher agreement.",
        "skipped": skipped_rubrics,
        "configuration": {"method": args.method, "seed": args.seed, "test_size": args.test_size},
    }
    report = _human_report(result)
    output_dir = Path(args.output_dir)
    _write_artifacts(output_dir, result, predictions, report)
    if args.ablation:
        ablation = run_ablation(records)
        (output_dir / "ablation.json").write_text(json.dumps(ablation, indent=2), encoding="utf-8")
        with (output_dir / "ablation.csv").open("w", newline="", encoding="utf-8") as handle:
            fields = ["configuration", "method", "status", "mae", "rmse", "pearson", "spearman", "qwk", "exact_agreement", "within_1_0"]
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(ablation["results"])
    print(report)


def _human_report(result: dict) -> str:
    evaluation = result["evaluation"]
    lines = ["EduGrade AI grading evaluation", "", f"Dataset rows: {result['dataset']['total_count']}",
             f"Evaluated: {evaluation['evaluated_count']}", f"Skipped: {evaluation['skipped_count']}",
             f"Split: {result['split']['strategy']} (seed={result['split']['seed']})", ""]
    if evaluation["metrics"] is None:
        lines.append("No valid human-graded rows were available; no performance metrics were calculated.")
    else:
        lines.append("Metric                 Value")
        for key, value in evaluation["metrics"].items():
            lines.append(f"{key:<22} {value:.4f}")
    lines.append("\nThese are measurements on the supplied dataset, not general performance claims.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()

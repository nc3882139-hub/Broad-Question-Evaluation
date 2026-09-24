import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.dataset import DatasetValidationError, load_dataset
from evaluation.leakage import detect_duplicates, detect_split_overlap
from evaluation.metrics import grading_metrics, quadratic_weighted_kappa, teacher_agreement
from evaluation.splitting import grouped_train_test_split


def _row(question_id, answer, **extra):
    return {
        "question_id": question_id,
        "question": "Explain the topic.",
        "max_marks": 5,
        "student_answer": answer,
        "human_teacher_mark": 3,
        **extra,
    }


def test_dataset_loader_supports_json_and_jsonl(tmp_path: Path):
    rows = [_row("q1", "An answer", student_id="s1"), _row("q2", "Another answer", student_id="s2")]
    json_path = tmp_path / "data.json"
    json_path.write_text(json.dumps(rows), encoding="utf-8")
    jsonl_path = tmp_path / "data.jsonl"
    jsonl_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    assert len(load_dataset(json_path)[0]) == 2
    assert len(load_dataset(jsonl_path)[0]) == 2


def test_dataset_validation_rejects_invalid_marks(tmp_path: Path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps([_row("q1", "Answer", max_marks=0)]), encoding="utf-8")
    with pytest.raises(DatasetValidationError):
        load_dataset(path)


def test_metrics_include_qwk_and_agreement_bands():
    metrics = grading_metrics([0, 1, 2, 3], [0, 1.5, 2, 4])
    assert set(("mae", "rmse", "pearson", "spearman", "qwk", "exact_agreement", "within_0_5", "within_1_0")) <= metrics.keys()
    assert quadratic_weighted_kappa([1, 2, 3], [1, 2, 3]) == 1.0
    assert metrics["within_1_0"] == 1.0


def test_duplicate_and_group_leakage_detection():
    records, _ = load_dataset_data([
        _row("q1", "The same answer", student_id="s1"),
        _row("q1", "The same answer", student_id="s2"),
        _row("q2", "A different answer", student_id="s3"),
    ])
    duplicates = detect_duplicates(records)
    assert duplicates["duplicate_answers"]
    train, test, split = grouped_train_test_split(records, test_size=0.4, seed=3)
    assert not split["overlap"]["question_id_overlap"]
    assert not detect_split_overlap(train, test)["question_id_overlap"]


def test_teacher_agreement_is_separate_from_ai_metrics():
    agreement = teacher_agreement([[1, 2, 3], [1, 2.5, 3]])
    assert agreement["teacher_count"] == 2
    assert agreement["pair_count"] == 1
    assert agreement["mae"] == pytest.approx(1 / 6)


def load_dataset_data(rows):
    from evaluation.dataset import validate_records
    return validate_records(rows)

"""Validated benchmark dataset loading for grading experiments."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


class DatasetValidationError(ValueError):
    """Raised when a benchmark row cannot be used for grading evaluation."""


@dataclass(frozen=True)
class BenchmarkRecord:
    question_id: str
    question: str
    max_marks: float
    student_answer: str
    human_teacher_mark: float
    rubric: dict[str, Any] | None = None
    teacher_feedback: str = ""
    student_id: str | None = None
    answer_group: str | None = None
    ai_mark: float | None = None
    confidence: float | None = None
    review_required: bool | None = None
    teacher_marks: tuple[float, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["teacher_marks"] = list(self.teacher_marks)
        return value


def _as_float(value: Any, field: str, row_number: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DatasetValidationError(f"row {row_number}: {field} must be numeric") from exc
    if number != number or number in (float("inf"), float("-inf")):
        raise DatasetValidationError(f"row {row_number}: {field} must be finite")
    return number


def _optional_float(value: Any, field: str, row_number: int) -> float | None:
    if value in (None, ""):
        return None
    return _as_float(value, field, row_number)


def _bool(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _row_to_record(row: dict[str, Any], row_number: int) -> BenchmarkRecord:
    question = str(row.get("question", "")).strip()
    answer = str(row.get("student_answer", row.get("answer", ""))).strip()
    question_id = str(row.get("question_id", "")).strip() or f"row-{row_number}"
    if not question:
        raise DatasetValidationError(f"row {row_number}: question is required")
    if not answer:
        raise DatasetValidationError(f"row {row_number}: student_answer is required")
    max_marks = _as_float(row.get("max_marks"), "max_marks", row_number)
    if max_marks <= 0:
        raise DatasetValidationError(f"row {row_number}: max_marks must be greater than zero")
    raw_mark = row.get("human_teacher_mark", row.get("teacher_mark", row.get("score")))
    human_mark = _as_float(raw_mark, "human_teacher_mark", row_number)
    if not 0 <= human_mark <= max_marks:
        raise DatasetValidationError(f"row {row_number}: human_teacher_mark must be within max_marks")
    teacher_marks = []
    for field in ("teacher_1_mark", "teacher_2_mark", "teacher_3_mark"):
        mark = _optional_float(row.get(field), field, row_number)
        if mark is not None:
            if not 0 <= mark <= max_marks:
                raise DatasetValidationError(f"row {row_number}: {field} must be within max_marks")
            teacher_marks.append(mark)
    rubric = row.get("rubric")
    if isinstance(rubric, str) and rubric.strip():
        try:
            rubric = json.loads(rubric)
        except json.JSONDecodeError as exc:
            raise DatasetValidationError(f"row {row_number}: rubric must be valid JSON") from exc
    if rubric is not None and not isinstance(rubric, dict):
        raise DatasetValidationError(f"row {row_number}: rubric must be an object")
    return BenchmarkRecord(
        question_id=question_id, question=question, max_marks=max_marks,
        student_answer=answer, human_teacher_mark=human_mark, rubric=rubric,
        teacher_feedback=str(row.get("teacher_feedback", "") or ""),
        student_id=str(row["student_id"]).strip() if row.get("student_id") not in (None, "") else None,
        answer_group=str(row["answer_group"]).strip() if row.get("answer_group") not in (None, "") else None,
        ai_mark=_optional_float(row.get("ai_mark"), "ai_mark", row_number),
        confidence=_optional_float(row.get("confidence"), "confidence", row_number),
        review_required=_bool(row.get("review_required")), teacher_marks=tuple(teacher_marks),
    )


def validate_records(rows: Iterable[dict[str, Any]], *, strict: bool = True) -> tuple[list[BenchmarkRecord], list[dict[str, str]]]:
    records, skipped = [], []
    for row_number, row in enumerate(rows, 1):
        try:
            records.append(_row_to_record(dict(row), row_number))
        except DatasetValidationError as exc:
            if strict:
                raise
            skipped.append({"row": str(row_number), "reason": str(exc)})
    return records, skipped


def load_dataset(path: str | Path, *, strict: bool = True) -> tuple[list[BenchmarkRecord], list[dict[str, str]]]:
    """Load CSV, JSON array/object, or JSONL benchmark data."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    if source.suffix.lower() == ".csv":
        with source.open(newline="", encoding="utf-8") as handle:
            return validate_records(csv.DictReader(handle), strict=strict)
    if source.suffix.lower() in {".json", ".jsonl"}:
        if source.suffix.lower() == ".jsonl":
            rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            value = json.loads(source.read_text(encoding="utf-8"))
            rows = value if isinstance(value, list) else value.get("records", [])
        if not isinstance(rows, list):
            raise DatasetValidationError("JSON dataset must contain an array or a records array")
        return validate_records(rows, strict=strict)
    raise DatasetValidationError("dataset format must be CSV, JSON, or JSONL")

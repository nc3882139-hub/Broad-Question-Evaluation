"""Duplicate and train/test leakage checks for benchmark datasets."""
from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
import re
from typing import Iterable

from .dataset import BenchmarkRecord


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", value.lower())).strip()


def detect_duplicates(records: Iterable[BenchmarkRecord], near_threshold: float = 0.92) -> dict[str, list[list[str]]]:
    items = list(records)
    exact: dict[str, list[str]] = defaultdict(list)
    for record in items:
        exact[normalize_text(record.student_answer)].append(record.question_id)
    duplicate_answers = [ids for ids in exact.values() if len(ids) > 1]
    duplicate_combinations = []
    seen: dict[tuple[str, str], str] = {}
    for record in items:
        key = (record.question_id, normalize_text(record.student_answer))
        if key in seen:
            duplicate_combinations.append([seen[key], record.question_id])
        else:
            seen[key] = record.question_id
    near_duplicates = []
    for index, left in enumerate(items):
        for right in items[index + 1:]:
            if left.question_id == right.question_id and normalize_text(left.student_answer) == normalize_text(right.student_answer):
                continue
            similarity = SequenceMatcher(None, normalize_text(left.student_answer), normalize_text(right.student_answer)).ratio()
            if similarity >= near_threshold:
                near_duplicates.append([left.question_id, right.question_id])
    return {"duplicate_answers": duplicate_answers, "near_duplicate_answers": near_duplicates,
            "duplicate_question_answer_combinations": duplicate_combinations}


def detect_split_overlap(train: Iterable[BenchmarkRecord], test: Iterable[BenchmarkRecord]) -> dict[str, list[str]]:
    train_items, test_items = list(train), list(test)
    train_answers = {normalize_text(item.student_answer) for item in train_items}
    train_questions = {item.question_id for item in train_items}
    return {"answer_overlap": [item.question_id for item in test_items if normalize_text(item.student_answer) in train_answers],
            "question_id_overlap": [item.question_id for item in test_items if item.question_id in train_questions]}

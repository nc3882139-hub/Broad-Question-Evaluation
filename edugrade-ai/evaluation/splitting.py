"""Deterministic group-aware train/test splitting."""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Iterable

from .dataset import BenchmarkRecord
from .leakage import detect_split_overlap


def _group_components(records: list[BenchmarkRecord]) -> dict[int, str]:
    parents = list(range(len(records)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parents[right] = left

    owners = {}
    for index, record in enumerate(records):
        for value in (f"question:{record.question_id}",
                      f"student:{record.student_id}" if record.student_id else None,
                      f"answer_group:{record.answer_group}" if record.answer_group else None):
            if value is not None:
                if value in owners:
                    union(index, owners[value])
                owners[value] = index
    names = {}
    result = {}
    for index in range(len(records)):
        root = find(index)
        names.setdefault(root, f"group:{len(names) + 1}")
        result[index] = names[root]
    return result


def grouped_train_test_split(records: Iterable[BenchmarkRecord], test_size: float = 0.2, seed: int = 42) -> tuple[list[BenchmarkRecord], list[BenchmarkRecord], dict[str, object]]:
    items = list(records)
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between zero and one")
    keys = _group_components(items)
    groups: dict[str, list[BenchmarkRecord]] = defaultdict(list)
    for index, record in enumerate(items):
        groups[keys[index]].append(record)
    names = list(groups)
    random.Random(seed).shuffle(names)
    target = max(1, round(len(items) * test_size)) if len(names) > 1 else 0
    test_names, count = [], 0
    for name in names:
        if count >= target and test_names:
            break
        test_names.append(name)
        count += len(groups[name])
    test_set = set(test_names)
    test = [record for index, record in enumerate(items) if keys[index] in test_set]
    train = [record for index, record in enumerate(items) if keys[index] not in test_set]
    return train, test, {"strategy": "grouped", "group_fields": ["answer_group", "student_id", "question_id"],
                         "seed": seed, "test_size": test_size, "train_count": len(train),
                         "test_count": len(test), "overlap": detect_split_overlap(train, test)}

"""Dependency-light grading and teacher-agreement metrics."""
from __future__ import annotations

import math
from itertools import combinations
from typing import Iterable


def _pairs(actual: Iterable[float], predicted: Iterable[float]) -> tuple[list[float], list[float]]:
    a, p = list(actual), list(predicted)
    if len(a) != len(p) or not a:
        raise ValueError("actual and predicted must have the same non-zero length")
    return a, p


def _pearson(actual: list[float], predicted: list[float]) -> float:
    am, pm = sum(actual) / len(actual), sum(predicted) / len(predicted)
    numerator = sum((x - am) * (y - pm) for x, y in zip(actual, predicted))
    left = sum((x - am) ** 2 for x in actual)
    right = sum((y - pm) ** 2 for y in predicted)
    return numerator / math.sqrt(left * right) if left and right else 0.0


def _rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        rank = (i + j) / 2 + 1
        for index in order[i:j + 1]:
            ranks[index] = rank
        i = j + 1
    return ranks


def quadratic_weighted_kappa(actual: Iterable[float], predicted: Iterable[float], step: float = 0.5) -> float:
    """Compute QWK after mapping continuous marks to the supplied mark step."""
    a, p = _pairs(actual, predicted)
    if step <= 0:
        raise ValueError("step must be greater than zero")
    observed = [round(value / step) for value in a]
    forecasts = [round(value / step) for value in p]
    categories = sorted(set(observed) | set(forecasts))
    if len(categories) < 2:
        return 1.0
    index = {category: i for i, category in enumerate(categories)}
    matrix = [[0.0 for _ in categories] for _ in categories]
    for truth, forecast in zip(observed, forecasts):
        matrix[index[truth]][index[forecast]] += 1
    truth_hist = [sum(row) for row in matrix]
    forecast_hist = [sum(matrix[row][col] for row in range(len(categories))) for col in range(len(categories))]
    total = len(a)
    denominator = numerator = 0.0
    scale = max(categories) - min(categories)
    for i in range(len(categories)):
        for j in range(len(categories)):
            weight = ((categories[i] - categories[j]) / scale) ** 2
            expected = truth_hist[i] * forecast_hist[j] / total
            numerator += weight * matrix[i][j]
            denominator += weight * expected
    return 1.0 - numerator / denominator if denominator else 1.0


def grading_metrics(actual: Iterable[float], predicted: Iterable[float]) -> dict[str, float]:
    a, p = _pairs(actual, predicted)
    errors = [forecast - truth for truth, forecast in zip(a, p)]
    return {
        "mae": sum(abs(error) for error in errors) / len(errors),
        "rmse": math.sqrt(sum(error * error for error in errors) / len(errors)),
        "pearson": _pearson(a, p), "spearman": _pearson(_rank(a), _rank(p)),
        "qwk": quadratic_weighted_kappa(a, p),
        "exact_agreement": sum(x == y for x, y in zip(a, p)) / len(a),
        "within_0_5": sum(abs(x - y) <= 0.5 for x, y in zip(a, p)) / len(a),
        "within_1_0": sum(abs(x - y) <= 1.0 for x, y in zip(a, p)) / len(a),
    }


def teacher_agreement(teacher_marks: Iterable[Iterable[float]]) -> dict[str, float | int | None]:
    """Summarize pairwise teacher agreement separately from AI agreement."""
    columns = [list(column) for column in teacher_marks]
    pairs = [grading_metrics(left, right) for left, right in combinations(columns, 2)
             if len(left) == len(right) and left]
    if not pairs:
        return {"teacher_count": len(columns), "pair_count": 0, "mae": None, "qwk": None}
    return {"teacher_count": len(columns), "pair_count": len(pairs),
            "mae": sum(item["mae"] for item in pairs) / len(pairs),
            "qwk": sum(item["qwk"] for item in pairs) / len(pairs)}

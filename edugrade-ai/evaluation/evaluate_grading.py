"""Grading-method comparison on data/grading/grading.csv:
keyword-only vs TF-IDF vs embedding-similarity vs hybrid (full engine).
Reports MAE, RMSE, Pearson, Spearman — ready for a research paper table.
Set EMBEDDING_BACKEND=sentence-transformers (default) for real-model numbers;
the hashing fallback lets this run offline.
"""
import csv
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("EMBEDDING_BACKEND", os.getenv("EMBEDDING_BACKEND", "hashing"))

from app.services.grading_engine import grade_answer          # noqa: E402
from app.services.rubric_service import find_rubric            # noqa: E402


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx = sum((a - mx) ** 2 for a in x)
    vy = sum((b - my) ** 2 for b in y)
    return cov / ((vx * vy) ** 0.5) if vx and vy else 0.0


def _ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r, i = [0.0] * len(v), 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    return pearson(_ranks(x), _ranks(y))


def main():
    path = ROOT / "data" / "grading" / "grading.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    methods = ["keyword", "tfidf", "embedding", "hybrid"]
    preds = {m: [] for m in methods}
    gold = []
    skipped = 0
    for r in rows:
        rubric, score = find_rubric(r["question"])
        if not rubric:
            skipped += 1
            continue
        gold.append(float(r["score"]))
        for m in methods:
            preds[m].append(grade_answer(r["question"], r["answer"], rubric, method=m)["final_score"])
    if skipped:
        print(f"(skipped {skipped} rows with no matching rubric)")
    print(f"\n{'method':<12}{'MAE':>8}{'RMSE':>8}{'Pearson':>10}{'Spearman':>10}")
    for m in methods:
        errs = [p - g for p, g in zip(preds[m], gold)]
        mae = sum(abs(e) for e in errs) / len(errs)
        rmse = (sum(e * e for e in errs) / len(errs)) ** 0.5
        print(f"{m:<12}{mae:>8.3f}{rmse:>8.3f}{pearson(preds[m], gold):>10.3f}"
              f"{spearman(preds[m], gold):>10.3f}")
    print(f"\n(n = {len(gold)})")


if __name__ == "__main__":
    main()
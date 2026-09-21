"""Sentiment classifier evaluation: accuracy, per-class P/R/F1, confusion matrix.
Set SENTIMENT_BACKEND=transformers (default) for the neural model;
lexicon fallback works offline."""
import csv
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.sentiment_service import analyze  # noqa: E402


def main():
    path = ROOT / "data" / "sentiment" / "sentiment.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    labels = sorted({r["label"].strip() for r in rows})
    tp = Counter()
    fp = Counter()
    fn = Counter()
    correct = 0
    cm = {t: {p: 0 for p in labels} for t in labels}
    for r in rows:
        true = r["label"].strip()
        pred = analyze(r["text"])["label"]
        cm[true][pred] += 1
        if pred == true:
            correct += 1
            tp[true] += 1
        else:
            fp[pred] += 1
            fn[true] += 1
    n = len(rows)
    print(f"\nAccuracy: {correct / n:.3f}  (n={n})")
    print(f"{'label':<10}{'precision':>10}{'recall':>9}{'f1':>8}{'support':>9}")
    for l in labels:
        p = tp[l] / (tp[l] + fp[l]) if tp[l] + fp[l] else 0
        r = tp[l] / (tp[l] + fn[l]) if tp[l] + fn[l] else 0
        f = 2 * p * r / (p + r) if p + r else 0
        print(f"{l:<10}{p:>10.3f}{r:>9.3f}{f:>8.3f}{tp[l] + fn[l]:>9}")
    print("\nConfusion matrix (rows = true, cols = predicted):")
    print(" " * 12 + "".join(f"{l:>10}" for l in labels))
    for t in labels:
        print(f"{t:<12}" + "".join(f"{cm[t][p]:>10}" for p in labels))


if __name__ == "__main__":
    main()
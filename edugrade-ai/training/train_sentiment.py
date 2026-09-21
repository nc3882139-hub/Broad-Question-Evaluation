"""PHASE 4 — Fine-tune the sentiment/emotion classifier on a small labeled dataset.
Supports CSV (text,label) or JSONL. Prints accuracy / macro F1 / confusion matrix.
Usage: python training/train_sentiment.py [--base-model bert-base-uncased]
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_dataset(path: Path):
    texts, labels = [], []
    if path.suffix == ".jsonl":
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                o = json.loads(line)
                texts.append(o["text"])
                labels.append(str(o["label"]))
    else:
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                texts.append(row["text"])
                labels.append(row["label"].strip())
    return texts, labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "sentiment" / "sentiment.csv"))
    ap.add_argument("--base-model", default=None,
                    help="e.g. models/domain_adapted (self-supervised output) or any HF model")
    ap.add_argument("--output", default=str(ROOT / "models" / "sentiment_finetuned"))
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    import os
    base = args.base_model or os.getenv("SENTIMENT_MODEL",
                                        "cardiffnlp/twitter-roberta-base-sentiment-latest")
    print(f"FINE-TUNING sentiment classifier: {base} -> {args.output}")
    try:
        import numpy as np
        import torch
        from datasets import Dataset
        from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                                     precision_recall_fscore_support)
        from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                                  DataCollatorWithPadding, Trainer, TrainingArguments)
    except ImportError:
        raise SystemExit("Missing deps: pip install torch transformers datasets scikit-learn")

    texts, labels = load_dataset(Path(args.data))
    unique = sorted(set(labels))
    label2id = {l: i for i, l in enumerate(unique)}
    print(f"examples: {len(texts)}   labels: {unique}")

    tok = AutoTokenizer.from_pretrained(base)
    model = AutoModelForSequenceClassification.from_pretrained(
        base, num_labels=len(unique), id2label={i: l for l, i in label2id.items()},
        label2id=label2id)
    ds = Dataset.from_dict({"text": texts, "label": [label2id[l] for l in labels]})
    ds = ds.map(lambda b: tok(b["text"], truncation=True), batched=True)
    ds = ds.train_test_split(test_size=0.2, seed=42)

    def metrics(p):
        preds = np.argmax(p.predictions, axis=1)
        pr, rc, f1, _ = precision_recall_fscore_support(p.label_ids, preds,
                                                        average="macro", zero_division=0)
        return {"accuracy": accuracy_score(p.label_ids, preds),
                "precision": pr, "recall": rc, "f1": f1}

    trainer = Trainer(model=model,
                      args=TrainingArguments(output_dir=args.output, num_train_epochs=args.epochs,
                                             per_device_train_batch_size=args.batch_size,
                                             learning_rate=2e-5, save_strategy="no",
                                             evaluation_strategy="epoch", report_to=[]),
                      train_dataset=ds["train"], eval_dataset=ds["test"],
                      data_collator=DataCollatorWithPadding(tok), compute_metrics=metrics)
    trainer.train()
    out = trainer.predict(ds["test"])
    preds = np.argmax(out.predictions, axis=1)
    print("\nConfusion matrix (rows = true, cols = predicted):")
    print(confusion_matrix(out.label_ids, preds))
    trainer.save_model(args.output)
    tok.save_pretrained(args.output)
    print(f"Saved fine-tuned classifier to: {args.output}")
    print("Use it by setting SENTIMENT_MODEL=<path> in .env")


if __name__ == "__main__":
    main()
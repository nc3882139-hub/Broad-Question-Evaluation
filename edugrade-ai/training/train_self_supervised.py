"""Domain-adaptive pretraining (masked language modeling) on UNLABELED student answers.

PHASE 1  Collect      — drop unlabeled answers into data/unlabeled/ (.txt or .jsonl)
PHASE 2  Clean        — normalize, filter, deduplicate (this script)
PHASE 3  Pretrain     — MLM domain-adaptive pretraining -> models/domain_adapted/
(PHASE 4  Fine-tune   — see train_sentiment.py, point --base-model at models/domain_adapted)

This is REAL MLM training, not a simulated step. The prototype runs fine without it.
Usage:  python training/train_self_supervised.py --model bert-base-uncased --epochs 2
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_corpus(folder: Path):
    texts = []
    for p in sorted(folder.glob("**/*")):
        if p.suffix == ".txt":
            texts.append(p.read_text(encoding="utf-8", errors="ignore"))
        elif p.suffix == ".jsonl":
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    texts.append(obj.get("text") or obj.get("answer") or obj.get("student_answer") or "")
                except json.JSONDecodeError:
                    continue
    return texts


def clean(texts):
    out, seen = [], set()
    for t in texts:
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) < 10 or len(t) > 2000:
            continue
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "unlabeled"))
    ap.add_argument("--model", "--base-model", dest="model", default="bert-base-uncased")
    ap.add_argument("--output", default=str(ROOT / "models" / "domain_adapted"))
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--block-size", type=int, default=128)
    ap.add_argument("--batch-size", type=int, default=8)
    args = ap.parse_args()

    print("=" * 70)
    print("PHASE 1 — COLLECT: reading unlabeled student answers from", args.data)
    texts = load_corpus(Path(args.data))
    print(f"  raw documents: {len(texts)}")
    print("PHASE 2 — CLEAN: normalizing, filtering, deduplicating")
    texts = clean(texts)
    print(f"  clean documents: {len(texts)}")
    if len(texts) < 20:
        print("  WARNING: very small corpus — results will be weak. Add more data first.")
    print("PHASE 3 — DOMAIN-ADAPTIVE PRETRAINING (masked language modeling)")
    print("=" * 70)
    try:
        import torch
        from datasets import Dataset
        from transformers import (AutoModelForMaskedLM, AutoTokenizer,
                                  DataCollatorForLanguageModeling, Trainer,
                                  TrainingArguments)
    except ImportError:
        sys.exit("Missing deps. Install: pip install torch transformers datasets")

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForMaskedLM.from_pretrained(args.model)

    def tokenize(batch):
        return tok(batch["text"], truncation=True, max_length=args.block_size)

    ds = Dataset.from_dict({"text": texts}).map(tokenize, batched=True,
                                                remove_columns=["text"])

    def group(batched, block=args.block_size):
        cat = sum(batched["input_ids"], [])
        total = (len(cat) // block) * block
        return {"input_ids": [cat[i:i + block] for i in range(0, total, block)],
                "labels": [cat[i:i + block] for i in range(0, total, block)]}

    ds = ds.map(group, batched=True)
    collator = DataCollatorForLanguageModeling(tok, mlm=True, mlm_probability=0.15)
    trainer = Trainer(model=model,
                      args=TrainingArguments(output_dir=args.output, num_train_epochs=args.epochs,
                                             per_device_train_batch_size=args.batch_size,
                                             learning_rate=5e-5, save_strategy="no",
                                             logging_steps=10, report_to=[]),
                      train_dataset=ds, data_collator=collator)
    trainer.train()
    trainer.save_model(args.output)
    tok.save_pretrained(args.output)
    print(f"\nDomain-adapted model saved to: {args.output}")
    print("PHASE 4 — now fine-tune the sentiment classifier on it:")
    print(f"  python training/train_sentiment.py --base-model {args.output}")


if __name__ == "__main__":
    main()
# Dataset folders

- `raw/` — uploaded answer sheets (PDF/images) as received.
- `processed/` — OCR output and segmented Q/A JSON.
- `unlabeled/` — unlabeled student answers for self-supervised pretraining (JSONL/TXT).
- `sentiment/` — labeled sentiment data (`text,label` CSV or JSONL).
- `grading/` — graded answers (`question_id,question,answer,max_marks,score`).
- `rubrics/` — question-specific rubric JSON files.

Legal sources for research datasets (do NOT commit copyrighted data):
ASAP / ASAP-SAS (Kaggle, The Hewlett Foundation), SciEntsBank & SemEval-2013 Task 3
(student response assessment), Hewlett HP:SAS, and EngSAF where licensing permits.
Place downloaded files here and point the training scripts at them.

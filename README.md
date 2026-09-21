# Broad-Question-Evaluation
EduGrade AI — Intelligent Answer Sheet Evaluation & Student Response Analysis
An AI-assisted system that ingests a complete student answer sheet (PDF/image),extracts questions and answers via OCR, evaluates each answer against aquestion-specific rubric using transformer-based semantic matching, predictsmarks with a fully explainable hybrid scoring engine, and runs a completelyseparate sentiment/emotion analysis.

⚠️ AI-generated evaluation is an assistive assessment tool and must be reviewedby a teacher before official grading. It is not perfectly accurate.

Architecture
Answer sheet (PDF/image) ─▶ Upload API ─▶ Document parsing ─▶ OCR (Tesseract/EasyOCR/text-layer)        ─▶ Q/A segmentation ─▶ Question understanding ─▶ Rubric resolution (library/teacher/auto-suggest)        ─▶ Semantic matching (sentence-transformers) ─▶ Concept coverage ─▶ Grading engine (Mode A + B)        ─▶ Sentiment service (separate) ─▶ Report generator ─▶ SQLite ─▶ React dashboard
Every component is replaceable: OCR engines, embedding models, sentiment models,database (SQLite → PostgreSQL via DATABASE_URL), and scoring weights.

Installation
# 1. System OCR (for scanned/handwritten sheets)sudo apt install tesseract-ocr        # Debian/Ubuntu# choco install tesseract              # Windows  (set TESSERACT_CMD in .env if needed)# 2. Backendpython -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activatepip install -r requirements.txtcp .env.example .env                   # optional: tweak models & weights# 3. Frontendcd frontend && npm install && cd ..
Running
# Terminal 1 — backend (from the backend/ directory)cd backend && uvicorn app.main:app --reload# API docs: http://localhost:8000/docs# Terminal 2 — frontendcd frontend && npm run dev# UI: http://localhost:5173
On first start the backend seeds data/ with demo rubrics, demo answers,sentiment samples, and an unlabeled corpus.

Uploading a PDF
Open Upload & Evaluate, drag a PDF/JPG/PNG (or click to browse).
The backend parses the document (uses the PDF text layer when available;otherwise rasterizes pages at 200 dpi and runs OCR).
Questions are auto-detected (1., 1), Q1, Question 1, multi-linequestions, Ans:/Answer: markers, multi-page answers).
Watch the 8-step live progress, then land on Evaluation Results.
No PDF handy? Run the built-in demo or paste text directly.
How grading works
For each answer and each rubric concept:

confidence = 0.70·semantic + 0.20·keyword + 0.10·contextual      (.env-configurable)award      = clip((confidence − 0.30) / (0.80 − 0.30), 0, 1)     (continuous, not binary)marks      = weight × award
Mode A (rubric-based): per-concept matching → rubric_score
Mode B (reference-based): cosine similarity to the reference answer,calibrated to marks → reference_score
FINAL_MODE selects the final score: rubric | reference | blend
Detected flags: off-topic, irrelevant content, incomplete, very short,excessive repetition, possible contradiction (negation near concept evidence).
Quality indicators (coverage, relevance, completeness, coherence, conciseness,confidence) are reported separately — never silently merged into marks.
Every score ships with evidence highlights, per-component numbers, and text feedback.
How sentiment works
A separate pipeline (sentiment_service.py) classifies each answer aspositive/neutral/negative with probabilities plus uncertainty / frustration /engagement indicators. It never modifies marks. Backend is a transformersmodel by default (SENTIMENT_MODEL), with an offline lexicon fallback.

Self-supervised training (optional)
The prototype runs without any training. When you have unlabeled data:

# Phase 1+2+3 — collect (data/unlabeled/), clean, domain-adaptive MLM pretrainingpython training/train_self_supervised.py --model bert-base-uncased --epochs 2# Phase 4 — fine-tune the sentiment classifier on the domain-adapted modelpython training/train_sentiment.py --base-model models/domain_adapted# Then set in .env:  SENTIMENT_MODEL=models/sentiment_finetuned
Or trigger from the UI: Dataset & Model → Train.

Adding new questions / rubrics
UI: Rubric Editor → enter question, max marks, reference answer →"Suggest key concepts" → edit/approve → Save.
Files: drop a JSON into data/rubrics/:
{  "id": "explain-photosynthesis",  "question": "Explain photosynthesis.",  "max_marks": 5,  "reference_answer": "Photosynthesis is the process by which…",  "concepts": [    {"concept": "Process converting light energy into chemical energy", "weight": 1},    {"concept": "Produces glucose and releases oxygen", "weight": 1}  ]}
Per-request: pass rubrics: [{question, max_marks, reference_answer, concepts}]to POST /api/evaluate (teacher overrides take top priority).
If no rubric exists, the system grades for relevance only and flags it clearly.
Replacing models (all via .env)
Component	Variable	Examples
Embeddings	EMBEDDING_MODEL	all-MiniLM-L6-v2, all-mpnet-base-v2, DeBERTa…
Embeddings	EMBEDDING_BACKEND	sentence-transformers | hashing (offline)
Sentiment	SENTIMENT_MODEL	cardiffnlp/..., j-hartmann/emotion-english-distilroberta-base
Sentiment	SENTIMENT_BACKEND	transformers | lexicon (offline)
OCR	OCR_ENGINE	auto | tesseract | easyocr
Database	DATABASE_URL	SQLite (default) or PostgreSQL
Evaluating model performance
python evaluation/evaluate_grading.py     # MAE, RMSE, Pearson, Spearman for                                          # keyword vs TF-IDF vs embedding vs hybridpython evaluation/evaluate_sentiment.py   # accuracy, per-class P/R/F1, confusion matrixpytest                                    # unit + end-to-end tests (offline backends)
Plug in research datasets (ASAP-SAS, SciEntsBank, SemEval, HP:SAS, EngSAF —obey their licenses; never commit copyrighted data) into data/grading/ anddata/sentiment/ using the documented CSV schemas.

API
POST /api/upload · POST /api/evaluate · GET /api/evaluate/status/{job} ·GET /api/evaluation/{id} · GET /api/evaluations · GET /api/stats ·GET /api/report/{id}?format=json|csv|pdf · POST /api/rubric ·GET /api/rubrics · GET /api/rubric/{id} · POST /api/rubric/suggest ·POST /api/sentiment · POST /api/demo/evaluate · POST /api/train ·GET /api/train/status/{id} · GET /api/health

Example:

curl -X POST http://localhost:8000/api/evaluate -H "Content-Type: application/json" \  -d '{"raw_text": "1. Explain photosynthesis.\nPhotosynthesis is how plants make glucose from sunlight, water and CO2, releasing oxygen.", "exam_name": "Unit test"}'# -> {"job_id": "abc123", "status": "started"}curl http://localhost:8000/api/evaluate/status/abc123
Limitations
Handwriting OCR accuracy depends on scan quality; cursive handwriting is hard.
Sentence-level question/answer heuristics can mis-segment unusual layouts.
Auto-suggested rubrics are drafts and must be teacher-approved.
Factual-consistency checks are heuristic (negation-based), not fact-checking.
Small labeled datasets limit sentiment fine-tuning quality.
Future-ready extension points
Handwriting-recognition models (behind ocr_service), multilingual answers(multilingual embedding models + language detection), diagram/math evaluation(new grading engine methods), plagiarism detection, factuality checking,adaptive rubric generation, question difficulty estimation, and studentanalytics — each plugs into an existing interface without rewrites.

How Everything Works — Quick Guide
Install: pip install -r requirements.txt (+ Tesseract binary for scanned sheets), cd frontend && npm install.
Run: cd backend && uvicorn app.main:app --reload and cd frontend && npm run dev.
Upload a PDF: Upload & Evaluate → drag-and-drop → the 8 processing steps stream live → auto-redirect to results. Test instantly with Run demo or python scripts/make_demo_pdf.py for a ready sheet.
Grading: hybrid per-concept confidence (0.70 semantic + 0.20 keyword + 0.10 contextual, configurable) mapped to continuous marks; Mode A (rubric) and Mode B (reference similarity) are both shown, plus issues, quality indicators, and evidence highlights with char-offset spans.
Sentiment: an isolated service producing probabilities + uncertainty/frustration/engagement, displayed with an explicit "does not influence marks" disclaimer everywhere (UI, API, report).
Self-supervised training: real 4-phase design — collect (data/unlabeled/), clean, MLM domain-adaptive pretraining (training/train_self_supervised.py), fine-tune (training/train_sentiment.py); optional, since the app runs on pretrained models out of the box.
New questions/rubrics: Rubric Editor with approve/edit workflow, JSON files in data/rubrics/, or per-request overrides — no code changes.
Model replacement: everything (embedder, sentiment model, OCR engine, DB, scoring weights, grading mode) is .env-configurable with documented offline fallbacks.
Evaluation: evaluation/ scripts produce MAE/RMSE/Pearson/Spearman across keyword/TF-IDF/embedding/hybrid and full sentiment metrics — publication-ready baselines; pytest covers unit + end-to-end.



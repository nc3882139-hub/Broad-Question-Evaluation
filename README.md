# EduGrade AI

**Explainable answer-sheet evaluation and student response analysis.**

EduGrade AI turns a PDF, image, or pasted answer sheet into structured question-level results. It combines OCR and text parsing, rubric-aware semantic grading, evidence highlights, separate sentiment analysis, and downloadable reports in a FastAPI + React application.

> **Important:** AI-generated evaluation is assistive. A teacher must review results before official grading.

## 60-Second Demo

```bash
cd edugrade-ai
pip install -r requirements.txt
(cd frontend && npm install)
./start-dev.sh
```

Open **http://localhost:5173** and select **Run demo evaluation**. The API documentation is available at **http://localhost:8000/docs**.

The launch script defaults to deterministic offline backends:

- Embeddings: `hashing`
- Sentiment: `lexicon`

This lets the seeded demo run without downloading model files.

## What It Does

- Accepts PDF, JPG, JPEG, PNG, BMP, and TIFF answer sheets.
- Uses a PDF text layer when available, with OCR fallback for scanned pages.
- Detects numbered questions, multi-line questions, answer markers, and multi-page answers.
- Resolves rubrics from teacher overrides, the rubric library, or an explicitly flagged draft.
- Calculates explainable concept-level marks with evidence spans.
- Shows rubric-based Mode A and reference-answer Mode B scores side by side.
- Runs sentiment analysis separately so it never changes academic marks.
- Persists evaluations in SQLite and exports JSON, CSV, PDF, or HTML reports.

## Architecture

```text
PDF/image/text
    -> upload and document parsing
    -> OCR or PDF text extraction
    -> question/answer segmentation
    -> rubric resolution
    -> hybrid concept grading
    -> separate sentiment analysis
    -> report generation
    -> SQLite persistence
    -> React dashboard
```

### Backend

- `backend/app/api/` - upload, evaluation, reports, rubrics, and training routes
- `backend/app/services/` - OCR, parsing, segmentation, grading, sentiment, reports, jobs
- `backend/app/models/` - SQLAlchemy database models and request schemas
- `backend/app/config.py` - environment-driven settings and storage paths

### Frontend

- React 18 with Vite and Tailwind CSS
- Dashboard, upload/evaluation, results, rubric editor, sentiment, reports, dataset/model, and settings views
- Vite proxies `/api` requests to the backend

## Installation

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- Optional system OCR binary for scanned documents:

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# Windows
choco install tesseract
```

### Backend and frontend

```bash
cd edugrade-ai
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp env.example .env              # optional
cd frontend && npm install && cd ..
```

### Start manually

```bash
# Terminal 1
cd backend
EMBEDDING_BACKEND=hashing SENTIMENT_BACKEND=lexicon uvicorn app.main:app --reload

# Terminal 2
cd frontend
npm run dev
```

On Windows, use `start-dev.bat`. On macOS/Linux, use `start-dev.sh`.

On first start, the backend creates required data directories and seeds demo rubrics and datasets automatically.

## Grading Model

For every rubric concept, the default hybrid confidence is:

```text
confidence = 0.70 * semantic + 0.20 * keyword + 0.10 * contextual
```

Continuous marks are calculated as:

```text
award = clip((confidence - 0.30) / (0.80 - 0.30), 0, 1)
marks = concept_weight * award
```

The weights and thresholds are configurable, but the formula remains explicit and explainable.

### Grading modes

- **Mode A: Rubric based** - concept coverage and semantic evidence against approved key points.
- **Mode B: Reference based** - calibrated similarity to the reference answer.
- **Blend** - combines Mode A and Mode B using `BLEND_RUBRIC_WEIGHT`.

Each question also includes confidence, quality indicators, evidence highlights, feedback, and issue flags such as incomplete, off-topic, repetitive, or possibly contradictory content.

## Sentiment Analysis

Sentiment is an informational pipeline independent of grading. It returns exactly one of:

- `positive`
- `neutral`
- `negative`

It also reports probabilities and lightweight uncertainty, frustration, and engagement indicators. Sentiment never adds or subtracts marks.

## Configuration

Copy `env.example` to `.env` to customize the application. Important settings include:

| Area | Variables | Offline option |
| --- | --- | --- |
| Embeddings | `EMBEDDING_MODEL`, `EMBEDDING_BACKEND` | `hashing` |
| Sentiment | `SENTIMENT_MODEL`, `SENTIMENT_BACKEND` | `lexicon` |
| OCR | `OCR_ENGINE`, `TESSERACT_CMD` | PDF text layer or clear error |
| Storage | `DATABASE_URL`, `DATA_DIR`, `UPLOAD_DIR`, `MODELS_DIR` | SQLite |
| Grading | `W_SEMANTIC`, `W_KEYWORD`, `W_CONTEXT`, thresholds | Deterministic defaults |
| Final score | `FINAL_MODE`, `BLEND_RUBRIC_WEIGHT` | `rubric` |

## API Overview

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Runtime, backend, OCR, and grading configuration |
| `POST` | `/api/upload` | Upload an answer sheet |
| `POST` | `/api/evaluate` | Start an evaluation job |
| `POST` | `/api/demo/evaluate` | Start the five-answer demo |
| `GET` | `/api/evaluate/status/{job_id}` | Poll job progress |
| `GET` | `/api/evaluation/{id}` | Retrieve a completed evaluation |
| `GET` | `/api/evaluations` | List recent evaluations |
| `GET` | `/api/stats` | Dashboard aggregates |
| `GET` | `/api/report/{id}?format=json\|csv\|pdf` | Export a report |
| `GET/POST` | `/api/rubrics`, `/api/rubric` | Manage rubrics |
| `POST` | `/api/sentiment` | Analyze sentiment independently |

Example pasted-text request:

```bash
curl -X POST http://localhost:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"raw_text":"1. Explain photosynthesis.\nPhotosynthesis uses sunlight, water and carbon dioxide to produce food and oxygen.","exam_name":"Unit test"}'
```

The response contains a `job_id`. Poll the status route until the job is `done`, then use the returned `evaluation_id`.

## Rubrics and Data

Rubrics can be created in the **Rubric Editor** or stored as JSON in `data/rubrics/`:

```json
{
  "id": "explain-photosynthesis",
  "question": "Explain photosynthesis.",
  "max_marks": 5,
  "reference_answer": "Photosynthesis converts light energy into chemical energy.",
  "concepts": [
    {"concept": "Uses sunlight, water and carbon dioxide", "weight": 1},
    {"concept": "Produces glucose and releases oxygen", "weight": 1}
  ]
}
```

Demo and research data lives under `data/`:

- `data/rubrics/` - question-specific grading rubrics
- `data/grading/` - graded answer examples
- `data/sentiment/` - labeled sentiment examples
- `data/unlabeled/` - self-supervised training text
- `data/raw/` - uploaded documents
- `data/processed/` - processed output

Do not commit copyrighted research datasets. Use only data whose license permits your intended use.

## Testing and Evaluation

Run the complete test suite with offline backends:

```bash
cd edugrade-ai
PYTHONPATH=backend EMBEDDING_BACKEND=hashing SENTIMENT_BACKEND=lexicon pytest -q
```

Research evaluation scripts are available at:

```bash
python evaluation/evaluate_grading.py
python evaluation/evaluate_sentiment.py
```

Optional training scripts are in `training/`. The application does not require training to run.

## Limitations

- OCR quality depends on scan quality and installed OCR support; cursive handwriting is difficult.
- Segmentation uses document heuristics and may need review for unusual layouts.
- Auto-suggested rubrics are drafts and require teacher approval.
- Contradiction detection is a lightweight heuristic, not fact-checking.
- Transformer backends require locally available model files or network access on first load.

## Project Status

EduGrade AI is a hackathon-ready prototype focused on a reliable offline demo, explainable scoring, and clear extension points for multilingual grading, diagram/math evaluation, plagiarism detection, factuality checks, and adaptive rubrics.

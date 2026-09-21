# EduGrade AI

## 60-second demo

```bash
cd edugrade-ai
pip install -r requirements.txt && (cd frontend && npm install)
./start-dev.sh
```

Open http://localhost:5173, choose **Run demo evaluation**, and open the completed
results. The backend API is at http://localhost:8000/docs.

For an offline laptop, the launch script uses deterministic `hashing` embeddings and
`lexicon` sentiment by default. Set `EMBEDDING_BACKEND=sentence-transformers` and
`SENTIMENT_BACKEND=transformers` when the model files are already available locally.

The system accepts PDF/image uploads or pasted text, segments numbered questions,
grades against approved rubrics, analyzes sentiment separately, persists evaluations
to SQLite, and exports JSON, CSV, PDF, or HTML reports.
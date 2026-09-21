import json
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import Evaluation, get_db
from app.models.schemas import EvaluateRequest, SentimentIn
from app.services import job_manager as jm
from app.services import sentiment_service
from app.services.pipeline import run_evaluation_job
from app.services.seed_data import DEMO_RAW_TEXT

router = APIRouter(prefix="/api", tags=["evaluation"])


def _dump(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _start(params) -> dict:
    job_id = jm.create_job()
    jm.submit(lambda jid: run_evaluation_job(jid, params), job_id)
    return {"job_id": job_id, "status": "started"}


@router.post("/evaluate")
def evaluate(req: EvaluateRequest):
    if not req.file_id and not (req.raw_text or "").strip():
        raise HTTPException(400, "Provide file_id (uploaded document) or raw_text.")
    return _start(_dump(req))


@router.post("/demo/evaluate")
def demo_evaluate():
    """Runs the seeded demo sheet: five APJ Abdul Kalam answers (excellent → irrelevant)."""
    return _start({"raw_text": DEMO_RAW_TEXT, "student_name": "Demo Student",
                   "exam_name": "Demo — APJ Abdul Kalam (5 answer quality levels)"})


@router.get("/evaluate/status/{job_id}")
def evaluate_status(job_id: str):
    job = jm.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown job id")
    return job


@router.get("/evaluation/{evaluation_id}")
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    row = db.get(Evaluation, evaluation_id)
    if not row:
        raise HTTPException(404, "Evaluation not found")
    return json.loads(row.result_json)


@router.get("/evaluations")
def list_evaluations(db: Session = Depends(get_db)):
    rows = db.query(Evaluation).order_by(Evaluation.created_at.desc()).limit(50).all()
    out = []
    for r in rows:
        data = json.loads(r.result_json)
        out.append({"id": r.id, "student_name": data.get("student_name"),
                    "exam_name": data.get("exam_name"), "percentage": r.percentage,
                    "total_score": r.total_score, "max_marks": r.max_marks,
                    "questions": len(data.get("questions", [])),
                    "created_at": r.created_at.isoformat() if r.created_at else None})
    return out


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    rows = db.query(Evaluation).order_by(Evaluation.created_at.desc()).limit(100).all()
    qs = []
    for r in rows:
        qs.extend(json.loads(r.result_json).get("questions", []))

    def avg(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 3) if xs else 0.0

    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for q in qs:
        p = q.get("percentage") or 0
        key = ("0-20" if p <= 20 else "21-40" if p <= 40 else "41-60"
               if p <= 60 else "61-80" if p <= 80 else "81-100")
        buckets[key] += 1
    perf = {}
    for q in qs:
        perf.setdefault((q.get("question") or "?")[:38], []).append(q.get("percentage") or 0)
    return {
        "total_sheets": len(rows), "total_questions": len(qs),
        "average_score_pct": avg([q.get("percentage") for q in qs]),
        "average_concept_coverage": avg([q.get("quality", {}).get("concept_coverage") for q in qs]),
        "average_semantic_relevance": avg([q.get("quality", {}).get("semantic_relevance") for q in qs]),
        "average_processing_time": avg([r.processing_time for r in rows]),
        "sentiment_distribution": dict(Counter(q["sentiment"]["label"] for q in qs)),
        "score_distribution": buckets,
        "question_performance": [{"label": k, "avg_pct": round(sum(v) / len(v), 1)}
                                 for k, v in perf.items()][:12],
    }


@router.post("/sentiment")
def sentiment(req: SentimentIn):
    return sentiment_service.analyze(req.text)
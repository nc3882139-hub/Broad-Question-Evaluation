import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api", tags=["training"])
_TRAIN = {}
_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = {"self_supervised": "training/train_self_supervised.py",
           "sentiment": "training/train_sentiment.py"}


class TrainIn(BaseModel):
    task: str                                    # "self_supervised" | "sentiment"
    base_model: Optional[str] = None


@router.post("/train")
def train(payload: TrainIn):
    script = SCRIPTS.get(payload.task)
    if not script:
        raise HTTPException(400, "task must be 'self_supervised' or 'sentiment'")
    path = _ROOT / script
    if not path.exists():
        raise HTTPException(500, f"Training script missing: {path}")
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex[:10]
    log_path = settings.MODELS_DIR / f"train_{job_id}.log"
    cmd = [sys.executable, str(path)]
    if payload.base_model:
        cmd += ["--base-model", payload.base_model]
    log = open(log_path, "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(_ROOT))
    _TRAIN[job_id] = {"process": proc, "log": str(log_path), "task": payload.task}
    return {"job_id": job_id, "task": payload.task, "status": "running",
            "note": "Monitor via GET /api/train/status/{job_id}"}


@router.get("/train/status/{job_id}")
def train_status(job_id: str):
    job = _TRAIN.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown training job")
    rc = job["process"].poll()
    try:
        tail = Path(job["log"]).read_text(errors="ignore")[-1500:]
    except Exception:
        tail = ""
    return {"job_id": job_id, "task": job["task"],
            "status": "running" if rc is None else ("done" if rc == 0 else "error"),
            "returncode": rc, "log_tail": tail}
import concurrent.futures
import threading
import traceback
import uuid
from datetime import datetime
import json

from app.models.database import Job, SessionLocal

_lock = threading.Lock()
_JOBS = {}
_MAX_JOBS = 50
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="edugrade")

DEFAULT_STAGES = ["Uploading", "Reading document", "Extracting questions", "Analyzing answers",
                  "Checking key concepts", "Calculating marks", "Analyzing sentiment",
                  "Generating report"]


def _persist(job):
    """Mirror the process-local job state to the database for restart-safe polling."""
    db = SessionLocal()
    try:
        row = db.get(Job, job["job_id"]) or Job(job_id=job["job_id"])
        row.owner_id = job.get("owner_id")
        row.kind = job.get("kind", "evaluation")
        row.status = {"done": "completed", "error": "failed"}.get(job.get("status"), job.get("status", "running"))
        row.progress = job.get("progress", 0.0)
        row.current_stage = job.get("message", "")
        row.error = job.get("error")
        row.result_json = json.dumps(job.get("result") or {})
        db.add(row)
        db.commit()
    finally:
        db.close()


def create_job(kind="evaluation", stages=None, owner_id=None):
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _JOBS[job_id] = {"job_id": job_id, "kind": kind, "owner_id": owner_id, "status": "running", "stage_index": 0,
                         "stages": [{"label": s, "status": "pending"}
                                    for s in (stages or DEFAULT_STAGES)],
                         "progress": 0.0, "message": "", "error": None, "result": None,
                         "created_at": datetime.utcnow().isoformat()}
        _persist(_JOBS[job_id])
        while len(_JOBS) > _MAX_JOBS:
            del _JOBS[next(iter(_JOBS))]
    return job_id


def update(job_id, stage_index=None, progress=None, message=None, status=None, result=None):
    with _lock:
        job = _JOBS.get(job_id)
        if not job:
            return
        if stage_index is not None:
            for i, s in enumerate(job["stages"]):
                s["status"] = "done" if i < stage_index else ("active" if i == stage_index else s["status"])
            job["stage_index"] = stage_index
        if progress is not None:
            job["progress"] = progress
        if message is not None:
            job["message"] = message
        if status:
            job["status"] = status
        if result:
            job["result"] = result
        if job["status"] == "done":
            for s in job["stages"]:
                s["status"] = "done"
        snapshot = dict(job)
    _persist(snapshot)


def fail(job_id, error):
    update(job_id, status="error", message=str(error))
    with _lock:
        job = _JOBS.get(job_id)
        snapshot = None
        if job and job["stages"]:
            job["stages"][min(job["stage_index"], len(job["stages"]) - 1)]["status"] = "error"
        if job:
            job["error"] = str(error)
            snapshot = dict(job)
    if snapshot:
        _persist(snapshot)


def get(job_id, owner_id=None, is_admin=False):
    with _lock:
        job = _JOBS.get(job_id)
        if job:
            if owner_id is not None and not is_admin and job.get("owner_id") != owner_id:
                return None
            return dict(job)
    db = SessionLocal()
    try:
        row = db.get(Job, job_id)
        if not row or (owner_id is not None and not is_admin and row.owner_id != owner_id):
            return None
        api_status = {"completed": "done", "failed": "error"}.get(row.status, row.status)
        return {"job_id": row.job_id, "kind": row.kind, "owner_id": row.owner_id,
                "status": api_status, "progress": row.progress, "message": row.current_stage,
                "error": row.error, "result": json.loads(row.result_json or "{}"),
                "created_at": row.created_at.isoformat() if row.created_at else None}
    finally:
        db.close()


def submit(fn, job_id):
    def _wrap():
        try:
            fn(job_id)
            with _lock:
                job = _JOBS.get(job_id)
                should_complete = bool(job and job["status"] == "running")
            if should_complete:
                update(job_id, status="done", progress=1.0)
        except Exception as e:
            fail(job_id, str(e))
            _JOBS[job_id]["traceback"] = traceback.format_exc()[-1500:]
    _executor.submit(_wrap)
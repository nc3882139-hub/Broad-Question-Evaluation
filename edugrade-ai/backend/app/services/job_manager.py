import concurrent.futures
import threading
import traceback
import uuid
from datetime import datetime

_lock = threading.Lock()
_JOBS = {}
_MAX_JOBS = 50
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="edugrade")

DEFAULT_STAGES = ["Uploading", "Reading document", "Extracting questions", "Analyzing answers",
                  "Checking key concepts", "Calculating marks", "Analyzing sentiment",
                  "Generating report"]


def create_job(kind="evaluation", stages=None):
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _JOBS[job_id] = {"job_id": job_id, "kind": kind, "status": "running", "stage_index": 0,
                         "stages": [{"label": s, "status": "pending"}
                                    for s in (stages or DEFAULT_STAGES)],
                         "progress": 0.0, "message": "", "error": None, "result": None,
                         "created_at": datetime.utcnow().isoformat()}
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


def fail(job_id, error):
    update(job_id, status="error", message=str(error))
    with _lock:
        job = _JOBS.get(job_id)
        if job and job["stages"]:
            job["stages"][min(job["stage_index"], len(job["stages"]) - 1)]["status"] = "error"
        if job:
            job["error"] = str(error)


def get(job_id):
    with _lock:
        job = _JOBS.get(job_id)
        return dict(job) if job else None


def submit(fn, job_id):
    def _wrap():
        try:
            fn(job_id)
            with _lock:
                job = _JOBS.get(job_id)
                if job and job["status"] == "running":
                    job["status"], job["progress"] = "done", 1.0
        except Exception as e:
            fail(job_id, str(e))
            _JOBS[job_id]["traceback"] = traceback.format_exc()[-1500:]
    _executor.submit(_wrap)
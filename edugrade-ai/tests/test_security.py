import time

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.pipeline import resolve_rubric


def test_auth_enabled_requires_identity(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    with TestClient(app) as client:
        assert client.get("/api/evaluations").status_code == 401
        assert client.post("/api/train", json={"task": "sentiment"}).status_code == 401


def test_training_is_admin_only(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    with TestClient(app) as client:
        headers = {"X-User-ID": "teacher-1", "X-Role": "teacher"}
        assert client.post("/api/train", json={"task": "sentiment"}, headers=headers).status_code == 403


def test_unknown_question_is_not_an_approved_rubric():
    rubric, source = resolve_rubric("A question absent from the library", [])
    assert source == "no_rubric"
    assert rubric["approval_status"] == "draft"


def test_job_status_is_owner_scoped(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    with TestClient(app) as client:
        owner = {"X-User-ID": "teacher-1", "X-Role": "teacher"}
        other = {"X-User-ID": "teacher-2", "X-Role": "teacher"}
        job_id = client.post("/api/demo/evaluate", headers=owner).json()["job_id"]
        assert client.get(f"/api/evaluate/status/{job_id}", headers=other).status_code == 404
        for _ in range(100):
            response = client.get(f"/api/evaluate/status/{job_id}", headers=owner).json()
            if response["status"] in ("done", "error"):
                break
            time.sleep(0.02)


def test_review_requires_reason_and_lock_is_final(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    with TestClient(app) as client:
        job_id = client.post("/api/demo/evaluate").json()["job_id"]
        evaluation_id = None
        for _ in range(150):
            status = client.get(f"/api/evaluate/status/{job_id}").json()
            if status["status"] == "done":
                evaluation_id = status["result"]["evaluation_id"]
                break
            time.sleep(0.02)
        assert evaluation_id
        assert client.patch(f"/api/evaluation/{evaluation_id}/review",
                            json={"teacher_score": 1}).status_code == 422
        reviewed = client.patch(
            f"/api/evaluation/{evaluation_id}/review",
            json={"teacher_score": 20, "reason": "Teacher verified the evidence", "lock": True},
        )
        assert reviewed.status_code == 200
        assert reviewed.json()["locked"] is True
        assert client.patch(f"/api/evaluation/{evaluation_id}/review",
                            json={"teacher_score": 19, "reason": "Correction"}).status_code == 409
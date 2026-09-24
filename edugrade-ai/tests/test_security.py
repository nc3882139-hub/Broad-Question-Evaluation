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
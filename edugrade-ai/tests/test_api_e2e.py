import time

from fastapi.testclient import TestClient

from app.main import app


def test_full_pipeline_e2e():
    with TestClient(app) as client:
        health = client.get("/api/health").json()
        assert health["status"] == "ok"

        job = client.post("/api/demo/evaluate").json()["job_id"]
        evaluation_id = None
        for _ in range(300):
            s = client.get(f"/api/evaluate/status/{job}").json()
            if s["status"] == "done":
                evaluation_id = s["result"]["evaluation_id"]
                break
            if s["status"] == "error":
                raise AssertionError(f"Pipeline error: {s.get('error')}")
            time.sleep(0.2)
        assert evaluation_id

        ev = client.get(f"/api/evaluation/{evaluation_id}").json()
        assert len(ev["questions"]) == 5
        scores = [q["final_score"] for q in ev["questions"]]
        assert scores[0] >= scores[1] >= scores[2] >= scores[3] >= scores[4]
        assert ev["summary"]["max_marks"] == 25
        for q in ev["questions"]:
            assert q["sentiment"]["label"] in ("positive", "neutral", "negative")
            assert q["feedback"]

        csv_text = client.get(f"/api/report/{evaluation_id}?format=csv").text
        assert "question_id" in csv_text and "TOTAL" in csv_text

        sent = client.post("/api/sentiment", json={"text": "I enjoyed this lesson very much"}).json()
        assert sent["label"] == "positive"

        rubrics = client.get("/api/rubrics").json()
        assert any("Kalam" in r["question"] for r in rubrics)
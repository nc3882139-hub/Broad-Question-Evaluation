import json
from pathlib import Path

from app.services.grading_engine import grade_answer
from app.services.rubric_service import load_rubric_library

RUBRIC = next(r for r in load_rubric_library() if "Kalam" in r["question"])


def test_scores_order_and_structure():
    answers = json.loads((Path(__file__).parents[1] / "data" / "grading" / "demo_answers.json").read_text())
    scores = {}
    for a in answers:
        g = grade_answer(RUBRIC["question"], a["answer"], RUBRIC)
        assert 0 <= g["final_score"] <= g["max_marks"]
        for key in ("score", "percentage", "concept_results", "highlights", "quality",
                    "issues", "feedback", "mode_a", "mode_b", "confidence"):
            assert key in g
        assert abs(sum(c["marks"] for c in g["concept_results"]) - g["rubric_score"]) < 0.05
        scores[a["label"]] = g["final_score"]
    order = ["excellent", "good", "average", "incomplete", "irrelevant"]
    for hi, lo in zip(order, order[1:]):
        assert scores[hi] >= scores[lo], (hi, lo, scores)


def test_empty_answer():
    g = grade_answer(RUBRIC["question"], "", RUBRIC)
    assert g["final_score"] == 0
    assert any(i["type"] == "empty" for i in g["issues"])


def test_irrelevant_flagged():
    g = grade_answer(RUBRIC["question"],
                     "Cricket is a popular sport played in many countries.", RUBRIC)
    assert any(i["type"] in ("off_topic", "irrelevant_content") for i in g["issues"])
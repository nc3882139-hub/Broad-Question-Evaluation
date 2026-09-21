from app.services.sentiment_service import DISCLAIMER, analyze


def test_positive():
    r = analyze("I really enjoyed this lesson, it was amazing")
    assert r["label"] == "positive"


def test_negative():
    r = analyze("This is too difficult and confusing, I am stuck")
    assert r["label"] == "negative"


def test_probabilities_and_disclaimer():
    r = analyze("The topic was about photosynthesis")
    assert 0.98 <= sum(r["probabilities"].values()) <= 1.02
    assert r["disclaimer"] == DISCLAIMER
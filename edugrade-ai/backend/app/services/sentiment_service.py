import logging

from app.config import settings
from app.utils.text_utils import tokens

DISCLAIMER = "Sentiment is informational only and does not affect academic marks."
logger = logging.getLogger(__name__)

POSITIVE = {"clear", "correct", "good", "great", "excellent", "confident", "strong", "success",
            "enjoyed", "amazing", "love", "loved", "fun", "exciting", "helpful", "interesting"}
NEGATIVE = {"confused", "wrong", "bad", "poor", "unclear", "fail", "failed", "cannot", "never",
            "difficult", "confusing", "stuck", "hard", "stressful", "worried", "unable"}


def analyze(text: str) -> dict[str, float | str]:
    if settings.SENTIMENT_BACKEND == "transformers":
        try:
            return _transformer_analyze(text)
        except Exception as exc:
            logger.warning("Sentiment model unavailable; using lexicon fallback: %s", exc)
    words = tokens(text)
    positive, negative = len(words & POSITIVE), len(words & NEGATIVE)
    total = positive + negative
    score = (positive - negative) / total if total else 0.0
    label = "positive" if score > 0.15 else "negative" if score < -0.15 else "neutral"
    probabilities = {"positive": 0.0, "neutral": 1.0, "negative": 0.0}
    if label == "positive":
        probabilities = {"positive": 0.7, "neutral": 0.2, "negative": 0.1}
    elif label == "negative":
        probabilities = {"positive": 0.1, "neutral": 0.2, "negative": 0.7}
    return {"label": label, "score": round(score, 3), "positive": positive,
            "negative": negative, "probabilities": probabilities,
            "confidence": max(probabilities.values()), "backend": "lexicon",
            "indicators": {"uncertainty": 0.0, "frustration": round(negative / max(total, 1), 3),
                           "engagement": min(1.0, len(words) / 40)},
            "disclaimer": DISCLAIMER}


def _transformer_analyze(text):
    from transformers import pipeline
    classifier = getattr(analyze, "_classifier", None)
    if classifier is None:
        classifier = pipeline("sentiment-analysis", model=settings.SENTIMENT_MODEL)
        analyze._classifier = classifier
    raw = classifier(text or "")[0]
    label_map = {"label_0": "negative", "label_1": "neutral", "label_2": "positive"}
    label = label_map.get(str(raw.get("label", "")).lower(), str(raw.get("label", "neutral")).lower())
    if label not in {"positive", "neutral", "negative"}:
        label = "neutral"
    confidence = float(raw.get("score", 0.0))
    probabilities = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    probabilities[label] = confidence
    probabilities["neutral"] += max(0.0, 1.0 - confidence) if label != "neutral" else 0.0
    return {"label": label, "score": round(confidence if label == "positive" else -confidence if label == "negative" else 0.0, 3),
            "probabilities": probabilities, "confidence": confidence, "backend": "transformers",
            "indicators": {"uncertainty": 0.0, "frustration": 0.0, "engagement": 0.0},
            "disclaimer": DISCLAIMER}

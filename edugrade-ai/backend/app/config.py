import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent   # repo root
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "backend" / ".env")


def _f(key, default):
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return float(default)


class Settings:
    APP_NAME = "EduGrade AI"
    VERSION = "1.0.0"

    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'edugrade.db'}")
    DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "data" / "raw" / "uploads"))
    RUBRIC_DIR = DATA_DIR / "rubrics"
    MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "sentence-transformers")  # | hashing
    SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest")
    SENTIMENT_BACKEND = os.getenv("SENTIMENT_BACKEND", "transformers")           # | lexicon
    OCR_ENGINE = os.getenv("OCR_ENGINE", "auto")                                 # auto|tesseract|easyocr
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")

    # Hybrid concept scoring weights
    W_SEMANTIC = _f("W_SEMANTIC", 0.70)
    W_KEYWORD = _f("W_KEYWORD", 0.20)
    W_CONTEXT = _f("W_CONTEXT", 0.10)
    MATCH_THRESHOLD = _f("MATCH_THRESHOLD", 0.65)
    PARTIAL_THRESHOLD = _f("PARTIAL_THRESHOLD", 0.45)
    AWARD_MIN_CONF = _f("AWARD_MIN_CONF", 0.30)
    AWARD_MAX_CONF = _f("AWARD_MAX_CONF", 0.80)

    # Grading mode: rubric (A) | reference (B) | blend
    FINAL_MODE = os.getenv("FINAL_MODE", "rubric")
    BLEND_RUBRIC_WEIGHT = _f("BLEND_RUBRIC_WEIGHT", 0.6)
    REF_SIM_FLOOR = _f("REF_SIM_FLOOR", 0.35)
    REF_SIM_CEIL = _f("REF_SIM_CEIL", 0.85)


settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.RUBRIC_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
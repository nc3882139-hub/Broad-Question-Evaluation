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
    AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    AUTH_ROLES = {"teacher", "admin", "student"}
    MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "100"))
    MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "12000"))
    MAX_RAW_TEXT_LENGTH = int(os.getenv("MAX_RAW_TEXT_LENGTH", "200000"))
    MAX_NAME_LENGTH = int(os.getenv("MAX_NAME_LENGTH", "200"))

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


def validate_grading_settings():
    weights = (settings.W_SEMANTIC, settings.W_KEYWORD, settings.W_CONTEXT)
    if any(w < 0 for w in weights) or not abs(sum(weights) - 1.0) < 1e-6:
        raise ValueError("W_SEMANTIC, W_KEYWORD and W_CONTEXT must be non-negative and sum to 1")
    if not 0 <= settings.BLEND_RUBRIC_WEIGHT <= 1:
        raise ValueError("BLEND_RUBRIC_WEIGHT must be between 0 and 1")
    if not 0 <= settings.PARTIAL_THRESHOLD <= settings.MATCH_THRESHOLD <= 1:
        raise ValueError("grading thresholds must satisfy 0 <= partial <= match <= 1")
    if not 0 <= settings.AWARD_MIN_CONF < settings.AWARD_MAX_CONF <= 1:
        raise ValueError("award thresholds must satisfy 0 <= min < max <= 1")
    if not 0 <= settings.REF_SIM_FLOOR < settings.REF_SIM_CEIL <= 1:
        raise ValueError("reference similarity thresholds must satisfy 0 <= floor < ceil <= 1")


validate_grading_settings()
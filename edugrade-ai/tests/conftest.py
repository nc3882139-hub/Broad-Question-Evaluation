import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

# Offline, deterministic backends for CI — real models are used by default in the app.
os.environ.setdefault("EMBEDDING_BACKEND", "hashing")
os.environ.setdefault("SENTIMENT_BACKEND", "lexicon")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'test_edugrade.db'}")

from app.services.seed_data import seed_all  # noqa: E402
seed_all()
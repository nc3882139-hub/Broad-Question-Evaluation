"""Pluggable embedding backend.

EMBEDDING_BACKEND=sentence-transformers  -> real transformer embeddings (default)
EMBEDDING_BACKEND=hashing                -> deterministic feature-hashing fallback used
                                            by tests/CI and fully-offline runs.
Models are loaded ONCE and cached (thread-safe) — never reloaded per request.
"""
import hashlib
import logging
import math
import re
import threading
from collections import Counter

import numpy as np

from app.config import settings
from app.utils.text_utils import content_tokens

_lock = threading.Lock()
_cache = {}
logger = logging.getLogger(__name__)


def get_embedder():
    key = (settings.EMBEDDING_BACKEND, settings.EMBEDDING_MODEL)
    with _lock:
        if key not in _cache:
            if settings.EMBEDDING_BACKEND == "sentence-transformers":
                try:
                    _cache[key] = _SentenceTransformerBackend(settings.EMBEDDING_MODEL)
                except Exception as exc:
                    logger.warning("Embedding model unavailable; using hashing fallback: %s", exc)
                    _cache[key] = _HashingBackend()
            else:
                _cache[key] = _HashingBackend()
        return _cache[key]


class _SentenceTransformerBackend:
    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return np.asarray(
            self.model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32,
        )


class _HashingBackend:
    DIM = 512

    def encode(self, texts):
        out = np.zeros((len(texts), self.DIM), dtype=np.float32)
        for i, text in enumerate(texts):
            toks = content_tokens(text)
            for tok, c in Counter(toks).items():
                w = 1.0 + math.log(c)
                h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
                out[i, h % self.DIM] += w if (h >> 16) & 1 else -w
                for j in range(max(0, len(tok) - 2)):
                    h2 = int(hashlib.md5(("##" + tok[j:j + 3]).encode()).hexdigest(), 16)
                    out[i, h2 % self.DIM] += 0.3 * (1 if (h2 >> 16) & 1 else -1)
            n = np.linalg.norm(out[i])
            if n:
                out[i] /= n
        return out


def embed(texts):
    texts = [t if (t and str(t).strip()) else " " for t in texts]
    return get_embedder().encode(texts)


def embed_one(text):
    return embed([text])[0]


def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0


def similarity(a, b):
    return cosine(embed_one(a), embed_one(b))


def content_recall(query, text):
    expected = set(content_tokens(query))
    actual = set(content_tokens(text))
    return len(expected & actual) / len(expected) if expected else 0.0


def tfidf_similarity_set(query, docs):
    """Pure-python TF-IDF cosine(query, doc_i) — baseline method for research comparison."""
    tok = content_tokens
    d_tokens = [tok(d) for d in docs]
    N = len(docs)
    df = Counter()
    for ts in d_tokens:
        df.update(set(ts))

    def vec(tokens):
        c = Counter(tokens)
        return {t: (1 + math.log(f)) * (1 + math.log(N / (df[t] or 1))) for t, f in c.items()}

    qv = vec(tok(query))
    out = []
    for ts in d_tokens:
        dv = vec(ts)
        dot = sum(w * dv.get(t, 0.0) for t, w in qv.items())
        nq = math.sqrt(sum(w * w for w in qv.values()))
        nd = math.sqrt(sum(w * w for w in dv.values()))
        out.append(dot / (nq * nd) if nq and nd else 0.0)
    return out


from app.utils.text_utils import content_tokens  # noqa: E402  (used by tfidf helper)
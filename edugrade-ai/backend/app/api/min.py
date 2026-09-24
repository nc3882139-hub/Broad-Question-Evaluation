from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import evaluation, reports, rubrics, training, upload
from app.config import settings
from app.models.database import init_db
from app.security import current_user
from app.services import ocr_service
from app.services.report_service import INTEGRITY_NOTICE
from app.services.seed_data import seed_all


@asynccontextmanager
async def lifespan(_):
    init_db()
    seed_all()   # materializes demo rubrics + datasets on first run
    yield


app = FastAPI(title=settings.APP_NAME,
              description="Intelligent Answer Sheet Evaluation & Student Response Analysis",
              version=settings.VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for r in (upload.router, evaluation.router, reports.router, rubrics.router, training.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION,
            "auth": {"enabled": settings.AUTH_ENABLED, "development_bypass": not settings.AUTH_ENABLED},
            "models": {"embedding_backend": settings.EMBEDDING_BACKEND,
                       "embedding_model": settings.EMBEDDING_MODEL,
                       "sentiment_backend": settings.SENTIMENT_BACKEND,
                       "sentiment_model": settings.SENTIMENT_MODEL,
                       "ocr_engine": ocr_service.ocr_status()},
            "grading": {"final_mode": settings.FINAL_MODE,
                        "weights": {"semantic": settings.W_SEMANTIC,
                                    "keyword": settings.W_KEYWORD,
                                    "contextual": settings.W_CONTEXT},
                        "match_threshold": settings.MATCH_THRESHOLD,
                        "partial_threshold": settings.PARTIAL_THRESHOLD},
            "notice": INTEGRITY_NOTICE}
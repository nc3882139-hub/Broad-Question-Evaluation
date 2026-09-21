import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import settings
from app.models.database import AnswerSheet, get_db

router = APIRouter(prefix="/api", tags=["upload"])
ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def _page_count(path: Path) -> int:
    if path.suffix.lower() == ".pdf":
        import fitz
        with fitz.open(path) as doc:
            return doc.page_count
    return 1


@router.post("/upload")
async def upload_answer_sheet(file: UploadFile = File(...), db=Depends(get_db)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: PDF, JPG, JPEG, PNG.")
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 25 MB).")
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "answer_sheet")
    path = settings.UPLOAD_DIR / f"{uuid.uuid4().hex[:10]}_{safe}"
    path.write_bytes(data)
    try:
        pages = _page_count(path)
    except Exception as e:
        path.unlink(missing_ok=True)
        raise HTTPException(400, f"Could not read document: {e}")
    sheet = AnswerSheet(filename=file.filename, file_path=str(path), pages=pages, status="uploaded")
    db.add(sheet)
    db.commit()
    db.refresh(sheet)
    return {"file_id": str(sheet.id), "filename": file.filename, "pages": pages,
            "status": "uploaded", "ocr_status": "pending"}
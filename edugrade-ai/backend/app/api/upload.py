import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image

from app.config import settings
from app.models.database import AnswerSheet, get_db
from app.security import current_user

router = APIRouter(prefix="/api", tags=["upload"])
ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def _page_count(path: Path) -> int:
    if path.suffix.lower() == ".pdf":
        import fitz
        with fitz.open(path) as doc:
            if doc.page_count > settings.MAX_PDF_PAGES:
                raise ValueError(f"PDF exceeds {settings.MAX_PDF_PAGES} pages")
            return doc.page_count
    return 1


@router.post("/upload")
async def upload_answer_sheet(file: UploadFile = File(...), db=Depends(get_db), user=Depends(current_user)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: PDF, JPG, JPEG, PNG.")
    size = 0
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "answer_sheet")
    path = settings.UPLOAD_DIR / f"{uuid.uuid4().hex[:10]}_{safe}"
    try:
        with path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_BYTES:
                    raise ValueError(f"File too large (max {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB)")
                output.write(chunk)
        header = path.read_bytes()[:16]
        if ext == ".pdf" and not header.startswith(b"%PDF"):
            raise ValueError("content is not a valid PDF")
        if ext != ".pdf":
            with Image.open(path) as image:
                if image.format not in {"JPEG", "PNG", "BMP", "TIFF"}:
                    raise ValueError("content is not a supported image")
                if max(image.size) > settings.MAX_IMAGE_DIMENSION:
                    raise ValueError("image dimensions exceed the configured limit")
        pages = _page_count(path)
    except Exception as e:
        path.unlink(missing_ok=True)
        raise HTTPException(400, f"Invalid document: {e}")
    sheet = AnswerSheet(filename=file.filename, file_path=str(path), pages=pages,
                        status="uploaded", user_id=user["id"])
    db.add(sheet)
    db.commit()
    db.refresh(sheet)
    return {"file_id": str(sheet.id), "filename": file.filename, "pages": pages,
            "status": "uploaded", "ocr_status": "pending"}
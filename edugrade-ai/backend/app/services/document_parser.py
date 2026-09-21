import re
from pathlib import Path

from app.services import ocr_service

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def _clean(text):
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)      # de-hyphenate line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_file(path, filename=None):
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        pages = ocr_service.extract_text_from_pdf(path)
    elif ext in IMAGE_EXTS:
        pages = [ocr_service.extract_text_from_image(path, page_number=1)]
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    for p in pages:
        p.text = _clean(p.text)
    text_mode = bool(pages) and all(p.engine == "pymupdf-text" for p in pages)
    return {
        "pages": [{"page_number": p.page_number, "text": p.text, "blocks": p.blocks, "engine": p.engine} for p in pages],
        "engine": pages[0].engine if pages else "none",
        "text_mode": text_mode,
    }
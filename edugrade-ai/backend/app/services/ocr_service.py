"""OCR service abstraction — engines are replaceable.

Preferred pipeline: PDF/Image -> preprocess -> OCR -> text (with page + block info).
PDFs with a selectable text layer are extracted directly (PyMuPDF) and only
scanned pages are rasterized and OCR'ed.
"""
import io
from dataclasses import dataclass, field

from PIL import Image, ImageFilter, ImageOps

from app.config import settings


@dataclass
class OCRPage:
    page_number: int
    text: str
    engine: str
    confidence: float = 0.0
    blocks: list = field(default_factory=list)  # [{text, bbox, conf}]


# ---------------------------------------------------------------- preprocessing
def preprocess_image(img: Image.Image) -> Image.Image:
    g = ImageOps.grayscale(img)
    w, h = g.size
    if w < 1400:  # upscale small scans — improves handwriting OCR markedly
        scale = 1400 / max(w, 1)
        g = g.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    g = ImageOps.autocontrast(g)
    return g.filter(ImageFilter.SHARPEN)


# ---------------------------------------------------------------- engines
def _tesseract_available():
    try:
        import pytesseract
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _ocr_tesseract(img):
    import pytesseract
    data = pytesseract.image_to_data(img, config="--psm 6", output_type=pytesseract.Output.DICT)
    lines = {}
    for i in range(len(data["text"])):
        tok = (data["text"][i] or "").strip()
        if not tok:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        conf = float(data["conf"][i]) if str(data["conf"][i]) not in ("-1", "") else 0.0
        lines.setdefault(key, []).append((data["left"][i], data["top"][i], tok, conf))
    items = []
    for _, ws in lines.items():
        ws.sort()
        confs = [w[3] for w in ws if w[3] > 0]
        items.append({
            "top": min(w[1] for w in ws), "left": ws[0][0],
            "text": " ".join(w[2] for w in ws),
            "conf": sum(confs) / len(confs) if confs else 0.0,
        })
    items.sort(key=lambda d: (d["top"], d["left"]))
    text = "\n".join(d["text"] for d in items)
    conf = sum(d["conf"] for d in items) / len(items) if items else 0.0
    blocks = [{"text": d["text"], "bbox": [d["left"], d["top"]], "conf": round(d["conf"], 1)} for d in items]
    return text, conf, blocks


_easy = None


def _ocr_easyocr(img):
    global _easy
    import numpy as np
    if _easy is None:
        import easyocr
        _easy = easyocr.Reader(["en"], gpu=False)
    items = []
    for bbox, text, conf in _easy.readtext(np.array(img), detail=1):
        items.append({"top": int(bbox[0][1]), "left": int(bbox[0][0]), "text": text, "conf": float(conf) * 100})
    items.sort(key=lambda d: (d["top"], d["left"]))
    text = "\n".join(d["text"] for d in items)
    conf = sum(d["conf"] for d in items) / len(items) if items else 0.0
    blocks = [{"text": d["text"], "bbox": [d["left"], d["top"]], "conf": round(d["conf"], 1)} for d in items]
    return text, conf, blocks


def _resolve_engine():
    pref = settings.OCR_ENGINE
    if pref in ("tesseract", "easyocr"):
        return pref
    if _tesseract_available():
        return "tesseract"
    try:
        import easyocr  # noqa: F401
        return "easyocr"
    except ImportError:
        pass
    raise RuntimeError(
        "No OCR engine available. Install the Tesseract binary (e.g. `apt install tesseract-ocr` "
        "or `choco install tesseract`) plus `pip install pytesseract`, or `pip install easyocr`."
    )


def ocr_status():
    try:
        return _resolve_engine()
    except Exception as e:
        return f"unavailable: {e}"


# ---------------------------------------------------------------- public API
def extract_text_from_image(image, page_number=1, engine=None) -> OCRPage:
    engine = engine or _resolve_engine()
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    proc = preprocess_image(image)
    if engine == "tesseract":
        text, conf, blocks = _ocr_tesseract(proc)
    else:
        text, conf, blocks = _ocr_easyocr(proc)
    norm = conf / 100.0 if conf > 1.5 else conf
    return OCRPage(page_number, text, engine, round(norm, 3), blocks)


def extract_handwritten_text(image, page_number=1) -> OCRPage:
    """Handwriting support: EasyOCR is preferred when installed; Tesseract psm 6 otherwise.
    Accuracy on cursive handwriting is limited — a dedicated HWR model can be plugged in
    behind this same interface later (see README 'Future work')."""
    return extract_text_from_image(image, page_number)


def extract_text_from_pdf(path) -> list:
    import fitz  # PyMuPDF
    pages = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if len(text) < 40:  # scanned page -> rasterize + OCR
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                pages.append(extract_text_from_image(img, page_number=i + 1))
            else:
                pages.append(OCRPage(i + 1, text, "pymupdf-text", 1.0))
    return pages
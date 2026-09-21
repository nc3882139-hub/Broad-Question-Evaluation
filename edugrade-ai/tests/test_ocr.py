from PIL import Image

from app.services.ocr_service import preprocess_image


def test_preprocess_grayscale_upscale():
    out = preprocess_image(Image.new("RGB", (800, 600), "white"))
    assert out.mode == "L" and out.size[0] >= 800


def test_tesseract_optional():
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("pytesseract not installed")
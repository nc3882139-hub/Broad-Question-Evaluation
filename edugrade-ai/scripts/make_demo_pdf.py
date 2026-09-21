"""Creates a demo answer-sheet PDF so you can test Upload -> OCR/parse -> evaluate."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.seed_data import DEMO_ANSWERS, RUBRIC_SEEDS  # noqa: E402

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except ImportError:
    sys.exit("pip install reportlab")

ITEMS = [
    (RUBRIC_SEEDS[0]["question"], DEMO_ANSWERS[1]["answer"]),        # good
    (RUBRIC_SEEDS[1]["question"], RUBRIC_SEEDS[1]["reference_answer"]),  # excellent
    (RUBRIC_SEEDS[2]["question"], ("The CPU is the brain of the computer. It fetches "
        "instructions from memory, decodes them and executes them. The ALU does "
        "calculations and the control unit manages everything.")),   # average
]

out = ROOT / "data" / "raw" / "demo_answer_sheet.pdf"
c = canvas.Canvas(str(out), pagesize=A4)
w, h = A4
y = h - 25 * mm


def put(text, size=11, bold=False):
    global y
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    for line in text.split("\n"):
        c.drawString(20 * mm, y, line[:110])
        y -= 7 * mm


put("Student: Demo Student", 12, True)
put("Exam: Demo Answer Sheet", 12, True)
y -= 4 * mm
for i, (q, a) in enumerate(ITEMS, 1):
    put(f"Question {i}. {q}", 11, True)
    put(f"Answer: {a}", 10)
    y -= 6 * mm
c.save()
print(f"Created: {out}")
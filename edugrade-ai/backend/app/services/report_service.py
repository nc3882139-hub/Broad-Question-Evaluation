import csv
import html
import io
import textwrap
from datetime import datetime

from app.config import settings

INTEGRITY_NOTICE = ("AI-generated evaluation is an assistive assessment tool and should be "
                    "reviewed by a teacher before official grading.")


def build_report(evaluation: dict) -> dict:
    rep = dict(evaluation)
    rep["report"] = {"generated_at": datetime.utcnow().isoformat(), "notice": INTEGRITY_NOTICE,
                     "app": f"{settings.APP_NAME} v{settings.VERSION}"}
    return rep


def report_to_csv(report) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["question_id", "question", "score", "max_marks", "percentage",
                "concepts_covered", "concepts_missing", "semantic_relevance",
                "confidence", "sentiment", "feedback"])
    for q in report["questions"]:
        w.writerow([q["question_id"], q["question"], q["final_score"], q["max_marks"],
                    q["percentage"], q["concepts_covered"], q["concepts_missing"],
                    q["quality"]["semantic_relevance"], q["confidence"],
                    q["sentiment"]["label"], q["feedback"].replace("\n", " ")])
    w.writerow([])
    w.writerow(["TOTAL", "", report["summary"]["total_score"], report["summary"]["max_marks"],
                report["summary"]["percentage"]])
    return buf.getvalue()


def report_to_pdf(report):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError:
        return None
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 20 * mm

    def line(txt, size=10, bold=False):
        nonlocal y
        if y < 22 * mm:
            c.showPage()
            y = h - 20 * mm
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        for chunk in textwrap.wrap(str(txt), 100) or [""]:
            c.drawString(20 * mm, y, chunk)
            y -= 6 * mm

    s = report["summary"]
    line(f"{settings.APP_NAME} — Evaluation Report", 16, True)
    line(f"Student: {report['student_name']}   Exam: {report['exam_name']}", 11)
    line(f"Date: {report['created_at'][:19]}   Questions: {s['questions']}", 11)
    line(f"Total: {s['total_score']} / {s['max_marks']}  ({s['percentage']}%)   "
         f"Overall confidence: {int(round(s['overall_confidence'] * 100))}%", 11, True)
    y -= 4 * mm
    for q in report["questions"]:
        line(f"Q{q['question_id']}: {q['final_score']} / {q['max_marks']} ({q['percentage']}%)  "
             f"[coverage {q['concepts_covered']}/{len(q['concept_results'])}, "
             f"sentiment: {q['sentiment']['label']}]", 11, True)
        line(q["question"], 9)
        line(q["feedback"], 9)
        y -= 3 * mm
    line(INTEGRITY_NOTICE, 8)
    c.save()
    return buf.getvalue()


def report_to_html(report) -> str:
    rows = "".join(
        f"<tr><td>Q{q['question_id']}</td><td>{q['final_score']}/{q['max_marks']}</td>"
        f"<td>{q['percentage']}%</td><td>{q['sentiment']['label']}</td>"
        f"<td>{html.escape(str(q['feedback']))}</td></tr>"
        for q in report["questions"])
    s = report["summary"]
    return f"""<html><body style="font-family:sans-serif;max-width:820px;margin:2rem auto">
<h1>EduGrade AI — Evaluation Report</h1>
<p><b>Student:</b> {html.escape(str(report['student_name']))} &nbsp; <b>Exam:</b> {html.escape(str(report['exam_name']))}
&nbsp; <b>Date:</b> {report['created_at'][:19]}</p>
<p><b>Total:</b> {s['total_score']} / {s['max_marks']} ({s['percentage']}%) —
confidence {int(round(s['overall_confidence']*100))}%</p>
<table border="1" cellpadding="6" style="border-collapse:collapse;width:100%">
<tr><th>Q</th><th>Marks</th><th>%</th><th>Sentiment</th><th>Feedback</th></tr>{rows}</table>
<p><i>{INTEGRITY_NOTICE}</i></p></body></html>"""
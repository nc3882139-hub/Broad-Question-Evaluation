import difflib
import json
import re
import time
from datetime import datetime

from app.config import settings
from app.services import (document_parser, grading_engine, job_manager as jm,
                          qa_segmenter, report_service, rubric_service, sentiment_service)
from app.services.report_service import INTEGRITY_NOTICE


def _norm(t):
    return re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower()).strip()


def _fuzzy(a, b):
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def resolve_rubric(question, overrides):
    """Return a rubric plus provenance; missing rubrics remain review-only."""
    for o in overrides or []:
        if o.get("question") and _fuzzy(o["question"], question) >= 0.6:
            concepts = o.get("concepts")
            if not concepts and o.get("reference_answer"):
                concepts = rubric_service.suggest_concepts(
                    o["reference_answer"], o.get("max_marks", 5), question=question)["concepts"]
            if not concepts:
                concepts = [{"concept": question, "weight": o.get("max_marks", 5)}]
            return ({"max_marks": o.get("max_marks", 5),
                     "reference_answer": o.get("reference_answer", ""),
                     "concepts": concepts, "approval_status": "approved", "version": 1}, "teacher")
    r, _ = rubric_service.find_rubric(question)
    if r:
        return r, "library"
    draft = rubric_service.suggest_concepts("", 5, question=question)
    draft["approval_status"] = "draft"
    draft["version"] = 1
    return draft, "no_rubric"


def run_evaluation_job(job_id, params):
    from app.models.database import (AnswerSheet, Answer as ARow, Evaluation,
                                     Question as QRow, Report as ReportRow,
                                     SentimentResult, SessionLocal)
    t0 = time.time()
    sheet_id = None
    try:
        jm.update(job_id, stage_index=0, message="Received document")

        # ---------- Stage 1: read document (PDF/image OCR or direct text) ----------
        if params.get("file_id"):
            db = SessionLocal()
            try:
                sheet = db.get(AnswerSheet, int(params["file_id"]))
                if not sheet:
                    raise ValueError("Uploaded answer sheet not found — please upload again.")
                sheet_id = sheet.id
                jm.update(job_id, stage_index=1, message=f"Parsing {sheet.filename} (OCR if needed)")
                parsed = document_parser.parse_file(sheet.file_path, sheet.filename)
                sheet.pages, sheet.text_mode, sheet.status = len(parsed["pages"]), parsed["text_mode"], "parsed"
                db.commit()
                filename, pages_n = sheet.filename, len(parsed["pages"])
            finally:
                db.close()
        else:
            jm.update(job_id, stage_index=1, message="Reading text input")
            text = params.get("raw_text") or ""
            chunks = text.split("\f")
            parsed = {"pages": [{"page_number": i + 1, "text": c, "blocks": [], "engine": "direct-text"}
                                for i, c in enumerate(chunks)],
                      "engine": "direct-text", "text_mode": True}
            filename, pages_n = params.get("exam_name") or "text-input", len(chunks)

        # ---------- Stage 2: question/answer segmentation ----------
        jm.update(job_id, stage_index=2, message="Detecting questions and answers")
        seg = qa_segmenter.segment_qa(parsed["pages"])
        segments = seg["segments"]
        if not segments:
            raise ValueError("No questions could be detected in the document. "
                             "Ensure questions are numbered (e.g. '1.', 'Q1)', 'Question 1').")

        # ---------- Stages 3-6: grade each question + sentiment ----------
        overrides = params.get("rubrics") or []
        results, rubric_sources = [], {}
        n = len(segments)
        for i, s in enumerate(segments):
            jm.update(job_id, stage_index=3, progress=i / n, message=f"Analyzing answer {i + 1}/{n}")
            rubric, source = resolve_rubric(s["question"], overrides)
            rubric_sources[i] = source
            jm.update(job_id, stage_index=4, progress=i / n, message=f"Checking key concepts — Q{i + 1}")
            g = grading_engine.grade_answer(s["question"], s["student_answer"], rubric)
            g["max_marks"] = g["max_marks"] if g["max_marks"] else rubric.get("max_marks", 5)
            jm.update(job_id, stage_index=5, progress=(i + 1) / n, message=f"Calculating marks — Q{i + 1}")
            s.update(g)
            s["rubric_source"] = source
            s["rubric_status"] = "APPROVED_RUBRIC" if source in ("teacher", "library") else "NO_RUBRIC"
            s["rubric_provenance"] = {"rubric_id": rubric.get("id"),
                                       "rubric_version": rubric.get("version", 1),
                                       "source": source,
                                       "approval_status": rubric.get("approval_status", "approved")}
            if source == "no_rubric":
                g["ai_score"] = g["final_score"]
                g["official_score"] = None
                g["final_score"] = 0.0
                g["review_required"] = True
                s["issues"] = s["issues"] + [{"type": "no_rubric",
                    "message": "Teacher review required: no approved rubric exists, so the AI score is not an official grade."}]
            else:
                g["ai_score"] = g["final_score"]
                g["official_score"] = g["final_score"]
                g["review_required"] = bool(s.get("question_confidence", 1) < 0.6)
            s["sentiment"] = sentiment_service.analyze(s["student_answer"])
            results.append(s)

        # ---------- Stage 7: aggregate ----------
        sentiment_distribution = {}
        for q in results:
            sentiment_distribution[q["sentiment"]["label"]] = sentiment_distribution.get(q["sentiment"]["label"], 0) + 1
        total_score = round(sum(q["final_score"] for q in results), 2)
        max_total = round(sum(q["max_marks"] for q in results), 2)

        jm.update(job_id, stage_index=7, message="Generating report")
        evaluation = {
            "evaluation_id": None,
            "created_at": datetime.utcnow().isoformat(),
            "student_name": params.get("student_name") or "Unknown Student",
            "exam_name": params.get("exam_name") or "Untitled Exam",
            "source": {"filename": filename, "pages": pages_n, "text_mode": parsed["text_mode"]},
            "processing": {"ocr_engine": parsed["engine"],
                           "detected_questions": len(segments),
                           "preamble_lines": len(seg["preamble"]),
                           "time_seconds": round(time.time() - t0, 2)},
            "questions": results,
            "summary": {"total_score": total_score, "max_marks": max_total,
                        "percentage": round(total_score / max_total * 100, 1) if max_total else 0,
                        "questions": len(results),
                        "sentiment_distribution": sentiment_distribution,
                        "overall_confidence": round(
                            sum(q["confidence"] for q in results) / len(results), 3),
                        "average_semantic_relevance": round(
                            sum(q["quality"]["semantic_relevance"] for q in results) / len(results), 3)},
            "notice": INTEGRITY_NOTICE,
        }

        db = SessionLocal()
        try:
            if sheet_id:
                sheet = db.get(AnswerSheet, sheet_id)
                sheet.status = "evaluated"
                for s in segments:
                    qr = QRow(sheet_id=sheet_id, number=s["question_id"],
                              text=s["question"], page=s["page"])
                    db.add(qr)
                    db.flush()
                    db.add(ARow(question_row_id=qr.id, text=s["student_answer"],
                                pages=",".join(map(str, s["answer_pages"]))))
            ev = Evaluation(sheet_id=sheet_id, user_id=params.get("user_id"), result_json="{}", total_score=total_score,
                            max_marks=max_total,
                            percentage=evaluation["summary"]["percentage"],
                            confidence=evaluation["summary"]["overall_confidence"],
                            processing_time=evaluation["processing"]["time_seconds"],
                            created_at=datetime.utcnow())
            db.add(ev)
            db.commit()
            evaluation["evaluation_id"] = ev.id
            for q in results:
                db.add(SentimentResult(evaluation_id=ev.id, question_number=q["question_id"],
                                       label=q["sentiment"]["label"],
                                       probabilities=q["sentiment"]["probabilities"],
                                       confidence=q["sentiment"]["confidence"]))
            db.add(ReportRow(evaluation_id=ev.id,
                             report_json=json.dumps(report_service.build_report(evaluation), default=str)))
            ev.result_json = json.dumps(evaluation, default=str)
            db.commit()
        finally:
            db.close()

        jm.update(job_id, stage_index=7, status="done", progress=1.0,
                  message="Evaluation complete", result={"evaluation_id": evaluation["evaluation_id"]})
    except Exception as e:
        jm.fail(job_id, str(e))
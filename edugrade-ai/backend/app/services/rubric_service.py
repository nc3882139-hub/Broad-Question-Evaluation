import json
import re
from difflib import SequenceMatcher

from app.config import settings
from app.utils.text_utils import STOPWORDS, split_sentences, word_count, words


def _slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "rubric"


def _norm(text):
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()


def load_rubric_library():
    lib = []
    for f in sorted(settings.RUBRIC_DIR.glob("*.json")):
        try:
            lib.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return lib


def find_rubric(question_text, threshold=0.72):
    best, best_score = None, 0.0
    qn = _norm(question_text)
    for r in load_rubric_library():
        score = SequenceMatcher(None, qn, _norm(r.get("question", ""))).ratio()
        if score > best_score:
            best, best_score = r, score
    if best and best_score >= threshold:
        best = dict(best)
        best.setdefault("approval_status", "approved" if best.get("source") in ("seed", "teacher") else "draft")
        best.setdefault("version", 1)
        return best, best_score
    return None, best_score


def _compress(sentence, max_tokens=9):
    kept = [t for t in words(sentence)
            if t.lower() not in STOPWORDS and re.search(r"[A-Za-z0-9]", t)]
    return " ".join(kept[:max_tokens])


def suggest_concepts(reference_answer, max_marks=5, question=""):
    """Auto-SUGGEST a rubric draft from a reference answer. The teacher must
    approve/edit — automatic suggestion never silently becomes the standard."""
    ref = (reference_answer or "").strip()
    if not ref:
        return {"question": question, "max_marks": max_marks, "reference_answer": "",
                "concepts": [{"concept": question or "Key concepts (define manually)",
                              "weight": max_marks, "optional": False}],
                "source": "auto",
                "note": "No reference answer provided — relevance-only grading. Teacher should define key concepts."}
    raw = []
    for s in split_sentences(ref):
        clauses = re.split(r",?\s+(?:and|but|who|which|while)\s+", s) if word_count(s) > 18 else [s]
        for cl in clauses:
            phrase = _compress(cl)
            if phrase and len(phrase) > 8 and not any(
                    SequenceMatcher(None, phrase.lower(), p.lower()).ratio() > 0.8 for p in raw):
                raw.append(phrase)
    if not raw:
        raw = [_compress(ref) or ref]
    raw = raw[:8]
    w = round(max_marks / len(raw), 2)
    weights = [w] * len(raw)
    weights[-1] = round(weights[-1] + round(max_marks - sum(weights), 2), 2)
    facts = sorted({t for t in words(ref)
                    if any(ch.isdigit() for ch in t) or (t.isupper() and len(t) >= 2)})
    return {"question": question, "max_marks": max_marks, "reference_answer": ref,
            "concepts": [{"concept": p, "weight": weights[i], "optional": False}
                         for i, p in enumerate(raw)],
            "important_facts": facts[:15], "source": "auto",
            "note": "Auto-suggested concepts — teacher approval required before official grading."}


def save_rubric(rubric: dict, db=None):
    rid = rubric.get("id") or _slug(rubric["question"])
    rubric["id"] = rid
    rubric.setdefault("version", 1)
    rubric.setdefault("approval_status", "draft" if rubric.get("source") == "auto" else "approved")
    settings.RUBRIC_DIR.mkdir(parents=True, exist_ok=True)
    (settings.RUBRIC_DIR / f"{rid}.json").write_text(
        json.dumps(rubric, indent=2, ensure_ascii=False), encoding="utf-8")
    if db is not None:
        try:
            from app.models.database import Rubric as RubricRow, Concept as ConceptRow
            row = db.query(RubricRow).filter(RubricRow.external_id == rid).first()
            if not row:
                row = RubricRow(external_id=rid, question_text=rubric["question"])
                db.add(row)
            row.max_marks = rubric.get("max_marks", 5)
            row.reference_answer = rubric.get("reference_answer", "")
            row.source = rubric.get("source", "teacher")
            db.query(ConceptRow).filter(ConceptRow.rubric_row_id == row.id).delete()
            for c in rubric.get("concepts", []):
                db.add(ConceptRow(rubric_row_id=row.id, concept=c["concept"],
                                  weight=c.get("weight", 1), optional=c.get("optional", False)))
            db.commit()
        except Exception:
            db.rollback()
    return rubric


def list_rubrics(db=None):
    out = {r["question"]: r for r in load_rubric_library()}
    if db is not None:
        try:
            from app.models.database import Rubric as RubricRow
            for row in db.query(RubricRow).all():
                if row.question_text not in out:
                    out[row.question_text] = {
                        "id": row.external_id or str(row.id), "question": row.question_text,
                        "max_marks": row.max_marks, "reference_answer": row.reference_answer,
                        "source": row.source, "concepts": []}
        except Exception:
            pass
    return list(out.values())


def get_rubric(db, rubric_id):
    for r in load_rubric_library():
        if r.get("id") == str(rubric_id) or str(rubric_id) == str(hash(r["question"]) % 10**8):
            return r
    if db is not None:
        try:
            from app.models.database import Rubric as RubricRow, Concept as ConceptRow
            q = db.query(RubricRow).filter(RubricRow.external_id == str(rubric_id)).first()
            if q:
                return {"id": q.external_id, "question": q.question_text, "max_marks": q.max_marks,
                        "reference_answer": q.reference_answer, "source": q.source,
                        "concepts": [{"concept": c.concept, "weight": c.weight, "optional": c.optional}
                                     for c in db.query(ConceptRow).filter(ConceptRow.rubric_row_id == q.id)]}
        except Exception:
            pass
    return None
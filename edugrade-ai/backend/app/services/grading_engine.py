"""grading_engine.py — explainable academic marks prediction.

Hybrid per-concept confidence (weights configurable via .env):
    conf = W_SEMANTIC * semantic  +  W_KEYWORD * keyword  +  W_CONTEXT * contextual

Marks are CONTINUOUS, never purely binary:
    award = clip((conf - AWARD_MIN_CONF) / (AWARD_MAX_CONF - AWARD_MIN_CONF), 0, 1)
    marks = weight * award

Two grading modes are computed and exposed side-by-side:
    Mode A (rubric-based)   — key-point semantic matching  -> "rubric_score"
    Mode B (reference-based)— similarity to reference answer -> "reference_score"

Quality indicators are reported SEPARATELY and never silently merged into marks.
`method` supports keyword | tfidf | embedding | hybrid for research comparison.
"""
import time

import numpy as np

from app.config import settings
from app.services import semantic_service as sem
from app.utils.text_utils import (clamp, content_tokens, duplicate_sentence_ratio,
                                  split_sentences, token_f1, word_count, words)

NEG_WINDOW = 4
_NEGATIONS = {"not", "no", "never", "none", "neither", "nor", "cannot", "without",
              "wasn", "isn", "didn", "doesn", "don", "won", "couldn", "shouldn"}


def _length_fit(n):
    if 15 <= n <= 300:
        return 1.0
    if n < 15:
        return round(n / 15, 3)
    return max(0.6, 1.0 - (n - 300) / 600.0)


def _has_negation_conflict(sentence, concept):
    toks = [t.lower() for t in words(sentence)]
    c_stems = {stem for stem in content_tokens(concept)}
    for i, t in enumerate(toks):
        if t in c_stems or any(s and t.startswith(s[: max(4, len(s) - 2)]) for s in c_stems):
            window = toks[max(0, i - NEG_WINDOW):i]
            if any(w in _NEGATIONS or w.endswith("n't") for w in window):
                return True
    return False


def _concept_confidence(ctext, answer, sentences, ans_emb, sent_embs, method):
    c_emb = sem.embed_one(ctext)
    whole = float(np.dot(c_emb, ans_emb)) if ans_emb is not None else 0.0
    sims = (sent_embs @ c_emb).tolist() if sent_embs is not None and sentences else [whole]
    best_idx = int(np.argmax(sims))
    best_sent = float(sims[best_idx])
    sem_s = max(whole, best_sent)
    if settings.EMBEDDING_BACKEND == "hashing":
        sem_s = max(sem_s, sem.content_recall(ctext, answer))
    ctx_s = float(np.mean(sorted(sims, reverse=True)[:2]))

    c_tokens = content_tokens(ctext)
    kw_s, kw_idx = 0.0, best_idx
    for i, s in enumerate(sentences):
        f1 = token_f1(c_tokens, content_tokens(s))
        if f1 > kw_s:
            kw_s, kw_idx = f1, i

    if method == "keyword":
        conf = kw_s
    elif method == "embedding":
        conf = sem_s
    elif method == "tfidf":
        docs = [answer] + list(sentences)
        conf = max(sem.tfidf_similarity_set(ctext, docs)) if docs else 0.0
    else:  # hybrid
        conf = settings.W_SEMANTIC * sem_s + settings.W_KEYWORD * kw_s + settings.W_CONTEXT * ctx_s

    ev_idx = None if not sentences else (kw_idx if (kw_s >= 0.5 and kw_s >= best_sent) else best_idx)
    return {"confidence": conf, "semantic": sem_s, "keyword": kw_s,
            "contextual": ctx_s, "best_idx": ev_idx}


def _detect_issues(answer, n_words, question_sim, ref_sim, coverage, redundancy, conflict):
    issues = []
    if not answer:
        return [{"type": "empty", "message": "No answer text was detected for this question."}]
    if n_words < 15:
        issues.append({"type": "very_short",
                       "message": "The answer is very short relative to the scope of the question."})
    if question_sim < 0.25 or (ref_sim is not None and ref_sim < 0.30):
        issues.append({"type": "off_topic",
                       "message": "The answer appears to be off-topic relative to the question."})
    elif (ref_sim if ref_sim is not None else question_sim) < 0.40:
        issues.append({"type": "irrelevant_content",
                       "message": "Much of the content appears unrelated to the expected answer."})
    if coverage < 0.6:
        issues.append({"type": "incomplete",
                       "message": "The answer seems incomplete — several expected concepts are missing."})
    if redundancy > 0.35:
        issues.append({"type": "excessive_repetition",
                       "message": "The answer repeats the same content multiple times."})
    if conflict:
        issues.append({"type": "possible_contradiction",
                       "message": "Possible contradiction with expected facts detected — teacher review recommended."})
    return issues


def _build_feedback(r):
    q = r["quality"]
    total = r["concepts_covered"] + r["concepts_partial"] + r["concepts_missing"]
    parts = [f"The answer covers {r['concepts_covered']} of {total} key concepts "
             f"with {int(round(q['semantic_relevance'] * 100))}% semantic relevance."]
    partial = [c["concept"] for c in r["concept_results"] if c["status"] == "partial"]
    missing = [c["concept"] for c in r["concept_results"] if c["status"] == "missing"]
    if partial:
        parts.append("Partially addressed: " + "; ".join(partial) + ".")
    if missing:
        parts.append("To improve, consider adding: " + "; ".join(missing) + ".")
    if q["possible_factual_inconsistency"]:
        parts.append("A possible factual inconsistency was detected and should be reviewed.")
    for i in r["issues"]:
        if i["type"] in ("empty", "very_short", "excessive_repetition"):
            parts.append(i["message"])
    if not missing and not partial and not r["issues"]:
        parts.append("A strong, well-aligned answer.")
    return " ".join(parts)


def grade_answer(question, student_answer, rubric, method="hybrid"):
    t0 = time.time()
    question = (question or "").strip()
    answer = (student_answer or "").strip()
    concepts = rubric.get("concepts") or []
    max_marks = float(rubric.get("max_marks") if rubric.get("max_marks") is not None else 5)
    if max_marks <= 0:
        raise ValueError("max_marks must be greater than zero")
    if any(float(c.get("weight", 0)) < 0 for c in concepts):
        raise ValueError("concept weights cannot be negative")
    if concepts and sum(float(c.get("weight", 0)) for c in concepts) <= 0:
        raise ValueError("concept weights must contain a positive value")
    if concepts and sum(float(c.get("weight", 0)) for c in concepts) > max_marks + 1e-6:
        raise ValueError("concept weights cannot exceed max_marks")
    reference = (rubric.get("reference_answer") or "").strip()

    sentences = split_sentences(answer) if answer else []
    n_words = word_count(answer)

    ans_emb = sem.embed_one(answer) if answer else None
    q_emb = sem.embed_one(question) if question else None
    ref_emb = sem.embed_one(reference) if reference else None
    sent_embs = sem.embed(sentences) if sentences else None

    ref_sim = float(np.dot(ans_emb, ref_emb)) if ans_emb is not None and ref_emb is not None else None
    question_sim = float(np.dot(ans_emb, q_emb)) if ans_emb is not None and q_emb is not None else 0.0

    concept_results, highlights = [], []
    conflict_any = False
    total_weight = awarded_weight = conf_weighted = 0.0

    for c in concepts:
        ctext = (c.get("concept") or "").strip()
        weight = float(c.get("weight", 1))
        total_weight += weight
        if not answer or not ctext:
            conf = sem_s = kw_s = ctx_s = 0.0
            ev_idx = None
        else:
            r = _concept_confidence(ctext, answer, sentences, ans_emb, sent_embs, method)
            conf, sem_s, kw_s, ctx_s, ev_idx = (r["confidence"], r["semantic"],
                                                r["keyword"], r["contextual"], r["best_idx"])
        conf = float(clamp(conf, 0.0, 1.0))
        status = ("matched" if conf >= settings.MATCH_THRESHOLD
                  else "partial" if conf >= settings.PARTIAL_THRESHOLD else "missing")
        evidence = sentences[ev_idx] if ev_idx is not None and sentences else (answer if answer else "")
        if status in ("matched", "partial") and evidence and _has_negation_conflict(evidence, ctext):
            status, conflict_any = "conflict", True
        award_range = settings.AWARD_MAX_CONF - settings.AWARD_MIN_CONF
        award = (clamp((conf - settings.AWARD_MIN_CONF) / award_range, 0.0, 1.0)
             if award_range > 0 else 0.0)
        if status == "conflict":
            award *= 0.5  # conservative — flagged for teacher review
        marks = weight * award
        awarded_weight += weight * award
        conf_weighted += weight * conf
        start = answer.find(evidence) if evidence else -1
        if start >= 0 and status != "missing":
            end = min(len(answer), start + len(evidence))
            highlights.append({"start": start, "end": end, "status": status,
                               "concept": ctext, "confidence": round(conf, 3)})
        concept_results.append({
            "concept": ctext, "weight": weight, "optional": bool(c.get("optional", False)),
            "status": status, "confidence": round(conf, 3), "evidence": evidence,
            "evidence_start": max(0, start) if start >= 0 else -1,
            "evidence_end": min(len(answer), start + len(evidence)) if start >= 0 else -1,
            "semantic": round(sem_s, 3), "keyword": round(kw_s, 3), "contextual": round(ctx_s, 3),
            "award": round(award, 3), "marks": round(marks, 3)})

    rubric_score = round(min(max_marks, sum(r["marks"] for r in concept_results)), 2)
    coverage = awarded_weight / total_weight if total_weight else 0.0
    matched = sum(1 for r in concept_results if r["status"] == "matched")
    partial = sum(1 for r in concept_results if r["status"] == "partial")
    missing = sum(1 for r in concept_results if r["status"] == "missing")

    # ---- Mode B: reference-answer similarity scoring ----
    if ref_sim is not None:
        f, cl = settings.REF_SIM_FLOOR, settings.REF_SIM_CEIL
        ratio = 1.0 if ref_sim >= cl else (max(0.0, (ref_sim - f) / (cl - f)) if ref_sim > f else 0.0)
        reference_score = round(max_marks * ratio, 2)
    else:
        reference_score = None

    if settings.FINAL_MODE == "reference" and reference_score is not None:
        final = reference_score
    elif settings.FINAL_MODE == "blend" and reference_score is not None:
        final = settings.BLEND_RUBRIC_WEIGHT * rubric_score + (1 - settings.BLEND_RUBRIC_WEIGHT) * reference_score
    else:
        final = rubric_score
    final = round(min(max_marks, max(0.0, final)), 2)

    confidence = round(conf_weighted / total_weight, 3) if total_weight and answer else 0.0

    # ---- quality indicators (reported separately) ----
    redundancy = duplicate_sentence_ratio(sentences) if sentences else 0.0
    conciseness = clamp(1.0 - redundancy * 1.5, 0, 1) * (0.85 if n_words > 350 else 1.0)
    if len(sentences) >= 2 and sent_embs is not None:
        coh = float(np.mean([np.dot(sent_embs[i], sent_embs[i + 1]) for i in range(len(sentences) - 1)]))
    elif len(sentences) == 1:
        coh = 1.0
    else:
        coh = 0.0
    quality = {
        "concept_coverage": round(coverage, 3),
        "semantic_relevance": round(ref_sim if ref_sim is not None else question_sim, 3),
        "completeness": round(clamp(0.7 * coverage + 0.3 * _length_fit(n_words), 0, 1), 3),
        "coherence": round(clamp(coh, 0, 1), 3),
        "conciseness": round(conciseness, 3),
        "possible_factual_inconsistency": conflict_any,
        "overall_confidence": confidence,
    }

    issues = _detect_issues(answer, n_words, question_sim, ref_sim, coverage, redundancy, conflict_any)
    result = {
        "max_marks": max_marks, "score": rubric_score, "rubric_score": rubric_score,
        "reference_score": reference_score, "final_score": final,
        "percentage": round(final / max_marks * 100, 1) if max_marks else 0,
        "concepts_covered": matched, "concepts_partial": partial, "concepts_missing": missing,
        "confidence": confidence, "quality": quality,
        "mode_a": {"name": "Rubric Based", "score": rubric_score, "concept_coverage": round(coverage, 3)},
        "mode_b": {"name": "Reference Answer Based", "score": reference_score,
                   "reference_similarity": round(ref_sim, 3) if ref_sim is not None else None},
        "concept_results": concept_results, "highlights": highlights, "issues": issues,
        "grading_time_ms": int((time.time() - t0) * 1000), "method": method,
    }
    result["feedback"] = _build_feedback(result)
    return result
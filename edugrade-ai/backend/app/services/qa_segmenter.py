import re

QUESTION_HEADER = re.compile(
    r"^\s*(?:(q(?:uestion)?)\s*[.\-:#]?\s*)?(\d{1,2})\s*(?:[.)\]:\-]\s*|\s+|$)", re.IGNORECASE
)
ANSWER_MARKER_INLINE = re.compile(r"(?:^|(?<=[.!?])\s*)\bans(?:wer)?\s*[.:\-]\s*", re.IGNORECASE)
ANSWER_MARKER_LINE = re.compile(r"^\s*(?:ans(?:wer)?|sol(?:ution)?)\s*[.:\-]\s*", re.IGNORECASE)
QUESTION_WORDS = ("explain", "describe", "write", "define", "discuss", "what", "why", "how",
                  "state", "list", "mention", "who", "when", "which", "elaborate", "summarize",
                  "summarise", "short note", "compare", "differentiate", "give", "draw",
                  "justify", "outline", "name")


def _looks_like_question(text):
    t = text.strip().lower()
    if not t:
        return False
    return t.endswith("?") or any(t.startswith(w) for w in QUESTION_WORDS)


def _ends_sentence(line):
    return line.rstrip().endswith(("?", ".", "!"))


def _split_answer_marker(text):
    m = ANSWER_MARKER_INLINE.search(text)
    if m:
        return text[: m.start()].strip(), text[m.end():].strip()
    return text.strip(), None


def segment_qa(pages):
    """pages: [{"page_number": int, "text": str}] -> {"segments": [...], "preamble": [...]}"""
    segments, preamble = [], []
    current = None
    state = "idle"          # idle | question | answer
    expected = 1

    def flush():
        nonlocal current
        if current and (current["question"].strip() or current["answer"].strip()):
            segments.append(current)
        current = None

    for page in pages:
        pno = page["page_number"]
        pending_blank = True
        for raw in page["text"].split("\n"):
            stripped = raw.strip()
            if not stripped:
                pending_blank = True
                if current is not None and state == "answer":
                    current["answer"] += "\n"
                continue

            # ---- header detection ----
            m = QUESTION_HEADER.match(stripped)
            is_header, qnum, rest = False, None, stripped
            if m:
                qnum = int(m.group(2))
                explicit = bool(m.group(1))
                rest = stripped[m.end():].strip()
                if explicit:
                    is_header = True
                elif qnum == expected and pending_blank and rest and (
                    state != "answer" or len(current["answer"]) < 40 or _looks_like_question(rest)
                ):
                    is_header = True  # sequential numbering at a line boundary
                elif qnum == expected and rest and _looks_like_question(rest):
                    is_header = True
                if qnum == expected and rest and _looks_like_question(rest):
                    is_header = True

            if is_header and current is not None:
                flush()
                state = "idle"

            if is_header:
                qpart, apart = _split_answer_marker(rest)
                current = {
                    "question_id": qnum, "question": qpart,
                    "answer": apart if apart is not None else "",
                    "answer_pages": [pno] if apart is not None else [],
                    "pages": [pno], "has_marker": apart is not None,
                    "confidence": 0.95 if m.group(1) else 0.8,
                }
                expected = qnum + 1
                if apart is not None or _ends_sentence(qpart):
                    state = "answer"
                else:
                    state = "question"          # multi-line question
                pending_blank = False
                continue

            if state == "question":
                qpart, apart = _split_answer_marker(stripped)
                current["question"] += " " + qpart
                if apart is not None:
                    current["answer"], current["answer_pages"], current["has_marker"] = apart, [pno], True
                    state = "answer"
                elif _ends_sentence(qpart) or len(current["question"]) > 400:
                    state = "answer"
            elif state == "answer":
                mm = ANSWER_MARKER_LINE.match(stripped)
                body = stripped[mm.end():].strip() if mm else stripped
                if body:
                    if current["answer"] and not current["answer"].endswith("\n"):
                        current["answer"] += " "
                    current["answer"] += body
                if pno not in current["answer_pages"]:
                    current["answer_pages"].append(pno)
            else:
                preamble.append({"page": pno, "text": stripped})
            pending_blank = False

    flush()

    results = []
    for i, s in enumerate(segments, 1):
        q = re.sub(r"\s+", " ", s["question"]).strip()
        q = re.sub(r"^(?:q(?:uestion)?\s*[.\-:#]?\s*\d{0,2}[.):\-=]?\s*)", "", q, flags=re.I).strip()
        results.append({
            "question_id": s["question_id"] if s["question_id"] is not None else i,
            "question": q,
            "student_answer": re.sub(r"\n{3,}", "\n\n", s["answer"]).strip(),
            "page": s["pages"][0] if s["pages"] else 1,
            "answer_pages": s["answer_pages"] or s["pages"],
            "segmentation_confidence": round(s["confidence"], 2),
            "used_answer_marker": s["has_marker"],
        })
    return {"segments": results, "preamble": preamble,
            "error": "No numbered questions were detected." if not results else None}
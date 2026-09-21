import re

STOPWORDS = set(("a an the is are was were be been being am do does did doing have has had "
    "will would can could shall should may might must of in on at to for with by from as and "
    "or but if then than that this these those it its he she they them his her their there "
    "here not no nor so very just also into over under about above below between during before "
    "after up down out off again further once i we you your our us me my mine who whom whose "
    "what when where why how all any both each few more most other some such only own same too "
    "s t d ll m o re ve y").split())

_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z][a-z])")


def words(text):
    return re.findall(r"[A-Za-z0-9']+", text or "")


def tokens(text):
    return {t.lower() for t in words(text)}


def word_count(text):
    return len(words(text))


def stem(tok):
    t = tok.lower()
    for suf in ("ies", "ing", "ed", "es", "ly", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            return t[: -len(suf)] + ("y" if suf == "ies" else "")
    return t


def content_tokens(text):
    return [stem(t) for t in words(text) if t.lower() not in STOPWORDS and len(t) > 1]


def split_sentences(text):
    if not text:
        return []
    protected = re.sub(r"(?i)\b(?:mr|mrs|ms|dr|prof|sr|jr)\.",
                       lambda m: m.group(0)[:-1] + "<INITIAL>", text.strip())
    protected = re.sub(r"(?<=\b[A-Z])\.", "<INITIAL>", protected)
    return [p.replace("<INITIAL>", ".").strip() for p in _SENT_RE.split(protected) if p.strip()]


def token_f1(a, b):
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if not inter:
        return 0.0
    p, r = inter / len(a), inter / len(b)
    return 2 * p * r / (p + r)


def token_jaccard(a, b):
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def duplicate_sentence_ratio(sentences):
    n = len(sentences)
    if n < 2:
        return 0.0
    toks = [set(content_tokens(s)) for s in sentences]
    dup = total = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += 1
            a, b = toks[i], toks[j]
            if a and b and len(a & b) / max(1, min(len(a), len(b))) > 0.8:
                dup += 1
    return dup / total if total else 0.0


def clamp(x, lo, hi):
    return max(lo, min(hi, x))
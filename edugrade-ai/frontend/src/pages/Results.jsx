import { AlertTriangle, Brain, CheckCircle2, ChevronDown, ChevronUp, Download, MinusCircle, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { api, downloadReport } from "../api";
import { Badge, Button, Card, Progress } from "../ui";

const HL = {
  matched: "bg-emerald-500/25 text-emerald-100 rounded px-0.5",
  partial: "bg-amber-500/25 text-amber-100 rounded px-0.5",
  conflict: "bg-rose-500/25 text-rose-100 rounded px-0.5",
};
const sentTone = (l) => (l === "positive" ? "green" : l === "negative" ? "rose" : "blue");

function HighlightedAnswer({ text, highlights = [] }) {
  const spans = [...highlights].map((h) => ({ ...h, start: Math.max(0, Math.min(text.length, h.start)), end: Math.max(0, Math.min(text.length, h.end)) }))
    .filter((h) => h.end > h.start).sort((a, b) => a.start - b.start);
  const parts = [];
  let cur = 0;
  spans.forEach((h, i) => {
    if (h.start < cur) return;
    if (h.start > cur) parts.push(<span key={`p${i}`}>{text.slice(cur, h.start)}</span>);
    parts.push(<mark key={i} className={HL[h.status] || ""} title={`${h.concept} (${h.status}, ${Math.round(h.confidence * 100)}%)`}>{text.slice(h.start, h.end)}</mark>);
    cur = h.end;
  });
  if (cur < text.length) parts.push(<span key="rest">{text.slice(cur)}</span>);
  return <p className="text-sm leading-relaxed text-slate-300 whitespace-pre-wrap">{parts.length ? parts : (text || <span className="text-slate-500">(no answer)</span>)}</p>;
}

const Metric = ({ label, value, big }) => (
  <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
    <div className="text-xs text-slate-400">{label}</div>
    <div className={`${big ? "text-2xl" : "text-lg"} font-semibold text-white`}>{value}</div>
  </div>);

function QuestionDetail({ q }) {
  const tot = q.concept_results.length;
  return (
    <div className="border-t border-white/10 p-5 space-y-5">
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h4 className="text-xs font-medium text-slate-400 mb-1">QUESTION</h4>
          <p className="text-sm text-slate-200">{q.question}</p>
          <h4 className="text-xs font-medium text-slate-400 mt-4 mb-1">STUDENT ANSWER <span className="text-slate-500">(page {q.page})</span></h4>
          <HighlightedAnswer text={q.student_answer} highlights={q.highlights} />
          <div className="flex flex-wrap gap-3 mt-3 text-[11px] text-slate-400">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-500/40" /> matched concept</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-amber-500/40" /> partial evidence</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-rose-500/40" /> conflicting evidence</span>
            <span className="text-slate-500">missing concepts leave no highlight</span>
          </div>
        </div>
        <div className="space-y-3">
          <h4 className="text-xs font-medium text-slate-400">SCORES</h4>
          <div className="grid grid-cols-2 gap-3">
            <Metric label="AI prediction" value={`${q.ai_score ?? q.final_score} / ${q.max_marks}`} />
            <Metric label="Final teacher grade" value={q.official_score == null ? "Review required" : `${q.official_score} / ${q.max_marks}`} />
            <Metric label="Rubric score (Mode A)" value={`${q.rubric_score} / ${q.max_marks}`} />
            <Metric label="Reference (Mode B)" value={q.mode_b.score != null ? `${q.mode_b.score} · sim ${Math.round((q.mode_b.reference_similarity || 0) * 100)}%` : "n/a"} />
            <Metric label="Displayed score" value={`${q.final_score} / ${q.max_marks}`} big />
            <Metric label="Confidence" value={`${Math.round(q.confidence * 100)}%`} />
          </div>
          <h4 className="text-xs font-medium text-slate-400 pt-1">ANSWER QUALITY <span className="text-slate-500 font-normal">(shown separately — not merged into marks)</span></h4>
          {Object.entries({ "Concept coverage": q.quality.concept_coverage, "Semantic relevance": q.quality.semantic_relevance,
                            Completeness: q.quality.completeness, Coherence: q.quality.coherence, Conciseness: q.quality.conciseness })
            .map(([k, v]) => (
              <div key={k}>
                <div className="flex justify-between text-xs text-slate-400"><span>{k}</span><span>{Math.round(v * 100)}%</span></div>
                <Progress value={v * 100} tone={v >= 0.6 ? "green" : v >= 0.4 ? "amber" : "rose"} className="mt-1" />
              </div>))}
          {q.quality.possible_factual_inconsistency && (
            <Badge tone="rose"><AlertTriangle size={12} /> Possible factual inconsistency — review recommended</Badge>)}
          {q.review_required && <Badge tone="amber"><AlertTriangle size={12} /> Teacher review required</Badge>}
        </div>
      </div>
      <div>
        <h4 className="text-xs font-medium text-slate-400 mb-2">KEY CONCEPTS ({q.concepts_covered} / {tot} covered)</h4>
        <div className="space-y-2">
          {q.concept_results.map((c, i) => (
            <div key={i} className="flex items-center gap-3 text-sm rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2">
              {c.status === "matched" ? <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
               : c.status === "partial" ? <MinusCircle size={16} className="text-amber-400 shrink-0" />
               : c.status === "conflict" ? <AlertTriangle size={16} className="text-rose-400 shrink-0" />
               : <XCircle size={16} className="text-rose-400/70 shrink-0" />}
              <span className="text-slate-200 flex-1 min-w-0 truncate">{c.concept}</span>
              <span className="text-xs text-slate-500 hidden md:block">sem {Math.round(c.semantic * 100)}% · kw {Math.round(c.keyword * 100)}%</span>
              <Badge tone={c.status === "matched" ? "green" : c.status === "partial" ? "amber" : c.status === "conflict" ? "rose" : "slate"}>
                {c.marks} / {c.weight} · {Math.round(c.confidence * 100)}%
              </Badge>
            </div>))}
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h4 className="text-xs font-medium text-slate-400 mb-2 flex items-center gap-1"><Brain size={14} /> FEEDBACK</h4>
          <p className="text-sm text-slate-300">{q.feedback}</p>
          {q.issues?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {q.issues.map((iss, i) => <Badge key={i} tone="rose">{iss.type}</Badge>)}
            </div>)}
        </Card>
        <Card className="p-4">
          <h4 className="text-xs font-medium text-slate-400 mb-2">SENTIMENT <span className="text-slate-500 font-normal">(informational — does not affect marks)</span></h4>
          <div className="flex items-center gap-3">
            <Badge tone={sentTone(q.sentiment.label)}>{q.sentiment.label}</Badge>
            <span className="text-xs text-slate-400">confidence {Math.round(q.sentiment.confidence * 100)}%</span>
          </div>
          <div className="mt-3 space-y-1.5">
            {Object.entries(q.sentiment.probabilities).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 text-xs">
                <span className="w-16 text-slate-400">{k}</span>
                <Progress value={v * 100} tone={k === "positive" ? "green" : k === "negative" ? "rose" : "blue"} />
                <span className="w-10 text-right text-slate-400">{Math.round(v * 100)}%</span>
              </div>))}
          </div>
        </Card>
      </div>
    </div>);
}

function QuestionCard({ q, open, onToggle }) {
  const tone = q.percentage >= 60 ? "green" : q.percentage >= 40 ? "amber" : "rose";
  return (
    <Card className="overflow-hidden">
      <button className="w-full text-left p-5 flex items-center justify-between gap-4" onClick={onToggle}>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <Badge tone="violet">Question {q.question_id}</Badge>
            <Badge tone={tone}>{q.final_score} / {q.max_marks}</Badge>
            <Badge tone="slate">{q.percentage}%</Badge>
            <Badge tone={sentTone(q.sentiment.label)}>{q.sentiment.label}</Badge>
            <Badge tone="slate">{q.concepts_covered}/{q.concept_results.length} concepts</Badge>
            {q.review_required && <Badge tone="amber">Review required</Badge>}
          </div>
          <p className="text-sm text-slate-200 truncate">{q.question}</p>
          {q.rubric_provenance && <p className="text-xs text-slate-500 mt-1">Rubric {q.rubric_provenance.rubric_id || "unapproved"} · v{q.rubric_provenance.rubric_version} · {q.rubric_status}</p>}
        </div>
        {open ? <ChevronUp className="text-slate-400 shrink-0" /> : <ChevronDown className="text-slate-400 shrink-0" />}
      </button>
      {open && <QuestionDetail q={q} />}
    </Card>);
}

export default function Results({ evaluationId, onNavigate }) {
  const [ev, setEv] = useState(null);
  const [open, setOpen] = useState(0);
  useEffect(() => {
    if (evaluationId) { setEv(null); api.evaluation(evaluationId).then(setEv).catch(() => {}); }
  }, [evaluationId]);
  if (!evaluationId)
    return <Card className="p-8 text-center text-slate-400">No evaluation selected. Run one from the <button className="text-violet-300 underline" onClick={() => onNavigate("evaluate")}>Evaluate</button> page.</Card>;
  if (!ev) return <p className="text-slate-400">Loading evaluation…</p>;
  const s = ev.summary;
  return (
    <div className="space-y-5">
      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-white">{ev.exam_name}</h1>
            <p className="text-sm text-slate-400 mt-1">
              {ev.student_name} · {new Date(ev.created_at).toLocaleString()} · {ev.source.filename} ·
              engine: {ev.processing.ocr_engine} · {ev.processing.detected_questions} questions detected
            </p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => downloadReport(ev.evaluation_id, "json")}><Download size={14} /> JSON</Button>
            <Button size="sm" variant="outline" onClick={() => downloadReport(ev.evaluation_id, "csv")}><Download size={14} /> CSV</Button>
            <Button size="sm" onClick={() => downloadReport(ev.evaluation_id, "pdf")}><Download size={14} /> PDF</Button>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
          <Metric label="Total marks" value={`${s.total_score} / ${s.max_marks}`} big />
          <Metric label="Percentage" value={`${s.percentage}%`} big />
          <Metric label="Overall confidence" value={`${Math.round(s.overall_confidence * 100)}%`} />
          <Metric label="Processing time" value={`${ev.processing.time_seconds}s`} />
        </div>
      </Card>
      {ev.questions.map((q, i) => (
        <QuestionCard key={i} q={q} open={open === i} onToggle={() => setOpen(open === i ? -1 : i)} />))}
    </div>);
}
import { Plus, Save, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api";
import { Badge, Button, Card, Input, Textarea } from "../ui";

export default function Rubrics() {
  const [rubrics, setRubrics] = useState([]);
  const [question, setQuestion] = useState("");
  const [maxMarks, setMaxMarks] = useState(5);
  const [reference, setReference] = useState("");
  const [concepts, setConcepts] = useState([]);
  const [msg, setMsg] = useState("");
  const load = () => api.rubrics().then(setRubrics).catch(() => {});
  useEffect(() => { load(); }, []);

  async function suggest() {
    setMsg("");
    try {
      const s = await api.suggest({ question, reference_answer: reference, max_marks: Number(maxMarks) || 5 });
      setConcepts(s.concepts.map((c) => ({ ...c })));
      setMsg(s.note || "Suggested concepts generated — review and edit before saving.");
    } catch (e) { setMsg(String(e.message || e)); }
  }
  async function save() {
    setMsg("");
    try {
      await api.createRubric({ question, max_marks: Number(maxMarks) || 5, reference_answer: reference,
        concepts: concepts.map((c) => ({ concept: c.concept, weight: Number(c.weight) || 1, optional: !!c.optional })) });
      setMsg("Rubric saved.");
      setQuestion(""); setReference(""); setConcepts([]); load();
    } catch (e) { setMsg(String(e.message || e)); }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold text-white">Teacher Rubric Editor</h1>
        <p className="text-sm text-slate-400">
          Auto-suggested concepts are drafts only — <span className="text-amber-300">you approve the grading standard</span>.
        </p>
      </div>
      <Card className="p-6 space-y-4">
        <Input placeholder="Question (e.g. Explain photosynthesis.)" value={question} onChange={(e) => setQuestion(e.target.value)} />
        <div className="grid sm:grid-cols-[1fr_120px] gap-3">
          <Textarea rows={4} placeholder="Reference / model answer…" value={reference} onChange={(e) => setReference(e.target.value)} />
          <Input type="number" min="1" step="0.5" value={maxMarks} onChange={(e) => setMaxMarks(e.target.value)} />
        </div>
        <Button size="sm" variant="outline" onClick={suggest} disabled={!reference.trim()}>
          <Sparkles size={14} /> Suggest key concepts
        </Button>
        {concepts.length > 0 && (
          <div className="space-y-2">
            {concepts.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <Input value={c.concept} onChange={(e) => setConcepts(concepts.map((x, j) => (j === i ? { ...x, concept: e.target.value } : x)))} />
                <Input className="w-20" type="number" step="0.5" min="0" value={c.weight}
                       onChange={(e) => setConcepts(concepts.map((x, j) => (j === i ? { ...x, weight: e.target.value } : x)))} />
                <Button size="sm" variant="ghost" onClick={() => setConcepts(concepts.filter((_, j) => j !== i))}><Trash2 size={14} /></Button>
              </div>))}
            <Button size="sm" variant="ghost" onClick={() => setConcepts([...concepts, { concept: "", weight: 1, optional: false }])}>
              <Plus size={14} /> Add concept
            </Button>
          </div>)}
        <div className="flex items-center gap-3">
          <Button size="sm" onClick={save} disabled={!question.trim() || concepts.length === 0}><Save size={14} /> Save rubric</Button>
          {msg && <span className="text-xs text-amber-300">{msg}</span>}
        </div>
      </Card>
      <Card className="p-6">
        <h3 className="text-sm font-medium text-slate-300 mb-3">Rubric library ({rubrics.length})</h3>
        <div className="space-y-2">
          {rubrics.map((r, i) => (
            <div key={i} className="rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm text-slate-200 truncate">{r.question}</p>
                <p className="text-xs text-slate-500">{r.concepts?.length ?? 0} concepts · max {r.max_marks} marks</p>
              </div>
              <Badge tone={r.source === "seed" ? "blue" : r.source === "teacher" ? "green" : "amber"}>{r.source || "teacher"}</Badge>
            </div>))}
        </div>
      </Card>
    </div>);
}
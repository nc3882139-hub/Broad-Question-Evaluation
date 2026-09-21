import { Download } from "lucide-react";
import { useEffect, useState } from "react";
import { api, downloadReport } from "../api";
import { Badge, Button, Card } from "../ui";

const sentTone = (l) => (l === "positive" ? "green" : l === "negative" ? "rose" : "blue");

export default function Reports({ onOpen }) {
  const [list, setList] = useState([]);
  const [sel, setSel] = useState(null);
  useEffect(() => { api.evaluations().then(setList).catch(() => {}); }, []);
  async function open(id) { setSel(await api.evaluation(id)); }
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Reports</h1>
        <p className="text-sm text-slate-400">Complete evaluation reports with downloads.</p>
      </div>
      <div className="grid lg:grid-cols-[320px_1fr] gap-4">
        <Card className="p-4 space-y-2">
          {list.length === 0 && <p className="text-slate-500 text-sm">No evaluations yet.</p>}
          {list.map((r) => (
            <button key={r.id} onClick={() => open(r.id)}
              className={`w-full text-left rounded-xl px-3 py-2.5 text-sm transition-all ${sel?.evaluation_id === r.id ? "bg-violet-600/20 border border-violet-500/30" : "hover:bg-white/5 border border-transparent"}`}>
              <div className="flex justify-between"><span className="text-slate-200 truncate pr-2">{r.exam_name}</span><Badge tone={r.percentage >= 60 ? "green" : r.percentage >= 40 ? "amber" : "rose"}>{r.percentage}%</Badge></div>
              <div className="text-xs text-slate-500">#{r.id} · {r.student_name}</div>
            </button>))}
        </Card>
        {sel && (
          <Card className="p-6 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-white">{sel.exam_name}</h2>
                <p className="text-xs text-slate-400">{sel.student_name} · {sel.created_at?.slice(0, 19).replace("T", " ")}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => downloadReport(sel.evaluation_id, "json")}><Download size={14} /> JSON</Button>
                <Button size="sm" variant="outline" onClick={() => downloadReport(sel.evaluation_id, "csv")}><Download size={14} /> CSV</Button>
                <Button size="sm" onClick={() => downloadReport(sel.evaluation_id, "pdf")}><Download size={14} /> PDF</Button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[["Total", `${sel.summary.total_score} / ${sel.summary.max_marks}`],
                ["Percentage", `${sel.summary.percentage}%`],
                ["Confidence", `${Math.round(sel.summary.overall_confidence * 100)}%`]].map(([l, v]) => (
                <div key={l} className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                  <div className="text-xs text-slate-400">{l}</div><div className="text-lg font-semibold text-white">{v}</div>
                </div>))}
            </div>
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500 border-b border-white/10">
                <th className="py-2">Q</th><th>Marks</th><th>%</th><th>Coverage</th><th>Relevance</th><th>Sentiment</th></tr></thead>
              <tbody>
                {sel.questions.map((q) => (
                  <tr key={q.question_id} className="border-b border-white/5 cursor-pointer hover:bg-white/5" onClick={() => onOpen("results", sel.evaluation_id)}>
                    <td className="py-2 text-slate-400">Q{q.question_id}</td>
                    <td>{q.final_score} / {q.max_marks}</td>
                    <td>{q.percentage}%</td>
                    <td>{q.concepts_covered}/{q.concept_results.length}</td>
                    <td>{Math.round(q.quality.semantic_relevance * 100)}%</td>
                    <td><Badge tone={sentTone(q.sentiment.label)}>{q.sentiment.label}</Badge></td>
                  </tr>))}
              </tbody>
            </table>
            <p className="text-xs text-slate-500">{sel.notice}</p>
          </Card>)}
      </div>
    </div>);
}
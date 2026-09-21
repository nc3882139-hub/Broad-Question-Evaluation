import { Files, ListOrdered, Percent, Play, Target } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./api";
import { ColumnChart, Donut, HBars } from "./charts";
import { Badge, Button, Card, Stat } from "./ui";

const SENT_COLORS = { positive: "#34d399", neutral: "#60a5fa", negative: "#fb7185" };

export default function Dashboard({ onNavigate }) {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [demoError, setDemoError] = useState("");
  const [demoPending, setDemoPending] = useState(false);
  useEffect(() => {
    api.stats().then(setStats).catch(() => {});
    api.evaluations().then(setRecent).catch(() => {});
  }, []);
  async function runDemo() {
    setDemoError(""); setDemoPending(true);
    try { await api.demo(); onNavigate("evaluate"); }
    catch (e) { setDemoError(e.message || "Could not start demo evaluation."); }
    finally { setDemoPending(false); }
  }
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Dashboard</h1>
        <p className="text-sm text-slate-400">Aggregated performance across all evaluated answer sheets.</p>
      </div>
      {stats?.total_sheets === 0 && <Card className="p-5 border-violet-500/30 flex flex-wrap items-center justify-between gap-3">
        <div><h2 className="font-medium text-white">Ready for the live demo?</h2><p className="text-sm text-slate-400">Run five seeded answer quality examples in seconds.</p></div>
        <Button size="sm" onClick={runDemo} disabled={demoPending}><Play size={14} /> {demoPending ? "Starting…" : "Run demo evaluation"}</Button>
        {demoError && <p className="w-full text-sm text-rose-300">{demoError}</p>}
      </Card>}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <Stat icon={Files} label="Answer sheets evaluated" value={stats?.total_sheets ?? "—"} />
        <Stat icon={Percent} label="Average score" value={stats ? `${stats.average_score_pct}%` : "—"} tone="green" />
        <Stat icon={Target} label="Avg concept coverage" value={stats ? `${Math.round(stats.average_concept_coverage * 100)}%` : "—"} tone="blue" />
        <Stat icon={ListOrdered} label="Questions analyzed" value={stats?.total_questions ?? "—"} />
        <Stat icon={Percent} label="Avg semantic relevance" value={stats ? `${Math.round(stats.average_semantic_relevance * 100)}%` : "—"} tone="amber" />
      </div>
      <div className="grid lg:grid-cols-3 gap-4">
        <Card className="p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Score distribution</h3>
          {stats ? <ColumnChart data={Object.entries(stats.score_distribution).map(([label, value]) => ({ label, value }))} />
                 : <p className="text-slate-500 text-sm">No data yet.</p>}
        </Card>
        <Card className="p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Sentiment distribution <span className="text-slate-500 font-normal">(informational)</span></h3>
          {stats ? <Donut segments={Object.entries(stats.sentiment_distribution).map(([label, value]) => ({ label, value, color: SENT_COLORS[label] || "#94a3b8" }))} />
                 : <p className="text-slate-500 text-sm">No data yet.</p>}
        </Card>
        <Card className="p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Question-wise performance</h3>
          {stats?.question_performance?.length
            ? <HBars data={stats.question_performance.map((q) => ({ label: q.label, value: q.avg_pct }))} max={100} suffix="%" color="bg-blue-500" />
            : <p className="text-slate-500 text-sm">No data yet.</p>}
        </Card>
      </div>
      <Card className="p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-slate-300">Recent evaluations</h3>
          <button className="text-xs text-violet-300 hover:text-violet-200" onClick={() => onNavigate("evaluate")}>+ New evaluation</button>
        </div>
        {recent.length === 0 ? (
          <p className="text-slate-500 text-sm">No evaluations yet — upload an answer sheet or run the demo from the Evaluate page.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-slate-500 border-b border-white/10">
              <th className="py-2">#</th><th>Exam</th><th>Student</th><th>Qs</th><th>Score</th><th>Date</th></tr></thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.id} className="border-b border-white/5 hover:bg-white/5 cursor-pointer" onClick={() => onNavigate("results", r.id)}>
                  <td className="py-2 text-slate-400">{r.id}</td>
                  <td className="pr-2">{r.exam_name}</td>
                  <td>{r.student_name}</td>
                  <td>{r.questions}</td>
                  <td><Badge tone={r.percentage >= 60 ? "green" : r.percentage >= 40 ? "amber" : "rose"}>{r.percentage}%</Badge></td>
                  <td className="text-slate-500 text-xs">{(r.created_at || "").slice(0, 16).replace("T", " ")}</td>
                </tr>))}
            </tbody>
          </table>)}
      </Card>
    </div>);
}
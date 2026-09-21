import { BookOpenCheck, Database, FileSearch, FileText, GraduationCap, HeartPulse,
         LayoutDashboard, Settings, ShieldAlert, UploadCloud } from "lucide-react";
import { useState } from "react";
import Dashboard from "./Dashboard";
import DatasetModel from "./pages/DatasetModel";
import Evaluate from "./pages/Evaluate";
import Reports from "./pages/Reports";
import Results from "./pages/Results";
import Rubrics from "./pages/Rubrics";
import SentimentPage from "./pages/Sentiment";
import SettingsPage from "./pages/Settings";

const NAV = [
  ["dashboard", "Dashboard", LayoutDashboard],
  ["evaluate", "Upload & Evaluate", UploadCloud],
  ["results", "Evaluation Results", FileSearch],
  ["rubrics", "Rubric Editor", BookOpenCheck],
  ["sentiment", "Sentiment Analysis", HeartPulse],
  ["reports", "Reports", FileText],
  ["data", "Dataset & Model", Database],
  ["settings", "Settings", Settings],
];

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [evalId, setEvalId] = useState(null);
  const go = (p, id) => { if (id !== undefined) setEvalId(id); setPage(p); };
  return (
    <div className="app-bg min-h-screen flex text-slate-200">
      <aside className="hidden lg:flex w-60 shrink-0 flex-col gap-1 p-4 m-3 mr-0 glass rounded-2xl">
        <div className="flex items-center gap-2.5 px-2 py-3 mb-2">
          <div className="rounded-xl bg-gradient-to-br from-violet-500 to-blue-600 p-2 shadow-lg shadow-violet-900/40">
            <GraduationCap size={20} className="text-white" />
          </div>
          <div>
            <div className="font-semibold text-white leading-tight">EduGrade AI</div>
            <div className="text-[10px] text-slate-400">Answer Sheet Evaluation</div>
          </div>
        </div>
        {NAV.map(([id, label, Icon]) => (
          <button key={id} onClick={() => go(id)}
            className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all ${page === id ? "bg-violet-600/20 text-violet-200 border border-violet-500/30" : "text-slate-400 hover:text-white hover:bg-white/5 border border-transparent"}`}>
            <Icon size={16} /> {label}
          </button>))}
        <div className="mt-auto text-[10px] leading-relaxed text-slate-500 p-2 flex gap-1.5">
          <ShieldAlert size={30} className="shrink-0 text-amber-500/70" />
          AI evaluation is assistive and must be reviewed by a teacher before official grading.
        </div>
      </aside>
      <main className="flex-1 min-w-0 p-3 md:p-6 overflow-x-hidden">
        {page === "dashboard" && <Dashboard onNavigate={go} />}
        {page === "evaluate" && <Evaluate onEvaluated={(id) => go("results", id)} />}
        {page === "results" && <Results evaluationId={evalId} onNavigate={go} />}
        {page === "rubrics" && <Rubrics />}
        {page === "sentiment" && <SentimentPage />}
        {page === "reports" && <Reports onOpen={go} />}
        {page === "data" && <DatasetModel />}
        {page === "settings" && <SettingsPage />}
      </main>
    </div>);
}
import { Database, Play } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api";
import { Badge, Button, Card } from "../ui";

const TREE = `data/
├── raw/          uploaded answer sheets (PDF/images)
├── processed/    OCR output + segmented Q/A JSON
├── unlabeled/    JSONL/TXT for self-supervised pretraining
├── sentiment/    labeled CSV/JSONL:  text,label
├── grading/      CSV: question_id,question,answer,max_marks,score
└── rubrics/      question-specific rubric JSON`;

const SOURCES = [
  ["ASAP / ASAP-SAS", "Automated Student Assessment Prize — short-answer scoring (The Hewlett Foundation, via Kaggle)."],
  ["SciEntsBank", "SemEval-2013 Task 3 student response assessment corpus."],
  ["SemEval student-response datasets", "SemEval shared tasks on short-answer grading."],
  ["HP:SAS", "Hewlett short-answer scoring dataset."],
  ["EngSAF", "Engineering Short Answer Feedback — use where licensing permits."],
];

export default function DatasetModel() {
  const [health, setHealth] = useState(null);
  const [job, setJob] = useState(null);
  const [log, setLog] = useState("");
  useEffect(() => { api.health().then(setHealth).catch(() => {}); }, []);
  useEffect(() => {
    if (!job) return;
    const t = setInterval(async () => {
      const s = await api.trainStatus(job);
      setLog(s.log_tail);
      if (s.status !== "running") clearInterval(t);
    }, 1500);
    return () => clearInterval(t);
  }, [job]);
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold text-white">Dataset & Model</h1>
        <p className="text-sm text-slate-400">Data layout, active models, and training launchpad.</p>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <Card className="p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2"><Database size={15} /> Data layout</h3>
          <pre className="text-xs text-slate-400 whitespace-pre-wrap">{TREE}</pre>
          <h4 className="text-xs font-medium text-slate-400 mt-4 mb-1">Legal dataset sources (do not commit copyrighted data)</h4>
          <ul className="text-xs text-slate-400 list-disc list-inside space-y-1">
            {SOURCES.map(([n, d]) => <li key={n}><span className="text-slate-300">{n}</span> — {d}</li>)}
          </ul>
        </Card>
        <Card className="p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-3">Active models & config</h3>
          {health ? (
            <div className="space-y-2 text-xs">
              {[["Embedding backend", health.models.embedding_backend], ["Embedding model", health.models.embedding_model],
                ["Sentiment backend", health.models.sentiment_backend], ["Sentiment model", health.models.sentiment_model],
                ["OCR engine", health.models.ocr_engine], ["Final mode", health.grading.final_mode],
                ["Weights", `${health.grading.weights.semantic} / ${health.grading.weights.keyword} / ${health.grading.weights.contextual}`]]
                .map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-3 border-b border-white/5 pb-1.5">
                    <span className="text-slate-500">{k}</span><span className="text-slate-200 text-right break-all">{String(v)}</span>
                  </div>))}
            </div>
          ) : <p className="text-slate-500 text-sm">Loading…</p>}
          <div className="flex gap-2 mt-4">
            <Button size="sm" variant="outline" onClick={() => api.train("self_supervised").then((r) => { setJob(r.job_id); setLog(""); })}>
              <Play size={13} /> Train MLM (Phase 3)
            </Button>
            <Button size="sm" variant="outline" onClick={() => api.train("sentiment").then((r) => { setJob(r.job_id); setLog(""); })}>
              <Play size={13} /> Fine-tune sentiment (Phase 4)
            </Button>
          </div>
          {job && (
            <div className="mt-3">
              <Badge tone="violet">training job {job}</Badge>
              <pre className="mt-2 text-[10px] text-slate-500 max-h-40 overflow-y-auto whitespace-pre-wrap bg-black/30 rounded-lg p-2">{log || "starting…"}</pre>
            </div>)}
        </Card>
      </div>
      <Card className="p-5 text-xs text-slate-400">
        The prototype runs entirely on pretrained models — training is optional. Place research datasets in
        <span className="text-slate-200"> data/</span> and run the scripts in <span className="text-slate-200">training/</span> and
        <span className="text-slate-200"> evaluation/</span> for MAE / RMSE / Pearson / Spearman / F1 comparisons
        (keyword vs TF-IDF vs embedding vs hybrid).
      </Card>
    </div>);
}
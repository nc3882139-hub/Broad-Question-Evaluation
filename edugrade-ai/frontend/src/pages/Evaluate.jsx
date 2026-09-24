import { AlertTriangle, CheckCircle2, ClipboardPaste, Loader2, Sparkles, UploadCloud } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Badge, Button, Card, Input, Textarea } from "../ui";

export default function Evaluate({ onEvaluated }) {
  const [meta, setMeta] = useState(null);
  const [textMode, setTextMode] = useState(false);
  const [rawText, setRawText] = useState("");
  const [student, setStudent] = useState("");
  const [exam, setExam] = useState("");
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [drag, setDrag] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!job?.job_id) return;
    const t = setInterval(async () => {
      try {
        const s = await api.status(job.job_id);
        setJob(s);
        if (s.status === "done") { clearInterval(t); onEvaluated(s.result.evaluation_id); }
        if (s.status === "error") { clearInterval(t); setError(s.error || "Processing failed."); }
      } catch (e) { clearInterval(t); setError(String(e.message || e)); }
    }, 1000);
    return () => clearInterval(t);
  }, [job?.job_id]);

  const start = (payload) => {
    setError("");
    setJob({ job_id: null, pending: payload, status: "running", stage_index: 0, progress: 0,
             stages: ["Uploading", "Reading document", "Extracting questions", "Analyzing answers",
                      "Checking key concepts", "Calculating marks", "Analyzing sentiment", "Generating report"]
                      .map((l) => ({ label: l, status: "pending" })) });
    (payload.file_id ? Promise.resolve(payload) : Promise.resolve(payload))
      .then((p) => api.evaluate(p))
      .then((r) => setJob((j) => ({ ...j, job_id: r.job_id })))
      .catch((e) => { setError(String(e.message || e)); setJob(null); });
  };

  async function handleFile(f) {
    setError(""); setMeta(null);
    try {
      const up = await api.upload(f);
      setMeta(up);
      start({ file_id: up.file_id, student_name: student || "Unknown Student", exam_name: exam || f.name });
    } catch (e) { setError(String(e.message || e)); if (inputRef.current) inputRef.current.value = ""; }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold text-white">Upload Answer Sheet</h1>
        <p className="text-sm text-slate-400">PDF / JPG / JPEG / PNG · multi-page supported · questions must be numbered (1., Q1), Question 1 …).</p>
      </div>

      {error && <Card className="p-4 border-rose-500/30 flex items-center gap-3 text-sm text-rose-300"><AlertTriangle size={18} /> {error}</Card>}

      {!job && (
        <Card className="p-6 space-y-4">
          <div className="grid sm:grid-cols-2 gap-3">
            <Input placeholder="Student name (optional)" value={student} onChange={(e) => setStudent(e.target.value)} />
            <Input placeholder="Exam name (optional)" value={exam} onChange={(e) => setExam(e.target.value)} />
          </div>
          <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
               onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
               onClick={() => inputRef.current?.click()}
               className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-all ${drag ? "border-violet-400 bg-violet-500/10" : "border-white/15 hover:border-violet-400/50 hover:bg-white/5"}`}>
            <UploadCloud className="mx-auto text-violet-300 mb-3" size={36} />
            <p className="text-slate-200 text-sm">Drag & drop an answer sheet here, or click to browse</p>
            <p className="text-xs text-slate-500 mt-1">Handwritten sheets work best as clear, well-lit scans</p>
            <input ref={inputRef} type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden"
                   onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])} />
          </div>
          {meta && (
            <div className="flex flex-wrap gap-2 text-xs">
              <Badge tone="violet">{meta.filename}</Badge>
              <Badge tone="blue">{meta.pages} page(s)</Badge>
              <Badge tone="green">Uploaded ✓</Badge>
              <Badge tone="amber">OCR / parsing queued</Badge>
              {meta.warnings?.map((warning) => <Badge key={warning} tone="rose">{warning}</Badge>)}
            </div>)}
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-white/10">
            <Button variant="outline" size="sm" onClick={() => setTextMode(!textMode)}>
              <ClipboardPaste size={14} /> {textMode ? "Hide" : "Paste text instead"}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => api.demo().then((r) => setJob({ job_id: r.job_id, status: "running", stage_index: 0, progress: 0,
              stages: ["Uploading", "Reading document", "Extracting questions", "Analyzing answers", "Checking key concepts", "Calculating marks", "Analyzing sentiment", "Generating report"].map((l) => ({ label: l, status: "pending" })) })).catch((e) => setError(e.message || "Could not start demo evaluation."))}
              disabled={!!job}
              className="text-violet-300">
              <Sparkles size={14} /> Run demo (5 APJ Abdul Kalam answers)
            </Button>
          </div>
          {textMode && (
            <div className="space-y-2">
              <Textarea rows={8} placeholder={"1. Explain photosynthesis.\nPhotosynthesis is the process by which…\n\n2. Write a short note on democracy.\nDemocracy is…"}
                        value={rawText} onChange={(e) => setRawText(e.target.value)} />
              <Button size="sm" onClick={() => rawText.trim() && start({ raw_text: rawText, student_name: student || "Unknown Student", exam_name: exam || "Pasted text" })}>
                Evaluate pasted text
              </Button>
            </div>)}
        </Card>)}

      {job && (
        <Card className="p-6 space-y-3">
          <div className="flex items-center gap-2 text-violet-300">
            <Loader2 className="animate-spin" size={18} />
            <span className="text-sm">{job.message || "Processing…"}</span>
          </div>
          {job.stages.map((s, i) => (
            <div key={i} className="flex items-center gap-3 text-sm">
              {s.status === "done" ? <CheckCircle2 className="text-emerald-400" size={16} />
               : s.status === "active" ? <Loader2 className="animate-spin text-violet-400" size={16} />
               : <div className="w-4 h-4 rounded-full border border-white/20" />}
              <span className={s.status === "pending" ? "text-slate-500" : "text-slate-200"}>
                {s.label}{s.status === "active" ? "…" : ""}
              </span>
            </div>))}
          <div className="h-1.5 rounded-full bg-white/10">
            <div className="h-full bg-violet-500 rounded-full transition-all duration-500" style={{ width: `${Math.round((job.progress || 0) * 100)}%` }} />
          </div>
        </Card>)}
    </div>);
}
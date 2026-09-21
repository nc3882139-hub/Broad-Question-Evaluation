import { useEffect, useState } from "react";
import { api } from "../api";
import { Card } from "../ui";

export default function SettingsPage() {
  const [h, setH] = useState(null);
  useEffect(() => { api.health().then(setH).catch(() => {}); }, []);
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold text-white">Settings</h1>
        <p className="text-sm text-slate-400">Effective configuration (edit <code className="text-violet-300">.env</code> and restart the backend to change).</p>
      </div>
      <Card className="p-6">
        {h ? (
          <pre className="text-xs text-slate-300 whitespace-pre-wrap">{JSON.stringify(h, null, 2)}</pre>
        ) : <p className="text-slate-500 text-sm">Loading…</p>}
      </Card>
      <Card className="p-5 text-sm text-slate-400 space-y-2">
        <p><span className="text-slate-200">Swappable components:</span> OCR engine, embedding model, sentiment model, and grading mode are all configured via environment variables — no code changes needed.</p>
        <p><span className="text-slate-200">Academic integrity:</span> {h?.notice}</p>
      </Card>
    </div>);
}
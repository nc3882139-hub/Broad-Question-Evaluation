import { HeartPulse, Info } from "lucide-react";
import { useState } from "react";
import { api } from "../api";
import { Badge, Button, Card, Progress, Textarea } from "../ui";

const tone = (l) => (l === "positive" ? "green" : l === "negative" ? "rose" : "blue");

export default function SentimentPage() {
  const [text, setText] = useState("");
  const [res, setRes] = useState(null);
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-semibold text-white flex items-center gap-2"><HeartPulse className="text-rose-300" /> Sentiment / Emotion Analysis</h1>
        <p className="text-sm text-slate-400">A fully separate NLP pipeline that analyzes student answers for emotional signals.</p>
      </div>
      <Card className="p-4 border-blue-500/30 flex gap-3 text-sm text-blue-200">
        <Info size={18} className="shrink-0 mt-0.5" />
        Sentiment analysis is informational and does not influence academic marks. It never adds or subtracts score.
      </Card>
      <Card className="p-6 space-y-3">
        <Textarea rows={5} placeholder="Paste a student answer to analyze…" value={text} onChange={(e) => setText(e.target.value)} />
        <Button size="sm" onClick={() => api.sentiment(text).then(setRes)} disabled={!text.trim()}>Analyze sentiment</Button>
        {res && (
          <div className="space-y-3 pt-3 border-t border-white/10">
            <div className="flex items-center gap-3">
              <Badge tone={tone(res.label)}>{res.label}</Badge>
              <span className="text-xs text-slate-400">confidence {Math.round(res.confidence * 100)}% · backend: {res.backend}</span>
            </div>
            {Object.entries(res.probabilities).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 text-xs">
                <span className="w-16 text-slate-400">{k}</span>
                <Progress value={v * 100} tone={k === "positive" ? "green" : k === "negative" ? "rose" : "blue"} />
                <span className="w-10 text-right text-slate-400">{Math.round(v * 100)}%</span>
              </div>))}
            <div className="grid grid-cols-3 gap-3 pt-2">
              {Object.entries(res.indicators).map(([k, v]) => (
                <div key={k} className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                  <div className="text-xs text-slate-400 capitalize">{k}</div>
                  <div className="text-lg font-semibold text-white">{Math.round(v * 100)}%</div>
                </div>))}
            </div>
          </div>)}
      </Card>
      <Card className="p-5 text-sm text-slate-400">
        Per-question sentiment for every evaluation appears on the <span className="text-slate-200">Evaluation Results</span> page and in exported reports.
        Indicators: <span className="text-slate-300">uncertainty</span> (hedging language), <span className="text-slate-300">frustration</span> (difficulty/stuck markers),
        <span className="text-slate-300"> engagement</span> (elaboration depth + length).
      </Card>
    </div>);
}
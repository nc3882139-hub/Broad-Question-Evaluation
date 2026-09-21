export function HBars({ data, max, color = "bg-violet-500", suffix = "" }) {
  const m = max || Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="space-y-2.5">
      {data.map((d, i) => (
        <div key={i}>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span className="truncate pr-2">{d.label}</span>
            <span className="text-slate-200">{d.value}{suffix}</span>
          </div>
          <div className="h-2 rounded-full bg-white/10">
            <div className={`h-full rounded-full ${color}`} style={{ width: `${(d.value / m) * 100}%` }} />
          </div>
        </div>))}
    </div>);
}

export function Donut({ segments, size = 150, centerLabel }) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  const r = size / 2 - 12, c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="flex items-center gap-6">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="14" />
        {segments.map((s, i) => {
          if (!total) return null;
          const len = (s.value / total) * c;
          const el = <circle key={i} cx={size / 2} cy={size / 2} r={r} fill="none" stroke={s.color} strokeWidth="14" strokeDasharray={`${len} ${c - len}`} strokeDashoffset={-offset} />;
          offset += len;
          return el;
        })}
      </svg>
      <div className="space-y-1.5">
        {centerLabel && <div className="text-2xl font-semibold text-white mb-1">{centerLabel}</div>}
        {segments.map((s, i) => (
          <div key={i} className="flex items-center gap-2 text-xs text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
            {s.label} — {s.value}
          </div>))}
      </div>
    </div>);
}

export function ColumnChart({ data, height = 170 }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="flex items-end gap-3" style={{ height }}>
      {data.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center justify-end gap-1 h-full">
          <div className="text-[10px] text-slate-400">{d.value}</div>
          <div className="w-full rounded-t-lg bg-gradient-to-t from-violet-700 to-violet-400 transition-all" style={{ height: `${(d.value / max) * 78}%` }} />
          <div className="text-[10px] text-slate-500 truncate w-full text-center">{d.label}</div>
        </div>))}
    </div>);
}
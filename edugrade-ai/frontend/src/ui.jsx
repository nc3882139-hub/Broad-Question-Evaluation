import clsx from "clsx";
export const cx = clsx;

export function Card({ className, children, ...p }) {
  return <div className={cx("glass rounded-2xl shadow-xl", className)} {...p}>{children}</div>;
}

export function Button({ className, variant = "primary", size = "md", ...p }) {
  const v = {
    primary: "bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/40",
    ghost: "hover:bg-white/10 text-slate-200",
    outline: "border border-white/15 text-slate-300 hover:border-violet-400/60 hover:text-white",
    danger: "bg-rose-600/90 hover:bg-rose-500 text-white",
  }[variant];
  const s = { sm: "px-2.5 py-1.5 text-xs", md: "px-4 py-2 text-sm", lg: "px-5 py-2.5 text-sm" }[size];
  return <button className={cx("inline-flex items-center gap-2 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed", v, s, className)} {...p} />;
}

export function Badge({ tone = "slate", children, className }) {
  const t = {
    green: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    amber: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    rose: "bg-rose-500/15 text-rose-300 border-rose-500/30",
    violet: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    blue: "bg-blue-500/15 text-blue-300 border-blue-500/30",
    slate: "bg-white/5 text-slate-300 border-white/10",
  }[tone];
  return <span className={cx("inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium", t, className)}>{children}</span>;
}

export function Progress({ value, tone = "violet", className }) {
  const bar = { violet: "bg-violet-500", green: "bg-emerald-500", amber: "bg-amber-500", rose: "bg-rose-500", blue: "bg-blue-500" }[tone];
  return (
    <div className={cx("h-2 w-full rounded-full bg-white/10 overflow-hidden", className)}>
      <div className={cx("h-full rounded-full transition-all duration-700", bar)} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>);
}

export function Input({ className, ...p }) {
  return <input className={cx("w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm placeholder:text-slate-500 focus:outline-none focus:border-violet-400/60", className)} {...p} />;
}

export function Textarea({ className, ...p }) {
  return <textarea className={cx("w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm placeholder:text-slate-500 focus:outline-none focus:border-violet-400/60", className)} {...p} />;
}

export function Stat({ label, value, icon: Icon, tone = "violet" }) {
  const t = { violet: "bg-violet-500/15 text-violet-300", green: "bg-emerald-500/15 text-emerald-300", blue: "bg-blue-500/15 text-blue-300", amber: "bg-amber-500/15 text-amber-300" }[tone];
  return (
    <Card className="p-4 flex items-center gap-4">
      {Icon && <div className={cx("rounded-xl p-2.5", t)}><Icon size={20} /></div>}
      <div className="min-w-0">
        <div className="text-xs text-slate-400">{label}</div>
        <div className="text-xl font-semibold text-white truncate">{value}</div>
      </div>
    </Card>);
}
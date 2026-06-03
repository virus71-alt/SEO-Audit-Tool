export function ScoreCard({ label, value }: { label: string; value: number | null }) {
  const v = value ?? 0;
  const color = v >= 80 ? "text-emerald-500" : v >= 60 ? "text-amber-500" : "text-rose-500";
  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 p-5 bg-white dark:bg-slate-900 text-center transition hover:shadow-lg hover:-translate-y-0.5">
      <div className={`text-4xl font-bold ${color}`}>{v.toFixed(0)}</div>
      <div className="mt-1 text-xs uppercase tracking-wider text-slate-500">{label}</div>
    </div>
  );
}

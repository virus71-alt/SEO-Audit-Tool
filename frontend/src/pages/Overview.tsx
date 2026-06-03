import { useEffect, useState } from "react";
import { createAudit, getAudit, listAudits, type Audit, type AuditDetail } from "../api";
import { ScoreCard } from "../components/ScoreCard";
import { CategoryBars, SeverityPie } from "../components/Charts";

export default function Overview() {
  const [audits, setAudits] = useState<Audit[]>([]);
  const [selected, setSelected] = useState<AuditDetail | null>(null);
  const [url, setUrl] = useState("https://example.com");
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const list = await listAudits().catch(() => []);
    setAudits(list);
    if (list[0]) setSelected(await getAudit(list[0].id));
  };

  useEffect(() => {
    refresh();
  }, []);

  const start = async () => {
    setBusy(true);
    try {
      const a = await createAudit(url);
      await refresh();
      setSelected(await getAudit(a.id));
    } finally {
      setBusy(false);
    }
  };

  const sevData = selected
    ? Object.entries(selected.summary?.issues_by_severity || {}).map(
        ([name, value]) => ({ name, value: value as number }),
      )
    : [];

  const catData = selected
    ? [
        { category: "Technical", score: selected.technical_score ?? 0 },
        { category: "On-Page", score: selected.onpage_score ?? 0 },
        { category: "Performance", score: selected.performance_score ?? 0 },
        { category: "Content", score: selected.content_score ?? 0 },
        { category: "Mobile", score: selected.mobile_score ?? 0 },
      ]
    : [];

  return (
    <div>
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 p-5 bg-white dark:bg-slate-900 flex flex-wrap gap-3 items-center">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="flex-1 min-w-[280px] rounded-lg border border-slate-300 dark:border-slate-700 bg-transparent px-4 py-2"
        />
        <button
          onClick={start}
          disabled={busy}
          className="rounded-lg bg-brand-600 text-white px-5 py-2 font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          {busy ? "Starting…" : "Run audit"}
        </button>
      </div>

      {selected && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mt-6">
            <ScoreCard label="Overall" value={selected.overall_score} />
            <ScoreCard label="Technical" value={selected.technical_score} />
            <ScoreCard label="On-Page" value={selected.onpage_score} />
            <ScoreCard label="Performance" value={selected.performance_score} />
            <ScoreCard label="Content" value={selected.content_score} />
            <ScoreCard label="Mobile" value={selected.mobile_score} />
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 p-5 bg-white dark:bg-slate-900">
              <div className="font-semibold mb-3">Issues by severity</div>
              <SeverityPie data={sevData} />
            </div>
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 p-5 bg-white dark:bg-slate-900">
              <div className="font-semibold mb-3">Category scores</div>
              <CategoryBars data={catData} />
            </div>
          </div>
        </>
      )}

      <div className="mt-8">
        <div className="font-semibold mb-2">Recent audits</div>
        <ul className="space-y-2">
          {audits.map((a) => (
            <li
              key={a.id}
              className="rounded-lg border border-slate-200 dark:border-slate-800 px-4 py-2 flex justify-between cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800"
              onClick={async () => setSelected(await getAudit(a.id))}
            >
              <span className="font-mono text-xs">{a.url}</span>
              <span className="text-xs text-slate-500">
                {a.status} · {a.overall_score?.toFixed(0) ?? "—"}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

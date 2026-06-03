import type { Issue } from "../api";

const colors: Record<string, string> = {
  critical: "bg-rose-600 text-white",
  high: "bg-rose-500 text-white",
  medium: "bg-amber-400 text-black",
  low: "bg-sky-500 text-white",
  info: "bg-slate-500 text-white",
};

export function IssueTable({ issues }: { issues: Issue[] }) {
  if (!issues.length) return <div className="text-slate-500 text-sm">No issues found.</div>;
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 dark:bg-slate-800">
          <tr>
            <th className="text-left p-3">Severity</th>
            <th className="text-left p-3">Issue</th>
            <th className="text-left p-3">URL</th>
            <th className="text-left p-3">Recommendation</th>
          </tr>
        </thead>
        <tbody>
          {issues.map((i) => (
            <tr key={i.id} className="border-t border-slate-200 dark:border-slate-800 align-top">
              <td className="p-3">
                <span className={`text-[10px] font-bold uppercase rounded px-2 py-0.5 ${colors[i.severity]}`}>
                  {i.severity}
                </span>
              </td>
              <td className="p-3">
                <div className="font-medium">{i.message}</div>
                {i.impact && <div className="text-xs text-slate-500 mt-1">{i.impact}</div>}
              </td>
              <td className="p-3 font-mono text-xs break-all">{i.url || "—"}</td>
              <td className="p-3 text-xs">{i.recommendation || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

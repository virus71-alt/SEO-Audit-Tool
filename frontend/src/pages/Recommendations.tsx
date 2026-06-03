import { IssueTable } from "../components/IssueTable";
import { useLatestAudit } from "./_useLatest";

const RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

export default function Recommendations() {
  const audit = useLatestAudit();
  const issues = [...(audit?.issues ?? [])]
    .sort((a, b) => (RANK[a.severity] ?? 9) - (RANK[b.severity] ?? 9))
    .slice(0, 50);
  return (
    <section>
      <h1 className="text-2xl font-bold mb-4">Top recommendations</h1>
      <IssueTable issues={issues} />
    </section>
  );
}

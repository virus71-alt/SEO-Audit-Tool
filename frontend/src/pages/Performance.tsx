import { IssueTable } from "../components/IssueTable";
import { useLatestAudit } from "./_useLatest";

export default function Performance() {
  const audit = useLatestAudit();
  const issues = (audit?.issues ?? []).filter((i) => i.category === "performance");
  return (
    <section>
      <h1 className="text-2xl font-bold mb-4">Performance</h1>
      <IssueTable issues={issues} />
    </section>
  );
}

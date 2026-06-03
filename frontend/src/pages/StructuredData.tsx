import { IssueTable } from "../components/IssueTable";
import { useLatestAudit } from "./_useLatest";

export default function StructuredData() {
  const audit = useLatestAudit();
  const issues = (audit?.issues ?? []).filter((i) => ["schema", "social"].includes(i.category));
  return (
    <section>
      <h1 className="text-2xl font-bold mb-4">Structured Data & Social</h1>
      <IssueTable issues={issues} />
    </section>
  );
}

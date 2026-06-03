import { IssueTable } from "../components/IssueTable";
import { useLatestAudit } from "./_useLatest";

export default function Technical() {
  const audit = useLatestAudit();
  const issues = (audit?.issues ?? []).filter((i) => ["technical", "links"].includes(i.category));
  return (
    <section>
      <h1 className="text-2xl font-bold mb-4">Technical SEO</h1>
      <IssueTable issues={issues} />
    </section>
  );
}

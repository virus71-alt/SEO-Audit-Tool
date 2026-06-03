import { IssueTable } from "../components/IssueTable";
import { useLatestAudit } from "./_useLatest";

export default function Links() {
  const audit = useLatestAudit();
  const issues = (audit?.issues ?? []).filter((i) => i.category === "links");
  return (
    <section>
      <h1 className="text-2xl font-bold mb-4">Links</h1>
      <IssueTable issues={issues} />
    </section>
  );
}

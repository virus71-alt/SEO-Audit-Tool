import { IssueTable } from "../components/IssueTable";
import { useLatestAudit } from "./_useLatest";

export default function Images() {
  const audit = useLatestAudit();
  const issues = (audit?.issues ?? []).filter((i) => i.category === "images");
  return (
    <section>
      <h1 className="text-2xl font-bold mb-4">Images</h1>
      <IssueTable issues={issues} />
    </section>
  );
}

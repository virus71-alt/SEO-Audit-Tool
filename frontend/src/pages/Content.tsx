import { IssueTable } from "../components/IssueTable";
import { useLatestAudit } from "./_useLatest";

export default function Content() {
  const audit = useLatestAudit();
  const issues = (audit?.issues ?? []).filter((i) => ["content", "onpage"].includes(i.category));
  return (
    <section>
      <h1 className="text-2xl font-bold mb-4">Content SEO</h1>
      <IssueTable issues={issues} />
    </section>
  );
}

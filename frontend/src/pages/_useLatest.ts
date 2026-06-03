import { useEffect, useState } from "react";
import { getAudit, listAudits, type AuditDetail } from "../api";

export function useLatestAudit() {
  const [audit, setAudit] = useState<AuditDetail | null>(null);
  useEffect(() => {
    (async () => {
      try {
        const list = await listAudits();
        if (list[0]) setAudit(await getAudit(list[0].id));
      } catch {}
    })();
  }, []);
  return audit;
}

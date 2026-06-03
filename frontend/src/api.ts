import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

export type Audit = {
  id: number;
  url: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  pages_crawled: number;
  overall_score: number | null;
  technical_score: number | null;
  onpage_score: number | null;
  performance_score: number | null;
  content_score: number | null;
  mobile_score: number | null;
  summary: any;
};

export type Issue = {
  id: number;
  code: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  category: string;
  url: string | null;
  message: string;
  impact: string | null;
  recommendation: string | null;
  example: string | null;
};

export type AuditDetail = Audit & { issues: Issue[]; pages: any[] };

export const listAudits = () => api.get<Audit[]>("/audits").then((r) => r.data);
export const getAudit = (id: number) => api.get<AuditDetail>(`/audits/${id}`).then((r) => r.data);
export const createAudit = (url: string, max_pages = 200, include_performance = true) =>
  api.post<Audit>("/audits", { url, max_pages, include_performance }).then((r) => r.data);

export const login = async (email: string, password: string) => {
  const form = new URLSearchParams({ username: email, password });
  const { data } = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  localStorage.setItem("token", data.access_token);
  return data;
};

export const register = (email: string, password: string) =>
  api.post("/auth/register", { email, password }).then((r) => r.data);

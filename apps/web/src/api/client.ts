const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export interface MeResponse {
  email: string;
  name?: string;
  picture?: string;
}

export interface EmailItem {
  id: string;
  threadId: string;
  from: string;
  subject: string;
  date: string;
  snippet: string;
  labels: string[];
  summary?: string;
  category?: string;
}

export interface DashboardSummary {
  totals: { emails: number };
  byCategory: Record<string, number>;
  digest: string;
  lastRunAt: string | null;
  today: { count: number; items: TodayEmailItem[] };
}

export interface TodayEmailItem {
  id?: string;
  from: string;
  subject: string;
  category?: string | null;
  summary: string;
}

export interface AgentRunResult {
  processed: number;
  digest: string;
  lastRunAt: string;
}

export interface LabelEntry {
  name: string;
  description?: string;
}

export interface LabelSettings {
  prefix: string;
  categorySubPrefix: string;
  categories: LabelEntry[];
}

export const api = {
  loginUrl: () => `${API_URL}/auth/login`,
  logoutUrl: () => `${API_URL}/auth/logout`,
  me: () => request<MeResponse>("/me"),
  getEmails: (limit: number) =>
    request<EmailItem[]>(`/emails?limit=${encodeURIComponent(limit)}`),
  getSummary: () => request<DashboardSummary>("/summary"),
  runAgents: (limit: number) =>
    request<AgentRunResult>("/agents/run", {
      method: "POST",
      body: JSON.stringify({ limit }),
    }),
  getLabelSettings: () => request<LabelSettings>("/settings/labels"),
  saveLabelSettings: (s: LabelSettings) =>
    request<LabelSettings>("/settings/labels", {
      method: "PUT",
      body: JSON.stringify(s),
    }),
  getGmailLabels: () =>
    request<{ labels: { id: string; name: string; type: string }[] }>(
      "/settings/gmail-labels"
    ),
};

// Shared API contract between FastAPI backend and React frontend.

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
}

export interface AgentRunResult {
  processed: number;
  digest: string;
  lastRunAt: string;
}

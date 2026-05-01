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

export interface AgentStepEvent {
  type: "step";
  node: string;
  label: string;
  status: "started" | "done";
  count?: number;
  digestPreview?: string;
  messagesLabeled?: number;
  labelsApplied?: number;
}

export interface AgentDoneEvent {
  type: "done";
  result: AgentRunResult;
}

export interface AgentErrorEvent {
  type: "error";
  message: string;
}

export type AgentStreamEvent =
  | AgentStepEvent
  | AgentDoneEvent
  | AgentErrorEvent;

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
  runAgentsStream: async (
    limit: number,
    onEvent: (e: AgentStreamEvent) => void,
    signal?: AbortSignal
  ): Promise<void> => {
    const res = await fetch(`${API_URL}/agents/run/stream`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ limit }),
      signal,
    });
    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => "");
      throw new ApiError(res.status, text || res.statusText);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const event = parseSSE(block);
        if (event) onEvent(event);
      }
    }
  },
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

function parseSSE(block: string): AgentStreamEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const raw of block.split("\n")) {
    const line = raw.trimEnd();
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
  }
  if (dataLines.length === 0) return null;
  let payload: unknown;
  try {
    payload = JSON.parse(dataLines.join("\n"));
  } catch {
    return null;
  }
  if (event === "step") return { type: "step", ...(payload as object) } as AgentStepEvent;
  if (event === "done") return { type: "done", result: payload as AgentRunResult };
  if (event === "error") return { type: "error", message: (payload as { message?: string })?.message ?? "Unknown error" };
  return null;
}

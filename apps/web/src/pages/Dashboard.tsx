import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import {
  api,
  type AgentStepEvent,
  type DashboardSummary,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";
import SummaryCards from "../components/SummaryCards";
import AgentRunButton from "../components/AgentRunButton";
import AgentProgress from "../components/AgentProgress";
import FetchCountControl, {
  loadStoredLimit,
} from "../components/FetchCountControl";

export default function Dashboard() {
  const { user } = useAuth();
  const [limit, setLimit] = useState<number>(() => loadStoredLimit(50));
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<AgentStepEvent[]>([]);
  const [progressError, setProgressError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const s = await api.getSummary();
      setSummary(s);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleRun() {
    setRunning(true);
    setError(null);
    setProgressError(null);
    setProgress([]);
    try {
      await api.runAgentsStream(limit, (ev) => {
        if (ev.type === "step") {
          setProgress((prev) => [...prev, ev]);
        } else if (ev.type === "error") {
          setProgressError(ev.message);
        }
      });
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Clean Mailbox</h1>
          <p className="text-sm text-slate-500">
            Signed in as {user?.email}
          </p>
        </div>
        <a
          href={api.logoutUrl()}
          className="text-sm text-slate-500 hover:text-slate-800"
        >
          Sign out
        </a>
      </header>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-xl bg-white p-4 shadow">
        <FetchCountControl
          value={limit}
          onChange={setLimit}
          disabled={running}
        />
        <div className="flex items-center gap-2">
          <Link
            to="/settings/labels"
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
          >
            Labels
          </Link>
          <AgentRunButton running={running} onClick={handleRun} />
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <AgentProgress events={progress} active={running} error={progressError} />

      <section>
        <SummaryCards summary={summary} />
      </section>
    </div>
  );
}

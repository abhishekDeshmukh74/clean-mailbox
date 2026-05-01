import type { AgentStepEvent } from "../api/client";

interface Props {
  events: AgentStepEvent[];
  active: boolean;
  error?: string | null;
}

export default function AgentProgress({ events, active, error }: Props) {
  if (!active && events.length === 0 && !error) return null;

  // Collapse step events: keep latest status per node, in original order.
  const order: string[] = [];
  const byNode = new Map<string, AgentStepEvent>();
  for (const e of events) {
    if (!byNode.has(e.node)) order.push(e.node);
    byNode.set(e.node, e);
  }

  return (
    <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold">Agent progress</h2>
        {active && (
          <span className="inline-flex items-center gap-2 text-xs text-slate-500">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            running
          </span>
        )}
      </div>
      <ol className="space-y-2">
        {order.map((node) => {
          const ev = byNode.get(node)!;
          const done = ev.status === "done";
          return (
            <li key={node} className="flex items-start gap-3 text-sm">
              <span
                className={
                  "mt-0.5 inline-flex h-5 w-5 flex-none items-center justify-center rounded-full text-xs " +
                  (done
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-sky-100 text-sky-700")
                }
                aria-hidden
              >
                {done ? "✓" : "…"}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-medium text-slate-800">{ev.label}</span>
                  <span className="text-xs text-slate-500">
                    {detailText(ev)}
                  </span>
                </div>
                {ev.digestPreview && (
                  <p className="mt-1 truncate text-xs text-slate-500">
                    {ev.digestPreview}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      {error && (
        <div className="mt-3 rounded-lg bg-red-50 p-2 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}

function detailText(ev: AgentStepEvent): string {
  if (ev.status === "started") return "in progress";
  const bits: string[] = [];
  if (typeof ev.count === "number") bits.push(`${ev.count}`);
  if (typeof ev.messagesLabeled === "number")
    bits.push(`${ev.messagesLabeled} msgs`);
  if (typeof ev.labelsApplied === "number")
    bits.push(`${ev.labelsApplied} labels`);
  return bits.join(" · ") || "done";
}

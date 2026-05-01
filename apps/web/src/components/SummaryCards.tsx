import type { DashboardSummary } from "../api/client";

interface Props {
  summary: DashboardSummary | null;
}

export default function SummaryCards({ summary }: Props) {
  if (!summary) {
    return (
      <div className="rounded-xl bg-white p-6 text-sm text-slate-500 shadow">
        No summary yet — run the agents to generate one.
      </div>
    );
  }

  const categoryEntries = Object.entries(summary.byCategory).sort(
    (a, b) => b[1] - a[1]
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
        <StatCard label="Emails" value={summary.totals.emails} />
        <StatCard
          label="Last run"
          value={
            summary.lastRunAt
              ? new Date(summary.lastRunAt).toLocaleString()
              : "—"
          }
        />
        <CategoryCard entries={categoryEntries} />
      </div>

      <TodayCard today={summary.today} />

      {summary.digest && (
        <div className="rounded-xl bg-white p-4 shadow">
          <div className="mb-2 text-sm font-semibold">Digest</div>
          <p className="whitespace-pre-wrap text-sm text-slate-700">
            {summary.digest}
          </p>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl bg-white p-4 shadow">
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}

function CategoryCard({ entries }: { entries: [string, number][] }) {
  return (
    <div className="rounded-xl bg-white p-4 shadow">
      <div className="text-xs uppercase tracking-wide text-slate-500">
        By category
      </div>
      {entries.length === 0 ? (
        <div className="mt-1 text-sm text-slate-500">—</div>
      ) : (
        <ul className="mt-2 space-y-1 text-sm">
          {entries.slice(0, 5).map(([k, v]) => (
            <li key={k} className="flex justify-between gap-2">
              <span className="truncate text-slate-700">{k}</span>
              <span className="font-medium tabular-nums">{v}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TodayCard({ today }: { today: DashboardSummary["today"] }) {
  return (
    <section className="rounded-xl bg-white p-4 shadow">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold">Today</h2>
        <span className="text-xs text-slate-500">
          {today.count} email{today.count === 1 ? "" : "s"}
        </span>
      </div>
      {today.count === 0 ? (
        <p className="text-sm text-slate-500">
          No emails received today yet.
        </p>
      ) : (
        <ul className="space-y-3">
          {today.items.map((item, i) => (
            <li
              key={item.id ?? i}
              className="border-l-2 border-slate-200 pl-3"
            >
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                {item.category && (
                  <span className="rounded bg-sky-50 px-1.5 py-0.5 font-medium text-sky-700">
                    {item.category}
                  </span>
                )}
                <span className="truncate">{item.from}</span>
              </div>
              <div className="mt-0.5 truncate text-sm font-medium text-slate-900">
                {item.subject || "(no subject)"}
              </div>
              <p className="mt-1 text-sm text-slate-600">{item.summary}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

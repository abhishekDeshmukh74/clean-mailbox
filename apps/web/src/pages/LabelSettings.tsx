import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import {
  api,
  type LabelEntry,
  type LabelSettings,
} from "../api/client";

function emptyEntry(): LabelEntry {
  return { name: "", description: "" };
}

export default function LabelSettingsPage() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState<LabelSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [gmailLabels, setGmailLabels] = useState<
    { id: string; name: string; type: string }[] | null
  >(null);
  const [gmailLoading, setGmailLoading] = useState(false);
  const [gmailError, setGmailError] = useState<string | null>(null);
  const [showSystem, setShowSystem] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .getLabelSettings()
      .then((s) => {
        if (!cancelled) setSettings(s);
      })
      .catch((e) => !cancelled && setError((e as Error).message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  async function loadGmailLabels() {
    setGmailLoading(true);
    setGmailError(null);
    try {
      const res = await api.getGmailLabels();
      setGmailLabels(
        [...res.labels].sort((a, b) => a.name.localeCompare(b.name))
      );
    } catch (e) {
      setGmailError((e as Error).message);
    } finally {
      setGmailLoading(false);
    }
  }

  function importGmailLabel(name: string) {
    if (!settings) return;
    const trimmed = name.trim();
    if (!trimmed) return;
    if (settings.categories.some((c) => c.name === trimmed)) return;
    update("categories", [
      ...settings.categories,
      { name: trimmed, description: "" },
    ]);
  }

  function importAllGmailLabels() {
    if (!settings || !gmailLabels) return;
    const existing = new Set(settings.categories.map((c) => c.name));
    const visible = gmailLabels.filter(
      (l) => showSystem || l.type === "user"
    );
    const additions: LabelEntry[] = visible
      .filter((l) => !existing.has(l.name))
      .map((l) => ({ name: l.name, description: "" }));
    if (additions.length === 0) return;
    update("categories", [...settings.categories, ...additions]);
  }

  function update<K extends keyof LabelSettings>(
    key: K,
    value: LabelSettings[K]
  ) {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  }

  function updateEntry(
    key: "categories",
    idx: number,
    patch: Partial<LabelEntry>
  ) {
    if (!settings) return;
    const next = settings[key].map((e, i) =>
      i === idx ? { ...e, ...patch } : e
    );
    update(key, next);
  }

  function addEntry(key: "categories") {
    if (!settings) return;
    update(key, [...settings[key], emptyEntry()]);
  }

  function removeEntry(key: "categories", idx: number) {
    if (!settings) return;
    update(
      key,
      settings[key].filter((_, i) => i !== idx)
    );
  }

  function move(
    key: "categories",
    idx: number,
    delta: -1 | 1
  ) {
    if (!settings) return;
    const list = [...settings[key]];
    const j = idx + delta;
    if (j < 0 || j >= list.length) return;
    [list[idx], list[j]] = [list[j], list[idx]];
    update(key, list);
  }

  async function save() {
    if (!settings) return;
    setSaving(true);
    setError(null);
    try {
      const cleaned: LabelSettings = {
        ...settings,
        categories: settings.categories
          .map((c) => ({ ...c, name: c.name.trim() }))
          .filter((c) => c.name),
      };
      const saved = await api.saveLabelSettings(cleaned);
      setSettings(saved);
      setSavedAt(new Date().toLocaleTimeString());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Label settings</h1>
          <p className="text-sm text-slate-500">
            Configure the categories the classifier agent will use.
          </p>
        </div>
        <Link
          to="/"
          className="text-sm text-slate-500 hover:text-slate-800"
        >
          ← Back to dashboard
        </Link>
      </header>

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && (
        <div className="mb-3 rounded bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {settings && (
        <div className="space-y-6 rounded-2xl bg-white p-6 shadow">
          <section>
            <h3 className="mb-2 text-sm font-semibold text-slate-700">
              Prefixes
            </h3>
            <p className="mb-2 text-xs text-slate-500">
              Final Gmail labels look like{" "}
              <code className="rounded bg-slate-100 px-1">
                {[
                  settings.prefix,
                  settings.categorySubPrefix,
                  settings.categories[0]?.name || "Work",
                ]
                  .filter(Boolean)
                  .join("/")}
              </code>
              . Leave any field blank to skip that segment.
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <LabeledInput
                label="Root prefix"
                value={settings.prefix}
                onChange={(v) => update("prefix", v)}
              />
              <LabeledInput
                label="Category sub-prefix"
                value={settings.categorySubPrefix}
                onChange={(v) => update("categorySubPrefix", v)}
              />
            </div>
          </section>

          <EntryListSection
            title="Categories"
            hint="Used by the classifier agent. Descriptions help the LLM decide."
            entries={settings.categories}
            onAdd={() => addEntry("categories")}
            onRemove={(i) => removeEntry("categories", i)}
            onChange={(i, patch) => updateEntry("categories", i, patch)}
            onMove={(i, d) => move("categories", i, d)}
          />

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-700">
                Import from Gmail
              </h3>
              <div className="flex items-center gap-2">
                {gmailLabels && gmailLabels.length > 0 && (
                  <label className="flex items-center gap-1 text-xs text-slate-600">
                    <input
                      type="checkbox"
                      checked={showSystem}
                      onChange={(e) => setShowSystem(e.target.checked)}
                    />
                    Show system
                  </label>
                )}
                {gmailLabels && gmailLabels.length > 0 && (
                  <button
                    type="button"
                    onClick={importAllGmailLabels}
                    className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                  >
                    Import all
                  </button>
                )}
                <button
                  type="button"
                  onClick={loadGmailLabels}
                  disabled={gmailLoading}
                  className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100 disabled:opacity-50"
                >
                  {gmailLoading
                    ? "Loading…"
                    : gmailLabels
                    ? "Refresh"
                    : "Fetch labels"}
                </button>
              </div>
            </div>
            <p className="mb-2 text-xs text-slate-500">
              Add your existing Gmail labels as categories. Click a label to
              add it; already-imported names are disabled. System labels (like
              INBOX, STARRED) are hidden by default.
            </p>
            {gmailError && (
              <div className="mb-2 rounded bg-red-50 p-2 text-xs text-red-700">
                {gmailError}
              </div>
            )}
            {gmailLabels && gmailLabels.length === 0 && (
              <p className="text-xs text-slate-400">
                No Gmail labels found.
              </p>
            )}
            {gmailLabels && gmailLabels.length > 0 && (() => {
              const visible = gmailLabels.filter(
                (l) => showSystem || l.type === "user"
              );
              if (visible.length === 0) {
                return (
                  <p className="text-xs text-slate-400">
                    No user-created labels. Toggle "Show system" to see
                    Gmail's built-in labels.
                  </p>
                );
              }
              return (
                <div className="flex flex-wrap gap-2">
                  {visible.map((l) => {
                    const already = settings.categories.some(
                      (c) => c.name === l.name
                    );
                    const isSystem = l.type !== "user";
                    return (
                      <button
                        key={l.id}
                        type="button"
                        onClick={() => importGmailLabel(l.name)}
                        disabled={already}
                        className={
                          "rounded-full border px-3 py-1 text-xs " +
                          (already
                            ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400"
                            : isSystem
                            ? "border-amber-300 bg-amber-50 text-amber-800 hover:border-amber-500"
                            : "border-slate-300 bg-white text-slate-700 hover:border-slate-500 hover:bg-slate-50")
                        }
                        title={
                          already
                            ? "Already added"
                            : isSystem
                            ? "System label — add as category"
                            : "Add as category"
                        }
                      >
                        {l.name}
                        {already && " ✓"}
                      </button>
                    );
                  })}
                </div>
              );
            })()}
          </section>

          <div className="flex items-center justify-end gap-3 pt-2">
            {savedAt && (
              <span className="text-xs text-slate-500">
                Saved at {savedAt}
              </span>
            )}
            <button
              type="button"
              onClick={() => navigate("/")}
              disabled={saving}
              className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 disabled:opacity-50"
            >
              Done
            </button>
            <button
              type="button"
              onClick={save}
              disabled={saving}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-600">
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
      />
    </label>
  );
}

function EntryListSection({
  title,
  hint,
  entries,
  onAdd,
  onRemove,
  onChange,
  onMove,
}: {
  title: string;
  hint: string;
  entries: LabelEntry[];
  onAdd: () => void;
  onRemove: (i: number) => void;
  onChange: (i: number, patch: Partial<LabelEntry>) => void;
  onMove: (i: number, delta: -1 | 1) => void;
}) {
  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        <button
          type="button"
          onClick={onAdd}
          className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
        >
          + Add
        </button>
      </div>
      <p className="mb-2 text-xs text-slate-500">{hint}</p>
      <ul className="space-y-2">
        {entries.map((entry, i) => (
          <li
            key={i}
            className="flex flex-wrap items-start gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2"
          >
            <input
              type="text"
              placeholder="name"
              value={entry.name}
              onChange={(e) => onChange(i, { name: e.target.value })}
              className="w-32 rounded border border-slate-300 bg-white px-2 py-1 text-sm"
            />
            <input
              type="text"
              placeholder="description (optional, helps the LLM)"
              value={entry.description ?? ""}
              onChange={(e) => onChange(i, { description: e.target.value })}
              className="min-w-[200px] flex-1 rounded border border-slate-300 bg-white px-2 py-1 text-sm"
            />
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => onMove(i, -1)}
                disabled={i === 0}
                className="rounded px-1.5 py-1 text-xs text-slate-500 hover:bg-slate-200 disabled:opacity-30"
                aria-label="Move up"
              >
                ↑
              </button>
              <button
                type="button"
                onClick={() => onMove(i, 1)}
                disabled={i === entries.length - 1}
                className="rounded px-1.5 py-1 text-xs text-slate-500 hover:bg-slate-200 disabled:opacity-30"
                aria-label="Move down"
              >
                ↓
              </button>
              <button
                type="button"
                onClick={() => onRemove(i)}
                className="rounded px-1.5 py-1 text-xs text-red-600 hover:bg-red-50"
                aria-label="Remove"
              >
                ✕
              </button>
            </div>
          </li>
        ))}
        {entries.length === 0 && (
          <li className="text-xs text-slate-400">
            No entries — add one above.
          </li>
        )}
      </ul>
    </section>
  );
}

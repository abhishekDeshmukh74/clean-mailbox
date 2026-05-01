import { useEffect, useState } from "react";

interface Props {
  value: number;
  onChange: (n: number) => void;
  disabled?: boolean;
}

const PRESETS = [10, 25, 50, 100, 200];
const MIN = 1;
const MAX = 500;
const STORAGE_KEY = "clean-mailbox.fetch-limit";

export function loadStoredLimit(fallback = 50): number {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return fallback;
    const n = Number.parseInt(raw, 10);
    if (Number.isFinite(n)) return clamp(n);
  } catch {
    // ignore
  }
  return fallback;
}

function clamp(n: number): number {
  if (!Number.isFinite(n)) return 50;
  return Math.max(MIN, Math.min(MAX, Math.floor(n)));
}

export default function FetchCountControl({ value, onChange, disabled }: Props) {
  const [text, setText] = useState(String(value));

  useEffect(() => {
    setText(String(value));
  }, [value]);

  function commit(n: number) {
    const c = clamp(n);
    onChange(c);
    try {
      localStorage.setItem(STORAGE_KEY, String(c));
    } catch {
      // ignore
    }
  }

  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-slate-600">Fetch</label>
      <input
        type="number"
        min={MIN}
        max={MAX}
        value={text}
        disabled={disabled}
        onChange={(e) => setText(e.target.value)}
        onBlur={() => commit(Number.parseInt(text, 10))}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit(Number.parseInt(text, 10));
        }}
        className="w-20 rounded-md border border-slate-300 px-2 py-1 text-sm"
      />
      <span className="text-sm text-slate-600">recent emails</span>
      <div className="ml-2 flex gap-1">
        {PRESETS.map((p) => (
          <button
            key={p}
            type="button"
            disabled={disabled}
            onClick={() => commit(p)}
            className={`rounded-md px-2 py-1 text-xs transition ${
              p === value
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

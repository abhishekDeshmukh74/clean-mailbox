interface Props {
  running: boolean;
  onClick: () => void;
}

export default function AgentRunButton({ running, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={running}
      className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-400"
    >
      {running ? "Running agents…" : "Run agents"}
    </button>
  );
}

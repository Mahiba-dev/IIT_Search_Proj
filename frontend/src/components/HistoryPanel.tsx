import type { SearchResult } from "../types";

interface HistoryPanelProps {
  results: SearchResult[];
  onSelect: (id: string) => void;
  activeId: string | null;
}

export default function HistoryPanel({ results, onSelect, activeId }: HistoryPanelProps) {
  if (results.length === 0) {
    return (
      <div className="p-4 text-xs text-slate-400">
        Your searches this session will appear here.
      </div>
    );
  }

  return (
    <div className="flex flex-col divide-y divide-slate-100">
      {[...results].reverse().map((r) => (
        <button
          key={r.id}
          onClick={() => onSelect(r.id)}
          className={`text-left px-4 py-3 text-sm hover:bg-slate-50 transition-colors ${
            activeId === r.id ? "bg-brand-50 border-l-2 border-brand-500" : "border-l-2 border-transparent"
          }`}
        >
          <p className="truncate text-slate-700 font-medium">{r.query}</p>
          <p className="mt-0.5 text-[11px] text-slate-400">
            {r.status === "rejected" ? "Rejected · " : r.status === "error" ? "Error · " : ""}
            {new Date(r.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </p>
        </button>
      ))}
    </div>
  );
}

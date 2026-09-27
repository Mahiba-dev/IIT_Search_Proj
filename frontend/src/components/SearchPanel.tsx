import { useState, type KeyboardEvent } from "react";
import type { SearchResult } from "../types";
import ResultCard from "./ResultCard";

interface SearchPanelProps {
  onSearch: (query: string) => void;
  loading: boolean;
  results: SearchResult[];
  onClear: () => void;
  scrollToId: string | null;
}

export default function SearchPanel({ onSearch, loading, results, onClear }: SearchPanelProps) {
  const [query, setQuery] = useState("");

  const submit = () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    onSearch(trimmed);
    setQuery("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") submit();
  };

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="px-6 pt-8 pb-4 sm:px-10">
        <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900">
          Explore the World of AI
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Ask about LLMs, machine learning, AI agents, RAG, frameworks, research, and more.
        </p>

        <div className="mt-5 flex gap-2">
          <input
            className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            placeholder="Search anything related to AI..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={submit}
            disabled={loading || !query.trim()}
            className="rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors px-5 py-3 text-sm font-medium text-white shrink-0"
          >
            {loading ? "Searching…" : "Search"}
          </button>
          {results.length > 0 && (
            <button
              onClick={onClear}
              className="rounded-xl border border-slate-300 hover:bg-slate-100 transition-colors px-4 py-3 text-sm font-medium text-slate-600 shrink-0"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-10 sm:px-10 space-y-4">
        {loading && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 flex items-center gap-3">
            <span className="h-4 w-4 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
            <span className="text-sm text-slate-500">Thinking…</span>
          </div>
        )}

        {results.length === 0 && !loading && (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400">
            No results yet. Try asking something like "What is retrieval-augmented generation?"
          </div>
        )}

        {[...results].reverse().map((r) => (
          <div key={r.id} id={`result-${r.id}`}>
            <ResultCard result={r} />
          </div>
        ))}
      </div>
    </div>
  );
}

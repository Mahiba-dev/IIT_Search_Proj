import ReactMarkdown from "react-markdown";
import type { SearchResult } from "../types";

export default function ResultCard({ result }: { result: SearchResult }) {
  if (result.status === "rejected") {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm font-medium text-amber-800">Query not answered</p>
        <p className="mt-1 text-sm text-amber-700">{result.message}</p>
      </div>
    );
  }

  if (result.status === "error") {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4">
        <p className="text-sm font-medium text-red-800">Something went wrong</p>
        <p className="mt-1 text-sm text-red-700">{result.message}</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500 truncate pr-4">{result.query}</p>
        {result.model && (
          <span className="shrink-0 text-[11px] rounded-full bg-slate-100 text-slate-500 px-2 py-0.5">
            {result.provider ? `${result.provider} · ` : ""}
            {result.model}
          </span>
        )}
      </div>
      <div className="px-5 py-4">
        {result.summary && (
          <p className="mb-3 text-sm italic text-slate-500 border-l-2 border-brand-200 pl-3">
            {result.summary}
          </p>
        )}
        <div className="prose prose-sm prose-slate max-w-none prose-pre:bg-slate-900 prose-pre:text-slate-100">
          <ReactMarkdown>{result.answer ?? ""}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

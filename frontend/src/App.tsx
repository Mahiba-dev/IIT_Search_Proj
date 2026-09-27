import { useEffect, useMemo, useState } from "react";
import Sidebar from "./components/Sidebar";
import SearchPanel from "./components/SearchPanel";
import HistoryPanel from "./components/HistoryPanel";
import { ApiError, fetchProviders, searchAI } from "./api/client";
import type { ChatTurn, ConnectionStatus, ProviderInfo, SearchResult } from "./types";

// A per-tab session id (not persisted) used only to scope server-side rate limiting.
const SESSION_ID = crypto.randomUUID();

export default function App() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [providersError, setProvidersError] = useState<string | null>(null);

  const [providerId, setProviderId] = useState("openai");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [temperature, setTemperature] = useState(0.3);
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState<ConnectionStatus>("not_connected");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    fetchProviders()
      .then((list) => {
        setProviders(list);
        if (list.length > 0) setProviderId((cur) => cur || list[0].id);
      })
      .catch(() => setProvidersError("Could not load AI providers. Is the backend running?"));
  }, []);

  useEffect(() => {
    // Collapse automatically on small screens on first load.
    if (window.innerWidth < 640) setSidebarCollapsed(true);
  }, []);

  const currentProvider = providers.find((p) => p.id === providerId);

  const history: ChatTurn[] = useMemo(() => {
    return results
      .filter((r) => r.status === "ok")
      .flatMap<ChatTurn>((r) => [
        { role: "user", content: r.query },
        { role: "assistant", content: r.answer ?? "" },
      ]);
  }, [results]);

  const handleSearch = async (query: string) => {
    if (!apiKey.trim()) {
      setResults((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          query,
          status: "error",
          message: "Please enter and save your API key in the sidebar first.",
          timestamp: Date.now(),
        },
      ]);
      return;
    }

    setLoading(true);
    try {
      const resp = await searchAI({
        apiKey,
        query,
        sessionId: SESSION_ID,
        selection: {
          provider: providerId,
          model: model || currentProvider?.default_model || "",
          baseUrl: baseUrl || (currentProvider?.default_base_url ?? undefined),
        },
        temperature,
        history,
      });

      const id = crypto.randomUUID();
      if (resp.status === "rejected") {
        setResults((prev) => [
          ...prev,
          { id, query, status: "rejected", message: resp.message, timestamp: Date.now() },
        ]);
      } else if (resp.status === "ok") {
        setResults((prev) => [
          ...prev,
          {
            id,
            query,
            status: "ok",
            answer: resp.answer,
            summary: resp.summary ?? undefined,
            model: resp.model,
            provider: resp.provider,
            timestamp: Date.now(),
          },
        ]);
      } else {
        setResults((prev) => [
          ...prev,
          { id, query, status: "error", message: resp.message ?? "Unknown error", timestamp: Date.now() },
        ]);
      }
      setActiveId(id);
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Network error. Please try again.";
      setResults((prev) => [
        ...prev,
        { id: crypto.randomUUID(), query, status: "error", message, timestamp: Date.now() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistory = (id: string) => {
    setActiveId(id);
    requestAnimationFrame(() => {
      document.getElementById(`result-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  return (
    <div className="h-full flex flex-col sm:flex-row">
      <Sidebar
        providers={providers}
        providerId={providerId}
        onProviderChange={setProviderId}
        model={model}
        onModelChange={setModel}
        baseUrl={baseUrl}
        onBaseUrlChange={setBaseUrl}
        temperature={temperature}
        onTemperatureChange={setTemperature}
        apiKey={apiKey}
        onApiKeyChange={setApiKey}
        status={status}
        onStatusChange={setStatus}
        collapsed={sidebarCollapsed}
        onToggleCollapsed={() => setSidebarCollapsed((c) => !c)}
      />

      <main className="flex-1 flex min-w-0 h-full">
        {providersError && (
          <div className="absolute top-2 left-1/2 -translate-x-1/2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-1.5 z-10">
            {providersError}
          </div>
        )}
        <SearchPanel
          onSearch={handleSearch}
          loading={loading}
          results={results}
          onClear={() => setResults([])}
          scrollToId={activeId}
        />
        {results.length > 0 && (
          <aside className="hidden lg:flex lg:flex-col w-72 shrink-0 border-l border-slate-200 bg-white overflow-y-auto">
            <div className="px-4 py-3 border-b border-slate-100">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                History
              </h3>
            </div>
            <HistoryPanel results={results} onSelect={handleSelectHistory} activeId={activeId} />
          </aside>
        )}
      </main>
    </div>
  );
}

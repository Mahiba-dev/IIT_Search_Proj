import { useEffect, useState } from "react";
import type { ConnectionStatus, ProviderInfo } from "../types";
import { checkKeyStatus } from "../api/client";

interface SidebarProps {
  providers: ProviderInfo[];
  providerId: string;
  onProviderChange: (id: string) => void;
  model: string;
  onModelChange: (model: string) => void;
  baseUrl: string;
  onBaseUrlChange: (url: string) => void;
  temperature: number;
  onTemperatureChange: (t: number) => void;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  status: ConnectionStatus;
  onStatusChange: (status: ConnectionStatus) => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

const STATUS_STYLES: Record<ConnectionStatus, { label: string; dot: string; text: string }> = {
  not_connected: { label: "Not Connected", dot: "bg-slate-400", text: "text-slate-500" },
  checking: { label: "Checking…", dot: "bg-amber-400 animate-pulse", text: "text-amber-600" },
  connected: { label: "Connected", dot: "bg-emerald-500", text: "text-emerald-600" },
  invalid: { label: "Invalid Key", dot: "bg-red-500", text: "text-red-600" },
};

export default function Sidebar({
  providers,
  providerId,
  onProviderChange,
  model,
  onModelChange,
  baseUrl,
  onBaseUrlChange,
  temperature,
  onTemperatureChange,
  apiKey,
  onApiKeyChange,
  status,
  onStatusChange,
  collapsed,
  onToggleCollapsed,
}: SidebarProps) {
  const [showKey, setShowKey] = useState(false);
  const [draftKey, setDraftKey] = useState(apiKey);
  const [customModelMode, setCustomModelMode] = useState(false);

  const provider = providers.find((p) => p.id === providerId);

  useEffect(() => {
    setDraftKey(apiKey);
  }, [apiKey]);

  useEffect(() => {
    // Provider changed: reset connection status until the user re-validates,
    // and drop out of custom-model entry mode for the new provider.
    onStatusChange("not_connected");
    setCustomModelMode(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [providerId]);

  const handleSave = async () => {
    onApiKeyChange(draftKey);
    if (!draftKey.trim()) {
      onStatusChange("not_connected");
      return;
    }
    onStatusChange("checking");
    try {
      const effectiveModel = model || provider?.default_model || "";
      const ok = await checkKeyStatus(draftKey, {
        provider: providerId,
        model: effectiveModel,
        baseUrl: baseUrl || (provider?.default_base_url ?? undefined),
      });
      onStatusChange(ok ? "connected" : "invalid");
    } catch {
      onStatusChange("invalid");
    }
  };

  const handleClear = () => {
    setDraftKey("");
    onApiKeyChange("");
    onStatusChange("not_connected");
  };

  const style = STATUS_STYLES[status];

  if (collapsed) {
    return (
      <div className="w-14 shrink-0 bg-brand-900 flex flex-col items-center py-4 gap-4">
        <button
          onClick={onToggleCollapsed}
          className="text-white/80 hover:text-white text-lg"
          aria-label="Expand sidebar"
          title="Expand sidebar"
        >
          ☰
        </button>
        <span className={`w-2.5 h-2.5 rounded-full ${style.dot}`} title={style.label} />
      </div>
    );
  }

  return (
    <aside className="w-full sm:w-80 shrink-0 bg-brand-900 text-white flex flex-col h-full overflow-y-auto">
      <div className="px-5 py-4 flex items-center justify-between border-b border-white/10">
        <h1 className="text-lg font-semibold tracking-tight">AI Explorer</h1>
        <button
          onClick={onToggleCollapsed}
          className="sm:hidden text-white/70 hover:text-white"
          aria-label="Collapse sidebar"
        >
          ✕
        </button>
      </div>

      <div className="p-5 space-y-6 flex-1">
        {/* Provider selection */}
        <div>
          <label className="block text-xs font-medium text-white/60 uppercase tracking-wide mb-1.5">
            AI Provider
          </label>
          <select
            className="w-full rounded-lg bg-white/10 border border-white/15 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={providerId}
            onChange={(e) => {
              onProviderChange(e.target.value);
              onModelChange("");
            }}
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id} className="text-slate-900">
                {p.label}
              </option>
            ))}
          </select>
        </div>

        {/* Model selection */}
        <div>
          <label className="block text-xs font-medium text-white/60 uppercase tracking-wide mb-1.5">
            Model
          </label>
          {provider && provider.models.length > 0 ? (
            <>
              <select
                className="w-full rounded-lg bg-white/10 border border-white/15 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={customModelMode ? "__custom__" : provider.models.includes(model) ? model : ""}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === "__custom__") {
                    setCustomModelMode(true);
                    onModelChange("");
                  } else {
                    setCustomModelMode(false);
                    onModelChange(value);
                  }
                }}
              >
                <option value="" className="text-slate-900">
                  {provider.default_model} (default)
                </option>
                {provider.models.map((m) => (
                  <option key={m} value={m} className="text-slate-900">
                    {m}
                  </option>
                ))}
                {provider.supports_custom_model && (
                  <option value="__custom__" className="text-slate-900">
                    Custom model name…
                  </option>
                )}
              </select>
              {customModelMode && (
                <input
                  className="mt-2 w-full rounded-lg bg-white/10 border border-white/15 px-3 py-2 text-sm placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="Enter model name"
                  value={model}
                  onChange={(e) => onModelChange(e.target.value)}
                  autoFocus
                />
              )}
            </>
          ) : (
            <input
              className="w-full rounded-lg bg-white/10 border border-white/15 px-3 py-2 text-sm placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="Enter model name"
              value={model}
              onChange={(e) => onModelChange(e.target.value)}
            />
          )}
        </div>

        {/* Base URL (for custom / OpenAI-compatible providers) */}
        {provider?.requires_base_url && (
          <div>
            <label className="block text-xs font-medium text-white/60 uppercase tracking-wide mb-1.5">
              API Base URL
            </label>
            <input
              className="w-full rounded-lg bg-white/10 border border-white/15 px-3 py-2 text-sm placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="https://your-endpoint.example.com/v1"
              value={baseUrl}
              onChange={(e) => onBaseUrlChange(e.target.value)}
            />
          </div>
        )}

        {/* API key */}
        <div>
          <label className="block text-xs font-medium text-white/60 uppercase tracking-wide mb-1.5">
            API Key
          </label>
          <div className="relative">
            <input
              type={showKey ? "text" : "password"}
              className="w-full rounded-lg bg-white/10 border border-white/15 px-3 py-2 pr-16 text-sm placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder={`Enter ${provider?.label ?? ""} API key`}
              value={draftKey}
              onChange={(e) => setDraftKey(e.target.value)}
              autoComplete="off"
            />
            <button
              type="button"
              onClick={() => setShowKey((s) => !s)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-white/60 hover:text-white"
            >
              {showKey ? "Hide" : "Show"}
            </button>
          </div>
          <p className="mt-1.5 text-[11px] leading-snug text-white/40">
            Kept in memory for this tab only — never saved to browser storage, cookies, or logs.
          </p>
          <div className="mt-2 flex gap-2">
            <button
              onClick={handleSave}
              className="flex-1 rounded-lg bg-brand-500 hover:bg-brand-600 transition-colors px-3 py-1.5 text-sm font-medium"
            >
              Save &amp; Test
            </button>
            <button
              onClick={handleClear}
              className="rounded-lg bg-white/10 hover:bg-white/15 transition-colors px-3 py-1.5 text-sm font-medium"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-2 text-sm">
          <span className={`w-2.5 h-2.5 rounded-full ${style.dot}`} />
          <span className={style.text}>{style.label}</span>
        </div>

        {/* Temperature */}
        {provider?.supports_temperature && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-medium text-white/60 uppercase tracking-wide">
                Temperature
              </label>
              <span className="text-xs text-white/60">{temperature.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min={0}
              max={2}
              step={0.1}
              value={temperature}
              onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
              className="w-full accent-brand-500"
            />
            <div className="flex justify-between text-[10px] text-white/40 mt-0.5">
              <span>Focused</span>
              <span>Creative</span>
            </div>
          </div>
        )}
      </div>

      <div className="px-5 py-4 border-t border-white/10 text-[11px] text-white/40">
        AI Explorer routes every query through AI-only validation before it reaches{" "}
        {provider?.label ?? "your provider"}.
      </div>
    </aside>
  );
}

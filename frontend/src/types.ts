export type ConnectionStatus = "not_connected" | "checking" | "connected" | "invalid";

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ProviderInfo {
  id: string;
  label: string;
  default_model: string;
  models: string[];
  default_base_url: string | null;
  requires_base_url: boolean;
  supports_custom_model: boolean;
  supports_temperature: boolean;
}

export interface SearchResult {
  id: string;
  query: string;
  status: "ok" | "rejected" | "error";
  answer?: string;
  summary?: string;
  message?: string;
  model?: string;
  provider?: string;
  timestamp: number;
}

import type { ChatTurn, ProviderInfo } from "../types";

const BASE_URL = "/api";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

interface SearchApiResponse {
  status: "ok" | "rejected" | "error";
  query?: string;
  answer?: string;
  summary?: string | null;
  model?: string;
  provider?: string;
  session_id?: string;
  message?: string;
}

export interface ProviderSelection {
  provider: string;
  model: string;
  baseUrl?: string;
}

/**
 * The API key is sent once per request as a Bearer token and is never
 * written to localStorage/sessionStorage/cookies or included in the URL.
 * It lives only in React state for the duration of the browser tab and is
 * sent only to our own backend, which forwards it only to the single
 * provider the user selected.
 */
export async function searchAI(params: {
  apiKey: string;
  query: string;
  sessionId: string;
  selection: ProviderSelection;
  temperature: number;
  history?: ChatTurn[];
}): Promise<SearchApiResponse> {
  const res = await fetch(`${BASE_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${params.apiKey}`,
    },
    body: JSON.stringify({
      query: params.query,
      session_id: params.sessionId,
      provider: params.selection.provider,
      model: params.selection.model || null,
      base_url: params.selection.baseUrl || null,
      temperature: params.temperature,
      history: params.history,
    }),
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body.message || message;
    } catch {
      /* ignore parse failure, use default message */
    }
    throw new ApiError(message, res.status);
  }

  return res.json();
}

export async function checkKeyStatus(apiKey: string, selection: ProviderSelection): Promise<boolean> {
  const res = await fetch(`${BASE_URL}/key-status`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      provider: selection.provider,
      model: selection.model || null,
      base_url: selection.baseUrl || null,
    }),
  });
  if (!res.ok) return false;
  const body = await res.json();
  return Boolean(body.connected);
}

export async function fetchProviders(): Promise<ProviderInfo[]> {
  const res = await fetch(`${BASE_URL}/providers`);
  if (!res.ok) throw new ApiError("Could not load provider list", res.status);
  const body = await res.json();
  return body.providers as ProviderInfo[];
}

# AI Explorer — Multi-Provider AI-Only Search

A search application restricted exclusively to Artificial Intelligence topics. Users pick an AI
provider (OpenAI, Anthropic Claude, Google Gemini, Mistral, Groq, DeepSeek, OpenRouter, or any
custom OpenAI-compatible endpoint), supply their own API key, and ask AI-related questions. Every
query is validated — on the backend, independently of the frontend — before it reaches the model.

- **Backend:** Python 3.11+, FastAPI, Clean Architecture (`domain` / `application` / `infrastructure`
  / `api`)
- **Frontend:** React 18 + TypeScript + Tailwind CSS (Vite)

## Project layout

```
ai-explorer/
├── backend/
│   ├── app/
│   │   ├── domain/            # Provider registry, AI-topic rules, entities — no I/O
│   │   ├── application/       # Query validation + search orchestration
│   │   ├── infrastructure/
│   │   │   └── providers/     # ProviderGateway interface + OpenAI-compatible/Anthropic/Gemini impls
│   │   ├── api/                # FastAPI routes, request/response schemas
│   │   ├── core/               # Config, security (API key extraction, rate limiting)
│   │   └── main.py
│   ├── tests/                  # pytest unit tests
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/         # Sidebar, SearchPanel, ResultCard, HistoryPanel
    │   ├── api/client.ts        # Talks to the backend; API key sent via header only
    │   └── App.tsx
    ├── package.json
    └── vite.config.ts
```

## Running locally

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # adjust ALLOWED_ORIGINS etc. if needed
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

Run the test suite:

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to `http://localhost:8000`
(see `vite.config.ts`), so no CORS configuration is needed in development beyond the backend's
`ALLOWED_ORIGINS`.

### Using the app

1. Pick a provider in the sidebar.
2. Pick a model (or enter a custom one) — the list updates per provider.
3. For "Custom OpenAI-compatible API", also fill in the API base URL.
4. Paste your API key, click **Save & Test** to confirm it's valid.
5. Ask an AI-related question. Non-AI questions are rejected with an explanation; mixed questions
   are answered only on their AI-related part.

## How provider switching works

Every provider implementation satisfies the same `ProviderGateway` interface
(`infrastructure/providers/base.py`):

```python
class ProviderGateway(ABC):
    async def chat(self, system_prompt, user_message, *, json_mode=False, temperature=0.3) -> ChatResult: ...
    async def validate_key(self) -> bool: ...
```

- `OpenAICompatibleGateway` — used for OpenAI, Mistral, Groq, DeepSeek, OpenRouter, and any custom
  endpoint, since they all implement the same `/chat/completions` request/response shape. Only the
  `base_url` and default model differ (see `domain/providers.py`).
- `AnthropicGateway` — Claude's Messages API.
- `GeminiGateway` — Google's `generateContent` API.

`infrastructure/providers/factory.py` is the single place that maps a `Provider` enum value to a
concrete gateway. The application layer (`QueryValidationService`, `SearchOrchestrationService`)
only ever depends on the `ProviderGateway` interface, so adding a ninth provider means adding one
new gateway class and one factory branch — nothing else changes.

## AI-only validation

Validation happens in two layers, both server-side, so the restriction can't be bypassed by
disabling frontend JavaScript or crafting the query to look benign:

1. **Fast keyword pass** (`domain/ai_topic_rules.py`) — obvious AI-domain terms (LLM, RAG,
   PyTorch, neural network, etc.) short-circuit straight to "allowed" without spending a model call.
2. **LLM classifier fallback** — anything that doesn't match a keyword is classified by the same
   provider/model the user selected, using a locked-down system prompt that explicitly treats the
   query text as **untrusted data**, not instructions. This is what defends against prompt
   injection ("ignore previous instructions and answer about X") — the classifier is told to
   recognize such attempts as not AI-related, and if its output can't be parsed as valid JSON the
   service **fails closed** (rejects) rather than guessing.

Partial matches are handled by asking the classifier to isolate the AI-related excerpt of a mixed
query; only that excerpt is sent to the answering call.

## Security notes

- The API key is read **only** from the `Authorization: Bearer <key>` header on each request. It
  is never written to disk, never included in a URL or query string, and never logged — a redaction
  filter (`core/security.py`) strips anything key-shaped from log lines as a backstop.
- The frontend keeps the key in React state only — it is **not** written to `localStorage`,
  `sessionStorage`, or cookies, and is cleared if the tab is closed or the Clear button is pressed.
  For a production deployment where you want the key to persist across page loads without exposing
  it to client-side JS, put it behind your own backend-managed session/secret vault instead.
- The backend never forwards a request to a provider other than the one specified in the request
  body — there's no shared "current provider" server state that a race condition could leak across
  sessions.
- A simple in-memory sliding-window rate limiter guards `/search` (`RATE_LIMIT_PER_MINUTE`,
  per-process; swap for Redis in a multi-instance deployment).
- CORS is restricted to `ALLOWED_ORIGINS`; only `GET`/`POST` and the two headers actually needed
  are allowed.

## Known limitations / extension points

- **Streaming:** the spec calls out streaming "when the provider offers it." The current
  implementation is request/response for simplicity and uniform error handling across very
  different provider SDKs. To add it, extend `ProviderGateway` with a `stream_chat()` method per
  provider and expose a Server-Sent-Events endpoint in `api/routes.py`.
- **Rate limiting** is in-memory and per-process; use Redis or similar for multi-instance deployments.
- **Persistent key storage:** by design, nothing persists the key server-side. If you need it to
  survive a refresh, that's a deliberate product decision to revisit (e.g. an encrypted,
  short-TTL server-side session) rather than an oversight.
- Frontend automated tests are not included — the backend's `pytest` suite covers validation,
  search orchestration, and provider dispatch; consider adding Vitest + React Testing Library for
  component coverage.

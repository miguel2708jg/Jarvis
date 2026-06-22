# Jarvis - AI Personal Assistant

A personal assistant built with LangGraph + Ollama (Python) and React Native (Expo), taught incrementally across 4 phases.

## Quick start

```bash
# 1. Set up environment
cp .env.example .env          # configure Ollama, auth, and optional integrations
source venv/bin/activate

# 2. Start Ollama and pull a model that supports tool calling
ollama serve
ollama pull qwen3

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the API server
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# 5. Open Swagger docs
open http://localhost:8000/docs
```

If you are using a remote Ollama-compatible endpoint, set `OLLAMA_BASE_URL`, `OLLAMA_MODEL_ID`, and optionally `OLLAMA_API_KEY` in `.env`. Use the host root, for example `https://ollama.com`, not the `/api` path.

Notes, todos, thread memory, and the knowledge brain use Neon/Postgres through `DATABASE_URL`. The knowledge wiki is stored in the database and exported to `KNOWLEDGE_VAULT_PATH` as an Obsidian-compatible markdown mirror. Calendar events are managed through Google Calendar, and Drive access is available through agent tools.

## Google Workspace

Set `GOOGLE_CREDENTIALS_FILE=credentials.json` and `GOOGLE_TOKEN_FILE=token.json` for Gmail, Calendar, and Drive. The shared OAuth token must include `gmail.modify`, `calendar.events`, `drive.readonly`, and `drive.file`. If an existing token only has Gmail scope, delete `GOOGLE_TOKEN_FILE`/`token.json`, restart the backend, and approve the expanded scopes.

## Storage / Neon

Normal runtime requires `DATABASE_URL` to be set to the Neon connection URL. `DATABASE_PATH=Data/jarvis.db` is kept only as a legacy backup/recovery source; SQLite fallback is disabled unless `ALLOW_SQLITE_FALLBACK=true` is explicitly set.

Useful maintenance commands:

```bash
# Idempotently upsert legacy SQLite rows into Neon
python scripts/migrate_sqlite_to_postgres.py --source Data/jarvis.db

# Read-only check that every SQLite row exists in Neon
python scripts/verify_neon_migration.py --source Data/jarvis.db
```

## Auth configuration

Most backend routes require trusted web-to-backend auth headers. For local development, set these values in `.env` from `.env.example`:

```env
AUTH_ALLOWED_EMAILS=your_email@example.com
BACKEND_INTERNAL_AUTH_TOKEN=replace_with_random_internal_token
BACKEND_AUTH_TOKEN_SECRET=replace_with_random_ws_signing_secret
```

Use the same `BACKEND_INTERNAL_AUTH_TOKEN` and `BACKEND_AUTH_TOKEN_SECRET` values for the Next.js web app and the FastAPI backend. `/health` is the only unauthenticated backend route.

## Railway web deployment

`jarvis-web` is a Next.js app in the `web/` directory. In the Railway service for the web app, set:

```text
Root Directory: web
Build Command: npm run build
Start Command: npm run start -- -H 0.0.0.0 -p $PORT
Healthcheck Path: /
```

Set these variables on the `jarvis-web` service:

```env
BACKEND_API_URL=https://your-jarvis-backend.up.railway.app
NEXT_PUBLIC_API_URL=/api
NEXT_PUBLIC_WS_URL=wss://your-jarvis-backend.up.railway.app
AUTH_ALLOWED_EMAILS=your_email@example.com
AUTH_GOOGLE_ID=your_google_oauth_client_id
AUTH_GOOGLE_SECRET=your_google_oauth_client_secret
NEXTAUTH_SECRET=replace_with_32_plus_random_chars
NEXTAUTH_URL=https://your-jarvis-web.up.railway.app
BACKEND_INTERNAL_AUTH_TOKEN=same_value_as_backend
BACKEND_AUTH_TOKEN_SECRET=same_value_as_backend
```

Keep `NEXT_PUBLIC_API_URL=/api` so browser REST calls go through the Next.js proxy, which adds the trusted backend auth headers. `NEXT_PUBLIC_WS_URL` should point directly to the backend domain with `wss://` because WebSockets are authenticated with a short-lived signed token.

## Ollama Cloud models

To run Jarvis against Ollama Cloud directly, create an Ollama API key and set:

```env
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL_ID=minimax-m2.7:cloud
OLLAMA_API_KEY=your_ollama_api_key
```

You can also use the local Ollama app as the gateway for cloud models:

```bash
ollama signin
ollama run minimax-m2.7:cloud
```

Then keep:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_ID=minimax-m2.7:cloud
```

Ollama also has an Anthropic-compatible `/v1/messages` API for tools that expect Claude/Anthropic. Jarvis currently uses the native Ollama chat API through LangChain, so model names should still be Ollama model names such as `minimax-m2.7:cloud`, not real Anthropic Claude model IDs.

## Running tests

```bash
# Phase 1 - requires Ollama
pytest tests/phase1/ -m integration -v

# Phase 2 - no Ollama needed
pytest tests/phase2/test_tools.py -v

# Phase 2 - agent routing (requires Ollama)
pytest tests/phase2/test_agent_routing.py -m integration -v

# Phase 3 - API tests (no Ollama)
pytest tests/phase3/test_api_endpoints.py -v

# Phase 4 - end-to-end (requires Ollama)
pytest tests/phase4/test_integration.py -m integration -v
```

## Mobile app

```bash
cd mobile
npm install
npm start       # opens Expo Go - scan QR or press i for iOS simulator
```

Set `EXPO_PUBLIC_API_URL=http://<your-machine-ip>:8000` in `mobile/.env` when running on a physical device.

## Project structure

```text
backend/          Python backend (FastAPI + LangGraph)
  config.py       Pydantic-settings (.env)
  llm/            Ollama LLM factory
  agent/          LangGraph graph, state, nodes, prompts
  tools/          @tool functions + registry
  models/         Pydantic models
  services/       Domain logic (notes, todos, database-backed knowledge, etc.)
  storage/        Neon/Postgres store + explicit SQLite recovery fallback
  api/            FastAPI app, routers, dependencies

mobile/           React Native (Expo) app
  src/
    api/          axios client + TypeScript types
    hooks/        useJarvisChat (WS), useJarvisApi (REST)
    components/   MessageBubble, StreamingText, TypingIndicator
    screens/      Chat, Notes, Knowledge, Todos, Calendar
    navigation/   Bottom tab navigator

tests/
  phase1/         Ollama connection + graph basics
  phase2/         Tool unit tests + agent routing
  phase3/         API endpoint + WebSocket tests
  phase4/         End-to-end integration

docs/
  architecture.md
  api-contract.md
  tools.md
```

## Phases

| Phase | Focus | Key concepts |
|---|---|---|
| 1 | Real LLM + conversational graph | `MessagesState`, `BaseChatModel`, Ollama config |
| 2 | Tool calling + storage | `@tool`, `ToolNode`, `tools_condition`, local tools |
| 3 | FastAPI + WebSocket streaming | `astream_events`, async FastAPI, WebSocket protocol |
| 4 | React Native mobile app | WS hook, streaming state, bottom tab navigation |

# Jarvis - AI Personal Assistant

A personal assistant built with LangGraph + Ollama (Python) and React Native (Expo), taught incrementally across 4 phases.

## Quick start

```bash
# 1. Set up environment
cp .env.example .env          # configure your Ollama endpoint/model
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

Notes, todos, calendar events, thread memory, and the knowledge vault use local project storage. Calendar events are stored in SQLite and do not require Google Calendar credentials.

Voice input/output is optional. For Groq STT + Piper TTS, set `STT_PROVIDER=groq`, `GROQ_API_KEY`, `GROQ_STT_MODEL`, `TTS_PROVIDER=piper`, and `TTS_VOICE`; Piper model files are resolved from `/tmp/piper-voices/{TTS_VOICE}.onnx` unless `PIPER_MODEL_PATH` is set.

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
  services/       Domain logic (notes, todos, knowledge vault, etc.)
  storage/        SQLite + legacy JSON compatibility
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

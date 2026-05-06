# Jarvis - Architecture

## Overview

Jarvis is a personal assistant built with LangGraph (Python) and a React Native (Expo) app.

```text
Mobile (Expo)
    | REST + WebSocket
    v
FastAPI -------- LangGraph Agent -------- Ollama
                      |
                    Tool calls
            / Notes / ToDo / Calendar / Knowledge
                      |
            SQLite data + Obsidian-style knowledge vault
```

## Backend layers

| Layer | Location | Purpose |
|---|---|---|
| Config | `backend/config.py` | Environment-driven settings |
| LLM | `backend/llm/ollama.py` | `ChatOllama` factory |
| Graph | `backend/agent/graph.py` | Agent and tool orchestration |
| Nodes | `backend/agent/nodes.py` | Prompt + memory + model invocation |
| Tools | `backend/tools/` | LangChain `@tool` wrappers |
| Storage | `backend/storage/sqlite_store.py` | Generic SQLite CRUD backend |
| Notes service | `backend/services/notes_service.py` | Notes domain logic |
| Calendar service | `backend/services/calendar_service.py` | Local SQLite calendar event logic |
| Knowledge service | `backend/services/knowledge_service.py` | Vault initialization, ingest, lint, index/log generation |
| API routers | `backend/api/routers/` | REST + WebSocket endpoints |

## Knowledge Vault subsystem

The knowledge subsystem uses a real Obsidian-compatible vault rooted at `KNOWLEDGE_VAULT_PATH`.

```text
knowledge_vault/
  AGENTS.md
  raw/
    notes/
    uploads/
    extracted/
  wiki/
    overview.md
    entities/
    concepts/
    sources/
    analyses/
    index.md   (generated)
    log.md     (append-only generated)
```

Key rules:
- Raw sources are immutable snapshots.
- LLM writes only wiki content pages.
- `wiki/index.md` and `wiki/log.md` are system-generated.
- Retrieval is lexical index-first (no vector DB in v1).

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
            / Notes / ToDo / Google Calendar / Drive / Knowledge
                      |
            SQLite/Postgres data + Obsidian markdown mirror
```

## Backend layers

| Layer | Location | Purpose |
|---|---|---|
| Config | `backend/config.py` | Environment-driven settings |
| LLM | `backend/llm/ollama.py` | `ChatOllama` factory |
| Graph | `backend/agent/graph.py` | Agent and tool orchestration |
| Nodes | `backend/agent/nodes.py` | Prompt + memory + model invocation |
| Tools | `backend/tools/` | LangChain `@tool` wrappers |
| Storage | `backend/storage/postgres_store.py` | Neon/Postgres CRUD backend selected by `DATABASE_URL` |
| Notes service | `backend/services/notes_service.py` | Notes domain logic |
| Calendar service | `backend/services/calendar_service.py` | Google Calendar event logic |
| Drive service | `backend/services/drive_service.py` | Google Drive search, read, and create logic |
| Knowledge service | `backend/services/knowledge_service.py` | Database-backed knowledge brain, ingest, lint, and Obsidian mirror export |
| API routers | `backend/api/routers/` | REST + WebSocket endpoints |

## Knowledge subsystem

The knowledge subsystem stores the wiki in database tables. `KNOWLEDGE_VAULT_PATH` points to an Obsidian-compatible markdown mirror exported from the database.

Canonical tables:

```text
knowledge_pages    structured wiki pages and body text
knowledge_sources  source snapshots, extracted text, and upload bytes
knowledge_links    wikilinks extracted from page bodies
knowledge_log      generated operation log entries
```

Mirror layout:

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
- `DATABASE_URL` is required for normal runtime storage.
- SQLite is available only as an explicit recovery/test fallback via `ALLOW_SQLITE_FALLBACK=true`.
- The database is canonical; markdown is regenerated as a mirror.
- Existing vault markdown is auto-imported only when knowledge tables are empty.
- Raw sources are stored in DB and exported back to `raw/`.
- LLM writes are validated and persisted as structured DB rows.
- `wiki/index.md` and `wiki/log.md` are generated from DB state.
- Retrieval is lexical over structured page metadata (no vector DB in v1).

# Jarvis API Contract

Base URL: `http://localhost:8000`

## Health

```text
GET /health
-> { "status": "ok", "service": "jarvis" }
```

## Chat

```text
POST /chat
Body: { "message": str, "session_id": str, "user_id": str, "personality_id"?: str }
-> { "content": str, "session_id": str }

WS /ws/chat
Send: { "message": str, "session_id": str, "personality_id"?: str }
Recv: StreamChunk frames (see architecture.md)
```

Valid `personality_id` values are `mentor`, `ceo`, `coach`, `amigo`, `rizz`, `focus`, `analista`, `creativo`, and `social_copilot`. Omit it for Jarvis normal.

## Threads

```text
GET    /threads                    -> Thread[] (?user_id=default)
POST   /threads                    -> Thread (201)
GET    /threads/{id}               -> Thread
PUT    /threads/{id}               -> Thread
DELETE /threads/{id}               -> 204
GET    /threads/{id}/messages      -> Message[]
```

`session_id` is used as the persistent conversation/thread identifier for chat and voice requests.

## Notes

```text
GET    /notes              -> Note[]
POST   /notes              -> Note (201)
GET    /notes/{id}         -> Note
PUT    /notes/{id}         -> Note
DELETE /notes/{id}         -> 204
```

## ToDo

```text
GET    /todos              -> Todo[]  (?show_completed=false)
POST   /todos              -> Todo (201)
GET    /todos/{id}         -> Todo
PUT    /todos/{id}         -> Todo
PATCH  /todos/{id}/complete -> Todo
DELETE /todos/{id}         -> 204
```

Notes and todos CRUD is available through REST, the LangChain agent tools, and the standalone MCP server.

## Voice

Voice uses `STT_PROVIDER=groq` and `TTS_PROVIDER=piper` in v1. `GROQ_STT_MODEL` defaults to `whisper-large-v3-turbo`; `TTS_VOICE` resolves to `/tmp/piper-voices/{TTS_VOICE}.onnx` unless `PIPER_MODEL_PATH` is set.

```text
POST /voice
multipart/form-data: audio=file, session_id?: str, personality_id?: str
-> { "transcript": str, "response_text": str, "audio_base64": str, "session_id": str }

POST /voice/tts
Body: { "text": str }
-> { "audio_base64": str }
```

## Calendar

Calendar events are stored locally in SQLite.

```text
GET    /calendar           -> CalendarEvent[] (?upcoming_only=true)
POST   /calendar           -> CalendarEvent (201)
GET    /calendar/{id}      -> CalendarEvent
PUT    /calendar/{id}      -> CalendarEvent
DELETE /calendar/{id}      -> 204
```

## Knowledge Vault

```text
GET  /knowledge/status               -> KnowledgeStatus
GET  /knowledge/pages                -> KnowledgePage[] (?type=entity&q=term)
GET  /knowledge/pages/{path}         -> KnowledgePageDetail
GET  /knowledge/sources              -> KnowledgeSource[]
GET  /knowledge/sources/{source_id}/raw -> raw source file bytes
POST /knowledge/ingest/note          Body: { "note_id": str } -> KnowledgeIngestResult
POST /knowledge/ingest/file          multipart file -> KnowledgeIngestResult
POST /knowledge/lint                 -> KnowledgeIngestResult
```

`KnowledgeSource` includes `raw_storage` (`local` or `s3`) and `raw_object_key` for file uploads. Raw source downloads are proxied by the backend so Railway Buckets can remain private.

## Error format

```json
{ "detail": "Error message" }
```

HTTP status codes: `400` bad request, `404` not found, `503` service unavailable (for optional integrations and model backends).

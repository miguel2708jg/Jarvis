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

GET    /chat/threads                 -> ChatThreadSummary[]
POST   /chat/threads                 Body: { "title"?: str } -> ChatThreadSummary (201)
GET    /chat/threads/{thread_id}/messages -> ChatThreadMessage[]
DELETE /chat/threads/{thread_id}     -> 204
```

Valid `personality_id` values are `mentor`, `ceo`, `coach`, `amigo`, `rizz`, `focus`, `analista`, `creativo`, and `social_copilot`. Omit it for Jarvis normal.
`session_id` is the stable conversation ID used by the agent memory. The thread endpoints expose saved conversations for the authenticated user and reconstruct messages from persisted thread memory.

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

## Calendar

Calendar events are managed in Google Calendar through shared Google Workspace OAuth.

```text
GET    /calendar           -> CalendarEvent[] (?upcoming_only=true)
POST   /calendar           -> CalendarEvent (201)
GET    /calendar/{id}      -> CalendarEvent
PUT    /calendar/{id}      -> CalendarEvent
DELETE /calendar/{id}      -> 204
```

## Email / Gmail MCP

Gmail uses Google's remote MCP server and shared Google Workspace OAuth files from `.env`.

```text
GET  /emails                         -> EmailMessage[] (?label=INBOX&max=10)
GET  /emails/search                  -> EmailMessage[] (?q=from:person@example.com&max=10)
GET  /emails/threads/{thread_id}     -> EmailThread
GET  /emails/drafts                  -> Draft list (?q=subject:foo&max=20)
POST /emails/drafts                  Body: { "to": str[], "subject"?: str, "body"?: str, "cc"?: str[], "bcc"?: str[], "htmlBody"?: str, "replyToMessageId"?: str, "attachmentSourceIds"?: str[] } -> Draft
POST /emails/send                    Body: { "to": str[], "subject"?: str, "body"?: str, "cc"?: str[], "bcc"?: str[], "htmlBody"?: str, "replyToMessageId"?: str, "attachmentSourceIds"?: str[], "userConfirmed": true } -> Sent message
POST /emails/drafts/{draft_id}/send  Body: { "userConfirmed": true } -> Sent message
GET  /emails/labels                  -> Label list
POST /emails/labels                  Body: { "displayName": str, "color"?: object } -> Label
PUT  /emails/labels/{label_id}       Body: { "displayName"?: str, "color"?: object } -> Label
POST /emails/threads/{id}/labels     Body: { "labelIds": str[] } -> {}
POST /emails/threads/{id}/labels/remove -> {}
POST /emails/messages/{id}/labels    Body: { "labelIds": str[] } -> {}
POST /emails/messages/{id}/labels/remove -> {}
```

`EmailMessage` includes `message_id`, `thread_id`, `sender`, `recipient`, `subject`, `body`, `snippet`, `date`, `labels`, and `is_read`.
Direct send requires explicit confirmation. The API does not expose label deletion.

## Google Drive

Drive is agent-first and does not expose REST endpoints in v1. Registered tools:

```text
search_drive_files(query, max_results?)      -> Drive file metadata[]
get_drive_file(file_id, include_content?)    -> Drive file metadata + optional text content
create_drive_text_file(name, content, parent_id?, mime_type?) -> Drive file metadata
create_drive_folder(name, parent_id?)        -> Drive folder metadata
```

Drive tools do not delete, move, rename, or overwrite files.

## Knowledge Vault

```text
GET  /knowledge/status               -> KnowledgeStatus
GET  /knowledge/pages                -> KnowledgePage[] (?type=entity&q=term)
GET  /knowledge/pages/{path}         -> KnowledgePageDetail
GET  /knowledge/sources              -> KnowledgeSource[]
POST /knowledge/ingest/note          Body: { "note_id": str } -> KnowledgeIngestResult
POST /knowledge/ingest/file          multipart file -> KnowledgeIngestResult
POST /knowledge/lint                 -> KnowledgeIngestResult
```

`POST /knowledge/ingest/file` accepts `.md`, `.txt`, `.pdf`, and `.docx` uploads.

## Error format

```json
{ "detail": "Error message" }
```

HTTP status codes: `400` bad request, `404` not found, `503` service unavailable (for optional integrations and model backends).

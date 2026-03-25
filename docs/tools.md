# Jarvis Tools

All tools are registered in `backend/tools/registry.py`. To add a new tool:

1. Create a function decorated with `@tool` in the appropriate module
2. Add it to `ALL_TOOLS` in `registry.py` — no graph changes required

## Notes tools

| Tool | Description |
|---|---|
| `create_note(title, content, tags?)` | Create a new note |
| `list_notes(tag?)` | List notes, optionally filtered by tag |
| `get_note(note_id)` | Fetch a note by ID |
| `update_note(note_id, title?, content?, tags?)` | Update note fields |
| `delete_note(note_id)` | Delete a note |

## Todos tools

| Tool | Description |
|---|---|
| `create_todo(text, priority?, due_date?)` | Create a to-do item |
| `list_todos(show_completed?)` | List todos (incomplete by default) |
| `complete_todo(todo_id)` | Mark a todo as done |
| `delete_todo(todo_id)` | Delete a todo |

## Calendar tools

| Tool | Description |
|---|---|
| `create_calendar_event(title, start_datetime, end_datetime, description?, location?)` | Create an event |
| `list_calendar_events()` | List all events sorted by start time |
| `get_calendar_event(event_id)` | Fetch an event by ID |
| `delete_calendar_event(event_id)` | Delete an event |

## Email tools (Gmail)

Requires `GMAIL_CREDENTIALS_FILE` and `GMAIL_TOKEN_FILE` in `.env`.

| Tool | Description |
|---|---|
| `list_emails(max_results?, label?)` | List recent emails from a label |
| `get_email(message_id)` | Get full email content |
| `send_email(to, subject, body)` | Send an email |
| `search_emails(query, max_results?)` | Search with Gmail query syntax |

### Gmail setup

1. Go to Google Cloud Console → create a project → enable Gmail API
2. Create OAuth 2.0 credentials (Desktop app) → download `credentials.json`
3. Set `GMAIL_CREDENTIALS_FILE=credentials.json` in `.env`
4. Run any Gmail tool once — a browser window opens for OAuth consent
5. Token saved to `GMAIL_TOKEN_FILE` (default: `token.json`) for future use

# Jarvis Tools

All tools are registered in `backend/tools/registry.py`. To add a new tool:

1. Create a function decorated with `@tool` in the appropriate module.
2. Add it to `ALL_TOOLS` in `registry.py` (no graph changes needed).

## Notes tools

| Tool | Description |
|---|---|
| `create_note(title, content, tags?)` | Create a new note |
| `list_notes(tag?)` | List notes, optionally filtered by tag |
| `get_note(note_id)` | Fetch a note by ID |
| `update_note(note_id, title?, content?, tags?)` | Update note fields |
| `delete_note(note_id)` | Delete a note |

## ToDo tools

| Tool | Description |
|---|---|
| `create_todo(text, priority?, due_date?)` | Create a to-do item |
| `list_todos(show_completed?)` | List todos (incomplete by default) |
| `get_todo(todo_id)` | Fetch a todo by ID |
| `update_todo(todo_id, text?, priority?, due_date?, completed?, clear_due_date?)` | Update todo fields |
| `complete_todo(todo_id)` | Mark a todo as done |
| `delete_todo(todo_id)` | Delete a todo |

The standalone MCP server in `backend/mcp_server.py` exposes the same notes and todos CRUD surface as the LangChain agent tools.

## Calendar tools

Calendar tools manage local SQLite events through the same backend database used by other local modules.

| Tool | Description |
|---|---|
| `create_calendar_event(title, start_datetime, end_datetime, description?, location?)` | Create an event |
| `list_calendar_events(upcoming_only?)` | List local events sorted by start time |
| `get_calendar_event(event_id)` | Fetch an event by ID |
| `delete_calendar_event(event_id)` | Delete an event |

## Knowledge tools

| Tool | Description |
|---|---|
| `search_knowledge_pages(query, page_type?, limit?)` | Lexical search over knowledge index metadata |
| `get_knowledge_page(path)` | Fetch a wiki page with metadata, body, and wikilinks |
| `ingest_note_to_knowledge(note_id)` | Snapshot a note into raw sources and update wiki pages |
| `lint_knowledge_base()` | Run explicit wiki maintenance and apply fixes |

Email/Gmail tools are disabled in the active assistant registry for now. Calendar events are local and do not require Google OAuth.

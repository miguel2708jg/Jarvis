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
| `complete_todo(todo_id)` | Mark a todo as done |
| `delete_todo(todo_id)` | Delete a todo |

## Calendar tools

Calendar tools manage Google Calendar events through shared Google Workspace OAuth.

| Tool | Description |
|---|---|
| `create_calendar_event(title, start_datetime, end_datetime, description?, location?)` | Create an event |
| `list_calendar_events(upcoming_only?)` | List Google Calendar events sorted by start time |
| `get_calendar_event(event_id)` | Fetch an event by ID |
| `delete_calendar_event(event_id)` | Delete an event |

## Knowledge tools

| Tool | Description |
|---|---|
| `search_knowledge_pages(query, page_type?, limit?)` | Lexical search over database-backed knowledge page metadata |
| `get_knowledge_page(path)` | Fetch a wiki page from DB with metadata, body, and wikilinks |
| `ingest_note_to_knowledge(note_id)` | Snapshot a note into DB-backed sources and update wiki pages |
| `lint_knowledge_base()` | Run explicit knowledge maintenance and apply DB-backed wiki fixes |

## Gmail tools

Gmail tools use Google's remote Gmail MCP server for read/draft operations and direct Gmail API calls for sending and attachment-backed drafts. Google Workspace OAuth uses shared `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_TOKEN_FILE`, and the `gmail.modify` scope.

| Tool | Description |
|---|---|
| `search_email_threads(query, max_results?)` | Search Gmail threads with Gmail search syntax |
| `get_email_thread(thread_id)` | Fetch full thread content |
| `create_email_draft(to, subject?, body?, cc?, bcc?, html_body?, reply_to_message_id?, attachment_source_ids?)` | Create a draft; does not send |
| `send_email(to, subject?, body?, cc?, bcc?, html_body?, reply_to_message_id?, attachment_source_ids?, user_confirmed)` | Send an email only after explicit confirmation |
| `send_email_draft(draft_id, user_confirmed)` | Send an existing draft only after explicit confirmation |
| `list_email_drafts(query?, page_size?)` | List drafts |
| `list_email_labels(page_size?)` | List labels |
| `create_email_label(display_name)` | Create a label |
| `update_email_label(label_id, display_name)` | Rename a label |
| `apply_email_labels_to_thread(thread_id, label_ids)` | Apply labels to a thread |
| `remove_email_labels_from_thread(thread_id, label_ids)` | Remove labels from a thread |
| `apply_email_labels_to_message(message_id, label_ids)` | Apply labels to a message |
| `remove_email_labels_from_message(message_id, label_ids)` | Remove labels from a message |

Label deletion is intentionally not registered. Send tools require explicit confirmation.

## Google Drive tools

Drive tools use shared Google Workspace OAuth with `drive.readonly` and `drive.file` scopes.

| Tool | Description |
|---|---|
| `search_drive_files(query, max_results?)` | Search Drive files by name or Drive query syntax |
| `get_drive_file(file_id, include_content?)` | Fetch Drive file metadata and optional text content |
| `create_drive_text_file(name, content, parent_id?, mime_type?)` | Create a text file |
| `create_drive_folder(name, parent_id?)` | Create a folder |

Drive delete, move, rename, and overwrite tools are intentionally not registered.

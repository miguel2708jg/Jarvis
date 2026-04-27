"""Central tool registry — add new tools here only, no graph changes needed."""
from backend.tools.notes import create_note, list_notes, get_note, update_note, delete_note
from backend.tools.todos import (
    create_todo,
    list_todos,
    get_todo,
    update_todo,
    complete_todo,
    delete_todo,
)
from backend.tools.calendar import (
    create_calendar_event,
    list_calendar_events,
    get_calendar_event,
    update_calendar_event,
    delete_calendar_event,
)
from backend.tools.email import list_emails, get_email, send_email, search_emails
from backend.tools.knowledge import (
    search_knowledge_pages,
    get_knowledge_page,
    ingest_note_to_knowledge,
    lint_knowledge_base,
)

ALL_TOOLS = [
    # Notes
    create_note,
    list_notes,
    get_note,
    update_note,
    delete_note,
    # Todos
    create_todo,
    list_todos,
    get_todo,
    update_todo,
    complete_todo,
    delete_todo,
    # Calendar
    create_calendar_event,
    list_calendar_events,
    get_calendar_event,
    update_calendar_event,
    delete_calendar_event,
    # Email (Gmail)
    list_emails,
    get_email,
    send_email,
    search_emails,
    # Knowledge Vault
    search_knowledge_pages,
    get_knowledge_page,
    ingest_note_to_knowledge,
    lint_knowledge_base,
]

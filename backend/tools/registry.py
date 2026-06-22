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
from backend.tools.knowledge import (
    search_knowledge_pages,
    get_knowledge_page,
    ingest_note_to_knowledge,
    lint_knowledge_base,
)
from backend.tools.email import (
    search_email_threads,
    get_email_thread,
    create_email_draft,
    send_email,
    send_email_draft,
    list_email_drafts,
    list_email_labels,
    create_email_label,
    update_email_label,
    apply_email_labels_to_thread,
    remove_email_labels_from_thread,
    apply_email_labels_to_message,
    remove_email_labels_from_message,
)
from backend.tools.drive import (
    search_drive_files,
    get_drive_file,
    create_drive_text_file,
    create_drive_folder,
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
    # Knowledge Vault
    search_knowledge_pages,
    get_knowledge_page,
    ingest_note_to_knowledge,
    lint_knowledge_base,
    # Gmail MCP
    search_email_threads,
    get_email_thread,
    create_email_draft,
    send_email,
    send_email_draft,
    list_email_drafts,
    list_email_labels,
    create_email_label,
    update_email_label,
    apply_email_labels_to_thread,
    remove_email_labels_from_thread,
    apply_email_labels_to_message,
    remove_email_labels_from_message,
    # Google Drive
    search_drive_files,
    get_drive_file,
    create_drive_text_file,
    create_drive_folder,
]

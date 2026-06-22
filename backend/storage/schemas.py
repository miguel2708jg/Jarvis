"""SQL schemas for Jarvis relational storage."""

TODOS_SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    priority TEXT NOT NULL DEFAULT 'medium',
    due_date TEXT,
    created_at TEXT NOT NULL
)
"""

NOTES_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

THREADS_SCHEMA = """
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    title TEXT,
    user_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

MESSAGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

THREAD_MEMORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS thread_memory (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    messages TEXT NOT NULL,
    user_id TEXT,
    session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

CALENDAR_SCHEMA = """
CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    start_datetime TEXT NOT NULL,
    end_datetime TEXT NOT NULL,
    description TEXT,
    location TEXT,
    created_at TEXT NOT NULL
)
"""

KNOWLEDGE_PAGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_pages (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    body TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    source_ids TEXT,
    tags TEXT,
    aliases TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL
)
"""

KNOWLEDGE_SOURCES_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    extracted_path TEXT,
    note_id TEXT,
    original_filename TEXT,
    content_text TEXT,
    extracted_text TEXT,
    raw_bytes BYTEA,
    metadata TEXT
)
"""

KNOWLEDGE_LINKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_links (
    id TEXT PRIMARY KEY,
    from_path TEXT NOT NULL,
    target TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

KNOWLEDGE_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_log (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    operation TEXT NOT NULL,
    target TEXT NOT NULL,
    entry TEXT NOT NULL
)
"""

TABLE_SCHEMAS = {
    "todos": TODOS_SCHEMA,
    "notes": NOTES_SCHEMA,
    "threads": THREADS_SCHEMA,
    "messages": MESSAGES_SCHEMA,
    "thread_memory": THREAD_MEMORY_SCHEMA,
    "calendar_events": CALENDAR_SCHEMA,
    "knowledge_pages": KNOWLEDGE_PAGES_SCHEMA,
    "knowledge_sources": KNOWLEDGE_SOURCES_SCHEMA,
    "knowledge_links": KNOWLEDGE_LINKS_SCHEMA,
    "knowledge_log": KNOWLEDGE_LOG_SCHEMA,
}

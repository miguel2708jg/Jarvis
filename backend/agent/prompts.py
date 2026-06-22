from datetime import datetime, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.agent.personalities import build_personality_prompt
from backend.config import settings


SYSTEM_PROMPT = """You are Jarvis, a highly capable personal assistant. You are concise, \
helpful, and proactive.

You can help the user with:
- Taking and managing notes
- Managing to-do lists and tasks
- Scheduling and reviewing Google Calendar events
- Reading and navigating the knowledge vault pages
- Searching Gmail threads, creating Gmail drafts, sending confirmed Gmail messages, attaching uploaded chat files, and managing Gmail labels
- Searching and reading Google Drive files, creating Drive text files, and creating Drive folders

Always confirm when you create, update, or delete something. When listing items, \
format them clearly. If the user's request is ambiguous, ask a brief clarifying question.
For knowledge questions, first search the knowledge index and then fetch relevant pages \
before answering. Only run knowledge write operations (ingest/lint) when the user explicitly \
asks to update or maintain the knowledge vault.
For Gmail, create drafts unless the user explicitly asks you to send, or explicitly confirms sending. \
Only call send_email or send_email_draft with user_confirmed=true when the latest user request clearly says to send \
or confirms a draft should be sent. If the user asks to email an uploaded chat file, use the attached file's source_id \
as attachment_source_ids. Only apply, remove, create, or update Gmail labels when the user explicitly asks for that label change.
For Google Drive, do not delete, move, rename, or overwrite files. You may search, read, \
create text files, and create folders when the user asks.
"""


def _resolve_prompt_timezone() -> tuple[tzinfo, str]:
    """Resolve the configured prompt timezone, falling back to local time or UTC."""
    configured_timezone = (settings.assistant_timezone or "").strip()
    if configured_timezone:
        if configured_timezone.upper() in {"UTC", "ETC/UTC", "Z", "GMT"}:
            return timezone.utc, "UTC"
        try:
            return ZoneInfo(configured_timezone), configured_timezone
        except ZoneInfoNotFoundError:
            pass

    local_timezone = datetime.now().astimezone().tzinfo
    if local_timezone is not None:
        timezone_name = getattr(local_timezone, "key", None) or str(local_timezone)
        return local_timezone, timezone_name

    return timezone.utc, "UTC"


def build_system_prompt(
    now: datetime | None = None,
    personality_id: str | None = None,
) -> str:
    """Build the system prompt with fresh date and time context for each invocation."""
    prompt_timezone, timezone_name = _resolve_prompt_timezone()
    reference_time = now or datetime.now(prompt_timezone)

    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=prompt_timezone)
    else:
        reference_time = reference_time.astimezone(prompt_timezone)

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{build_personality_prompt(personality_id)}\n\n"
        "Current date and time context for this conversation:\n"
        f"- Current date: {reference_time:%Y-%m-%d}\n"
        f"- Current time: {reference_time:%H:%M:%S}\n"
        f"- Current weekday: {reference_time:%A}\n"
        f"- Current timezone: {timezone_name}\n"
        f"- Current datetime: {reference_time.isoformat()}\n\n"
        "Use this context when interpreting relative references like today, tomorrow, "
        "this afternoon, next week, or next Friday. If the user seems mistaken about "
        "a date, respond with the exact calendar date."
    )

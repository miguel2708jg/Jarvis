"""Knowledge service with database-canonical storage and Obsidian mirror export."""
from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import re
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree

import yaml
from pypdf import PdfReader

from backend.config import settings
from backend.llm import get_llm
from backend.models.knowledge import (
    KnowledgeIngestResult,
    KnowledgePage,
    KnowledgePageDetail,
    KnowledgeSource,
    KnowledgeStatus,
)
from backend.services import notes_service
from backend.storage.factory import create_store
from backend.storage.schemas import (
    KNOWLEDGE_LINKS_SCHEMA,
    KNOWLEDGE_LOG_SCHEMA,
    KNOWLEDGE_PAGES_SCHEMA,
    KNOWLEDGE_SOURCES_SCHEMA,
)

VAULT_STRUCTURE = [
    "raw/notes",
    "raw/uploads",
    "raw/extracted",
    "wiki/entities",
    "wiki/concepts",
    "wiki/sources",
    "wiki/analyses",
]
RESERVED_WIKI_FILES = {"index.md", "log.md"}
ALLOWED_ROOTS = {"entities", "concepts", "sources", "analyses"}
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
WRITESET_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
LOG_ENTRY_RE = re.compile(r"^## \[(?P<created_at>[^\]]+)\]\s+(?P<operation>.*?)\s+\|\s+(?P<target>.*)$")
DOCX_WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

_operation_lock = threading.Lock()
_stores_lock = threading.Lock()
_stores_signature: tuple[str | None, str | None, str] | None = None
_page_store = None
_source_store = None
_link_store = None
_log_store = None

AGENTS_TEMPLATE = """# Knowledge Vault Contract

This vault is mirrored from the Jarvis database and remains Obsidian-compatible.

## Page types
- overview
- entity
- concept
- source
- analysis

## Frontmatter contract
All wiki pages must include YAML frontmatter fields:
- type
- title
- summary
- updated_at
- source_ids
- tags
- aliases

## Body contract
- Use Obsidian wikilinks for cross references: [[Page Name]].
- Keep pages concise and factual.
- Source pages should point back to immutable source entries.

## System-managed files
- The Jarvis database is canonical.
- `wiki/index.md` and `wiki/log.md` are generated from database rows.
"""

HOME_TEMPLATE = """---
type: overview
title: Vault Home
summary: Entry page for the Jarvis knowledge vault in Obsidian.
updated_at: 2026-04-15T18:05:00-06:00
source_ids: []
tags:
  - home
  - vault
aliases:
  - Start Here
---

# Vault Home

This vault is mirrored by Jarvis from its database-backed knowledge brain.

## Open these first

- [[wiki/overview]]
- [[wiki/index]]
- [[wiki/analyses/knowledge-graph-chart]]

## What is here

- `raw/` contains source snapshots exported from the database.
- `wiki/` contains curated knowledge pages exported from the database.
- `wiki/index.md` and `wiki/log.md` are generated from structured rows.
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utcnow().isoformat()


def _vault_path() -> Path:
    return Path(settings.knowledge_vault_path)


def _wiki_root() -> Path:
    return _vault_path() / "wiki"


def _storage_signature() -> tuple[str | None, str | None, str]:
    return (settings.database_url, settings.database_path, settings.data_dir)


def _ensure_storage_initialized() -> None:
    global _stores_signature, _page_store, _source_store, _link_store, _log_store

    signature = _storage_signature()
    with _stores_lock:
        if _stores_signature == signature:
            return
        _page_store = create_store("knowledge_pages", KNOWLEDGE_PAGES_SCHEMA)
        _source_store = create_store("knowledge_sources", KNOWLEDGE_SOURCES_SCHEMA)
        _link_store = create_store("knowledge_links", KNOWLEDGE_LINKS_SCHEMA)
        _log_store = create_store("knowledge_log", KNOWLEDGE_LOG_SCHEMA)
        _stores_signature = signature


def _pages():
    _ensure_storage_initialized()
    return _page_store


def _sources():
    _ensure_storage_initialized()
    return _source_store


def _links():
    _ensure_storage_initialized()
    return _link_store


def _logs():
    _ensure_storage_initialized()
    return _log_store


def _safe_relative(base: Path, candidate: Path) -> Path:
    """Resolve a path and ensure it stays under base."""
    resolved_base = base.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(f"Unsafe path outside vault: {candidate}") from exc
    return resolved_candidate


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp-{uuid4().hex}")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp-{uuid4().hex}")
    temp_path.write_bytes(content)
    temp_path.replace(path)


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _json_load_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_load_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return _normalize_list(value)
    if not value:
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return _normalize_list(value)
    return _normalize_list(parsed)


def _coerce_bytes(value: Any) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return value.tobytes()
    return None


def _decode_bytes(data: bytes | None) -> str:
    if not data:
        return ""
    return data.decode("utf-8", errors="ignore").strip()


def _sanitize_slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or uuid4().hex[:8]


def _frontmatter_to_text(frontmatter: dict[str, Any], body: str) -> str:
    yaml_block = yaml.safe_dump(frontmatter, allow_unicode=False, sort_keys=True).strip()
    return f"---\n{yaml_block}\n---\n\n{body.strip()}\n"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text.strip()
    raw = match.group(1)
    metadata = yaml.safe_load(raw) or {}
    body = text[match.end():].strip()
    return metadata if isinstance(metadata, dict) else {}, body


def extract_wikilinks(body: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for match in WIKILINK_RE.finditer(body):
        link = match.group(1).strip()
        if not link:
            continue
        if link.lower() in seen:
            continue
        seen.add(link.lower())
        links.append(link)
    return links


def _normalize_wiki_read_path(path: str) -> str:
    if not path:
        raise ValueError("Page path is required")
    normalized = path.strip().replace("\\", "/")
    if normalized.startswith("wiki/"):
        normalized = normalized[5:]
    if normalized.startswith("/"):
        normalized = normalized[1:]
    if not normalized.endswith(".md"):
        normalized += ".md"
    candidate = _wiki_root() / normalized
    safe = _safe_relative(_wiki_root(), candidate)
    if safe.name in RESERVED_WIKI_FILES:
        raise ValueError("Reserved page path")
    return safe.resolve().relative_to(_wiki_root().resolve()).as_posix()


def _resolve_wiki_page_path(path: str) -> Path:
    return _wiki_root() / _normalize_wiki_read_path(path)


def _normalize_write_path(path: str) -> str:
    cleaned = _normalize_wiki_read_path(path)
    if cleaned == "overview.md":
        return cleaned
    root = cleaned.split("/", 1)[0]
    if root not in ALLOWED_ROOTS:
        raise ValueError(f"Writer path outside allowed wiki roots: {cleaned}")
    return cleaned


def _iter_wiki_pages(root: Path | None = None) -> list[Path]:
    wiki_root = root or _wiki_root()
    pages: list[Path] = []
    if not wiki_root.exists():
        return pages
    for file in wiki_root.rglob("*.md"):
        if file.name in RESERVED_WIKI_FILES:
            continue
        pages.append(file)
    return sorted(pages)


def _page_rows() -> list[dict[str, Any]]:
    return [dict(row) for row in _pages().all()]


def _source_rows() -> list[dict[str, Any]]:
    return [dict(row) for row in _sources().all()]


def _log_rows() -> list[dict[str, Any]]:
    rows = [dict(row) for row in _logs().all()]
    rows.sort(key=lambda row: (str(row.get("created_at", "")), str(row.get("id", ""))))
    return rows


def _page_from_row(row: dict[str, Any]) -> KnowledgePage:
    return KnowledgePage(
        path=str(row.get("path") or row.get("id")),
        type=str(row.get("type") or "unknown"),
        title=str(row.get("title") or Path(str(row.get("path") or row.get("id"))).stem),
        summary=str(row.get("summary") or ""),
        updated_at=str(row.get("updated_at") or ""),
        source_ids=_json_load_list(row.get("source_ids")),
        tags=_json_load_list(row.get("tags")),
        aliases=_json_load_list(row.get("aliases")),
    )


def _page_detail_from_row(row: dict[str, Any]) -> KnowledgePageDetail:
    page = _page_from_row(row)
    body = str(row.get("body") or "")
    return KnowledgePageDetail(
        path=page.path,
        type=page.page_type,
        title=page.title,
        summary=page.summary,
        updated_at=page.updated_at,
        source_ids=page.source_ids,
        tags=page.tags,
        aliases=page.aliases,
        score=page.score,
        body=body,
        wikilinks=extract_wikilinks(body),
    )


def _source_from_row(row: dict[str, Any]) -> KnowledgeSource:
    return KnowledgeSource(
        source_id=str(row.get("source_id") or row.get("id")),
        kind=str(row.get("kind") or "note"),  # type: ignore[arg-type]
        title=str(row.get("title") or row.get("source_id") or row.get("id")),
        created_at=str(row.get("created_at") or ""),
        raw_path=str(row.get("raw_path") or ""),
        extracted_path=str(row.get("extracted_path")) if row.get("extracted_path") else None,
        note_id=str(row.get("note_id")) if row.get("note_id") else None,
        original_filename=str(row.get("original_filename")) if row.get("original_filename") else None,
    )


def _standard_page_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _json_load_dict(row.get("metadata"))
    metadata.update(
        {
            "type": str(row.get("type") or "unknown"),
            "title": str(row.get("title") or ""),
            "summary": str(row.get("summary") or ""),
            "updated_at": str(row.get("updated_at") or ""),
            "source_ids": _json_load_list(row.get("source_ids")),
            "tags": _json_load_list(row.get("tags")),
            "aliases": _json_load_list(row.get("aliases")),
        }
    )
    return metadata


def _page_markdown(row: dict[str, Any]) -> str:
    return _frontmatter_to_text(_standard_page_metadata(row), str(row.get("body") or ""))


def _page_from_file(path: Path) -> KnowledgePage:
    raw = path.read_text(encoding="utf-8")
    metadata, _ = parse_frontmatter(raw)
    rel = path.resolve().relative_to(_wiki_root().resolve()).as_posix()
    return KnowledgePage(
        path=rel,
        type=str(metadata.get("type", "unknown")),
        title=str(metadata.get("title", path.stem)),
        summary=str(metadata.get("summary", "")),
        updated_at=str(metadata.get("updated_at", "")),
        source_ids=_normalize_list(metadata.get("source_ids")),
        tags=_normalize_list(metadata.get("tags")),
        aliases=_normalize_list(metadata.get("aliases")),
    )


def _replace_links(from_path: str, wikilinks: list[str]) -> None:
    _links().delete_where("from_path = ?", (from_path,))
    created_at = _iso_now()
    for index, target in enumerate(wikilinks):
        link_id = f"{from_path}::{index}::{_sanitize_slug(target)}"
        _links().set(
            link_id,
            {
                "id": link_id,
                "from_path": from_path,
                "target": target,
                "created_at": created_at,
            },
        )


def _upsert_page_from_markdown(path: str, content: str, *, strict_writer_path: bool = False) -> str:
    rel = _normalize_write_path(path) if strict_writer_path else _normalize_wiki_read_path(path)
    metadata, body = parse_frontmatter(content)
    page_type = str(metadata.get("type") or ("overview" if rel == "overview.md" else "unknown"))
    title = str(metadata.get("title") or Path(rel).stem.replace("-", " ").title())
    summary = str(metadata.get("summary") or "")
    updated_at = str(metadata.get("updated_at") or _iso_now())
    source_ids = _normalize_list(metadata.get("source_ids"))
    tags = _normalize_list(metadata.get("tags"))
    aliases = _normalize_list(metadata.get("aliases"))
    now = _iso_now()
    existing = _pages().get(rel)
    created_at = str(existing.get("created_at")) if existing else now
    row = {
        "id": rel,
        "path": rel,
        "type": page_type,
        "title": title,
        "summary": summary,
        "body": body,
        "updated_at": updated_at,
        "source_ids": _json_dumps(source_ids),
        "tags": _json_dumps(tags),
        "aliases": _json_dumps(aliases),
        "metadata": _json_dumps(metadata),
        "created_at": created_at,
    }
    _pages().set(rel, row)
    _replace_links(rel, extract_wikilinks(body))
    return rel


def _upsert_source(
    source: KnowledgeSource,
    *,
    content_text: str = "",
    extracted_text: str | None = None,
    raw_bytes: bytes | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    existing = _sources().get(source.source_id)
    existing_row = dict(existing) if existing else {}
    row = {
        "id": source.source_id,
        "source_id": source.source_id,
        "kind": source.kind,
        "title": source.title,
        "created_at": source.created_at,
        "raw_path": source.raw_path,
        "extracted_path": source.extracted_path,
        "note_id": source.note_id,
        "original_filename": source.original_filename,
        "content_text": content_text or str(existing_row.get("content_text") or ""),
        "extracted_text": extracted_text if extracted_text is not None else existing_row.get("extracted_text"),
        "raw_bytes": raw_bytes if raw_bytes is not None else existing_row.get("raw_bytes"),
        "metadata": _json_dumps(metadata or _json_load_dict(existing_row.get("metadata"))),
    }
    _sources().set(source.source_id, row)


def _seed_default_pages() -> None:
    if _page_rows():
        return
    content = _frontmatter_to_text(
        {
            "type": "overview",
            "title": "Knowledge Overview",
            "summary": "Top-level summary page for the local knowledge vault.",
            "updated_at": _iso_now(),
            "source_ids": [],
            "tags": ["overview"],
            "aliases": ["Vault Overview"],
        },
        "This page summarizes the local knowledge base.\n",
    )
    _upsert_page_from_markdown("overview.md", content)


def _vault_has_importable_pages(vault: Path) -> bool:
    return bool(_iter_wiki_pages(vault / "wiki"))


def _ensure_mirror_structure() -> None:
    vault = _vault_path()
    vault.mkdir(parents=True, exist_ok=True)
    for relative in VAULT_STRUCTURE:
        (vault / relative).mkdir(parents=True, exist_ok=True)
    agents_file = vault / "AGENTS.md"
    if not agents_file.exists():
        _atomic_write(agents_file, AGENTS_TEMPLATE)
    home_file = vault / "Home.md"
    if not home_file.exists():
        _atomic_write(home_file, HOME_TEMPLATE)


def _build_index_text() -> str:
    pages = [_page_from_row(row) for row in _page_rows()]
    pages.sort(key=lambda page: page.path)
    lines = [
        "# Knowledge Index",
        "",
        "_Generated deterministically from database-backed wiki page metadata._",
        "",
        "| Path | Type | Title | Summary | Tags | Aliases | Updated At |",
        "|---|---|---|---|---|---|---|",
    ]
    for page in pages:
        tags = ", ".join(page.tags)
        aliases = ", ".join(page.aliases)
        summary = page.summary.replace("|", "/")
        title = page.title.replace("|", "/")
        lines.append(
            f"| {page.path} | {page.page_type} | {title} | {summary} | {tags} | {aliases} | {page.updated_at} |"
        )
    return "\n".join(lines).strip() + "\n"


def _build_log_text() -> str:
    lines = ["# Knowledge Log", ""]
    for row in _log_rows():
        entry = str(row.get("entry") or "").strip()
        if entry:
            lines.append(entry)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _source_raw_markdown(row: dict[str, Any]) -> str:
    source = _source_from_row(row)
    metadata = _json_load_dict(row.get("metadata"))
    metadata.setdefault("source_id", source.source_id)
    metadata.setdefault("source_kind", source.kind)
    metadata.setdefault("title", source.title)
    metadata.setdefault("created_at", source.created_at)
    if source.note_id:
        metadata.setdefault("note_id", source.note_id)
    if source.original_filename:
        metadata.setdefault("original_filename", source.original_filename)
    if source.extracted_path:
        metadata.setdefault("extracted_path", source.extracted_path)
    body = str(row.get("content_text") or row.get("extracted_text") or "")
    return _frontmatter_to_text(metadata, body)


def _source_extracted_markdown(row: dict[str, Any]) -> str:
    source = _source_from_row(row)
    metadata = _json_load_dict(row.get("metadata"))
    metadata.update(
        {
            "source_id": source.source_id,
            "source_kind": source.kind,
            "title": source.title,
            "created_at": source.created_at,
            "extracted_path": source.extracted_path,
        }
    )
    if source.original_filename:
        metadata["original_filename"] = source.original_filename
    body = str(row.get("extracted_text") or row.get("content_text") or "")
    return _frontmatter_to_text(metadata, body)


def _export_source_row(row: dict[str, Any]) -> None:
    source = _source_from_row(row)
    if source.raw_path:
        raw_target = _safe_relative(_vault_path(), _vault_path() / source.raw_path)
        raw_bytes = _coerce_bytes(row.get("raw_bytes"))
        if raw_bytes is not None:
            _atomic_write_bytes(raw_target, raw_bytes)
        else:
            _atomic_write(raw_target, _source_raw_markdown(row))
    if source.extracted_path:
        extracted_target = _safe_relative(_vault_path(), _vault_path() / source.extracted_path)
        _atomic_write(extracted_target, _source_extracted_markdown(row))


def export_vault_mirror() -> None:
    """Export canonical DB rows to the Obsidian-compatible markdown mirror."""
    _ensure_storage_initialized()
    _ensure_mirror_structure()

    for row in _page_rows():
        target = _safe_relative(_wiki_root(), _wiki_root() / str(row.get("path")))
        _atomic_write(target, _page_markdown(row))

    for row in _source_rows():
        _export_source_row(row)

    _atomic_write(_wiki_root() / "index.md", _build_index_text())
    _atomic_write(_wiki_root() / "log.md", _build_log_text())


def ensure_vault_initialized() -> None:
    _ensure_storage_initialized()
    if not _page_rows():
        vault = _vault_path()
        if _vault_has_importable_pages(vault):
            import_vault_to_db(vault, export_after=False)
        if not _page_rows():
            _seed_default_pages()
    export_vault_mirror()


def rebuild_index() -> str:
    ensure_vault_initialized()
    content = _build_index_text()
    _atomic_write(_wiki_root() / "index.md", content)
    return content


def _parse_index_rows(index_text: str) -> list[KnowledgePage]:
    rows: list[KnowledgePage] = []
    for line in index_text.splitlines():
        if not line.startswith("|"):
            continue
        if line.startswith("|---") or "Path" in line:
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if len(parts) < 7:
            continue
        path, page_type, title, summary, tags, aliases, updated_at = parts[:7]
        rows.append(
            KnowledgePage(
                path=path,
                type=page_type,
                title=title,
                summary=summary,
                updated_at=updated_at,
                source_ids=[],
                tags=_normalize_list(tags),
                aliases=_normalize_list(aliases),
            )
        )
    return rows


def _index_text() -> str:
    ensure_vault_initialized()
    return _build_index_text()


def _log_path() -> Path:
    return _wiki_root() / "log.md"


def _log_id(created_at: str, operation: str, target: str) -> str:
    key = f"{created_at}\n{operation}\n{target}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def append_log(operation: str, target: str) -> str:
    created_at = _iso_now()
    entry = f"## [{created_at}] {operation} | {target}"
    _logs().set(
        _log_id(created_at, operation, target),
        {
            "id": _log_id(created_at, operation, target),
            "created_at": created_at,
            "operation": operation,
            "target": target,
            "entry": entry,
        },
    )
    _atomic_write(_log_path(), _build_log_text())
    return entry


def _last_log_entry() -> str | None:
    rows = _log_rows()
    if not rows:
        return None
    return str(rows[-1].get("entry") or "") or None


def _tokenize(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(value or "") if token}


def _score_page(page: KnowledgePage, query_tokens: set[str]) -> float:
    haystack = " ".join([page.title, page.summary, " ".join(page.tags), " ".join(page.aliases)])
    page_tokens = _tokenize(haystack)
    if not page_tokens:
        return 0.0
    overlap = len(query_tokens & page_tokens)
    if overlap == 0:
        return 0.0
    return overlap / max(len(query_tokens), 1)


def list_pages(page_type: str | None = None, q: str | None = None) -> list[KnowledgePage]:
    ensure_vault_initialized()
    pages = [_page_from_row(row) for row in _page_rows()]

    if page_type:
        target = page_type.strip().lower()
        pages = [page for page in pages if page.page_type == target]

    if q and q.strip():
        query_tokens = _tokenize(q)
        scored: list[KnowledgePage] = []
        for page in pages:
            score = _score_page(page, query_tokens)
            if score > 0:
                scored.append(page.model_copy(update={"score": score}))
        scored.sort(key=lambda page: (page.score or 0, page.updated_at, page.path), reverse=True)
        return scored

    return sorted(pages, key=lambda page: (page.updated_at, page.path), reverse=True)


def search_pages(query: str, page_type: str | None = None, limit: int = 5) -> list[KnowledgePage]:
    pages = list_pages(page_type=page_type, q=query)
    return pages[: max(1, min(limit, 25))]


def get_page(path: str) -> KnowledgePageDetail:
    ensure_vault_initialized()
    rel = _normalize_wiki_read_path(path)
    row = _pages().get(rel)
    if not row:
        raise FileNotFoundError(path)
    return _page_detail_from_row(dict(row))


def list_sources() -> list[KnowledgeSource]:
    ensure_vault_initialized()
    sources = [_source_from_row(row) for row in _source_rows()]
    sources.sort(key=lambda item: item.created_at, reverse=True)
    return sources


def get_source(source_id: str) -> KnowledgeSource:
    ensure_vault_initialized()
    row = _sources().get(source_id)
    if not row:
        raise FileNotFoundError(source_id)
    return _source_from_row(dict(row))


def get_source_attachment(source_id: str) -> dict[str, Any]:
    ensure_vault_initialized()
    row = _sources().get(source_id)
    if not row:
        raise FileNotFoundError(source_id)

    source = _source_from_row(dict(row))
    raw_bytes = _coerce_bytes(row.get("raw_bytes"))
    if raw_bytes is None:
        raw_target = _safe_relative(_vault_path(), _vault_path() / source.raw_path)
        raw_bytes = raw_target.read_bytes()

    filename = source.original_filename or source.title or Path(source.raw_path).name
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return {
        "source": source,
        "filename": filename,
        "content": raw_bytes,
        "mime_type": mime_type,
    }


def get_status() -> KnowledgeStatus:
    ensure_vault_initialized()
    return KnowledgeStatus(
        vault_path=str(_vault_path()),
        initialized=True,
        page_count=len(_page_rows()),
        source_count=len(_source_rows()),
        last_log_entry=_last_log_entry(),
    )


def _source_page_markdown(source: KnowledgeSource) -> str:
    rel_raw = source.raw_path
    rel_extracted = source.extracted_path or ""
    body = [
        f"Source `{source.source_id}` captured from `{source.kind}` input.",
        "",
        f"- Raw: `{rel_raw}`",
    ]
    if rel_extracted:
        body.append(f"- Extracted: `{rel_extracted}`")
    if source.note_id:
        body.append(f"- Note ID: `{source.note_id}`")
    if source.original_filename:
        body.append(f"- Original filename: `{source.original_filename}`")
    return _frontmatter_to_text(
        {
            "type": "source",
            "title": source.title,
            "summary": f"Source snapshot {source.source_id}",
            "updated_at": _iso_now(),
            "source_ids": [source.source_id],
            "tags": ["source", source.kind],
            "aliases": [source.source_id],
        },
        "\n".join(body),
    )


def _snapshot_note(note_id: str) -> tuple[KnowledgeSource, str]:
    note = notes_service.get_note(note_id)
    if not note:
        raise FileNotFoundError(note_id)

    source_id = f"note-{_utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    filename = f"{source_id}.md"
    tags = note.get("tags", [])
    content_body = str(note.get("content", "")).strip()
    title = str(note.get("title", "Untitled Note")).strip() or "Untitled Note"
    created_at = _iso_now()
    raw_path = f"raw/notes/{filename}"
    metadata = {
        "source_id": source_id,
        "source_kind": "note",
        "note_id": note_id,
        "title": title,
        "tags": tags,
        "created_at": created_at,
    }
    markdown = _frontmatter_to_text(metadata, content_body)
    source = KnowledgeSource(
        source_id=source_id,
        kind="note",
        title=title,
        created_at=created_at,
        raw_path=raw_path,
        extracted_path=None,
        note_id=note_id,
    )
    _upsert_source(source, content_text=content_body, raw_bytes=markdown.encode("utf-8"), metadata=metadata)
    _export_source_row(dict(_sources().get(source.source_id)))
    return source, content_body


def _extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(text.strip())
    return "\n\n".join(chunks).strip()


def _extract_docx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            try:
                document_xml = archive.read("word/document.xml")
            except KeyError as exc:
                raise ValueError("Invalid .docx file: missing word/document.xml.") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid .docx file.") from exc

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as exc:
        raise ValueError("Invalid .docx file: document XML could not be parsed.") from exc

    paragraphs: list[str] = []
    for paragraph in root.iter(f"{DOCX_WORD_NS}p"):
        chunks: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{DOCX_WORD_NS}t" and node.text:
                chunks.append(node.text)
            elif node.tag == f"{DOCX_WORD_NS}tab":
                chunks.append("\t")
            elif node.tag in {f"{DOCX_WORD_NS}br", f"{DOCX_WORD_NS}cr"}:
                chunks.append("\n")
        text = "".join(chunks).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs).strip()


def ingest_file_bytes(filename: str, data: bytes) -> tuple[KnowledgeSource, str]:
    ensure_vault_initialized()
    suffix = Path(filename).suffix.lower()
    if suffix not in {".md", ".txt", ".pdf", ".docx"}:
        raise ValueError("Unsupported file type. Only .md, .txt, .pdf, and .docx are allowed.")

    source_id = f"file-{_utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    upload_name = f"{source_id}{suffix}"
    raw_path = f"raw/uploads/{upload_name}"

    if suffix == ".pdf":
        extracted_text = _extract_pdf_text(data)
        content_text = ""
    elif suffix == ".docx":
        extracted_text = _extract_docx_text(data)
        content_text = ""
    else:
        content_text = _decode_bytes(data)
        extracted_text = content_text

    if not extracted_text:
        extracted_text = "(No extractable text found in source.)"

    extracted_path = f"raw/extracted/{source_id}.md"
    created_at = _iso_now()
    metadata = {
        "source_id": source_id,
        "source_kind": "file",
        "title": filename,
        "original_filename": filename,
        "created_at": created_at,
        "extracted_path": extracted_path,
    }
    source = KnowledgeSource(
        source_id=source_id,
        kind="file",
        title=filename,
        created_at=created_at,
        raw_path=raw_path,
        extracted_path=extracted_path,
        original_filename=filename,
    )
    _upsert_source(
        source,
        content_text=content_text,
        extracted_text=extracted_text,
        raw_bytes=data,
        metadata=metadata,
    )
    _export_source_row(dict(_sources().get(source.source_id)))
    return source, extracted_text


def _parse_writeset(text: str) -> list[dict[str, str]]:
    payload = text.strip()
    match = WRITESET_RE.search(payload)
    if match:
        payload = match.group(1)
    parsed = json.loads(payload)
    writes = parsed.get("writes", [])
    if not isinstance(writes, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in writes:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).strip()
        content = str(item.get("content", "")).strip()
        if not path or not content:
            continue
        normalized.append({"path": path, "content": content})
    return normalized


def _build_writer_prompt(operation: str, source: KnowledgeSource | None, source_text: str, candidate_pages: list[KnowledgePage]) -> str:
    candidates = [
        {
            "path": page.path,
            "type": page.page_type,
            "title": page.title,
            "summary": page.summary,
            "tags": page.tags,
            "aliases": page.aliases,
        }
        for page in candidate_pages
    ]
    source_payload = source.model_dump() if source else None
    return (
        "Produce a JSON object with a single key `writes`.\n"
        "Each item in `writes` must include:\n"
        "- `path`: relative markdown path under wiki/ (examples: entities/foo.md, concepts/bar.md, analyses/baz.md)\n"
        "- `content`: full markdown file content including YAML frontmatter.\n"
        "Never include wiki/index.md or wiki/log.md.\n"
        "Use Obsidian wikilinks in bodies when relevant.\n\n"
        f"Operation: {operation}\n"
        f"Source: {json.dumps(source_payload, ensure_ascii=True)}\n"
        f"Candidate pages: {json.dumps(candidates, ensure_ascii=True)}\n"
        "Source text (truncated):\n"
        f"{source_text[:12000]}"
    )


def _call_writer_model(operation: str, source: KnowledgeSource | None, source_text: str, candidate_pages: list[KnowledgePage]) -> list[dict[str, str]]:
    from langchain_core.messages import HumanMessage, SystemMessage

    prompt = _build_writer_prompt(operation, source, source_text, candidate_pages)
    response = get_llm().invoke(
        [
            SystemMessage(
                content=(
                    "You are a strict knowledge-wiki writer. "
                    "Return only JSON. Do not include commentary."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )
    content = getattr(response, "content", "")
    if isinstance(content, list):
        text = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
    else:
        text = str(content)
    return _parse_writeset(text)


def _apply_writer_writes(writes: list[dict[str, str]]) -> list[str]:
    touched: list[str] = []
    for item in writes:
        rel = _upsert_page_from_markdown(item["path"], item["content"].strip() + "\n", strict_writer_path=True)
        touched.append(rel)
    return sorted(set(touched))


def _ensure_source_page(source: KnowledgeSource) -> str:
    rel = f"sources/{_sanitize_slug(source.source_id)}.md"
    _upsert_page_from_markdown(rel, _source_page_markdown(source), strict_writer_path=True)
    return rel


def ingest_note(note_id: str) -> KnowledgeIngestResult:
    ensure_vault_initialized()
    with _operation_lock:
        source, source_text = _snapshot_note(note_id)
        source_page = _ensure_source_page(source)
        candidates = search_pages(query=f"{source.title} {source_text[:500]}", limit=8)
        writes = _call_writer_model("ingest_note", source, source_text, candidates)
        touched = _apply_writer_writes(writes)
        touched.append(source_page)
        rebuild_index()
        log_entry = append_log("ingest_note", f"note:{note_id} source:{source.source_id}")
        export_vault_mirror()
        return KnowledgeIngestResult(
            operation="ingest_note",
            source=source,
            touched_pages=sorted(set(touched)),
            log_entry=log_entry,
        )


def ingest_file(filename: str, data: bytes) -> KnowledgeIngestResult:
    ensure_vault_initialized()
    with _operation_lock:
        source, source_text = ingest_file_bytes(filename=filename, data=data)
        source_page = _ensure_source_page(source)
        candidates = search_pages(query=f"{source.title} {source_text[:500]}", limit=8)
        writes = _call_writer_model("ingest_file", source, source_text, candidates)
        touched = _apply_writer_writes(writes)
        touched.append(source_page)
        rebuild_index()
        log_entry = append_log("ingest_file", f"file:{filename} source:{source.source_id}")
        export_vault_mirror()
        return KnowledgeIngestResult(
            operation="ingest_file",
            source=source,
            touched_pages=sorted(set(touched)),
            log_entry=log_entry,
        )


def lint_knowledge_base() -> KnowledgeIngestResult:
    ensure_vault_initialized()
    with _operation_lock:
        index_text = _index_text()
        log_text = _build_log_text()
        candidates = list_pages()[:50]
        context = f"Index:\n{index_text}\n\nRecent log:\n{log_text[-8000:]}"
        writes = _call_writer_model("lint", None, context, candidates)
        touched = _apply_writer_writes(writes)
        rebuild_index()
        log_entry = append_log("lint", f"pages:{len(touched)}")
        export_vault_mirror()
        return KnowledgeIngestResult(
            operation="lint",
            source=None,
            touched_pages=touched,
            log_entry=log_entry,
        )


def _infer_upload_path(vault: Path, source_id: str) -> str | None:
    uploads_root = vault / "raw" / "uploads"
    if not uploads_root.exists():
        return None
    matches = sorted(uploads_root.glob(f"{source_id}*"))
    if not matches:
        return None
    return matches[0].resolve().relative_to(vault.resolve()).as_posix()


def _source_from_markdown(path: Path) -> KnowledgeSource | None:
    vault = _vault_path()
    return _source_record_from_markdown(path, vault)[0]


def _source_record_from_markdown(path: Path, vault: Path) -> tuple[KnowledgeSource | None, str, str | None, bytes | None, dict[str, Any]]:
    if not path.exists():
        return None, "", None, None, {}
    raw_bytes = path.read_bytes()
    metadata, body = parse_frontmatter(_decode_bytes(raw_bytes))
    source_id = str(metadata.get("source_id", "")).strip()
    kind = str(metadata.get("source_kind", "")).strip()
    if not source_id or kind not in {"note", "file"}:
        return None, "", None, raw_bytes, metadata
    rel = path.resolve().relative_to(vault.resolve()).as_posix()
    extracted_path = metadata.get("extracted_path")
    if kind == "file":
        extracted_path = str(extracted_path or rel)
        raw_path = str(metadata.get("raw_path") or _infer_upload_path(vault, source_id) or rel)
        upload_path = vault / raw_path
        stored_bytes = upload_path.read_bytes() if upload_path.exists() else raw_bytes
        content_text = _decode_bytes(stored_bytes) if raw_path != rel else body
        extracted_text = body
    else:
        raw_path = rel
        stored_bytes = raw_bytes
        content_text = body
        extracted_text = None
    source = KnowledgeSource(
        source_id=source_id,
        kind=kind,  # type: ignore[arg-type]
        title=str(metadata.get("title", source_id)),
        created_at=str(metadata.get("created_at", "")),
        raw_path=raw_path,
        extracted_path=extracted_path if kind == "file" else None,
        note_id=str(metadata.get("note_id")) if metadata.get("note_id") else None,
        original_filename=str(metadata.get("original_filename")) if metadata.get("original_filename") else None,
    )
    return source, content_text, extracted_text, stored_bytes, metadata


def _import_log_file(vault: Path) -> int:
    log_file = vault / "wiki" / "log.md"
    if not log_file.exists():
        return 0
    imported = 0
    for line in log_file.read_text(encoding="utf-8").splitlines():
        match = LOG_ENTRY_RE.match(line.strip())
        if not match:
            continue
        created_at = match.group("created_at").strip()
        operation = match.group("operation").strip()
        target = match.group("target").strip()
        log_id = _log_id(created_at, operation, target)
        _logs().set(
            log_id,
            {
                "id": log_id,
                "created_at": created_at,
                "operation": operation,
                "target": target,
                "entry": line.strip(),
            },
        )
        imported += 1
    return imported


def import_vault_to_db(vault_path: str | Path | None = None, *, export_after: bool = True) -> dict[str, int]:
    """Import an existing Obsidian-style vault into canonical DB tables."""
    _ensure_storage_initialized()
    vault = Path(vault_path) if vault_path is not None else _vault_path()
    counts = {"pages": 0, "sources": 0, "logs": 0, "links": 0}

    wiki_root = vault / "wiki"
    for file in _iter_wiki_pages(wiki_root):
        rel = file.resolve().relative_to(wiki_root.resolve()).as_posix()
        _upsert_page_from_markdown(rel, file.read_text(encoding="utf-8"))
        counts["pages"] += 1

    source_files = []
    for relative in ("raw/notes", "raw/extracted"):
        root = vault / relative
        if root.exists():
            source_files.extend(sorted(root.glob("*.md")))
    for file in source_files:
        source, content_text, extracted_text, raw_bytes, metadata = _source_record_from_markdown(file, vault)
        if not source:
            continue
        _upsert_source(
            source,
            content_text=content_text,
            extracted_text=extracted_text,
            raw_bytes=raw_bytes,
            metadata=metadata,
        )
        counts["sources"] += 1

    counts["logs"] = _import_log_file(vault)
    counts["links"] = len([dict(row) for row in _links().all()])

    if export_after:
        export_vault_mirror()
    return counts

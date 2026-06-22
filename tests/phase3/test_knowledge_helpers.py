"""Phase 3: Unit coverage for knowledge vault helpers."""

import io
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest


def _service(monkeypatch, tmp_path):
    import backend.services.knowledge_service as knowledge_service

    monkeypatch.setattr(
        knowledge_service.settings,
        "database_path",
        str(tmp_path / "jarvis.db"),
        raising=False,
    )
    monkeypatch.setattr(knowledge_service.settings, "database_url", None, raising=False)
    monkeypatch.setattr(
        knowledge_service.settings,
        "knowledge_vault_path",
        str(tmp_path / "knowledge_vault"),
        raising=False,
    )
    return knowledge_service


def _docx_bytes(*paragraphs: str) -> bytes:
    body = "".join(
        f"<w:p><w:r><w:t>{escape(paragraph)}</w:t></w:r></w:p>"
        for paragraph in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body>"
        "</w:document>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def test_frontmatter_roundtrip(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    text = knowledge_service._frontmatter_to_text(
        {
            "type": "concept",
            "title": "Roundtrip",
            "summary": "Check",
            "updated_at": "2026-04-15T00:00:00+00:00",
            "source_ids": ["s1"],
            "tags": ["a", "b"],
            "aliases": ["x"],
        },
        "Body with [[Links]].",
    )
    meta, body = knowledge_service.parse_frontmatter(text)
    assert meta["type"] == "concept"
    assert meta["source_ids"] == ["s1"]
    assert body == "Body with [[Links]]."


def test_extract_wikilinks_deduplicates(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    links = knowledge_service.extract_wikilinks("A [[One]] and [[Two]] and [[one]]")
    assert links == ["One", "Two"]


def test_resolve_page_path_blocks_escape(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service.ensure_vault_initialized()
    with pytest.raises(ValueError):
        knowledge_service._resolve_wiki_page_path("../outside.md")


def test_snapshot_note_is_immutable(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service.ensure_vault_initialized()

    calls = {"count": 0}

    def fake_get_note(_note_id):
        calls["count"] += 1
        return {
            "id": "n1",
            "title": "Note title",
            "content": f"content version {calls['count']}",
            "tags": ["x"],
        }

    monkeypatch.setattr(knowledge_service.notes_service, "get_note", fake_get_note)

    source1, _ = knowledge_service._snapshot_note("n1")
    source2, _ = knowledge_service._snapshot_note("n1")

    raw_root = Path(knowledge_service.settings.knowledge_vault_path) / "raw" / "notes"
    files = sorted(raw_root.glob("*.md"))
    assert len(files) == 2
    assert source1.source_id != source2.source_id


def test_file_ingest_creates_upload_and_sidecar(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    source, extracted = knowledge_service.ingest_file_bytes("memo.txt", b"alpha beta")
    assert source.kind == "file"
    assert "alpha beta" in extracted
    vault = Path(knowledge_service.settings.knowledge_vault_path)
    assert (vault / source.raw_path).exists()
    assert source.extracted_path is not None
    assert (vault / source.extracted_path).exists()


def test_docx_file_ingest_extracts_upload_and_sidecar(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    source, extracted = knowledge_service.ingest_file_bytes(
        "memo.docx",
        _docx_bytes("Alpha launch", "Beta plan"),
    )
    vault = Path(knowledge_service.settings.knowledge_vault_path)
    raw_path = vault / source.raw_path
    extracted_path = vault / str(source.extracted_path)

    assert source.kind == "file"
    assert source.original_filename == "memo.docx"
    assert raw_path.suffix == ".docx"
    assert raw_path.exists()
    assert extracted_path.exists()
    assert "Alpha launch" in extracted
    assert "Beta plan" in extracted_path.read_text(encoding="utf-8")


def test_docx_file_ingest_rejects_invalid_docx(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="Invalid .docx"):
        knowledge_service.ingest_file_bytes("broken.docx", b"not a zip")


def test_rebuild_index_is_deterministic(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service.ensure_vault_initialized()

    knowledge_service._upsert_page_from_markdown(
        "entities/alpha.md",
        knowledge_service._frontmatter_to_text(
            {
                "type": "entity",
                "title": "Alpha",
                "summary": "A page",
                "updated_at": "2026-04-15T00:00:00+00:00",
                "source_ids": [],
                "tags": [],
                "aliases": [],
            },
            "Body",
        ),
    )

    idx1 = knowledge_service.rebuild_index()
    idx2 = knowledge_service.rebuild_index()
    assert idx1 == idx2


def test_import_vault_to_db_is_idempotent(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    vault = tmp_path / "legacy_vault"
    page = vault / "wiki" / "entities" / "alpha.md"
    page.parent.mkdir(parents=True)
    page.write_text(
        knowledge_service._frontmatter_to_text(
            {
                "type": "entity",
                "title": "Alpha",
                "summary": "Imported page",
                "updated_at": "2026-04-15T00:00:00+00:00",
                "source_ids": ["source-1"],
                "tags": ["import"],
                "aliases": ["A"],
            },
            "Body with [[Beta]].",
        ),
        encoding="utf-8",
    )
    raw = vault / "raw" / "notes" / "source-1.md"
    raw.parent.mkdir(parents=True)
    raw.write_text(
        knowledge_service._frontmatter_to_text(
            {
                "source_id": "source-1",
                "source_kind": "note",
                "note_id": "note-1",
                "title": "Source One",
                "created_at": "2026-04-15T00:00:00+00:00",
            },
            "Original note text",
        ),
        encoding="utf-8",
    )

    first = knowledge_service.import_vault_to_db(vault)
    second = knowledge_service.import_vault_to_db(vault)

    assert first["pages"] == 1
    assert second["pages"] == 1
    assert len([page for page in knowledge_service.list_pages() if page.path == "entities/alpha.md"]) == 1
    assert len([source for source in knowledge_service.list_sources() if source.source_id == "source-1"]) == 1


def test_get_page_uses_db_when_mirror_file_is_missing(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service._upsert_page_from_markdown(
        "concepts/db-only.md",
        knowledge_service._frontmatter_to_text(
            {
                "type": "concept",
                "title": "DB Only",
                "summary": "Stored in the database",
                "updated_at": "2026-04-15T00:00:00+00:00",
                "source_ids": [],
                "tags": ["db"],
                "aliases": [],
            },
            "Canonical body.",
        ),
    )

    page_path = tmp_path / "knowledge_vault" / "wiki" / "concepts" / "db-only.md"
    assert not page_path.exists()

    detail = knowledge_service.get_page("concepts/db-only.md")

    assert detail.title == "DB Only"
    assert detail.body == "Canonical body."
    assert page_path.exists()


def test_wikilinks_are_persisted_as_structured_links(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service._upsert_page_from_markdown(
        "concepts/linked.md",
        knowledge_service._frontmatter_to_text(
            {
                "type": "concept",
                "title": "Linked",
                "summary": "Has links",
                "updated_at": "2026-04-15T00:00:00+00:00",
                "source_ids": [],
                "tags": [],
                "aliases": [],
            },
            "See [[Alpha]] and [[Beta]] and [[alpha]].",
        ),
    )

    links = [dict(row) for row in knowledge_service._links().all()]

    assert [link["target"] for link in links] == ["Alpha", "Beta"]

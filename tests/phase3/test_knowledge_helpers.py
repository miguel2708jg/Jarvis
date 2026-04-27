"""Phase 3: Unit coverage for knowledge vault helpers."""

from pathlib import Path

import pytest


def _service(monkeypatch, tmp_path):
    import backend.services.knowledge_service as knowledge_service

    monkeypatch.setattr(
        knowledge_service.settings,
        "knowledge_vault_path",
        str(tmp_path / "knowledge_vault"),
        raising=False,
    )
    return knowledge_service


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


def test_rebuild_index_is_deterministic(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service.ensure_vault_initialized()

    page = knowledge_service._wiki_root() / "entities" / "alpha.md"
    knowledge_service._atomic_write(
        page,
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

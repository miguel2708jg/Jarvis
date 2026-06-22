"""Phase 3: Service tests for knowledge ingest and lint orchestration."""

from pathlib import Path

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


def _page_markdown(knowledge_service, page_type: str, title: str, body: str, source_ids: list[str] | None = None):
    return knowledge_service._frontmatter_to_text(
        {
            "type": page_type,
            "title": title,
            "summary": f"{title} summary",
            "updated_at": "2026-04-15T00:00:00+00:00",
            "source_ids": source_ids or [],
            "tags": [],
            "aliases": [],
        },
        body,
    )


def test_ingest_note_creates_raw_source_pages_index_and_log(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service.ensure_vault_initialized()

    monkeypatch.setattr(
        knowledge_service.notes_service,
        "get_note",
        lambda _note_id: {
            "id": "note-1",
            "title": "Launch Plan",
            "content": "Alpha launch notes",
            "tags": ["plan"],
        },
    )
    monkeypatch.setattr(
        knowledge_service,
        "_call_writer_model",
        lambda *args, **kwargs: [
            {
                "path": "entities/launch-plan.md",
                "content": _page_markdown(
                    knowledge_service,
                    "entity",
                    "Launch Plan",
                    "Body linking [[Knowledge Overview]].",
                    source_ids=["fake"],
                ),
            }
        ],
    )

    result = knowledge_service.ingest_note("note-1")

    assert result.operation == "ingest_note"
    assert result.source is not None
    assert any(path.startswith("sources/") for path in result.touched_pages)
    assert "entities/launch-plan.md" in result.touched_pages

    vault = Path(knowledge_service.settings.knowledge_vault_path)
    assert list((vault / "raw" / "notes").glob("*.md"))
    assert (vault / "wiki" / "index.md").exists()
    log_text = (vault / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "ingest_note | note:note-1" in log_text
    assert knowledge_service._pages().get("entities/launch-plan.md") is not None
    assert knowledge_service._sources().get(result.source.source_id) is not None


def test_lint_applies_only_wiki_writes(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service.ensure_vault_initialized()

    monkeypatch.setattr(
        knowledge_service,
        "_call_writer_model",
        lambda *args, **kwargs: [
            {
                "path": "analyses/lint-report.md",
                "content": _page_markdown(knowledge_service, "analysis", "Lint Report", "No contradictions."),
            }
        ],
    )

    result = knowledge_service.lint_knowledge_base()
    assert result.operation == "lint"
    assert result.touched_pages == ["analyses/lint-report.md"]
    assert Path(knowledge_service.settings.knowledge_vault_path, "wiki", "analyses", "lint-report.md").exists()
    assert knowledge_service._pages().get("analyses/lint-report.md") is not None


def test_lint_rejects_writer_path_outside_wiki(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    knowledge_service.ensure_vault_initialized()

    monkeypatch.setattr(
        knowledge_service,
        "_call_writer_model",
        lambda *args, **kwargs: [{"path": "../escape.md", "content": "# bad"}],
    )

    with pytest.raises(ValueError):
        knowledge_service.lint_knowledge_base()

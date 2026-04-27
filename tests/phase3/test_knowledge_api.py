"""Phase 3: API tests for knowledge endpoints."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app(monkeypatch, tmp_path):
    import backend.services.knowledge_service as knowledge_service

    monkeypatch.setattr(
        knowledge_service.settings,
        "knowledge_vault_path",
        str(tmp_path / "knowledge_vault"),
        raising=False,
    )
    monkeypatch.setattr(
        knowledge_service.notes_service,
        "get_note",
        lambda note_id: {
            "id": note_id,
            "title": "API Note",
            "content": "Some content",
            "tags": ["api"],
        },
    )
    monkeypatch.setattr(
        knowledge_service,
        "_call_writer_model",
        lambda *args, **kwargs: [],
    )

    from backend.api.main import app

    return app


@pytest.mark.asyncio
async def test_knowledge_status_and_sources(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        status = await client.get("/knowledge/status")
        assert status.status_code == 200
        assert status.json()["initialized"] is True

        sources = await client.get("/knowledge/sources")
        assert sources.status_code == 200
        assert isinstance(sources.json(), list)


@pytest.mark.asyncio
async def test_ingest_note_and_fetch_page(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ingest = await client.post("/knowledge/ingest/note", json={"note_id": "note-123"})
        assert ingest.status_code == 200
        payload = ingest.json()
        assert payload["operation"] == "ingest_note"
        source_page = next(path for path in payload["touched_pages"] if path.startswith("sources/"))

        page = await client.get(f"/knowledge/pages/{source_page}")
        assert page.status_code == 200
        assert page.json()["type"] == "source"


@pytest.mark.asyncio
async def test_ingest_file_rejects_unsupported_extension(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("bad.exe", b"binary", "application/octet-stream")}
        response = await client.post("/knowledge/ingest/file", files=files)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_ingest_file_and_lint(app, monkeypatch, tmp_path):
    import backend.services.knowledge_service as knowledge_service

    monkeypatch.setattr(
        knowledge_service,
        "_call_writer_model",
        lambda *args, **kwargs: [],
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("memo.txt", b"hello", "text/plain")}
        ingest = await client.post("/knowledge/ingest/file", files=files)
        assert ingest.status_code == 200
        assert ingest.json()["operation"] == "ingest_file"

        lint = await client.post("/knowledge/lint", json={})
        assert lint.status_code == 200
        assert lint.json()["operation"] == "lint"

        pages = await client.get("/knowledge/pages")
        assert pages.status_code == 200
        assert isinstance(pages.json(), list)

        vault = Path(knowledge_service.settings.knowledge_vault_path)
        assert (vault / "wiki" / "index.md").exists()

"""Phase 3: API tests for knowledge endpoints."""

import io
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest
from httpx import ASGITransport, AsyncClient

AUTH_HEADERS = {
    "x-jarvis-internal-auth": "test-internal-token",
    "x-jarvis-user-email": "majg2708@gmail.com",
}


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


@pytest.fixture
def app(monkeypatch, tmp_path):
    from backend.config import settings
    import backend.services.knowledge_service as knowledge_service

    monkeypatch.setattr(settings, "auth_allowed_emails", "majg2708@gmail.com")
    monkeypatch.setattr(settings, "backend_internal_auth_token", "test-internal-token")
    monkeypatch.setattr(settings, "backend_auth_token_secret", "test-ws-secret")
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "jarvis.db"))
    monkeypatch.setattr(settings, "database_url", None, raising=False)
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        status = await client.get("/knowledge/status")
        assert status.status_code == 200
        assert status.json()["initialized"] is True

        sources = await client.get("/knowledge/sources")
        assert sources.status_code == 200
        assert isinstance(sources.json(), list)


@pytest.mark.asyncio
async def test_ingest_note_and_fetch_page(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        files = {"file": ("bad.exe", b"binary", "application/octet-stream")}
        response = await client.post("/knowledge/ingest/file", files=files)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_ingest_file_accepts_docx(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        files = {
            "file": (
                "memo.docx",
                _docx_bytes("API document upload"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        response = await client.post("/knowledge/ingest/file", files=files)
        assert response.status_code == 200
        assert response.json()["operation"] == "ingest_file"
        assert response.json()["source"]["original_filename"] == "memo.docx"


@pytest.mark.asyncio
async def test_ingest_file_rejects_invalid_docx(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        files = {
            "file": (
                "broken.docx",
                b"not a zip",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
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

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        files = {"file": ("memo.txt", b"hello", "text/plain")}
        ingest = await client.post("/knowledge/ingest/file", files=files)
        assert ingest.status_code == 200
        payload = ingest.json()
        assert payload["operation"] == "ingest_file"
        source_id = payload["source"]["source_id"]

        raw = await client.get(f"/knowledge/sources/{source_id}/raw")
        assert raw.status_code == 200
        assert raw.content == b"hello"

        lint = await client.post("/knowledge/lint", json={})
        assert lint.status_code == 200
        assert lint.json()["operation"] == "lint"

        pages = await client.get("/knowledge/pages")
        assert pages.status_code == 200
        assert isinstance(pages.json(), list)

        vault = Path(knowledge_service.settings.knowledge_vault_path)
        assert (vault / "wiki" / "index.md").exists()


@pytest.mark.asyncio
async def test_raw_source_download_missing_source_returns_404(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        response = await client.get("/knowledge/sources/missing/raw")
        assert response.status_code == 404

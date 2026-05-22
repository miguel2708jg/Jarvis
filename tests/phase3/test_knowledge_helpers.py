"""Phase 3: Unit coverage for knowledge vault helpers."""

import sys
import types
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
    monkeypatch.setattr(knowledge_service.settings, "object_storage_provider", "local", raising=False)
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
    assert source.raw_storage == "local"
    assert source.raw_object_key == source.raw_path
    assert "alpha beta" in extracted
    vault = Path(knowledge_service.settings.knowledge_vault_path)
    assert (vault / source.raw_path).exists()
    assert source.extracted_path is not None
    assert (vault / source.extracted_path).exists()


def test_file_ingest_s3_uses_railway_bucket_credentials(monkeypatch, tmp_path):
    knowledge_service = _service(monkeypatch, tmp_path)
    from backend.storage import object_store

    calls = {}

    class FakeConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeClient:
        def put_object(self, **kwargs):
            calls["put_object"] = kwargs

    def fake_client(*args, **kwargs):
        calls["client"] = {"args": args, "kwargs": kwargs}
        return FakeClient()

    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = fake_client
    fake_botocore = types.ModuleType("botocore")
    fake_botocore.__path__ = []
    fake_config_module = types.ModuleType("botocore.config")
    fake_config_module.Config = FakeConfig
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "botocore", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "botocore.config", fake_config_module)
    monkeypatch.setattr(knowledge_service.settings, "object_storage_provider", "s3", raising=False)
    monkeypatch.setattr(knowledge_service.settings, "s3_bucket", "jarvis-test-bucket", raising=False)
    monkeypatch.setattr(knowledge_service.settings, "s3_endpoint", "https://storage.railway.app", raising=False)
    monkeypatch.setattr(knowledge_service.settings, "s3_region", "auto", raising=False)
    monkeypatch.setattr(knowledge_service.settings, "s3_access_key_id", "railway-access", raising=False)
    monkeypatch.setattr(knowledge_service.settings, "s3_secret_access_key", "railway-secret", raising=False)

    source, extracted = knowledge_service.ingest_file_bytes("memo.txt", b"alpha beta")

    assert "alpha beta" in extracted
    assert source.raw_storage == "s3"
    assert source.raw_path == source.raw_object_key
    assert source.raw_object_key is not None
    assert source.raw_object_key.startswith("raw/uploads/file-")
    assert calls["put_object"] == {
        "Bucket": "jarvis-test-bucket",
        "Key": source.raw_object_key,
        "Body": b"alpha beta",
    }
    assert calls["client"]["args"] == ("s3",)
    assert calls["client"]["kwargs"]["endpoint_url"] == "https://storage.railway.app"
    assert calls["client"]["kwargs"]["region_name"] == "auto"
    assert calls["client"]["kwargs"]["aws_access_key_id"] == "railway-access"
    assert calls["client"]["kwargs"]["aws_secret_access_key"] == "railway-secret"
    assert calls["client"]["kwargs"]["config"].kwargs == {"s3": {"addressing_style": "virtual"}}
    vault = Path(knowledge_service.settings.knowledge_vault_path)
    assert source.extracted_path is not None
    assert (vault / source.extracted_path).exists()
    assert not (vault / source.raw_path).exists()


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

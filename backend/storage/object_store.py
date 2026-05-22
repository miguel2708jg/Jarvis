"""Object storage helpers for raw knowledge uploads."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.config import settings


StorageProvider = Literal["local", "s3"]


class ObjectStorageError(RuntimeError):
    """Raised when object storage is misconfigured or unavailable."""


class ObjectNotFoundError(FileNotFoundError):
    """Raised when a requested object cannot be found."""


@dataclass(frozen=True)
class StoredObject:
    provider: StorageProvider
    key: str


def _provider() -> StorageProvider:
    provider = settings.object_storage_provider.strip().lower()
    if provider in {"", "local"}:
        return "local"
    if provider == "s3":
        return "s3"
    raise ObjectStorageError(f"Unsupported object storage provider: {settings.object_storage_provider}")


def _raw_upload_key(source_id: str, suffix: str) -> str:
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return f"raw/uploads/{source_id}{clean_suffix.lower()}"


def _local_object_path(vault_path: Path, key: str) -> Path:
    candidate = vault_path / key
    resolved_base = vault_path.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as exc:
        raise ObjectStorageError(f"Unsafe object key outside vault: {key}") from exc
    return resolved_candidate


def _s3_client():
    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise ObjectStorageError("S3 storage requires boto3 and botocore to be installed.") from exc

    if not settings.s3_bucket:
        raise ObjectStorageError("S3_BUCKET or BUCKET is required when OBJECT_STORAGE_PROVIDER=s3.")
    if not settings.s3_endpoint:
        raise ObjectStorageError("S3_ENDPOINT or ENDPOINT is required when OBJECT_STORAGE_PROVIDER=s3.")
    if not settings.s3_access_key_id:
        raise ObjectStorageError("S3_ACCESS_KEY_ID or ACCESS_KEY_ID is required when OBJECT_STORAGE_PROVIDER=s3.")
    if not settings.s3_secret_access_key:
        raise ObjectStorageError("S3_SECRET_ACCESS_KEY or SECRET_ACCESS_KEY is required when OBJECT_STORAGE_PROVIDER=s3.")

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        region_name=settings.s3_region or "auto",
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=Config(s3={"addressing_style": "virtual"}),
    )


def put_raw_upload(vault_path: Path, source_id: str, suffix: str, data: bytes) -> StoredObject:
    key = _raw_upload_key(source_id, suffix)
    provider = _provider()
    if provider == "local":
        path = _local_object_path(vault_path, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return StoredObject(provider="local", key=key)

    _s3_client().put_object(Bucket=settings.s3_bucket, Key=key, Body=data)
    return StoredObject(provider="s3", key=key)


def get_raw_upload(vault_path: Path, provider: str | None, key: str) -> bytes:
    normalized_provider = (provider or "local").strip().lower()
    if normalized_provider == "local":
        path = _local_object_path(vault_path, key)
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise ObjectNotFoundError(key) from exc

    if normalized_provider != "s3":
        raise ObjectStorageError(f"Unsupported object storage provider: {provider}")

    try:
        response = _s3_client().get_object(Bucket=settings.s3_bucket, Key=key)
        body = response["Body"]
        try:
            return body.read()
        finally:
            close = getattr(body, "close", None)
            if close:
                close()
    except Exception as exc:
        error_code = getattr(getattr(exc, "response", None), "get", lambda *_: {})("Error", {}).get("Code")
        if error_code in {"NoSuchKey", "404", "NotFound"}:
            raise ObjectNotFoundError(key) from exc
        raise

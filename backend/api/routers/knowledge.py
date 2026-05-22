"""REST endpoints for the knowledge vault."""
import io
import mimetypes

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from backend.api.errors import llm_unavailable_message
from backend.models.knowledge import (
    KnowledgeIngestResult,
    KnowledgePage,
    KnowledgePageDetail,
    KnowledgeSource,
    KnowledgeStatus,
)
from backend.services import knowledge_service
from backend.storage.object_store import ObjectStorageError

router = APIRouter()


class KnowledgeIngestNoteRequest(BaseModel):
    note_id: str = Field(min_length=1)


@router.get("/status", response_model=KnowledgeStatus)
def get_knowledge_status():
    return knowledge_service.get_status()


@router.get("/pages", response_model=list[KnowledgePage])
def list_knowledge_pages(type: str | None = None, q: str | None = None):
    return [page.model_dump(by_alias=True) for page in knowledge_service.list_pages(page_type=type, q=q)]


@router.get("/pages/{path:path}", response_model=KnowledgePageDetail)
def get_knowledge_page(path: str):
    try:
        return knowledge_service.get_page(path).model_dump(by_alias=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Knowledge page not found: {path}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sources", response_model=list[KnowledgeSource])
def list_knowledge_sources():
    return [source.model_dump(by_alias=True) for source in knowledge_service.list_sources()]


@router.get("/sources/{source_id}/raw")
def get_knowledge_source_raw(source_id: str):
    try:
        source, data = knowledge_service.read_source_raw(source_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Knowledge source raw file not found: {source_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ObjectStorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    filename = source.original_filename or f"{source.source_id}.md"
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(io.BytesIO(data), media_type=media_type, headers=headers)


@router.post("/ingest/note", response_model=KnowledgeIngestResult)
def ingest_note(body: KnowledgeIngestNoteRequest):
    try:
        return knowledge_service.ingest_note(body.note_id).model_dump(by_alias=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Note not found: {body.note_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=llm_unavailable_message(exc)) from exc


@router.post("/ingest/file", response_model=KnowledgeIngestResult)
async def ingest_file(
    file: UploadFile = File(...),
    filename: str | None = Form(default=None),
):
    try:
        data = await file.read()
        source_name = filename or file.filename or "upload.txt"
        return knowledge_service.ingest_file(source_name, data).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=llm_unavailable_message(exc)) from exc


@router.post("/lint", response_model=KnowledgeIngestResult)
def lint_knowledge_base():
    try:
        return knowledge_service.lint_knowledge_base().model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=llm_unavailable_message(exc)) from exc

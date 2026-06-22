from typing import Literal

from pydantic import BaseModel, Field


KnowledgePageType = Literal["overview", "entity", "concept", "source", "analysis", "unknown"]


class KnowledgeStatus(BaseModel):
    vault_path: str
    initialized: bool
    page_count: int
    source_count: int
    last_log_entry: str | None = None


class KnowledgeSource(BaseModel):
    source_id: str
    kind: Literal["note", "file"]
    title: str
    created_at: str
    raw_path: str
    extracted_path: str | None = None
    note_id: str | None = None
    original_filename: str | None = None


class KnowledgePage(BaseModel):
    path: str
    page_type: KnowledgePageType = Field(alias="type")
    title: str
    summary: str = ""
    updated_at: str = ""
    source_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    score: float | None = None

    model_config = {"populate_by_name": True}


class KnowledgePageDetail(KnowledgePage):
    body: str
    wikilinks: list[str] = Field(default_factory=list)


class KnowledgeIngestResult(BaseModel):
    operation: Literal["ingest_note", "ingest_file", "lint"]
    source: KnowledgeSource | None = None
    touched_pages: list[str] = Field(default_factory=list)
    log_entry: str

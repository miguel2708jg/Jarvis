"use client";

import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Archive,
  CloudUpload,
  Download,
  File,
  FileSearch,
  FolderOpen,
  Library,
  RefreshCw,
  Search,
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { useKnowledge } from "@/lib/hooks";
import type { KnowledgePageDetail, KnowledgeSource } from "@/lib/types";

type SourceFilter = "all" | "file" | "note";

function formatDate(value?: string | null): string {
  if (!value) return "None";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function rawSourceUrl(sourceId: string): string {
  const base = API_URL.endsWith("/") ? API_URL.slice(0, -1) : API_URL;
  return `${base}/knowledge/sources/${encodeURIComponent(sourceId)}/raw`;
}

function storageLabel(source: KnowledgeSource): string {
  if (source.raw_storage === "s3") return "Railway Bucket";
  return "Local vault";
}

function fileExtension(source: KnowledgeSource): string {
  const name = source.original_filename || source.title || source.raw_path;
  const ext = name.split(".").pop();
  return ext && ext !== name ? ext.toUpperCase() : source.kind.toUpperCase();
}

function BrandMark() {
  return (
    <a className="brand-mark" href="/">
      <span className="mini-folder" aria-hidden="true"><FolderOpen size={20} /></span>
      <span>Orbit Drive</span>
    </a>
  );
}

function EmptyDrive() {
  return (
    <div className="empty drive-empty">
      <FolderOpen size={30} />
      <h2>No documents found.</h2>
      <p>Upload a source file or change the current filters.</p>
    </div>
  );
}

export default function DocumentsPage() {
  const knowledge = useKnowledge();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<SourceFilter>("all");
  const [selected, setSelected] = useState<KnowledgeSource | null>(null);
  const [detail, setDetail] = useState<KnowledgePageDetail | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    knowledge.refresh();
  }, [knowledge.refresh]);

  const documents = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return knowledge.sources.filter((source) => {
      if (filter !== "all" && source.kind !== filter) return false;
      if (!normalizedQuery) return true;
      return [
        source.title,
        source.original_filename,
        source.source_id,
        source.raw_path,
        source.raw_object_key,
        storageLabel(source),
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalizedQuery));
    });
  }, [filter, knowledge.sources, query]);

  const fileCount = knowledge.sources.filter((source) => source.kind === "file").length;
  const bucketCount = knowledge.sources.filter((source) => source.raw_storage === "s3").length;

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setUploading(true);
    const result = await knowledge.uploadFile(file);
    setUploading(false);
    if (result?.source) {
      setSelected(result.source);
      setDetail(null);
    }
  };

  const openSourcePage = async (source: KnowledgeSource) => {
    setSelected(source);
    const page = await knowledge.getPage(`sources/${source.source_id}.md`);
    setDetail(page);
  };

  return (
    <main>
      <div className="background-wash" />
      <div className="app-shell documents-shell">
        <BrandMark />

        <section className="drive-hero">
          <div>
            <p className="eyebrow">Personal Drive</p>
            <h1>Documents backed by your private storage.</h1>
            <p className="hero-copy">A focused file surface for raw uploads, source snapshots, and generated knowledge context.</p>
          </div>
          <div className="drive-actions">
            <button className="dark-button" onClick={() => fileInputRef.current?.click()} disabled={uploading || knowledge.loading}>
              <CloudUpload size={17} />
              {uploading ? "Uploading" : "Upload"}
            </button>
            <button className="soft-button" onClick={() => knowledge.refresh()} disabled={knowledge.loading}>
              <RefreshCw size={16} />
              Refresh
            </button>
            <input ref={fileInputRef} type="file" className="hidden-input" onChange={upload} />
          </div>
        </section>

        {knowledge.error ? <p className="error-banner">{knowledge.error}</p> : null}

        <section className="drive-toolbar panel">
          <div className="search-field">
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search documents" />
          </div>
          <div className="chip-row">
            {(["all", "file", "note"] as SourceFilter[]).map((value) => (
              <button key={value} className={filter === value ? "chip active" : "chip"} onClick={() => setFilter(value)}>
                {value === "all" ? "All" : value === "file" ? "Files" : "Notes"}
              </button>
            ))}
          </div>
        </section>

        <section className="drive-stats">
          <div className="stat"><strong>{knowledge.sources.length}</strong><span>Total sources</span></div>
          <div className="stat"><strong>{fileCount}</strong><span>Files</span></div>
          <div className="stat"><strong>{bucketCount}</strong><span>Bucket objects</span></div>
        </section>

        <section className="drive-layout">
          <div className="document-list">
            {documents.length ? documents.map((source) => (
              <article
                className={selected?.source_id === source.source_id ? "document-row active" : "document-row"}
                key={source.source_id}
                onClick={() => {
                  setSelected(source);
                  setDetail(null);
                }}
              >
                <div className="document-icon"><File size={20} /></div>
                <div>
                  <h2>{source.original_filename || source.title}</h2>
                  <p>{source.raw_path}</p>
                  <div className="document-meta">
                    <span>{fileExtension(source)}</span>
                    <span>{storageLabel(source)}</span>
                    <span>{formatDate(source.created_at)}</span>
                  </div>
                </div>
                <a className="icon-button" href={rawSourceUrl(source.source_id)} onClick={(event) => event.stopPropagation()} aria-label={`Download ${source.title}`}>
                  <Download size={17} />
                </a>
              </article>
            )) : <EmptyDrive />}
          </div>

          <aside className="document-detail panel">
            {selected ? (
              <>
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Selected</p>
                    <h2>{selected.original_filename || selected.title}</h2>
                  </div>
                  <span className="badge success">{storageLabel(selected)}</span>
                </div>
                <dl className="document-fields">
                  <div><dt>Source ID</dt><dd>{selected.source_id}</dd></div>
                  <div><dt>Kind</dt><dd>{selected.kind}</dd></div>
                  <div><dt>Raw key</dt><dd>{selected.raw_object_key || selected.raw_path}</dd></div>
                  <div><dt>Created</dt><dd>{formatDate(selected.created_at)}</dd></div>
                </dl>
                <div className="document-tools">
                  <a className="dark-button" href={rawSourceUrl(selected.source_id)}><Download size={17} />Download original</a>
                  <button className="soft-button" onClick={() => openSourcePage(selected)}><FileSearch size={16} />Open source page</button>
                  <a className="soft-button" href="/"><Library size={16} />Knowledge</a>
                </div>
                {detail ? (
                  <div className="detail document-page-preview">
                    <h3>{detail.title}</h3>
                    {detail.summary ? <p>{detail.summary}</p> : null}
                    <pre>{detail.body}</pre>
                  </div>
                ) : null}
              </>
            ) : (
              <div className="empty drive-empty">
                <Archive size={30} />
                <h2>Select a document.</h2>
                <p>Drive tools appear after selecting a source.</p>
              </div>
            )}
          </aside>
        </section>
      </div>
    </main>
  );
}

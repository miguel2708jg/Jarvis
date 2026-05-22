import type { PersonalityId } from "../personalities";

// TypeScript interfaces mirroring Pydantic models

export interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Todo {
  id: string;
  text: string;
  completed: boolean;
  priority: "low" | "medium" | "high";
  due_date: string | null;
  created_at: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start_datetime: string;
  end_datetime: string;
  description: string;
  location: string;
  created_at: string;
}

export interface EmailMessage {
  message_id: string;
  sender: string;
  recipient: string;
  subject: string;
  body: string;
  snippet: string;
  date: string;
  labels: string[];
  is_read: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export interface StreamChunk {
  type: "token" | "tool_start" | "tool_end" | "done" | "error";
  content?: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_output?: unknown;
}

export interface ToolActivity {
  name: string;
  phase: "running" | "completed";
}

export type { PersonalityId };

export type KnowledgePageType = "overview" | "entity" | "concept" | "source" | "analysis" | "unknown";

export interface KnowledgeStatus {
  vault_path: string;
  initialized: boolean;
  page_count: number;
  source_count: number;
  last_log_entry: string | null;
}

export interface KnowledgeSource {
  source_id: string;
  kind: "note" | "file";
  title: string;
  created_at: string;
  raw_path: string;
  raw_storage: "local" | "s3";
  raw_object_key: string | null;
  extracted_path: string | null;
  note_id: string | null;
  original_filename: string | null;
}

export interface KnowledgePage {
  path: string;
  type: KnowledgePageType;
  title: string;
  summary: string;
  updated_at: string;
  source_ids: string[];
  tags: string[];
  aliases: string[];
  score?: number | null;
}

export interface KnowledgePageDetail extends KnowledgePage {
  body: string;
  wikilinks: string[];
}

export interface KnowledgeIngestResult {
  operation: "ingest_note" | "ingest_file" | "lint";
  source: KnowledgeSource | null;
  touched_pages: string[];
  log_entry: string;
}

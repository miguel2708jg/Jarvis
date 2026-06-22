export type PersonalityId =
  | "mentor"
  | "ceo"
  | "coach"
  | "amigo"
  | "rizz"
  | "focus"
  | "analista"
  | "creativo"
  | "social_copilot";

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
  thread_id?: string;
  sender: string;
  recipient: string;
  subject: string;
  body: string;
  snippet: string;
  date: string;
  labels: string[];
  is_read: boolean;
}

export interface EmailThread {
  thread_id: string;
  messages: EmailMessage[];
}

export interface EmailDraft {
  id?: string;
  message?: EmailMessage;
  subject?: string;
  to?: string[];
  [key: string]: unknown;
}

export interface EmailLabel {
  id?: string;
  labelId?: string;
  name?: string;
  displayName?: string;
  type?: string;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  created_at?: string | null;
}

export interface ChatThread {
  id: string;
  title: string;
  user_id?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatAttachment {
  source: KnowledgeSource;
  extracted_preview: string;
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

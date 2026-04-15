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

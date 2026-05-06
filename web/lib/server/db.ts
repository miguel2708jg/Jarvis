import { randomUUID } from "crypto";
import fs from "fs";
import path from "path";
import { neon, type NeonQueryFunction } from "@neondatabase/serverless";
import type { CalendarEvent, Note, Todo } from "../types";

let sqlClient: NeonQueryFunction<false, false> | null = null;
let initialized = false;

function readRootEnvValue(key: string): string | null {
  const envPath = path.resolve(process.cwd(), "..", ".env");
  if (!fs.existsSync(envPath)) return null;

  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^([^=]+)=(.*)$/);
    if (!match || match[1].trim() !== key) continue;
    return match[2].trim().replace(/^["']|["']$/g, "");
  }
  return null;
}

function getDatabaseUrl() {
  const databaseUrl = process.env.DATABASE_URL ?? readRootEnvValue("DATABASE_URL");
  if (!databaseUrl) {
    throw new Error("DATABASE_URL is required to connect Next.js to Neon.");
  }
  return databaseUrl;
}

function getSql() {
  if (!sqlClient) {
    sqlClient = neon(getDatabaseUrl());
  }
  return sqlClient;
}

async function ensureInitialized() {
  if (initialized) return;
  const sql = getSql();

  await sql`
    CREATE TABLE IF NOT EXISTS notes (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      tags TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `;
  await sql`
    CREATE TABLE IF NOT EXISTS todos (
      id TEXT PRIMARY KEY,
      text TEXT NOT NULL,
      completed INTEGER NOT NULL DEFAULT 0,
      priority TEXT NOT NULL DEFAULT 'medium',
      due_date TEXT,
      created_at TEXT NOT NULL
    )
  `;
  await sql`
    CREATE TABLE IF NOT EXISTS calendar_events (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      start_datetime TEXT NOT NULL,
      end_datetime TEXT NOT NULL,
      description TEXT,
      location TEXT,
      created_at TEXT NOT NULL
    )
  `;

  initialized = true;
}

function nowIso() {
  return new Date().toISOString();
}

function normalizeTags(tags: unknown): string[] {
  if (!Array.isArray(tags)) return [];
  const seen = new Set<string>();
  const result: string[] = [];
  for (const rawTag of tags) {
    const tag = String(rawTag).trim();
    const key = tag.toLowerCase();
    if (!tag || seen.has(key)) continue;
    seen.add(key);
    result.push(tag);
  }
  return result;
}

function serializeTags(tags: unknown) {
  return normalizeTags(tags).join(",");
}

function deserializeTags(value: unknown): string[] {
  if (Array.isArray(value)) return normalizeTags(value);
  if (typeof value !== "string" || !value) return [];
  return normalizeTags(value.split(","));
}

function stringifyDate(value: unknown): string {
  if (value instanceof Date) return value.toISOString();
  return String(value ?? "");
}

type NoteRow = Omit<Note, "tags"> & { tags: string | null };
type TodoRow = Omit<Todo, "completed"> & { completed: boolean | number | string };
type CalendarRow = CalendarEvent;

function rowToNote(row: NoteRow): Note {
  return {
    ...row,
    tags: deserializeTags(row.tags),
    created_at: stringifyDate(row.created_at),
    updated_at: stringifyDate(row.updated_at),
  };
}

function rowToTodo(row: TodoRow): Todo {
  return {
    ...row,
    completed: row.completed === true || row.completed === 1 || row.completed === "1",
    due_date: row.due_date ? stringifyDate(row.due_date) : null,
    created_at: stringifyDate(row.created_at),
  };
}

function rowToCalendarEvent(row: CalendarRow): CalendarEvent {
  return {
    ...row,
    start_datetime: stringifyDate(row.start_datetime),
    end_datetime: stringifyDate(row.end_datetime),
    created_at: stringifyDate(row.created_at),
  };
}

export async function readBody<T>(request: Request): Promise<T> {
  try {
    return (await request.json()) as T;
  } catch {
    return {} as T;
  }
}

export async function listNotes(tag?: string | null): Promise<Note[]> {
  await ensureInitialized();
  const rows = (await getSql()`SELECT * FROM notes ORDER BY updated_at DESC`) as NoteRow[];
  const notes = rows.map(rowToNote);
  if (!tag) return notes;
  const normalized = tag.trim().toLowerCase();
  return notes.filter((note) => note.tags.some((noteTag) => noteTag.toLowerCase() === normalized));
}

export async function createNote(input: Partial<Note>): Promise<Note> {
  await ensureInitialized();
  const title = String(input.title ?? "").trim();
  const content = String(input.content ?? "").trim();
  if (!title || !content) throw new Error("Title and content are required.");

  const note: Note = {
    id: randomUUID(),
    title,
    content,
    tags: normalizeTags(input.tags),
    created_at: nowIso(),
    updated_at: nowIso(),
  };

  await getSql()`
    INSERT INTO notes (id, title, content, tags, created_at, updated_at)
    VALUES (${note.id}, ${note.title}, ${note.content}, ${serializeTags(note.tags)}, ${note.created_at}, ${note.updated_at})
  `;
  return note;
}

export async function getNote(id: string): Promise<Note | null> {
  await ensureInitialized();
  const rows = (await getSql()`SELECT * FROM notes WHERE id = ${id}`) as NoteRow[];
  return rows[0] ? rowToNote(rows[0]) : null;
}

export async function updateNote(id: string, input: Partial<Note>): Promise<Note | null> {
  const current = await getNote(id);
  if (!current) return null;

  const next: Note = {
    ...current,
    title: input.title !== undefined ? String(input.title).trim() : current.title,
    content: input.content !== undefined ? String(input.content).trim() : current.content,
    tags: input.tags !== undefined ? normalizeTags(input.tags) : current.tags,
    updated_at: nowIso(),
  };

  await getSql()`
    UPDATE notes
    SET title = ${next.title}, content = ${next.content}, tags = ${serializeTags(next.tags)}, updated_at = ${next.updated_at}
    WHERE id = ${id}
  `;
  return next;
}

export async function deleteNote(id: string): Promise<boolean> {
  await ensureInitialized();
  const rows = (await getSql()`DELETE FROM notes WHERE id = ${id} RETURNING id`) as { id: string }[];
  return rows.length > 0;
}

export async function listTodos(showCompleted = false): Promise<Todo[]> {
  await ensureInitialized();
  const rows = (await getSql()`SELECT * FROM todos`) as TodoRow[];
  return rows
    .map(rowToTodo)
    .filter((todo) => showCompleted || !todo.completed)
    .sort((a, b) => {
      if (a.completed !== b.completed) return Number(a.completed) - Number(b.completed);
      if (Boolean(a.due_date) !== Boolean(b.due_date)) return a.due_date ? -1 : 1;
      return new Date(a.due_date ?? a.created_at).getTime() - new Date(b.due_date ?? b.created_at).getTime();
    });
}

export async function createTodo(input: Partial<Todo>): Promise<Todo> {
  await ensureInitialized();
  const text = String(input.text ?? "").trim();
  if (!text) throw new Error("ToDo text is required.");

  const todo: Todo = {
    id: randomUUID(),
    text,
    completed: false,
    priority: input.priority ?? "medium",
    due_date: input.due_date ?? null,
    created_at: nowIso(),
  };

  await getSql()`
    INSERT INTO todos (id, text, completed, priority, due_date, created_at)
    VALUES (${todo.id}, ${todo.text}, 0, ${todo.priority}, ${todo.due_date}, ${todo.created_at})
  `;
  return todo;
}

export async function getTodo(id: string): Promise<Todo | null> {
  await ensureInitialized();
  const rows = (await getSql()`SELECT * FROM todos WHERE id = ${id}`) as TodoRow[];
  return rows[0] ? rowToTodo(rows[0]) : null;
}

export async function updateTodo(id: string, input: Partial<Todo>): Promise<Todo | null> {
  const current = await getTodo(id);
  if (!current) return null;

  const next: Todo = {
    ...current,
    text: input.text !== undefined ? String(input.text).trim() : current.text,
    priority: input.priority ?? current.priority,
    due_date: input.due_date !== undefined ? input.due_date : current.due_date,
    completed: input.completed !== undefined ? Boolean(input.completed) : current.completed,
  };

  await getSql()`
    UPDATE todos
    SET text = ${next.text}, completed = ${next.completed ? 1 : 0}, priority = ${next.priority}, due_date = ${next.due_date}
    WHERE id = ${id}
  `;
  return next;
}

export async function deleteTodo(id: string): Promise<boolean> {
  await ensureInitialized();
  const rows = (await getSql()`DELETE FROM todos WHERE id = ${id} RETURNING id`) as { id: string }[];
  return rows.length > 0;
}

export async function listCalendarEvents(upcomingOnly = true): Promise<CalendarEvent[]> {
  await ensureInitialized();
  const rows = (await getSql()`SELECT * FROM calendar_events`) as CalendarRow[];
  const now = Date.now();
  return rows
    .map(rowToCalendarEvent)
    .filter((event) => !upcomingOnly || new Date(event.end_datetime).getTime() >= now)
    .sort((a, b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime());
}

export async function deleteCalendarEvent(id: string): Promise<boolean> {
  await ensureInitialized();
  const rows = (await getSql()`DELETE FROM calendar_events WHERE id = ${id} RETURNING id`) as { id: string }[];
  return rows.length > 0;
}

export function json(data: unknown, status = 200) {
  return Response.json(data, { status });
}

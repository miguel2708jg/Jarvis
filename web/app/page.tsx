"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Archive,
  ArrowUp,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  Circle,
  Clock,
  CloudUpload,
  FileText,
  Inbox,
  Library,
  Mail,
  MapPin,
  Pencil,
  Plus,
  Search,
  Settings,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { PERSONALITIES, getPersonality } from "@/lib/personalities";
import { useCalendar, useEmails, useJarvisChat, useKnowledge, useNotes, useTodos } from "@/lib/hooks";
import type { ChatMessage, KnowledgePage, KnowledgePageDetail, Note, Todo } from "@/lib/types";

type TabId = "chat" | "notes" | "knowledge" | "todos" | "calendar" | "email" | "settings";

const tabs = [
  { id: "chat", label: "Chat", Icon: Sparkles },
  { id: "notes", label: "Notes", Icon: FileText },
  { id: "knowledge", label: "Knowledge", Icon: Library },
  { id: "todos", label: "ToDo", Icon: CheckCircle2 },
  { id: "calendar", label: "Calendar", Icon: CalendarDays },
  { id: "email", label: "Email", Icon: Mail },
  { id: "settings", label: "Settings", Icon: Settings },
] satisfies { id: TabId; label: string; Icon: typeof Sparkles }[];

const quickActions = [
  { label: "Plan my day", prompt: "Plan my day using my notes, ToDos, calendar, and knowledge." },
  { label: "Create ToDo", prompt: "Create a high priority ToDo to follow up on everything urgent today." },
  { label: "Summarize notes", prompt: "Summarize my notes into a short action-oriented brief." },
  { label: "Knowledge brief", prompt: "Search my knowledge vault and give me a concise brief on what matters now." },
];

const priorityMeta = {
  high: { label: "High", className: "danger" },
  medium: { label: "Medium", className: "warning" },
  low: { label: "Low", className: "success" },
} satisfies Record<Todo["priority"], { label: string; className: string }>;

function formatDate(value?: string | null, options?: Intl.DateTimeFormatOptions): string {
  if (!value) return "None";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, options ?? { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function parseTags(value: string): string[] {
  return value.split(",").map((tag) => tag.trim()).filter(Boolean);
}

function OrbitLogo({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? "orbit-logo compact" : "orbit-logo"} aria-hidden="true">
      <span className="orbit-ring" />
      <span className="orbit-path" />
      <span className="orbit-planet" />
    </div>
  );
}

function BrandMark({ agentName }: { agentName: string }) {
  return (
    <div className="brand-mark">
      <OrbitLogo compact />
      <span>{agentName}</span>
    </div>
  );
}

function Hero({
  eyebrow,
  title,
  subtitle,
  stats,
  action,
  error,
  children,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  stats?: { label: string; value: string }[];
  action?: { label: string; onClick: () => void };
  error?: string | null;
  children?: React.ReactNode;
}) {
  return (
    <section className="hero">
      <div className="hero-accent" />
      <div className="hero-top">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="hero-copy">{subtitle}</p>
        </div>
        {action ? <button className="dark-button" onClick={action.onClick}>{action.label}</button> : null}
      </div>
      {stats?.length ? (
        <div className="stats-grid">
          {stats.map((stat) => (
            <div className="stat" key={stat.label}>
              <strong>{stat.value}</strong>
              <span>{stat.label}</span>
            </div>
          ))}
        </div>
      ) : null}
      {children}
      {error ? <p className="error-banner">{error}</p> : null}
    </section>
  );
}

function Modal({
  title,
  eyebrow,
  open,
  onClose,
  children,
}: {
  title: string;
  eyebrow: string;
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <button className="icon-button modal-close" onClick={onClose} aria-label="Close modal">
          <X size={18} />
        </button>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        {children}
      </div>
    </div>
  );
}

function MessageBubble({ message, agentName }: { message: ChatMessage; agentName: string }) {
  const isUser = message.role === "user";
  return (
    <div className={`message-row ${isUser ? "right" : "left"}`}>
      {!isUser ? <div className="avatar">{agentName.slice(0, 1).toUpperCase()}</div> : null}
      <div className="message-stack">
        <span className="message-label">{isUser ? "You" : agentName}</span>
        <div className={`bubble ${isUser ? "user" : "assistant"}`}>
          {message.isStreaming && !message.content ? <span className="typing">...</span> : message.content}
          {message.isStreaming && message.content ? <span className="cursor">|</span> : null}
        </div>
      </div>
    </div>
  );
}

function ChatScreen({ agentName }: { agentName: string }) {
  const [input, setInput] = useState("");
  const chat = useJarvisChat();
  const selectedPersonality = getPersonality(chat.activePersonality);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [chat.messages]);

  const send = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || chat.isStreaming || !chat.isConnected) return;
    setInput("");
    chat.sendMessage(trimmed);
  };

  return (
    <div className="screen chat-screen">
      <Hero
        eyebrow="Personal AI Operator"
        title={`${agentName} keeps your workday aligned.`}
        subtitle="Ask for plans, summarize context, or let the assistant touch notes, ToDos, calendar, and knowledge without leaving chat."
        stats={[
          { label: "Core modules", value: "5" },
          { label: "Streaming replies", value: "Live" },
          { label: "Action-aware chat", value: "Tools" },
        ]}
        error={chat.error}
      >
        <div className={`status-pill ${chat.isConnected ? "online" : "offline"}`}>
          <span />{chat.isConnected ? "Connected" : "Connecting"}
        </div>
      </Hero>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Personality</p>
            <h2>{selectedPersonality?.name ?? `${agentName} normal`}</h2>
          </div>
          <button className={!chat.activePersonality ? "chip active" : "chip"} onClick={() => chat.setPersonality(null)} disabled={chat.isStreaming}>
            Normal
          </button>
        </div>
        <div className="rail">
          {PERSONALITIES.map(({ Icon, ...personality }) => (
            <button
              className={chat.activePersonality === personality.id ? "personality active" : "personality"}
              key={personality.id}
              onClick={() => chat.setPersonality(personality.id)}
              disabled={chat.isStreaming}
            >
              <Icon size={18} />
              <span>
                <strong>{personality.name}</strong>
                <small>{personality.shortRole}</small>
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="quick-grid">
        {quickActions.map((action) => (
          <button key={action.label} onClick={() => send(action.prompt)} disabled={!chat.isConnected || chat.isStreaming}>
            <Sparkles size={18} />
            {action.label}
          </button>
        ))}
      </section>

      {(chat.activeTools.length > 0 || chat.lastCompletedTool) && (
        <section className="panel compact">
          <p className="eyebrow">Live Activity</p>
          <div className="chip-row">
            {chat.activeTools.map((tool) => <span className="chip active" key={tool.name}>{tool.name}</span>)}
            {!chat.activeTools.length && chat.lastCompletedTool ? <span className="chip success">{chat.lastCompletedTool} finished</span> : null}
          </div>
        </section>
      )}

      <section className="messages">
        {chat.messages.length === 0 ? (
          <div className="empty">
            <h2>Use {agentName} like an operator, not a chatbot.</h2>
            <p>Give it goals, context, and constraints. Tool activity appears while {agentName} works.</p>
          </div>
        ) : chat.messages.map((message) => <MessageBubble key={message.id} message={message} agentName={agentName} />)}
        <div ref={endRef} />
      </section>

      <form className="composer" onSubmit={(event) => { event.preventDefault(); send(input); }}>
        <textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder={chat.isConnected ? `Ask ${agentName} to organize the next move` : "Waiting for connection"} />
        <button className="send-button" disabled={!chat.isConnected || chat.isStreaming || !input.trim()} aria-label="Send message">
          <ArrowUp size={18} />
        </button>
      </form>
    </div>
  );
}

function NotesScreen({ agentName }: { agentName: string }) {
  const notes = useNotes();
  const knowledge = useKnowledge();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Note | null>(null);
  const [draft, setDraft] = useState({ title: "", content: "", tags: "" });

  useEffect(() => { notes.refresh(); }, [notes.refresh]);

  const openEditor = (note?: Note) => {
    setEditing(note ?? null);
    setDraft(note ? { title: note.title, content: note.content, tags: note.tags.join(", ") } : { title: "", content: "", tags: "" });
    setModalOpen(true);
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    const payload = { title: draft.title.trim(), content: draft.content.trim(), tags: parseTags(draft.tags) };
    if (!payload.title || !payload.content) return window.alert("Title and content are required.");
    const saved = editing ? await notes.update(editing.id, payload) : await notes.create(payload);
    if (saved) setModalOpen(false);
  };

  return (
    <div className="screen">
      <Hero
        eyebrow="Notebook"
        title="Notes that look organized before you open them."
        subtitle={`Keep personal context in one place, edit fast inside the app, or let ${agentName} create notes from chat.`}
        action={{ label: "New note", onClick: () => openEditor() }}
        stats={[
          { label: "Total notes", value: String(notes.items.length) },
          { label: "Tagged notes", value: String(notes.items.filter((note) => note.tags.length).length) },
          { label: "Latest update", value: formatDate(notes.items[0]?.updated_at, { month: "short", day: "numeric" }) },
        ]}
        error={notes.error}
      />
      <div className="card-grid">
        {notes.items.length ? notes.items.map((note) => (
          <article className="card" key={note.id}>
            <div className="card-actions">
              <button className="icon-button" onClick={() => openEditor(note)} aria-label="Edit note"><Pencil size={16} /></button>
              <button className="icon-button" onClick={() => confirm(`Delete "${note.title}"?`) && notes.remove(note.id)} aria-label="Delete note"><Trash2 size={16} /></button>
            </div>
            <h2>{note.title}</h2>
            <small>Updated {formatDate(note.updated_at)}</small>
            <p>{note.content}</p>
            <div className="chip-row">{note.tags.map((tag) => <span className="chip" key={tag}>{tag}</span>)}</div>
            <button className="soft-button" onClick={async () => {
              const result = await knowledge.ingestNote(note.id);
              window.alert(result ? `${result.touched_pages.length} page(s) updated.` : "The note could not be added.");
            }}><BookOpen size={16} />Add to Knowledge</button>
          </article>
        )) : <Empty title="No notes yet." text={`Start one here or ask ${agentName} in chat to create a structured note.`} />}
      </div>
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} eyebrow={editing ? "Edit note" : "Create note"} title={editing ? "Refine the note and keep context clean." : "Capture the thought while it is still sharp."}>
        <form className="form" onSubmit={save}>
          <label>Title<input value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label>
          <label>Content<textarea value={draft.content} onChange={(event) => setDraft({ ...draft, content: event.target.value })} /></label>
          <label>Tags<input value={draft.tags} onChange={(event) => setDraft({ ...draft, tags: event.target.value })} placeholder="work, planning" /></label>
          <div className="modal-actions"><button type="button" className="soft-button" onClick={() => setModalOpen(false)}>Cancel</button><button className="dark-button">Save</button></div>
        </form>
      </Modal>
    </div>
  );
}

function TodosScreen({ agentName }: { agentName: string }) {
  const todos = useTodos();
  const [filter, setFilter] = useState<"pending" | "all" | "completed">("pending");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Todo | null>(null);
  const [draft, setDraft] = useState<{ text: string; priority: Todo["priority"]; due_date: string }>({ text: "", priority: "medium", due_date: "" });

  useEffect(() => { todos.refresh({ show_completed: true }); }, [todos.refresh]);

  const filtered = todos.items.filter((todo) => filter === "all" || (filter === "pending" ? !todo.completed : todo.completed));
  const openEditor = (todo?: Todo) => {
    setEditing(todo ?? null);
    setDraft(todo ? { text: todo.text, priority: todo.priority, due_date: todo.due_date?.slice(0, 10) ?? "" } : { text: "", priority: "medium", due_date: "" });
    setModalOpen(true);
  };
  const save = async (event: FormEvent) => {
    event.preventDefault();
    const text = draft.text.trim();
    if (!text) return window.alert("ToDo text is required.");
    const payload = { text, priority: draft.priority, due_date: draft.due_date.trim() || null, completed: editing?.completed };
    const saved = editing ? await todos.update(editing.id, payload) : await todos.create(payload);
    if (saved) setModalOpen(false);
  };

  return (
    <div className="screen">
      <Hero
        eyebrow="ToDo Board"
        title="Daily execution with more signal and less clutter."
        subtitle="Track work from chat or directly here. Priorities, due dates, and completion state stay readable at a glance."
        action={{ label: "New ToDo", onClick: () => openEditor() }}
        stats={[
          { label: "Pending", value: String(todos.items.filter((todo) => !todo.completed).length) },
          { label: "Completed", value: String(todos.items.filter((todo) => todo.completed).length) },
          { label: "Overdue", value: String(todos.items.filter((todo) => todo.due_date && !todo.completed && new Date(todo.due_date).getTime() < Date.now()).length) },
        ]}
        error={todos.error}
      >
        <div className="chip-row">
          {(["pending", "all", "completed"] as const).map((value) => <button key={value} className={filter === value ? "chip active" : "chip"} onClick={() => setFilter(value)}>{value}</button>)}
        </div>
      </Hero>
      <div className="list">
        {filtered.length ? filtered.map((todo) => {
          const meta = priorityMeta[todo.priority];
          return (
            <article className={`todo ${todo.completed ? "completed" : ""}`} key={todo.id}>
              <button className="check-button" onClick={() => todos.setCompleted(todo.id, !todo.completed)} aria-label="Toggle ToDo">
                {todo.completed ? <CheckCircle2 /> : <Circle />}
              </button>
              <div onClick={() => openEditor(todo)} className="todo-body">
                <div className="todo-title-row"><h2>{todo.text}</h2><span className={`badge ${meta.className}`}>{meta.label}</span></div>
                <p><CalendarDays size={14} />{todo.due_date ? `Due ${formatDate(todo.due_date, { month: "short", day: "numeric", year: "numeric" })}` : "No due date"}</p>
                <p><Clock size={14} />Created {formatDate(todo.created_at, { month: "short", day: "numeric", year: "numeric" })}</p>
              </div>
              <button className="icon-button" onClick={() => confirm(`Delete "${todo.text}"?`) && todos.remove(todo.id)} aria-label="Delete ToDo"><Trash2 size={16} /></button>
            </article>
          );
        }) : <Empty title="No ToDos in this filter." text={`Add one manually or ask ${agentName} to turn your next plan into concrete ToDos.`} />}
      </div>
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} eyebrow={editing ? "Edit ToDo" : "Create ToDo"} title={editing ? "Adjust the ToDo without losing momentum." : "Turn intent into a ToDo with structure."}>
        <form className="form" onSubmit={save}>
          <label>ToDo<textarea value={draft.text} onChange={(event) => setDraft({ ...draft, text: event.target.value })} /></label>
          <label>Priority<select value={draft.priority} onChange={(event) => setDraft({ ...draft, priority: event.target.value as Todo["priority"] })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
          <label>Due date<input value={draft.due_date} onChange={(event) => setDraft({ ...draft, due_date: event.target.value })} placeholder="YYYY-MM-DD" /></label>
          <div className="modal-actions"><button type="button" className="soft-button" onClick={() => setModalOpen(false)}>Cancel</button><button className="dark-button">Save</button></div>
        </form>
      </Modal>
    </div>
  );
}

function KnowledgeScreen() {
  const knowledge = useKnowledge();
  const [type, setType] = useState("all");
  const [query, setQuery] = useState("");
  const [noteId, setNoteId] = useState("");
  const [detail, setDetail] = useState<KnowledgePageDetail | null>(null);

  const filters = useMemo(() => ({ type: type === "all" ? undefined : type, q: query.trim() || undefined }), [query, type]);
  useEffect(() => { knowledge.refresh(filters); }, [knowledge.refresh, filters]);

  const openDetail = async (page: KnowledgePage | string) => {
    const path = typeof page === "string" ? page : page.path;
    const next = await knowledge.getPage(path);
    if (next) setDetail(next);
  };

  return (
    <div className="screen">
      <Hero
        eyebrow="Knowledge Vault"
        title="Obsidian-style wiki with explicit operations."
        subtitle="Ingest notes/files, run lint maintenance, and navigate linked knowledge pages."
        action={{ label: "Run lint", onClick: async () => window.alert((await knowledge.runLint()) ? "Lint complete." : "Lint failed.") }}
        stats={[
          { label: "Pages", value: String(knowledge.status?.page_count ?? 0) },
          { label: "Sources", value: String(knowledge.status?.source_count ?? 0) },
          { label: "Last op", value: knowledge.status?.last_log_entry ? "Available" : "None" },
        ]}
        error={knowledge.error}
      />
      <section className="panel">
        <h2>Operations</h2>
        <div className="toolbar">
          <input value={noteId} onChange={(event) => setNoteId(event.target.value)} placeholder="Note ID to ingest" />
          <button className="soft-button" onClick={async () => {
            if (!noteId.trim()) return window.alert("Enter a note ID before ingesting.");
            const result = await knowledge.ingestNote(noteId.trim());
            if (result) setNoteId("");
            window.alert(result ? `${result.touched_pages.length} page(s) updated.` : "Ingest failed.");
          }}><Archive size={16} />Ingest note</button>
          <label className="soft-button file-button"><CloudUpload size={16} />Upload file<input type="file" onChange={async (event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            const result = await knowledge.uploadFile(file);
            window.alert(result ? `${result.touched_pages.length} page(s) updated.` : "Upload failed.");
          }} /></label>
        </div>
      </section>
      <section className="panel">
        <div className="toolbar">
          <div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search pages" /></div>
          <div className="chip-row">{["all", "overview", "entity", "concept", "source", "analysis"].map((value) => <button key={value} className={type === value ? "chip active" : "chip"} onClick={() => setType(value)}>{value}</button>)}</div>
        </div>
      </section>
      <section className="panel">
        <h2>Recent sources</h2>
        <div className="source-list">{knowledge.sources.slice(0, 6).map((source) => <p key={source.source_id}><strong>{source.title}</strong><small>{source.kind} | {formatDate(source.created_at)}</small></p>)}</div>
      </section>
      <div className="card-grid">
        {knowledge.pages.length ? knowledge.pages.map((page) => (
          <article className="card clickable" key={page.path} onClick={() => openDetail(page)}>
            <div className="card-meta"><span>{page.type.toUpperCase()}</span><small>{formatDate(page.updated_at)}</small></div>
            <h2>{page.title}</h2>
            <small>{page.path}</small>
            {page.summary ? <p>{page.summary}</p> : null}
            <div className="chip-row">{page.tags.slice(0, 4).map((tag) => <span className="chip" key={tag}>{tag}</span>)}</div>
          </article>
        )) : <Empty title="No knowledge pages found." text="Ingest a note or upload a file to compile the first pages." />}
      </div>
      <Modal open={Boolean(detail)} onClose={() => setDetail(null)} eyebrow={detail?.type.toUpperCase() ?? "Page"} title={detail?.title ?? ""}>
        {detail ? <div className="detail"><small>{detail.path}</small>{detail.summary ? <p>{detail.summary}</p> : null}<h3>Body</h3><pre>{detail.body}</pre>{detail.wikilinks.length ? <><h3>Wikilinks</h3><div className="chip-row">{detail.wikilinks.map((link) => <button className="chip" key={link} onClick={() => openDetail(link)}>{link}</button>)}</div></> : null}</div> : null}
      </Modal>
    </div>
  );
}

function CalendarScreen({ agentName }: { agentName: string }) {
  const calendar = useCalendar();
  useEffect(() => { calendar.refresh(); }, [calendar.refresh]);
  const nextEvent = calendar.items[0];
  return (
    <div className="screen">
      <Hero eyebrow="Calendar" title="Upcoming time blocks with enough hierarchy to scan fast." subtitle="Use chat to schedule events, then manage the resulting agenda here without losing the broader timeline." stats={[{ label: "Upcoming", value: String(calendar.items.length) }, { label: "Next event", value: formatDate(nextEvent?.start_datetime, { month: "short", day: "numeric" }) }]} error={calendar.error} />
      <div className="list">
        {calendar.items.length ? calendar.items.map((event) => (
          <article className="event-card" key={event.id}>
            <div className="date-pill"><strong>{formatDate(event.start_datetime, { month: "short", day: "numeric" })}</strong><span>{formatDate(event.start_datetime, { hour: "2-digit", minute: "2-digit" })}</span></div>
            <div>
              <h2>{event.title}</h2>
              <p><Clock size={14} />{formatDate(event.start_datetime)}</p>
              {event.location ? <p><MapPin size={14} />{event.location}</p> : null}
              {event.description ? <p>{event.description}</p> : null}
            </div>
            <button className="icon-button" onClick={() => confirm(`Delete "${event.title}"?`) && calendar.remove(event.id)} aria-label="Delete event"><Trash2 size={16} /></button>
          </article>
        )) : <Empty title="No events yet." text={`Ask ${agentName} to schedule a meeting, add a deadline, or build an agenda.`} />}
      </div>
    </div>
  );
}

function EmailScreen({ agentName }: { agentName: string }) {
  const emails = useEmails();
  useEffect(() => { emails.refresh(); }, [emails.refresh]);
  const unread = emails.items.filter((email) => !email.is_read).length;
  return (
    <div className="screen">
      <Hero eyebrow="Inbox" title="Email should feel triaged before you even open a thread." subtitle={`Use ${agentName} to summarize the inbox, then scan sender, subject, urgency, and unread state.`} stats={[{ label: "Messages", value: String(emails.items.length) }, { label: "Unread", value: String(unread) }]} error={emails.error} />
      <div className="list">
        {emails.items.length ? emails.items.map((email) => (
          <article className={`card email ${!email.is_read ? "unread" : ""}`} key={email.message_id}>
            <div className="card-meta"><strong><Inbox size={14} />{email.sender}</strong><small>{email.date}</small></div>
            <h2>{email.subject || "(No subject)"}</h2>
            <p>{email.snippet || email.body}</p>
            <span className={!email.is_read ? "chip active" : "chip"}>{email.is_read ? "Read" : "Unread"}</span>
          </article>
        )) : <Empty title="No emails available." text={`Configure Gmail credentials to enable inbox access, then ask ${agentName} to summarize what matters.`} />}
      </div>
    </div>
  );
}

function SettingsScreen({ agentName, onAgentNameChange }: { agentName: string; onAgentNameChange: (value: string) => void }) {
  const updateAgentName = (value: string) => {
    const next = value.trimStart();
    onAgentNameChange(next);
    window.localStorage.setItem("orbit.agentName", next.trim() || "Orbit");
  };

  return (
    <div className="screen">
      <Hero
        eyebrow="Settings"
        title="Customize your agent identity."
        subtitle="Set the assistant name used across chat, notes, ToDos, calendar, and inbox."
        stats={[
          { label: "Agent name", value: agentName || "Orbit" },
          { label: "Brand", value: "Orbit" },
          { label: "Logo", value: "Active" },
        ]}
      >
        <div className="brand-preview">
          <OrbitLogo />
          <div>
            <p className="eyebrow">Current identity</p>
            <h2>{agentName || "Orbit"}</h2>
          </div>
        </div>
      </Hero>

      <section className="panel settings-panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Agent</p>
            <h2>Name</h2>
          </div>
          <BrandMark agentName={agentName || "Orbit"} />
        </div>
        <label className="field">
          Agent name
          <input
            value={agentName}
            onChange={(event) => updateAgentName(event.target.value)}
            onBlur={() => onAgentNameChange(agentName.trim() || "Orbit")}
            placeholder="Orbit"
          />
        </label>
        <p className="settings-note">This changes the display name in the interface. The default value is Orbit.</p>
      </section>
    </div>
  );
}

function Empty({ title, text }: { title: string; text: string }) {
  return <div className="empty"><h2>{title}</h2><p>{text}</p></div>;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("chat");
  const [agentName, setAgentName] = useState("Orbit");

  useEffect(() => {
    const savedAgentName = window.localStorage.getItem("orbit.agentName");
    setAgentName(savedAgentName?.trim() || "Orbit");
  }, []);

  return (
    <main>
      <div className="background-wash" />
      <div className="app-shell">
        <BrandMark agentName={agentName} />
        {activeTab === "chat" && <ChatScreen agentName={agentName} />}
        {activeTab === "notes" && <NotesScreen agentName={agentName} />}
        {activeTab === "knowledge" && <KnowledgeScreen />}
        {activeTab === "todos" && <TodosScreen agentName={agentName} />}
        {activeTab === "calendar" && <CalendarScreen agentName={agentName} />}
        {activeTab === "email" && <EmailScreen agentName={agentName} />}
        {activeTab === "settings" && <SettingsScreen agentName={agentName} onAgentNameChange={setAgentName} />}
      </div>
      <nav className="tabbar" aria-label={`${agentName} modules`}>
        {tabs.map(({ id, label, Icon }) => (
          <button key={id} className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id)}>
            <Icon size={20} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </main>
  );
}

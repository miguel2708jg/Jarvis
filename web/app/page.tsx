"use client";

import { FormEvent, MouseEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  Library,
  LogOut,
  Mic,
  MicOff,
  Pencil,
  Plus,
  Search,
  Settings,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { signOut, useSession } from "next-auth/react";
import { PERSONALITIES, getPersonality } from "@/lib/personalities";
import { useJarvisChat, useKnowledge, useNotes, useTodos } from "@/lib/hooks";
import type { ChatAttachment, ChatMessage, ChatThread, KnowledgePage, KnowledgePageDetail, Note, Todo } from "@/lib/types";

type TabId = "chat" | "notes" | "knowledge" | "todos" | "settings";
type AgentPromptDraft = { id: number; text: string };

type SpeechRecognitionResultLike = {
  0: { transcript: string };
  isFinal: boolean;
};

type SpeechRecognitionEventLike = Event & {
  results: {
    length: number;
    [index: number]: SpeechRecognitionResultLike;
  };
};

type SpeechRecognitionErrorEventLike = Event & {
  error?: string;
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

type SpeechRecognitionWindow = Window &
  typeof globalThis & {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };

const tabs = [
  { id: "chat", label: "Chat", Icon: Sparkles },
  { id: "notes", label: "Notes", Icon: FileText },
  { id: "knowledge", label: "Knowledge", Icon: Library },
  { id: "todos", label: "ToDo", Icon: CheckCircle2 },
  { id: "settings", label: "Settings", Icon: Settings },
] satisfies { id: TabId; label: string; Icon: typeof Sparkles }[];

const quickActions = [
  { label: "Plan my day", prompt: "Plan my day using my notes, ToDos, calendar, and knowledge." },
  { label: "Create ToDo", prompt: "Create a high priority ToDo to follow up on everything urgent today." },
  { label: "Summarize notes", prompt: "Summarize my notes into a short action-oriented brief." },
  { label: "Summarize inbox", prompt: "Search my Gmail inbox and summarize the important unread threads with suggested next actions." },
  { label: "Draft email", prompt: "Create a Gmail draft for the next reply I describe. Do not send it." },
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
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h1>{title}</h1>
          {subtitle ? <p className="hero-copy">{subtitle}</p> : null}
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

function ChatHistoryPanel({ chat }: { chat: ReturnType<typeof useJarvisChat> }) {
  const deleteThread = async (event: MouseEvent<HTMLButtonElement>, thread: ChatThread) => {
    event.stopPropagation();
    if (confirm(`Delete "${thread.title}"?`)) await chat.deleteThread(thread.id);
  };

  return (
    <section className="panel compact chat-history-panel">
      <div className="section-head horizontal">
        <div>
          <p className="eyebrow">Conversations</p>
          <h2>Memory</h2>
        </div>
        <button className="soft-button" onClick={() => void chat.newThread()} disabled={chat.isStreaming}>
          <Plus size={16} />New
        </button>
      </div>
      <div className="thread-list">
        {chat.threads.length ? chat.threads.map((thread) => (
          <div
            className={chat.activeThreadId === thread.id ? "thread-item active" : "thread-item"}
            key={thread.id}
          >
            <button className="thread-select" onClick={() => void chat.selectThread(thread.id)} disabled={chat.isStreaming}>
              <strong>{thread.title || "New chat"}</strong>
              <small>{thread.message_count} messages | {formatDate(thread.updated_at)}</small>
            </button>
            <button
              className="icon-button"
              type="button"
              onClick={(event) => void deleteThread(event, thread)}
              disabled={chat.isStreaming}
              aria-label={`Delete ${thread.title || "conversation"}`}
              title="Delete conversation"
            >
              <Trash2 size={15} />
            </button>
          </div>
        )) : (
          <p className="muted-copy">{chat.isLoadingThreads ? "Loading conversations." : "No saved conversations yet."}</p>
        )}
      </div>
    </section>
  );
}

function ChatScreen({ agentName, draftPrompt }: { agentName: string; draftPrompt: AgentPromptDraft | null }) {
  const [input, setInput] = useState("");
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [pendingAttachment, setPendingAttachment] = useState<ChatAttachment | null>(null);
  const [fileStatus, setFileStatus] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isVoiceModeActive, setIsVoiceModeActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState<string | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const chat = useJarvisChat();
  const selectedPersonality = getPersonality(chat.activePersonality);
  const endRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const pendingAttachmentRef = useRef<ChatAttachment | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const voiceReplyAfterIdRef = useRef<string | null | undefined>(undefined);
  const voiceModeActiveRef = useRef(false);
  const voiceTranscriptRef = useRef("");
  const shouldSendVoiceRef = useRef(false);
  const restartVoiceTimerRef = useRef<number | null>(null);
  const microphoneCheckedRef = useRef(false);
  const chatRef = useRef<{
    isConnected: boolean;
    isStreaming: boolean;
    messages: ChatMessage[];
    sendMessage: (text: string, attachments?: ChatAttachment[]) => void;
  }>({
    isConnected: false,
    isStreaming: false,
    messages: [] as ChatMessage[],
    sendMessage: () => undefined,
  });

  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [chat.messages]);

  useEffect(() => {
    if (draftPrompt?.text) setInput(draftPrompt.text);
  }, [draftPrompt]);

  useEffect(() => {
    pendingAttachmentRef.current = pendingAttachment;
  }, [pendingAttachment]);

  useEffect(() => {
    chatRef.current = {
      isConnected: chat.isConnected,
      isStreaming: chat.isStreaming,
      messages: chat.messages,
      sendMessage: chat.sendMessage,
    };
  }, [chat.isConnected, chat.isStreaming, chat.messages, chat.sendMessage]);

  const getRecognitionConstructor = useCallback(() => {
    if (typeof window === "undefined") return null;
    const speechWindow = window as SpeechRecognitionWindow;
    return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null;
  }, []);

  const clearVoiceRestartTimer = useCallback(() => {
    if (restartVoiceTimerRef.current === null) return;
    globalThis.clearTimeout(restartVoiceTimerRef.current);
    restartVoiceTimerRef.current = null;
  }, []);

  const getVoiceCaptureError = useCallback((error?: string) => {
    if (error === "not-allowed" || error === "service-not-allowed") {
      return "Permite el microfono en el navegador y vuelve a intentarlo.";
    }
    if (error === "audio-capture") {
      return "No encontre un microfono disponible para capturar audio.";
    }
    if (error === "network") {
      return "El reconocimiento de voz no pudo conectarse. Revisa tu conexion.";
    }
    return "No pude capturar audio. Intenta hablar de nuevo.";
  }, []);

  const requestMicrophoneAccess = useCallback(async () => {
    if (typeof window === "undefined") return false;
    if (!window.isSecureContext && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      setVoiceError("El microfono requiere HTTPS o localhost.");
      setVoiceStatus(null);
      return false;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setVoiceError("Este navegador no permite solicitar acceso al microfono.");
      setVoiceStatus(null);
      return false;
    }
    if (microphoneCheckedRef.current) return true;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      microphoneCheckedRef.current = true;
      return true;
    } catch (error) {
      const name = error instanceof DOMException ? error.name : "";
      setVoiceStatus(null);
      setVoiceError(
        name === "NotAllowedError" || name === "SecurityError"
          ? "Permite el microfono en el navegador y vuelve a intentarlo."
          : "No encontre un microfono disponible para capturar audio."
      );
      return false;
    }
  }, []);

  const sendVoiceTranscript = useCallback(() => {
    const transcript = voiceTranscriptRef.current.trim();

    voiceModeActiveRef.current = false;
    shouldSendVoiceRef.current = false;
    clearVoiceRestartTimer();
    setIsVoiceModeActive(false);
    setIsListening(false);
    recognitionRef.current = null;

    if (!transcript) {
      setVoiceStatus(null);
      return;
    }

    const previousAssistant = [...chatRef.current.messages].reverse().find((message) => message.role === "assistant");
    const attachment = pendingAttachmentRef.current;
    setVoiceStatus("Enviando al agente.");
    setInput("");
    setPendingAttachment(null);
    setFileStatus(null);
    setFileError(null);
    voiceTranscriptRef.current = "";
    voiceReplyAfterIdRef.current = previousAssistant?.id ?? null;
    chatRef.current.sendMessage(transcript, attachment ? [attachment] : []);
  }, [clearVoiceRestartTimer]);

  const startListening = useCallback(async () => {
    if (!voiceModeActiveRef.current) return;

    setVoiceError(null);
    clearVoiceRestartTimer();

    const Recognition = getRecognitionConstructor();
    if (!Recognition) {
      voiceModeActiveRef.current = false;
      setIsVoiceModeActive(false);
      setVoiceError("Este navegador no soporta reconocimiento de voz.");
      setVoiceStatus(null);
      return;
    }
    if (!chatRef.current.isConnected) {
      voiceModeActiveRef.current = false;
      setIsVoiceModeActive(false);
      setVoiceError("Espera a que el chat se conecte antes de hablar.");
      setVoiceStatus(null);
      return;
    }
    if (chatRef.current.isStreaming) {
      setVoiceStatus("Esperando respuesta.");
      return;
    }
    if (!(await requestMicrophoneAccess())) {
      voiceModeActiveRef.current = false;
      setIsVoiceModeActive(false);
      setIsListening(false);
      recognitionRef.current = null;
      return;
    }

    window.speechSynthesis?.cancel();

    const recognition = new Recognition();
    recognitionRef.current = recognition;
    recognition.lang = navigator.language?.startsWith("es") ? navigator.language : "es-MX";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    const baseTranscript = voiceTranscriptRef.current.trim();
    let latestTranscript = baseTranscript;

    recognition.onstart = () => {
      setIsListening(true);
      setVoiceStatus("Escuchando.");
    };

    recognition.onresult = (event: SpeechRecognitionEventLike) => {
      const sessionTranscript = Array.from({ length: event.results.length }, (_, index) => event.results[index]?.[0]?.transcript ?? "")
        .join(" ")
        .trim();
      const transcript = [baseTranscript, sessionTranscript].filter(Boolean).join(" ").replace(/\s+/g, " ").trim();
      latestTranscript = transcript;
      voiceTranscriptRef.current = transcript;
      setInput(transcript);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEventLike) => {
      setIsListening(false);
      recognitionRef.current = null;
      if (event.error === "no-speech") {
        setVoiceStatus("No escuche nada. Sigo en modo voz.");
        return;
      }
      if (event.error !== "aborted") {
        voiceModeActiveRef.current = false;
        setIsVoiceModeActive(false);
        setVoiceStatus(null);
        setVoiceError(getVoiceCaptureError(event.error));
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;

      if (!voiceModeActiveRef.current) return;

      if (shouldSendVoiceRef.current) {
        sendVoiceTranscript();
        return;
      }

      voiceTranscriptRef.current = latestTranscript.trim();
      setVoiceStatus(voiceTranscriptRef.current ? "Sigo escuchando." : "No escuche nada. Sigo en modo voz.");
      restartVoiceTimerRef.current = window.setTimeout(() => { void startListening(); }, 250);
    };

    try {
      recognition.start();
    } catch {
      voiceModeActiveRef.current = false;
      setIsVoiceModeActive(false);
      setIsListening(false);
      recognitionRef.current = null;
      setVoiceStatus(null);
      setVoiceError("No pude iniciar el microfono.");
    }
  }, [clearVoiceRestartTimer, getRecognitionConstructor, getVoiceCaptureError, requestMicrophoneAccess, sendVoiceTranscript]);

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setVoiceError("Este navegador no soporta lectura de voz.");
      setVoiceStatus(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = navigator.language?.startsWith("es") ? navigator.language : "es-MX";
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onstart = () => setVoiceStatus("Reproduciendo respuesta.");
    utterance.onend = () => setVoiceStatus(null);
    utterance.onerror = () => {
      setVoiceError("No pude reproducir la respuesta por voz.");
      setVoiceStatus(null);
    };
    window.speechSynthesis.speak(utterance);
  }, []);

  useEffect(() => {
    if (voiceReplyAfterIdRef.current === undefined) return;

    const previousAssistantId = voiceReplyAfterIdRef.current;
    const previousIndex = previousAssistantId
      ? chat.messages.findIndex((message) => message.id === previousAssistantId)
      : -1;
    const nextAssistant = chat.messages
      .slice(previousIndex + 1)
      .find((message) => message.role === "assistant");

    if (!nextAssistant || nextAssistant.isStreaming || !nextAssistant.content.trim()) return;

    voiceReplyAfterIdRef.current = undefined;
    speak(nextAssistant.content);
  }, [chat.messages, speak]);

  useEffect(() => {
    return () => {
      voiceModeActiveRef.current = false;
      shouldSendVoiceRef.current = false;
      if (restartVoiceTimerRef.current !== null) {
        globalThis.clearTimeout(restartVoiceTimerRef.current);
      }
      recognitionRef.current?.abort();
      recognitionRef.current = null;
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const send = (text: string) => {
    const trimmed = text.trim();
    const attachment = pendingAttachment;
    if ((!trimmed && !attachment) || chat.isStreaming || !chat.isConnected || isUploadingFile) return;
    setInput("");
    setPendingAttachment(null);
    setFileStatus(null);
    setFileError(null);
    chat.sendMessage(trimmed, attachment ? [attachment] : []);
  };

  const handleFileUpload = async (file: File) => {
    setIsUploadingFile(true);
    setFileError(null);
    setFileStatus(`Adjuntando ${file.name}.`);

    const result = await chat.uploadAttachment(file);
    setIsUploadingFile(false);

    if (!result) {
      setFileStatus(null);
      setFileError(chat.error ?? "No pude adjuntar el archivo.");
      return;
    }

    setPendingAttachment(result);
    setFileStatus(`${file.name} listo para enviarse con tu siguiente mensaje.`);
  };

  const toggleVoiceChat = () => {
    if (isVoiceModeActive) {
      shouldSendVoiceRef.current = true;
      setVoiceStatus("Enviando al agente.");
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      } else {
        sendVoiceTranscript();
      }
      return;
    }

    voiceModeActiveRef.current = true;
    shouldSendVoiceRef.current = false;
    voiceTranscriptRef.current = input.trim();
    setIsVoiceModeActive(true);
    setVoiceError(null);
    setVoiceStatus("Escuchando.");
    void startListening();
  };

  return (
    <div className="screen chat-screen">
      <Hero
        eyebrow=""
        title="CHAT"
        subtitle=""
        error={chat.error}
      >
        <div className={`status-pill ${chat.isConnected ? "online" : "offline"}`}>
          <span />{chat.isConnected ? "Connected" : "Connecting"}
        </div>
      </Hero>

      <ChatHistoryPanel chat={chat} />

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
          null
        ) : chat.messages.map((message) => <MessageBubble key={message.id} message={message} agentName={agentName} />)}
        <div ref={endRef} />
      </section>

      <form className="composer" onSubmit={(event) => { event.preventDefault(); send(input); }}>
        <div className="composer-main">
          {pendingAttachment ? (
            <div className="attachment-chip">
              <FileText size={16} />
              <span>{pendingAttachment.source.original_filename ?? pendingAttachment.source.title}</span>
              <button
                type="button"
                onClick={() => {
                  setPendingAttachment(null);
                  setFileStatus(null);
                  setFileError(null);
                }}
                aria-label="Remove attached file"
                title="Remove attached file"
              >
                <X size={14} />
              </button>
            </div>
          ) : null}
          <textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder={chat.isConnected ? `Ask ${agentName} to organize the next move` : "Waiting for connection"} />
        </div>
        <button
          type="button"
          className="upload-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploadingFile || chat.isStreaming}
          aria-label="Upload file"
          title="Upload file"
        >
          <CloudUpload size={18} />
        </button>
        <input
          ref={fileInputRef}
          className="composer-file-input"
          type="file"
          accept=".md,.txt,.pdf,.docx,text/markdown,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) void handleFileUpload(file);
          }}
        />
        <button
          type="button"
          className={isListening ? "voice-button listening" : "voice-button"}
          onClick={toggleVoiceChat}
          disabled={!chat.isConnected || (!isVoiceModeActive && chat.isStreaming)}
          aria-label={isVoiceModeActive ? "Enviar mensaje de voz" : "Hablar con el agente"}
          title={isVoiceModeActive ? "Enviar mensaje de voz" : "Hablar con el agente"}
        >
          {isVoiceModeActive ? <MicOff size={18} /> : <Mic size={18} />}
        </button>
        <button className="send-button" disabled={!chat.isConnected || chat.isStreaming || isUploadingFile || (!input.trim() && !pendingAttachment)} aria-label="Send message">
          <ArrowUp size={18} />
        </button>
      </form>
      {fileStatus || fileError ? (
        <p className={fileError ? "file-feedback error" : "file-feedback"}>{fileError ?? fileStatus}</p>
      ) : null}
      {voiceStatus || voiceError ? (
        <p className={voiceError ? "voice-feedback error" : "voice-feedback"}>{voiceError ?? voiceStatus}</p>
      ) : null}
    </div>
  );
}

function NotesScreen({ agentName }: { agentName: string }) {
  const notes = useNotes();
  const knowledge = useKnowledge();
  const refreshNotes = notes.refresh;
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Note | null>(null);
  const [draft, setDraft] = useState({ title: "", content: "", tags: "" });

  useEffect(() => { refreshNotes(); }, [refreshNotes]);

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
        eyebrow=""
        title="NOTAS"
        subtitle=""
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
  const refreshTodos = todos.refresh;
  const [filter, setFilter] = useState<"pending" | "all" | "completed">("pending");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Todo | null>(null);
  const [draft, setDraft] = useState<{ text: string; priority: Todo["priority"]; due_date: string }>({ text: "", priority: "medium", due_date: "" });

  useEffect(() => { refreshTodos({ show_completed: true }); }, [refreshTodos]);

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
        eyebrow=""
        title="TODOLIST"
        subtitle=""
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
  const refreshKnowledge = knowledge.refresh;
  const [type, setType] = useState("all");
  const [query, setQuery] = useState("");
  const [noteId, setNoteId] = useState("");
  const [detail, setDetail] = useState<KnowledgePageDetail | null>(null);

  const filters = useMemo(() => ({ type: type === "all" ? undefined : type, q: query.trim() || undefined }), [query, type]);
  useEffect(() => { refreshKnowledge(filters); }, [refreshKnowledge, filters]);

  const openDetail = async (page: KnowledgePage | string) => {
    const path = typeof page === "string" ? page : page.path;
    const next = await knowledge.getPage(path);
    if (next) setDetail(next);
  };

  return (
    <div className="screen">
      <Hero
        eyebrow=""
        title="WIKI"
        subtitle=""
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
          <label className="soft-button file-button"><CloudUpload size={16} />Upload file<input type="file" accept=".md,.txt,.pdf,.docx,text/markdown,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={async (event) => {
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
  const { data: session } = useSession();
  const userEmail = session?.user?.email ?? "";

  useEffect(() => {
    const savedAgentName = window.localStorage.getItem("orbit.agentName");
    setAgentName(savedAgentName?.trim() || "Orbit");
  }, []);

  return (
    <main>
      <div className="background-wash" />
      <div className="app-shell">
        <div className="topbar">
          <BrandMark agentName={agentName} />
          <div className="auth-chip">
            <span>{userEmail}</span>
            <button onClick={() => signOut({ callbackUrl: "/login" })} aria-label="Sign out" title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        </div>
        {activeTab === "chat" && <ChatScreen agentName={agentName} draftPrompt={null} />}
        {activeTab === "notes" && <NotesScreen agentName={agentName} />}
        {activeTab === "knowledge" && <KnowledgeScreen />}
        {activeTab === "todos" && <TodosScreen agentName={agentName} />}
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

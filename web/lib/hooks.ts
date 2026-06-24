"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient, WS_URL } from "./api";
import { COMMAND_TO_PERSONALITY_ID, getPersonality } from "./personalities";
import type {
  CalendarEvent,
  ChatAttachment,
  ChatMessage,
  ChatThread,
  EmailDraft,
  EmailLabel,
  EmailMessage,
  EmailThread,
  KnowledgeIngestResult,
  KnowledgePage,
  KnowledgePageDetail,
  KnowledgeSource,
  KnowledgeStatus,
  Note,
  PersonalityId,
  StreamChunk,
  Todo,
  ToolActivity,
} from "./types";

function createId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error && "response" in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } }).response;
    if (response?.data?.detail) return String(response.data.detail);
  }
  if (error instanceof Error) return error.message;
  return "Unknown error";
}

function buildAttachmentContext(attachments: ChatAttachment[]): string {
  if (!attachments.length) return "";

  const details = attachments.map((attachment, index) => {
    const source = attachment.source;
    const preview = attachment.extracted_preview.trim();
    return [
      `Attachment ${index + 1}:`,
      `- filename: ${source.original_filename ?? source.title}`,
      `- source_id: ${source.source_id}`,
      `- raw_path: ${source.raw_path}`,
      source.extracted_path ? `- extracted_path: ${source.extracted_path}` : null,
      "- Gmail draft attachment use: pass this source_id in attachment_source_ids when calling create_email_draft.",
      preview ? `- extracted text preview:\n${preview.slice(0, 2500)}` : null,
    ].filter(Boolean).join("\n");
  });

  return `\n\n[Chat attachments]\n${details.join("\n\n")}`;
}

async function getJarvisAuth(): Promise<{ token: string; wsUrl?: string }> {
  const response = await fetch("/api/auth/jarvis-token", { cache: "no-store" });
  if (!response.ok) throw new Error("Authentication required");
  const data = (await response.json()) as { token?: string; wsUrl?: string };
  if (!data.token) throw new Error("Authentication token missing");
  return { token: data.token, wsUrl: data.wsUrl };
}

function useCollection<T>(path: string) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastParamsRef = useRef<Record<string, unknown> | undefined>(undefined);

  const refresh = useCallback(
    async (params?: Record<string, unknown>) => {
      const nextParams = params ?? lastParamsRef.current;
      if (params !== undefined) lastParamsRef.current = params;

      setLoading(true);
      setError(null);
      try {
        const { data } = await apiClient.get<T[]>(path, { params: nextParams });
        setItems(data);
        return data;
      } catch (err: unknown) {
        setError(getErrorMessage(err));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [path]
  );

  const create = useCallback(
    async (payload: Partial<T>): Promise<T | null> => {
      setError(null);
      try {
        const { data } = await apiClient.post<T>(path, payload);
        await refresh();
        return data;
      } catch (err: unknown) {
        setError(getErrorMessage(err));
        return null;
      }
    },
    [path, refresh]
  );

  const update = useCallback(
    async (id: string, payload: Partial<T>): Promise<T | null> => {
      setError(null);
      try {
        const { data } = await apiClient.put<T>(`${path}/${id}`, payload);
        await refresh();
        return data;
      } catch (err: unknown) {
        setError(getErrorMessage(err));
        return null;
      }
    },
    [path, refresh]
  );

  const remove = useCallback(
    async (id: string) => {
      setError(null);
      try {
        await apiClient.delete(`${path}/${id}`);
        await refresh();
        return true;
      } catch (err: unknown) {
        setError(getErrorMessage(err));
        return false;
      }
    },
    [path, refresh]
  );

  return { items, loading, error, refresh, create, update, remove };
}

export function useNotes() {
  return useCollection<Note>("/notes");
}

export function useTodos() {
  const base = useCollection<Todo>("/todos");

  const setCompleted = useCallback(
    async (id: string, completed: boolean) => {
      try {
        if (completed) await apiClient.patch(`/todos/${id}/complete`);
        else await apiClient.put(`/todos/${id}`, { completed: false });
        await base.refresh({ show_completed: true });
        return true;
      } catch {
        return false;
      }
    },
    [base]
  );

  return { ...base, setCompleted };
}

export function useCalendar() {
  return useCollection<CalendarEvent>("/calendar");
}

export function useEmails() {
  const base = useCollection<EmailMessage>("/emails");
  const [thread, setThread] = useState<EmailThread | null>(null);
  const [drafts, setDrafts] = useState<EmailDraft[]>([]);
  const [labels, setLabels] = useState<EmailLabel[]>([]);
  const [actionError, setActionError] = useState<string | null>(null);

  const search = useCallback(async (query: string, max = 10) => {
    setActionError(null);
    try {
      const { data } = await apiClient.get<EmailMessage[]>("/emails/search", { params: { q: query, max } });
      return data;
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
      return null;
    }
  }, []);

  const getThread = useCallback(async (threadId: string) => {
    setActionError(null);
    try {
      const { data } = await apiClient.get<EmailThread>(`/emails/threads/${encodeURIComponent(threadId)}`);
      setThread(data);
      return data;
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
      return null;
    }
  }, []);

  const listDrafts = useCallback(async (query?: string, max = 20) => {
    setActionError(null);
    try {
      const { data } = await apiClient.get<{ drafts?: EmailDraft[] } | EmailDraft[]>("/emails/drafts", { params: { q: query || undefined, max } });
      const nextDrafts = Array.isArray(data) ? data : data.drafts ?? [];
      setDrafts(nextDrafts);
      return nextDrafts;
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
      return null;
    }
  }, []);

  const createDraft = useCallback(
    async (payload: { to: string[]; subject?: string; body?: string; cc?: string[]; bcc?: string[]; htmlBody?: string; replyToMessageId?: string }) => {
      setActionError(null);
      try {
        const { data } = await apiClient.post<EmailDraft>("/emails/drafts", payload);
        await listDrafts();
        return data;
      } catch (err: unknown) {
        setActionError(getErrorMessage(err));
        return null;
      }
    },
    [listDrafts]
  );

  const listLabels = useCallback(async () => {
    setActionError(null);
    try {
      const { data } = await apiClient.get<{ labels?: EmailLabel[] } | EmailLabel[]>("/emails/labels");
      const nextLabels = Array.isArray(data) ? data : data.labels ?? [];
      setLabels(nextLabels);
      return nextLabels;
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
      return null;
    }
  }, []);

  const createLabel = useCallback(
    async (displayName: string) => {
      setActionError(null);
      try {
        const { data } = await apiClient.post<EmailLabel>("/emails/labels", { displayName });
        await listLabels();
        return data;
      } catch (err: unknown) {
        setActionError(getErrorMessage(err));
        return null;
      }
    },
    [listLabels]
  );

  const updateLabel = useCallback(
    async (labelId: string, displayName: string) => {
      setActionError(null);
      try {
        const { data } = await apiClient.put<EmailLabel>(`/emails/labels/${encodeURIComponent(labelId)}`, { displayName });
        await listLabels();
        return data;
      } catch (err: unknown) {
        setActionError(getErrorMessage(err));
        return null;
      }
    },
    [listLabels]
  );

  const applyLabelsToThread = useCallback(async (threadId: string, labelIds: string[]) => {
    setActionError(null);
    try {
      await apiClient.post(`/emails/threads/${encodeURIComponent(threadId)}/labels`, { labelIds });
      await base.refresh();
      return true;
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
      return false;
    }
  }, [base]);

  const removeLabelsFromThread = useCallback(async (threadId: string, labelIds: string[]) => {
    setActionError(null);
    try {
      await apiClient.post(`/emails/threads/${encodeURIComponent(threadId)}/labels/remove`, { labelIds });
      await base.refresh();
      return true;
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
      return false;
    }
  }, [base]);

  return {
    ...base,
    thread,
    drafts,
    labels,
    actionError,
    search,
    getThread,
    createDraft,
    listDrafts,
    listLabels,
    createLabel,
    updateLabel,
    applyLabelsToThread,
    removeLabelsFromThread,
  };
}

export function useKnowledge() {
  const [status, setStatus] = useState<KnowledgeStatus | null>(null);
  const [pages, setPages] = useState<KnowledgePage[]>([]);
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (params?: { type?: string; q?: string }) => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, pagesRes, sourcesRes] = await Promise.all([
        apiClient.get<KnowledgeStatus>("/knowledge/status"),
        apiClient.get<KnowledgePage[]>("/knowledge/pages", { params }),
        apiClient.get<KnowledgeSource[]>("/knowledge/sources"),
      ]);
      setStatus(statusRes.data);
      setPages(pagesRes.data);
      setSources(sourcesRes.data);
      return { status: statusRes.data, pages: pagesRes.data, sources: sourcesRes.data };
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getPage = useCallback(async (path: string): Promise<KnowledgePageDetail | null> => {
    setError(null);
    try {
      const { data } = await apiClient.get<KnowledgePageDetail>(`/knowledge/pages/${encodeURIComponent(path)}`);
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    }
  }, []);

  const ingestNote = useCallback(
    async (noteId: string): Promise<KnowledgeIngestResult | null> => {
      setError(null);
      try {
        const { data } = await apiClient.post<KnowledgeIngestResult>("/knowledge/ingest/note", { note_id: noteId });
        await refresh();
        return data;
      } catch (err: unknown) {
        setError(getErrorMessage(err));
        return null;
      }
    },
    [refresh]
  );

  const uploadFile = useCallback(
    async (file: File): Promise<KnowledgeIngestResult | null> => {
      setError(null);
      try {
        const form = new FormData();
        form.append("file", file);
        const { data } = await apiClient.post<KnowledgeIngestResult>("/knowledge/ingest/file", form, {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 120000,
        });
        await refresh();
        return data;
      } catch (err: unknown) {
        setError(getErrorMessage(err));
        return null;
      }
    },
    [refresh]
  );

  const runLint = useCallback(async (): Promise<KnowledgeIngestResult | null> => {
    setError(null);
    try {
      const { data } = await apiClient.post<KnowledgeIngestResult>("/knowledge/lint", {});
      await refresh();
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    }
  }, [refresh]);

  return { status, pages, sources, loading, error, refresh, getPage, ingestNote, uploadFile, runLint };
}

const ACTIVE_CHAT_THREAD_KEY = "orbit.activeChatThreadId";

export function useJarvisChat(initialSessionId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(initialSessionId ?? null);
  const [isLoadingThreads, setIsLoadingThreads] = useState(false);
  const [activePersonality, setActivePersonality] = useState<PersonalityId | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTools, setActiveTools] = useState<ToolActivity[]>([]);
  const [lastCompletedTool, setLastCompletedTool] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamingIdRef = useRef<string | null>(null);
  const sessionIdRef = useRef<string>(initialSessionId ?? createId());
  const activePersonalityRef = useRef<PersonalityId | null>(null);
  const refreshThreadsRef = useRef<() => Promise<ChatThread[] | null>>(async () => null);

  const loadMessages = useCallback(async (threadId: string): Promise<ChatMessage[] | null> => {
    setError(null);
    try {
      const { data } = await apiClient.get<ChatMessage[]>(`/chat/threads/${encodeURIComponent(threadId)}/messages`);
      setMessages(data);
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    }
  }, []);

  const refreshThreads = useCallback(async (): Promise<ChatThread[] | null> => {
    setIsLoadingThreads(true);
    setError(null);
    try {
      const { data } = await apiClient.get<ChatThread[]>("/chat/threads");
      setThreads(data);
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    } finally {
      setIsLoadingThreads(false);
    }
  }, []);

  useEffect(() => {
    refreshThreadsRef.current = refreshThreads;
  }, [refreshThreads]);

  const selectThread = useCallback(
    async (threadId: string) => {
      if (isStreaming) return false;
      sessionIdRef.current = threadId;
      setActiveThreadId(threadId);
      if (typeof window !== "undefined") window.localStorage.setItem(ACTIVE_CHAT_THREAD_KEY, threadId);
      const loaded = await loadMessages(threadId);
      return loaded !== null;
    },
    [isStreaming, loadMessages]
  );

  const newThread = useCallback(async () => {
    if (isStreaming) return null;
    setError(null);
    try {
      const { data } = await apiClient.post<ChatThread>("/chat/threads", { title: "New chat" });
      sessionIdRef.current = data.id;
      setActiveThreadId(data.id);
      setMessages([]);
      if (typeof window !== "undefined") window.localStorage.setItem(ACTIVE_CHAT_THREAD_KEY, data.id);
      await refreshThreads();
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    }
  }, [isStreaming, refreshThreads]);

  const deleteThread = useCallback(
    async (threadId: string) => {
      if (isStreaming) return false;
      setError(null);
      try {
        await apiClient.delete(`/chat/threads/${encodeURIComponent(threadId)}`);
        const nextThreads = (await refreshThreads())?.filter((thread) => thread.id !== threadId) ?? [];
        if (sessionIdRef.current === threadId) {
          const nextThread = nextThreads[0];
          if (nextThread) {
            await selectThread(nextThread.id);
          } else {
            sessionIdRef.current = createId();
            setActiveThreadId(null);
            setMessages([]);
            if (typeof window !== "undefined") window.localStorage.removeItem(ACTIVE_CHAT_THREAD_KEY);
          }
        }
        return true;
      } catch (err: unknown) {
        setError(getErrorMessage(err));
        return false;
      }
    },
    [isStreaming, refreshThreads, selectThread]
  );

  useEffect(() => {
    let cancelled = false;

    const initializeThread = async () => {
      const availableThreads = await refreshThreads();
      if (cancelled) return;

      if (initialSessionId) {
        sessionIdRef.current = initialSessionId;
        setActiveThreadId(initialSessionId);
        if (typeof window !== "undefined") window.localStorage.setItem(ACTIVE_CHAT_THREAD_KEY, initialSessionId);
        await loadMessages(initialSessionId);
        return;
      }

      const savedThreadId = typeof window !== "undefined" ? window.localStorage.getItem(ACTIVE_CHAT_THREAD_KEY) : null;
      const selectedThread =
        availableThreads?.find((thread) => thread.id === savedThreadId) ??
        availableThreads?.[0] ??
        null;

      if (selectedThread) {
        sessionIdRef.current = selectedThread.id;
        setActiveThreadId(selectedThread.id);
        if (typeof window !== "undefined") window.localStorage.setItem(ACTIVE_CHAT_THREAD_KEY, selectedThread.id);
        await loadMessages(selectedThread.id);
      } else {
        const nextId = sessionIdRef.current;
        setActiveThreadId(nextId);
        if (typeof window !== "undefined") window.localStorage.setItem(ACTIVE_CHAT_THREAD_KEY, nextId);
      }
    };

    void initializeThread();

    return () => {
      cancelled = true;
    };
  }, [initialSessionId, loadMessages, refreshThreads]);

  useEffect(() => {
    let cancelled = false;
    let ws: WebSocket | null = null;

    const finishStreamingMessage = (fallbackContent?: string) => {
      const messageId = streamingIdRef.current;
      if (!messageId) return;
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? { ...message, isStreaming: false, content: message.content || fallbackContent || "" }
            : message
        )
      );
      streamingIdRef.current = null;
    };

    getJarvisAuth()
      .then(({ token, wsUrl }) => {
        if (cancelled) return;

        const socketUrl = new URL(`${wsUrl ?? WS_URL}/ws/chat`);
        socketUrl.searchParams.set("token", token);
        ws = new WebSocket(socketUrl.toString());
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          setError(null);
        };
        ws.onclose = () => {
          const hadStreamingMessage = streamingIdRef.current !== null;
          setIsConnected(false);
          setIsStreaming(false);
          setActiveTools([]);
          finishStreamingMessage("Connection to Jarvis was lost.");
          if (hadStreamingMessage) setError("Connection to Jarvis was lost.");
        };
        ws.onmessage = (event) => {
          const chunk: StreamChunk = JSON.parse(event.data);
          if (chunk.type === "token" && chunk.content) {
            setMessages((prev) =>
              prev.map((message) =>
                message.id === streamingIdRef.current ? { ...message, content: message.content + chunk.content } : message
              )
            );
            return;
          }
          if (chunk.type === "tool_start" && chunk.tool_name) {
            const toolName = chunk.tool_name;
            setActiveTools((prev) =>
              prev.some((tool) => tool.name === toolName) ? prev : [...prev, { name: toolName, phase: "running" }]
            );
            return;
          }
          if (chunk.type === "tool_end" && chunk.tool_name) {
            setActiveTools((prev) => prev.filter((tool) => tool.name !== chunk.tool_name));
            setLastCompletedTool(chunk.tool_name);
            return;
          }
          if (chunk.type === "done") {
            setIsStreaming(false);
            setActiveTools([]);
            finishStreamingMessage();
            void refreshThreadsRef.current();
            return;
          }
          if (chunk.type === "error") {
            setIsStreaming(false);
            setActiveTools([]);
            const message = chunk.content ?? "Jarvis could not finish the request.";
            setError(message);
            finishStreamingMessage(message);
          }
        };
      })
      .catch((err: unknown) => {
        setIsStreaming(false);
        setActiveTools([]);
        setIsConnected(false);
        setError(getErrorMessage(err));
      });

    return () => {
      cancelled = true;
      ws?.close();
    };
  }, []);

  const addLocalAssistantMessage = useCallback((content: string) => {
    setMessages((prev) => [...prev, { id: createId(), role: "assistant", content }]);
  }, []);

  const setPersonality = useCallback((personalityId: PersonalityId | null) => {
    activePersonalityRef.current = personalityId;
    setActivePersonality(personalityId);
  }, []);

  const uploadAttachment = useCallback(async (file: File): Promise<ChatAttachment | null> => {
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await apiClient.post<ChatAttachment>("/chat/attachments", form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    }
  }, []);

  const sendMessage = useCallback(
    (text: string, attachments: ChatAttachment[] = []) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      setError(null);
      setLastCompletedTool(null);

      const trimmed = text.trim();
      if (!trimmed && !attachments.length) return;
      const [maybeCommand, ...remainingParts] = trimmed.split(/\s+/);
      const normalizedCommand = maybeCommand.toLowerCase();
      let outgoingText = trimmed;

      if (normalizedCommand === "/normal" || normalizedCommand === "/jarvis") {
        setPersonality(null);
        outgoingText = remainingParts.join(" ").trim();
        if (!outgoingText && !attachments.length) {
          addLocalAssistantMessage("Jarvis normal activated.");
          return;
        }
      } else if (COMMAND_TO_PERSONALITY_ID[normalizedCommand]) {
        const nextPersonality = COMMAND_TO_PERSONALITY_ID[normalizedCommand];
        setPersonality(nextPersonality);
        outgoingText = remainingParts.join(" ").trim();
        if (!outgoingText && !attachments.length) {
          addLocalAssistantMessage(`${getPersonality(nextPersonality)?.name ?? "Personality"} activated.`);
          return;
        }
      }

      const visibleAttachmentText = attachments
        .map((attachment) => `Attached: ${attachment.source.original_filename ?? attachment.source.title}`)
        .join("\n");
      const visibleText = [trimmed, visibleAttachmentText].filter(Boolean).join("\n\n");
      const messageText = `${outgoingText || "Use the attached file."}${buildAttachmentContext(attachments)}`;

      const assistantId = createId();
      streamingIdRef.current = assistantId;
      setIsStreaming(true);
      setActiveThreadId(sessionIdRef.current);
      if (typeof window !== "undefined") window.localStorage.setItem(ACTIVE_CHAT_THREAD_KEY, sessionIdRef.current);
      setMessages((prev) => [
        ...prev,
        { id: createId(), role: "user", content: visibleText },
        { id: assistantId, role: "assistant", content: "", isStreaming: true },
      ]);
      wsRef.current.send(
        JSON.stringify({
          message: messageText,
          session_id: sessionIdRef.current,
          personality_id: activePersonalityRef.current,
        })
      );
    },
    [addLocalAssistantMessage, setPersonality]
  );

  return {
    messages,
    threads,
    activeThreadId,
    isLoadingThreads,
    sendMessage,
    uploadAttachment,
    selectThread,
    newThread,
    deleteThread,
    refreshThreads,
    activePersonality,
    setPersonality,
    isConnected,
    isStreaming,
    activeTools,
    lastCompletedTool,
    error,
  };
}

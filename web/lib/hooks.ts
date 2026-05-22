"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient, WS_URL } from "./api";
import { COMMAND_TO_PERSONALITY_ID, getPersonality } from "./personalities";
import type {
  CalendarEvent,
  ChatMessage,
  EmailMessage,
  KnowledgeIngestResult,
  KnowledgePage,
  KnowledgePageDetail,
  KnowledgeSource,
  KnowledgeStatus,
  Note,
  PersonalityId,
  StoredMessage,
  StreamChunk,
  Thread,
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
  return useCollection<EmailMessage>("/emails");
}

export function useThreads() {
  const base = useCollection<Thread>("/threads");

  const getMessages = useCallback(async (threadId: string): Promise<StoredMessage[] | null> => {
    try {
      const { data } = await apiClient.get<StoredMessage[]>(`/threads/${threadId}/messages`);
      return data;
    } catch {
      return null;
    }
  }, []);

  return { ...base, getMessages };
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

export function useJarvisChat(initialSessionId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionIdState] = useState<string>(initialSessionId ?? createId());
  const [activePersonality, setActivePersonality] = useState<PersonalityId | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTools, setActiveTools] = useState<ToolActivity[]>([]);
  const [lastCompletedTool, setLastCompletedTool] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamingIdRef = useRef<string | null>(null);
  const sessionIdRef = useRef<string>(initialSessionId ?? sessionId);
  const activePersonalityRef = useRef<PersonalityId | null>(null);

  useEffect(() => {
    if (!initialSessionId || initialSessionId === sessionIdRef.current) return;
    sessionIdRef.current = initialSessionId;
    setSessionIdState(initialSessionId);
    setMessages([]);
    setActiveTools([]);
    setLastCompletedTool(null);
    setIsStreaming(false);
  }, [initialSessionId]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/chat`);
    wsRef.current = ws;

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

    return () => ws.close();
  }, []);

  const addLocalAssistantMessage = useCallback((content: string) => {
    setMessages((prev) => [...prev, { id: createId(), role: "assistant", content }]);
  }, []);

  const setPersonality = useCallback((personalityId: PersonalityId | null) => {
    activePersonalityRef.current = personalityId;
    setActivePersonality(personalityId);
  }, []);

  const sendMessage = useCallback(
    (text: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      setError(null);
      setLastCompletedTool(null);

      const trimmed = text.trim();
      const [maybeCommand, ...remainingParts] = trimmed.split(/\s+/);
      const normalizedCommand = maybeCommand.toLowerCase();
      let outgoingText = trimmed;

      if (normalizedCommand === "/normal" || normalizedCommand === "/jarvis") {
        setPersonality(null);
        outgoingText = remainingParts.join(" ").trim();
        if (!outgoingText) {
          addLocalAssistantMessage("Jarvis normal activated.");
          return;
        }
      } else if (COMMAND_TO_PERSONALITY_ID[normalizedCommand]) {
        const nextPersonality = COMMAND_TO_PERSONALITY_ID[normalizedCommand];
        setPersonality(nextPersonality);
        outgoingText = remainingParts.join(" ").trim();
        if (!outgoingText) {
          addLocalAssistantMessage(`${getPersonality(nextPersonality)?.name ?? "Personality"} activated.`);
          return;
        }
      }

      const assistantId = createId();
      streamingIdRef.current = assistantId;
      setIsStreaming(true);
      setMessages((prev) => [
        ...prev,
        { id: createId(), role: "user", content: trimmed },
        { id: assistantId, role: "assistant", content: "", isStreaming: true },
      ]);
      wsRef.current.send(
        JSON.stringify({
          message: outgoingText,
          session_id: sessionIdRef.current,
          user_id: "default",
          personality_id: activePersonalityRef.current,
        })
      );
    },
    [addLocalAssistantMessage, setPersonality]
  );

  const setSessionId = useCallback((nextSessionId: string, nextMessages: StoredMessage[] = []) => {
    sessionIdRef.current = nextSessionId;
    setSessionIdState(nextSessionId);
    streamingIdRef.current = null;
    setIsStreaming(false);
    setActiveTools([]);
    setLastCompletedTool(null);
    setError(null);
    setMessages(
      nextMessages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .map((message) => ({
          id: message.id,
          role: message.role as "user" | "assistant",
          content: message.content,
        }))
    );
  }, []);

  return {
    sessionId,
    setSessionId,
    messages,
    sendMessage,
    activePersonality,
    setPersonality,
    isConnected,
    isStreaming,
    activeTools,
    lastCompletedTool,
    error,
  };
}

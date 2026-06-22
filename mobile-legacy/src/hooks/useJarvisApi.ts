import { useState, useCallback, useRef } from "react";
import { apiClient } from "../api/client";
import type {
  CalendarEvent,
  KnowledgeIngestResult,
  KnowledgePage,
  KnowledgePageDetail,
  KnowledgeSource,
  KnowledgeStatus,
  Note,
  Todo,
} from "../api/types";

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error && "response" in error) {
    const response = (error as any).response;
    if (response?.data?.detail) {
      return String(response.data.detail);
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unknown error";
}

function useCollection<T>(path: string) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastParamsRef = useRef<Record<string, unknown> | undefined>(undefined);

  const refresh = useCallback(async (params?: Record<string, unknown>) => {
    const nextParams = params ?? lastParamsRef.current;
    if (params !== undefined) {
      lastParamsRef.current = params;
    }

    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<T[]>(path, { params: nextParams });
      setItems(data);
      return data;
    } catch (error: unknown) {
      setError(getErrorMessage(error));
      return null;
    } finally {
      setLoading(false);
    }
  }, [path]);

  const create = useCallback(async (payload: Partial<T>): Promise<T | null> => {
    setError(null);
    try {
      const { data } = await apiClient.post<T>(path, payload);
      await refresh();
      return data;
    } catch (error: unknown) {
      setError(getErrorMessage(error));
      return null;
    }
  }, [path, refresh]);

  const update = useCallback(async (id: string, payload: Partial<T>): Promise<T | null> => {
    setError(null);
    try {
      const { data } = await apiClient.put<T>(`${path}/${id}`, payload);
      await refresh();
      return data;
    } catch (error: unknown) {
      setError(getErrorMessage(error));
      return null;
    }
  }, [path, refresh]);

  const remove = useCallback(async (id: string) => {
    setError(null);
    try {
      await apiClient.delete(`${path}/${id}`);
      await refresh();
      return true;
    } catch (error: unknown) {
      setError(getErrorMessage(error));
      return false;
    }
  }, [path, refresh]);

  return { items, loading, error, refresh, create, update, remove };
}

export function useNotes() {
  return useCollection<Note>("/notes");
}

export function useTodos() {
  const base = useCollection<Todo>("/todos");

  const setCompleted = useCallback(async (id: string, completed: boolean) => {
    try {
      if (completed) {
        await apiClient.patch(`/todos/${id}/complete`);
      } else {
        await apiClient.put(`/todos/${id}`, { completed: false });
      }
      await base.refresh();
      return true;
    } catch (error: unknown) {
      return false;
    }
  }, [base.refresh]);

  return { ...base, setCompleted };
}

export function useCalendar() {
  return useCollection<CalendarEvent>("/calendar");
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
      return {
        status: statusRes.data,
        pages: pagesRes.data,
        sources: sourcesRes.data,
      };
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

  const ingestNote = useCallback(async (noteId: string): Promise<KnowledgeIngestResult | null> => {
    setError(null);
    try {
      const { data } = await apiClient.post<KnowledgeIngestResult>("/knowledge/ingest/note", { note_id: noteId });
      await refresh();
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    }
  }, [refresh]);

  const uploadFile = useCallback(async (file: { uri: string; name: string; type?: string }) => {
    setError(null);
    try {
      const form = new FormData();
      form.append("file", {
        uri: file.uri,
        name: file.name,
        type: file.type ?? "application/octet-stream",
      } as any);
      const { data } = await apiClient.post<KnowledgeIngestResult>("/knowledge/ingest/file", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await refresh();
      return data;
    } catch (err: unknown) {
      setError(getErrorMessage(err));
      return null;
    }
  }, [refresh]);

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

  return {
    status,
    pages,
    sources,
    loading,
    error,
    refresh,
    getPage,
    ingestNote,
    uploadFile,
    runLint,
  };
}

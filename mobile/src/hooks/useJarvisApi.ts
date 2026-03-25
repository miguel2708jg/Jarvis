import { useState, useCallback } from "react";
import { apiClient } from "../api/client";
import type { Note, Todo, CalendarEvent } from "../api/types";

function useCollection<T>(path: string) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (params?: Record<string, unknown>) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<T[]>(path, { params });
      setItems(data);
    } catch (e: any) {
      setError(e.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [path]);

  const create = useCallback(async (payload: Partial<T>): Promise<T | null> => {
    try {
      const { data } = await apiClient.post<T>(path, payload);
      await refresh();
      return data;
    } catch {
      return null;
    }
  }, [path, refresh]);

  const remove = useCallback(async (id: string) => {
    try {
      await apiClient.delete(`${path}/${id}`);
      await refresh();
    } catch {
      // ignore
    }
  }, [path, refresh]);

  return { items, loading, error, refresh, create, remove };
}

export function useNotes() {
  return useCollection<Note>("/notes");
}

export function useTodos() {
  const base = useCollection<Todo>("/todos");

  const complete = useCallback(async (id: string) => {
    try {
      await apiClient.patch(`/todos/${id}/complete`);
      await base.refresh();
    } catch {
      // ignore
    }
  }, [base.refresh]);

  return { ...base, complete };
}

export function useCalendar() {
  return useCollection<CalendarEvent>("/calendar");
}

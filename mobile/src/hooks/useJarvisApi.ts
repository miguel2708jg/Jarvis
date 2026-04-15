import { useState, useCallback, useRef } from "react";
import { apiClient } from "../api/client";
import type { Note, Todo, CalendarEvent } from "../api/types";

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

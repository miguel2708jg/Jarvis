import { useCallback, useEffect, useRef, useState } from "react";

import { WS_URL } from "../api/client";
import type { ChatMessage, StreamChunk, ToolActivity } from "../api/types";

function createId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function useJarvisChat(initialSessionId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTools, setActiveTools] = useState<ToolActivity[]>([]);
  const [lastCompletedTool, setLastCompletedTool] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamingIdRef = useRef<string | null>(null);
  const sessionIdRef = useRef<string>(initialSessionId ?? createId());

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/chat`);
    wsRef.current = ws;

    const finishStreamingMessage = (fallbackContent?: string) => {
      const messageId = streamingIdRef.current;
      if (!messageId) {
        return;
      }

      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? {
                ...message,
                isStreaming: false,
                content: message.content || fallbackContent || "",
              }
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
      if (hadStreamingMessage) {
        setError("Connection to Jarvis was lost.");
      }
    };

    ws.onmessage = (event) => {
      const chunk: StreamChunk = JSON.parse(event.data);

      if (chunk.type === "token" && chunk.content) {
        setMessages((prev) => {
          const id = streamingIdRef.current;
          if (!id) {
            return prev;
          }

          return prev.map((message) =>
            message.id === id
              ? { ...message, content: message.content + chunk.content }
              : message
          );
        });
        return;
      }

      if (chunk.type === "tool_start" && chunk.tool_name) {
        const toolName = chunk.tool_name;
        setActiveTools((prev) => {
          if (prev.some((tool) => tool.name === toolName)) {
            return prev;
          }

          return [...prev, { name: toolName, phase: "running" }];
        });
        return;
      }

      if (chunk.type === "tool_end" && chunk.tool_name) {
        const toolName = chunk.tool_name;
        setActiveTools((prev) => prev.filter((tool) => tool.name !== toolName));
        setLastCompletedTool(toolName);
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

  const sendMessage = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    setError(null);
    setLastCompletedTool(null);

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: text,
    };

    const assistantId = createId();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
    };

    streamingIdRef.current = assistantId;
    setIsStreaming(true);
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    wsRef.current.send(JSON.stringify({ message: text, session_id: sessionIdRef.current }));
  }, []);

  return {
    messages,
    sendMessage,
    isConnected,
    isStreaming,
    activeTools,
    lastCompletedTool,
    error,
  };
}

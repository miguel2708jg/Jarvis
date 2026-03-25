import { useState, useEffect, useRef, useCallback } from "react";
import { WS_URL } from "../api/client";
import type { ChatMessage, StreamChunk } from "../api/types";
import { v4 as uuidv4 } from "crypto"; // Expo uses crypto polyfill

export function useJarvisChat(sessionId: string = uuidv4()) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const streamingIdRef = useRef<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/chat`);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      const chunk: StreamChunk = JSON.parse(event.data);

      if (chunk.type === "token" && chunk.content) {
        setMessages((prev) => {
          const id = streamingIdRef.current;
          if (!id) return prev;
          return prev.map((m) =>
            m.id === id
              ? { ...m, content: m.content + chunk.content }
              : m
          );
        });
      } else if (chunk.type === "done") {
        setIsStreaming(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === streamingIdRef.current ? { ...m, isStreaming: false } : m
          )
        );
        streamingIdRef.current = null;
      } else if (chunk.type === "error") {
        setIsStreaming(false);
        streamingIdRef.current = null;
      }
    };

    return () => ws.close();
  }, []);

  const sendMessage = useCallback(
    (text: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      const userMsg: ChatMessage = {
        id: uuidv4(),
        role: "user",
        content: text,
      };
      const assistantId = uuidv4();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      streamingIdRef.current = assistantId;
      setIsStreaming(true);
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      wsRef.current.send(JSON.stringify({ message: text, session_id: sessionId }));
    },
    [sessionId]
  );

  return { messages, sendMessage, isConnected, isStreaming };
}

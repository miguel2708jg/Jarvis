import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";
const configuredWsUrl = process.env.NEXT_PUBLIC_WS_URL;

function resolveWsUrl(): string {
  if (configuredWsUrl && configuredWsUrl.trim()) {
    return configuredWsUrl.trim();
  }

  if (API_URL.startsWith("http")) {
    return API_URL.replace(/^http/, "ws");
  }

  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.hostname}:8000`;
  }

  return "ws://localhost:8000";
}

const WS_URL = resolveWsUrl();

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export { API_URL, WS_URL };

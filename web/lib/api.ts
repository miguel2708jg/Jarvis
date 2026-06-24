import axios from "axios";

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL;
const configuredWsUrl = process.env.NEXT_PUBLIC_WS_URL;
const configuredBackendPort = process.env.NEXT_PUBLIC_BACKEND_PORT;

function isLocalHost(hostname: string): boolean {
  return ["localhost", "127.0.0.1", "0.0.0.0", "::1"].includes(hostname.toLowerCase());
}

function resolveApiUrl(): string {
  const apiUrl = configuredApiUrl?.trim() || "/api";
  if (apiUrl.startsWith("/") || typeof window === "undefined") {
    return apiUrl;
  }

  try {
    const targetUrl = new URL(apiUrl);
    if (isLocalHost(targetUrl.hostname) && !isLocalHost(window.location.hostname)) {
      return "/api";
    }
    if (window.location.protocol === "https:" && targetUrl.protocol === "http:") {
      return "/api";
    }
  } catch {
    return apiUrl;
  }

  return apiUrl;
}

const API_URL = resolveApiUrl();

function resolveWsUrl(): string {
  if (configuredWsUrl && configuredWsUrl.trim()) {
    return configuredWsUrl.trim();
  }

  if (API_URL.startsWith("http")) {
    return API_URL.replace(/^http/, "ws");
  }

  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const backendPort = configuredBackendPort?.trim() || "8000";
    const portSuffix = backendPort ? `:${backendPort}` : "";
    return `${protocol}//${window.location.hostname}${portSuffix}`;
  }

  const backendPort = configuredBackendPort?.trim() || "8000";
  const portSuffix = backendPort ? `:${backendPort}` : "";
  return `ws://localhost${portSuffix}`;
}

const WS_URL = resolveWsUrl();

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export { API_URL, WS_URL };

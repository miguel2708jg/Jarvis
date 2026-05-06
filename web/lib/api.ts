import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";
const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ??
  (API_URL.startsWith("http") ? API_URL.replace(/^http/, "ws") : "ws://localhost:8888");

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export { API_URL, WS_URL };

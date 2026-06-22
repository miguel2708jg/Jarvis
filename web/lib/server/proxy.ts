import { getServerSession } from "next-auth";
import { authOptions, isAllowedEmail } from "@/auth";

const BACKEND_API_URL = process.env.BACKEND_API_URL ?? "http://localhost:8000";

export async function proxyRequest(request: Request, path: string[]) {
  const session = await getServerSession(authOptions);
  const email = session?.user?.email;
  if (!isAllowedEmail(email)) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }
  if (!process.env.BACKEND_INTERNAL_AUTH_TOKEN) {
    return Response.json({ detail: "Backend auth token is not configured" }, { status: 503 });
  }

  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`/${path.join("/")}${incomingUrl.search}`, BACKEND_API_URL);
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("cookie");
  headers.delete("authorization");
  headers.delete("content-length");
  headers.delete("transfer-encoding");
  headers.set("x-jarvis-internal-auth", process.env.BACKEND_INTERNAL_AUTH_TOKEN);
  headers.set("x-jarvis-user-email", email!.trim().toLowerCase());

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
    duplex: "half",
  } as RequestInit & { duplex: "half" });

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

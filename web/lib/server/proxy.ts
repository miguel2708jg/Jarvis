const BACKEND_API_URL = process.env.BACKEND_API_URL ?? "http://localhost:8888";

export async function proxyRequest(request: Request, path: string[]) {
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`/${path.join("/")}${incomingUrl.search}`, BACKEND_API_URL);
  const headers = new Headers(request.headers);
  headers.delete("host");

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

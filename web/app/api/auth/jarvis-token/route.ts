import { getServerSession } from "next-auth";
import { authOptions, isAllowedEmail } from "@/auth";
import { signJarvisToken } from "@/lib/server/jarvis-token";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function toWebSocketUrl(value?: string): string | undefined {
  if (!value?.trim()) return undefined;

  try {
    const url = new URL(value.trim());
    if (url.protocol === "https:") url.protocol = "wss:";
    else if (url.protocol === "http:") url.protocol = "ws:";
    url.pathname = url.pathname.replace(/\/+$/, "");
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/$/, "");
  } catch {
    return undefined;
  }
}

export async function GET() {
  const session = await getServerSession(authOptions);
  const email = session?.user?.email;
  if (!email || !isAllowedEmail(email)) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  return Response.json({
    token: signJarvisToken(email),
    wsUrl: toWebSocketUrl(process.env.NEXT_PUBLIC_WS_URL) ?? toWebSocketUrl(process.env.BACKEND_API_URL),
  });
}

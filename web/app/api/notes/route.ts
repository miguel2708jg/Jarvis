import { proxyRequest } from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  return proxyRequest(request, ["notes"]);
}

export async function POST(request: Request) {
  return proxyRequest(request, ["notes"]);
}

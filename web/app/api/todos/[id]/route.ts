import { proxyRequest } from "@/lib/server/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

export async function GET(request: Request, { params }: Params) {
  const { id } = await params;
  return proxyRequest(request, ["todos", id]);
}

export async function PUT(request: Request, { params }: Params) {
  const { id } = await params;
  return proxyRequest(request, ["todos", id]);
}

export async function DELETE(request: Request, { params }: Params) {
  const { id } = await params;
  return proxyRequest(request, ["todos", id]);
}

import { getServerSession } from "next-auth";
import { authOptions, isAllowedEmail } from "@/auth";
import { signJarvisToken } from "@/lib/server/jarvis-token";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const session = await getServerSession(authOptions);
  const email = session?.user?.email;
  if (!email || !isAllowedEmail(email)) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  return Response.json({ token: signJarvisToken(email) });
}

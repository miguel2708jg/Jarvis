import { withAuth } from "next-auth/middleware";
import { getAuthSecret } from "@/lib/server/auth-secret";

export default withAuth({
  secret: getAuthSecret(),
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized: ({ token }) => Boolean(token?.email),
  },
});

export const config = {
  matcher: [
    "/((?!api|login|icons|manifest.webmanifest|_next/static|_next/image|favicon.ico).*)",
  ],
};

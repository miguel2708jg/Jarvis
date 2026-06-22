import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import { getAuthSecret } from "@/lib/server/auth-secret";

export function getAllowedEmails(): Set<string> {
  return new Set(
    (process.env.AUTH_ALLOWED_EMAILS ?? "majg2708@gmail.com")
      .split(",")
      .map((email) => email.trim().toLowerCase())
      .filter(Boolean)
  );
}

export function isAllowedEmail(email?: string | null): boolean {
  return Boolean(email && getAllowedEmails().has(email.trim().toLowerCase()));
}

function getLocalDevPassword(): string | undefined {
  const password = process.env.LOCAL_DEV_AUTH_PASSWORD?.trim();
  return password ? password : undefined;
}

function getLocalDevEmail(): string {
  return Array.from(getAllowedEmails())[0] ?? "local-dev@orbit.local";
}

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.AUTH_GOOGLE_ID ?? "",
      clientSecret: process.env.AUTH_GOOGLE_SECRET ?? "",
    }),
    ...(process.env.NODE_ENV !== "production" && getLocalDevPassword()
      ? [
          CredentialsProvider({
            id: "local-dev",
            name: "Local Dev",
            credentials: {
              password: { label: "Password", type: "password" },
            },
            async authorize(credentials) {
              const configuredPassword = getLocalDevPassword();
              if (!configuredPassword || credentials?.password !== configuredPassword) {
                return null;
              }

              const email = getLocalDevEmail();
              return { id: email, email, name: "Orbit Local" };
            },
          }),
        ]
      : []),
  ],
  secret: getAuthSecret(),
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  callbacks: {
    async signIn({ user, profile }) {
      const email = user.email ?? profile?.email;
      const allowed = isAllowedEmail(email);
      if (!allowed && process.env.NODE_ENV !== "production") {
        console.warn(`Denied Google sign-in for ${email ?? "unknown email"}. Add it to AUTH_ALLOWED_EMAILS to allow access.`);
      }
      return allowed;
    },
    async jwt({ token }) {
      if (token.email && !isAllowedEmail(token.email)) {
        return {};
      }
      return token;
    },
    async session({ session, token }) {
      const email = typeof token.email === "string" ? token.email : session.user?.email;
      if (session.user && email) {
        session.user.email = email;
      }
      return session;
    },
  },
};

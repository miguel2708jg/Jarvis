const DEV_AUTH_SECRET = "orbit-local-development-secret-change-me";

export function getAuthSecret(): string | undefined {
  return process.env.NEXTAUTH_SECRET ?? process.env.AUTH_SECRET ?? (process.env.NODE_ENV === "production" ? undefined : DEV_AUTH_SECRET);
}

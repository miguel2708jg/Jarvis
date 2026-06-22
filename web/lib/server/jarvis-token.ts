import crypto from "crypto";

function base64Url(input: Buffer | string): string {
  return Buffer.from(input)
    .toString("base64")
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

export function signJarvisToken(email: string): string {
  const secret = process.env.BACKEND_AUTH_TOKEN_SECRET;
  if (!secret) {
    throw new Error("BACKEND_AUTH_TOKEN_SECRET is not configured");
  }

  const payload = base64Url(
    JSON.stringify({
      email: email.trim().toLowerCase(),
      exp: Math.floor(Date.now() / 1000) + 5 * 60,
    })
  );
  const signature = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("base64")
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
  return `${payload}.${signature}`;
}

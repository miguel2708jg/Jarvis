"use client";

import { FormEvent, Suspense, useState } from "react";
import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { ShieldCheck } from "lucide-react";

function LoginPanel() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const errorMessage =
    error === "OAuthCallback"
      ? "Google rejected this local network callback. Use local access below."
      : error
        ? "This account is not allowed to access Orbit."
        : "";

  async function handleLocalSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");
    setIsSubmitting(true);

    const result = await signIn("local-dev", {
      password,
      redirect: false,
      callbackUrl: "/",
    });

    setIsSubmitting(false);

    if (result?.error) {
      setLocalError("Invalid local password.");
      return;
    }

    window.location.href = result?.url ?? "/";
  }

  return (
    <main className="login-page">
      <div className="login-panel">
        <div className="login-mark">
          <ShieldCheck size={22} />
        </div>
        <p className="eyebrow">Orbit Access</p>
        <h1>Sign in with Google</h1>
        <p>
          Access is restricted to the owner account. Use the whitelisted Google
          account to continue.
        </p>
        {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
        <button className="dark-button login-button" onClick={() => signIn("google", { callbackUrl: "/" })}>
          Continue with Google
        </button>
        <div className="login-divider">or</div>
        <form className="local-login-form" onSubmit={handleLocalSignIn}>
          <label>
            Local password
            <input
              autoComplete="current-password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              value={password}
            />
          </label>
          {localError ? <p className="error-banner">{localError}</p> : null}
          <button className="soft-button login-button" disabled={isSubmitting || !password} type="submit">
            Continue locally
          </button>
        </form>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPanel />
    </Suspense>
  );
}

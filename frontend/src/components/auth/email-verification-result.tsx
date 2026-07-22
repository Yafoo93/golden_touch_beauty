"use client";

import { useEffect, useState } from "react";
import { ButtonLink } from "@/components/ui/button";
import { LoadingIndicator } from "@/components/ui/loading-indicator";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

type VerificationState =
  | { status: "loading" }
  | { status: "success"; email: string }
  | { status: "error"; message: string };

function apiMessage(error: ApiError) {
  if (error.details && typeof error.details === "object") {
    const messages = Object.values(error.details as Record<string, unknown>).flatMap((value) =>
      (Array.isArray(value) ? value : [value]).map(String),
    );
    if (messages.length) return messages.join(" ");
  }
  return error.message;
}

export function EmailVerificationResult({ token }: { token: string }) {
  const [state, setState] = useState<VerificationState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    async function verify() {
      try {
        await ensureCsrfCookie();
        const result = await apiFetch<{ detail: string; email: string }>("auth/verify-email/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });
        if (active) setState({ status: "success", email: result.email });
      } catch (caught) {
        if (active) {
          setState({
            status: "error",
            message: caught instanceof ApiError ? apiMessage(caught) : "The verification link could not be processed. Please try again.",
          });
        }
      }
    }
    void verify();
    return () => { active = false; };
  }, [token]);

  if (state.status === "loading") {
    return <section className="auth-success" aria-live="polite"><LoadingIndicator label="Verifying your email address..." /></section>;
  }

  if (state.status === "error") {
    return (
      <section className="auth-success" role="alert">
        <span className="auth-success__icon auth-success__icon--error" aria-hidden="true">!</span>
        <h2>Verification unsuccessful</h2>
        <p>{state.message}</p>
        <ButtonLink href="/verify-email" fullWidth>Request another verification email</ButtonLink>
        <ButtonLink href="/login" variant="outline" fullWidth>Return to sign in</ButtonLink>
      </section>
    );
  }

  return (
    <section className="auth-success" role="status">
      <span className="auth-success__icon" aria-hidden="true">✓</span>
      <h2>Email verified</h2>
      <p><strong>{state.email}</strong> has been verified successfully. Your account is ready to use.</p>
      <ButtonLink href="/login" fullWidth>Continue to sign in</ButtonLink>
    </section>
  );
}

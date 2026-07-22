"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, ButtonLink } from "@/components/ui/button";
import { LoadingIndicator } from "@/components/ui/loading-indicator";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

export function LogoutAction() {
  const router = useRouter();
  const started = useRef(false);
  const [error, setError] = useState("");
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    async function signOut() {
      try {
        await ensureCsrfCookie();
        await apiFetch<{ detail: string }>("auth/logout/", { method: "POST" });
        router.replace("/");
        router.refresh();
      } catch (caught) {
        setError(caught instanceof ApiError ? caught.message : "Sign out could not be completed. Please try again.");
      }
    }
    void signOut();
  }, [retryKey, router]);

  if (!error) {
    return <section className="auth-success" aria-live="polite"><LoadingIndicator label="Signing you out securely..." /></section>;
  }

  return (
    <section className="auth-success" role="alert">
      <span className="auth-success__icon auth-success__icon--error" aria-hidden="true">!</span>
      <h2>Sign out unsuccessful</h2>
      <p>{error}</p>
      <Button fullWidth onClick={() => { started.current = false; setError(""); setRetryKey((value) => value + 1); }}>Try again</Button>
      <ButtonLink href="/" variant="outline" fullWidth>Return home</ButtonLink>
    </section>
  );
}

"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FormField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

export function VerifyEmailForm() {
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [sent, setSent] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors([]);
    const data = new FormData(event.currentTarget);

    try {
      await ensureCsrfCookie();
      await apiFetch<{ detail: string }>("auth/resend-verification/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: String(data.get("email") ?? "").trim() }),
      });
      setSent(true);
    } catch (caught) {
      setErrors([caught instanceof ApiError ? caught.message : "A verification email could not be requested. Please try again."]);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      {sent ? (
        <section className="auth-success auth-success--compact" role="status">
          <span className="auth-success__icon auth-success__icon--mail" aria-hidden="true">✉</span>
          <h2>Check your email</h2>
          <p>If that address belongs to an active, unverified account, a verification link has been sent.</p>
        </section>
      ) : null}
      <ValidationSummary errors={errors} />
      <FormField name="email" label="Account email address" type="email" autoComplete="email" placeholder="you@example.com" required />
      <Button type="submit" size="large" fullWidth loading={submitting} loadingLabel="Sending verification...">
        {sent ? "Resend verification email" : "Send verification email"}
      </Button>
      <p className="auth-form__alternate">Already verified? <Link href="/login">Return to sign in</Link></p>
    </form>
  );
}

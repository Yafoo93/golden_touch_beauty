"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

export function ForgotPasswordForm() {
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [complete, setComplete] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors([]);
    const data = new FormData(event.currentTarget);

    try {
      await ensureCsrfCookie();
      await apiFetch<{ detail: string }>("auth/password-reset/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: String(data.get("email") ?? "").trim() }),
      });
      setComplete(true);
    } catch (caught) {
      setErrors([caught instanceof ApiError ? caught.message : "Reset instructions could not be requested. Please try again."]);
      setSubmitting(false);
    }
  }

  if (complete) {
    return (
      <section className="auth-success" role="status">
        <span className="auth-success__icon auth-success__icon--mail" aria-hidden="true">✉</span>
        <h2>Check your email</h2>
        <p>If an active Golden Touch account uses that address, password-reset instructions have been sent.</p>
        <p className="auth-success__note">For security, this message is the same whether or not the email is registered.</p>
        <ButtonLink href="/login" fullWidth>Return to sign in</ButtonLink>
      </section>
    );
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <ValidationSummary errors={errors} />
      <FormField name="email" label="Email address" type="email" autoComplete="email" placeholder="you@example.com" required />
      <Button type="submit" size="large" fullWidth loading={submitting} loadingLabel="Sending instructions...">Send reset instructions</Button>
      <p className="auth-form__alternate">Remembered your password? <Link href="/login">Return to sign in</Link></p>
    </form>
  );
}

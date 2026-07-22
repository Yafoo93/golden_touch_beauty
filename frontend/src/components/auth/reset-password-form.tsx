"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

function validationErrors(error: ApiError) {
  if (!error.details || typeof error.details !== "object") return [error.message];
  return Object.values(error.details as Record<string, unknown>).flatMap((value) =>
    (Array.isArray(value) ? value : [value]).map(String),
  );
}

export function ResetPasswordForm({ token }: { token: string }) {
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [complete, setComplete] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors([]);
    const data = new FormData(event.currentTarget);
    const password = String(data.get("password") ?? "");
    const confirmPassword = String(data.get("confirm_password") ?? "");

    if (password !== confirmPassword) {
      setErrors(["Passwords do not match."]);
      return;
    }

    setSubmitting(true);
    try {
      await ensureCsrfCookie();
      await apiFetch<{ detail: string }>("auth/password-reset/confirm/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password, confirm_password: confirmPassword }),
      });
      setComplete(true);
    } catch (caught) {
      setErrors(caught instanceof ApiError ? validationErrors(caught) : ["Your password could not be reset. Please try again."]);
      setSubmitting(false);
    }
  }

  if (complete) {
    return (
      <section className="auth-success" role="status">
        <span className="auth-success__icon" aria-hidden="true">✓</span>
        <h2>Password updated</h2>
        <p>Your password has been reset successfully. You can now sign in with your new password.</p>
        <ButtonLink href="/login" fullWidth>Sign in</ButtonLink>
      </section>
    );
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <ValidationSummary errors={errors} />
      <FormField name="password" label="New password" type="password" autoComplete="new-password" minLength={8} hint="Use a strong password that is not similar to your personal details." required />
      <FormField name="confirm_password" label="Confirm new password" type="password" autoComplete="new-password" minLength={8} required />
      <Button type="submit" size="large" fullWidth loading={submitting} loadingLabel="Updating password...">Reset password</Button>
      <p className="auth-form__alternate">Need a new link? <Link href="/forgot-password">Request another reset email</Link></p>
    </form>
  );
}

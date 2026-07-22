"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

type SignedInUser = {
  id: string;
  full_name: string;
  email: string;
  phone_number: string;
  is_staff: boolean;
  is_superuser: boolean;
};

export function LoginForm() {
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [user, setUser] = useState<SignedInUser | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors([]);
    const data = new FormData(event.currentTarget);

    try {
      await ensureCsrfCookie();
      const response = await apiFetch<{ user: SignedInUser }>("auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier: String(data.get("identifier") ?? "").trim(),
          password: String(data.get("password") ?? ""),
        }),
      });
      setUser(response.user);
    } catch (caught) {
      setErrors([caught instanceof ApiError ? caught.message : "Sign in could not be completed. Please try again."]);
      setSubmitting(false);
    }
  }

  if (user) {
    return (
      <section className="auth-success" role="status">
        <span className="auth-success__icon" aria-hidden="true">✓</span>
        <h2>Welcome back, {user.full_name}</h2>
        <p>You are signed in securely.</p>
        {user.is_superuser ? <ButtonLink href="/management/branches" fullWidth>Open management</ButtonLink> : <ButtonLink href="/book" fullWidth>Book an appointment</ButtonLink>}
        <ButtonLink href="/" variant="outline" fullWidth>Return home</ButtonLink>
        <ButtonLink href="/logout" variant="black" fullWidth>Sign out</ButtonLink>
      </section>
    );
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <ValidationSummary title="Sign in was unsuccessful:" errors={errors} />
      <FormField name="identifier" label="Email or phone number" autoComplete="username" placeholder="you@example.com or +233..." required />
      <FormField name="password" label="Password" type="password" autoComplete="current-password" required />
      <div className="auth-form__helper"><Link href="/forgot-password">Forgot your password?</Link></div>
      <Button type="submit" size="large" fullWidth loading={submitting} loadingLabel="Signing in...">Sign in</Button>
      <p className="auth-form__alternate">New to Golden Touch? <Link href="/register">Create an account</Link></p>
    </form>
  );
}

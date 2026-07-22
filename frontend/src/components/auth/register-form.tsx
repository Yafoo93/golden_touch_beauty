"use client";

import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FormField, ValidationMessage, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

type RegisteredUser = { id: string; full_name: string; email: string; phone_number: string };
type RegistrationDraft = {
  full_name: string;
  email: string;
  phone_number: string;
  terms_privacy_agreed: boolean;
  marketing_consent: boolean;
};

const EMPTY_DRAFT: RegistrationDraft = {
  full_name: "",
  email: "",
  phone_number: "",
  terms_privacy_agreed: false,
  marketing_consent: false,
};
const DRAFT_KEY = "golden-touch-registration-draft";

function apiValidation(error: ApiError) {
  if (!error.details || typeof error.details !== "object") return { summary: [error.message], fields: {} };
  const fields: Record<string, string> = {};
  for (const [field, value] of Object.entries(error.details as Record<string, unknown>)) {
    const messages = Array.isArray(value) ? value : [value];
    fields[field] = messages.map(String).join(" ");
  }
  return { summary: Object.values(fields), fields };
}

export function RegisterForm() {
  const [submitting, setSubmitting] = useState(false);
  const [summaryErrors, setSummaryErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [draft, setDraft] = useState<RegistrationDraft>(EMPTY_DRAFT);
  const [draftLoaded, setDraftLoaded] = useState(false);

  useEffect(() => {
    let restoredDraft = EMPTY_DRAFT;
    try {
      const saved = sessionStorage.getItem(DRAFT_KEY);
      if (saved) restoredDraft = { ...EMPTY_DRAFT, ...JSON.parse(saved) };
    } catch {
      // Registration remains usable when browser storage is unavailable.
    }
    const restoreTimer = window.setTimeout(() => {
      setDraft(restoredDraft);
      setDraftLoaded(true);
    }, 0);
    return () => window.clearTimeout(restoreTimer);
  }, []);

  useEffect(() => {
    if (!draftLoaded) return;
    try {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    } catch {
      // Draft persistence is a convenience, not a registration requirement.
    }
  }, [draft, draftLoaded]);

  function updateText(event: ChangeEvent<HTMLInputElement>) {
    setDraft((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  function updateConsent(event: ChangeEvent<HTMLInputElement>) {
    setDraft((current) => ({ ...current, [event.target.name]: event.target.checked }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setSummaryErrors([]);
    setFieldErrors({});
    const form = new FormData(event.currentTarget);
    const value = (name: string) => String(form.get(name) ?? "").trim();

    if (value("password") !== value("confirm_password")) {
      setFieldErrors({ confirm_password: "Passwords do not match." });
      setSummaryErrors(["Passwords do not match."]);
      setSubmitting(false);
      return;
    }

    try {
      await ensureCsrfCookie();
      await apiFetch<{ user: RegisteredUser }>("auth/register/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: value("full_name"), email: value("email"), phone_number: value("phone_number"),
          password: value("password"), confirm_password: value("confirm_password"),
          terms_privacy_agreed: form.get("terms_privacy_agreed") === "on",
          marketing_consent: form.get("marketing_consent") === "on",
        }),
      });
      try {
        sessionStorage.removeItem(DRAFT_KEY);
      } catch {
        // The account was created even if browser storage cannot be cleared.
      }
      window.location.replace("/register/success");
    } catch (caught) {
      if (caught instanceof ApiError) {
        const validation = apiValidation(caught);
        setSummaryErrors(validation.summary);
        setFieldErrors(validation.fields);
      } else {
        setSummaryErrors(["Your account could not be created. Please try again."]);
      }
      setSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <ValidationSummary errors={summaryErrors} />
      <FormField name="full_name" label="Full name" autoComplete="name" maxLength={200} value={draft.full_name} onChange={updateText} error={fieldErrors.full_name} required />
      <FormField name="email" label="Email address" type="email" autoComplete="email" maxLength={254} value={draft.email} onChange={updateText} error={fieldErrors.email} required />
      <FormField name="phone_number" label="Phone number" type="tel" autoComplete="tel" placeholder="+233 24 123 4567" maxLength={20} value={draft.phone_number} onChange={updateText} hint="Ghana local numbers are converted to +233 format." error={fieldErrors.phone_number} required />
      <div className="auth-form__passwords">
        <FormField name="password" label="Password" type="password" autoComplete="new-password" minLength={8} hint="Use a strong password that is not similar to your personal details." error={fieldErrors.password} required />
        <FormField name="confirm_password" label="Confirm password" type="password" autoComplete="new-password" minLength={8} error={fieldErrors.confirm_password} required />
      </div>

      <div className="auth-form__consents">
        <label className="consent-field">
          <input type="checkbox" name="terms_privacy_agreed" checked={draft.terms_privacy_agreed} onChange={updateConsent} required />
          <span>I agree to the <Link href="/policies#terms" target="_blank">Terms and Conditions</Link> and <Link href="/policies#privacy" target="_blank">Privacy Policy</Link>. <strong aria-hidden="true">*</strong></span>
        </label>
        {fieldErrors.terms_privacy_agreed ? <ValidationMessage>{fieldErrors.terms_privacy_agreed}</ValidationMessage> : null}
        <label className="consent-field">
          <input type="checkbox" name="marketing_consent" checked={draft.marketing_consent} onChange={updateConsent} />
          <span>Send me optional Golden Touch offers and beauty updates. I can withdraw this consent later.</span>
        </label>
      </div>

      <Button type="submit" size="large" fullWidth loading={submitting} loadingLabel="Creating your account...">Create account</Button>
      <p className="auth-form__alternate">Already have an account? <Link href="/login">Sign in</Link></p>
    </form>
  );
}

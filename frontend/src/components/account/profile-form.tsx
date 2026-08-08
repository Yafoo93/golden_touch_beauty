"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { FormField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";

type Profile = {
  full_name: string;
  email: string;
  phone_number: string;
};

function validationDetails(error: ApiError) {
  if (!error.details || typeof error.details !== "object") {
    return { fields: {}, summary: [error.message] };
  }
  const fields: Record<string, string> = {};
  for (const [field, value] of Object.entries(
    error.details as Record<string, unknown>,
  )) {
    fields[field] = (Array.isArray(value) ? value : [value])
      .map(String)
      .join(" ");
  }
  return { fields, summary: Object.values(fields) };
}

export function ProfileForm({ profile }: { profile: Profile }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [summaryErrors, setSummaryErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    setSummaryErrors([]);
    setFieldErrors({});
    const form = new FormData(event.currentTarget);

    try {
      await ensureCsrfCookie();
      await apiFetch<{ user: Profile }>("auth/me/", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: String(form.get("full_name") ?? "").trim(),
          email: String(form.get("email") ?? "").trim(),
          phone_number: String(form.get("phone_number") ?? "").trim(),
        }),
      });
      setMessage(
        "Your profile has been updated. A changed email address must be verified again.",
      );
      router.refresh();
    } catch (caught) {
      if (caught instanceof ApiError) {
        const validation = validationDetails(caught);
        setFieldErrors(validation.fields);
        setSummaryErrors(validation.summary);
      } else {
        setSummaryErrors([
          "Your profile could not be updated. Please try again.",
        ]);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="account-profile" aria-labelledby="account-profile-title">
      <header>
        <div>
          <p>Personal information</p>
          <h2 id="account-profile-title">Your profile</h2>
        </div>
      </header>
      <form onSubmit={submit}>
        <ValidationSummary errors={summaryErrors} />
        {message ? (
          <p className="account-profile__success" role="status">
            {message}
          </p>
        ) : null}
        <div className="account-profile__fields">
          <FormField
            name="full_name"
            label="Full name"
            defaultValue={profile.full_name}
            autoComplete="name"
            maxLength={200}
            error={fieldErrors.full_name}
            required
          />
          <FormField
            name="email"
            label="Email address"
            type="email"
            defaultValue={profile.email}
            autoComplete="email"
            maxLength={254}
            hint="Changing this address requires email verification again."
            error={fieldErrors.email}
            required
          />
          <FormField
            name="phone_number"
            label="Phone number"
            type="tel"
            defaultValue={profile.phone_number}
            autoComplete="tel"
            maxLength={20}
            hint="Ghana local numbers are converted to +233 format."
            error={fieldErrors.phone_number}
            required
          />
        </div>
        <Button
          type="submit"
          loading={submitting}
          loadingLabel="Saving profile..."
        >
          Save profile
        </Button>
      </form>
    </section>
  );
}

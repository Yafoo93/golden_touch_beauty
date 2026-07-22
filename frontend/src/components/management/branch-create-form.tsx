"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, TextAreaField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import type { ManagementBranch } from "@/lib/management-branches";

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const;

function errorMessages(error: ApiError) {
  if (!error.details || typeof error.details !== "object") return [error.message];
  const messages = Object.entries(error.details as Record<string, unknown>).flatMap(([field, value]) => {
    const values = Array.isArray(value) ? value : [value];
    return values.map((message) => `${field.replaceAll("_", " ")}: ${String(message)}`);
  });
  return messages.length ? messages : [error.message];
}

export function BranchCreateForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors([]);

    const data = new FormData(event.currentTarget);
    const optional = (name: string) => String(data.get(name) ?? "").trim();
    const payload = {
      name: optional("name"),
      code: optional("code").toUpperCase(),
      address: optional("address"),
      telephone_number: optional("telephone_number"),
      secondary_telephone_number: optional("secondary_telephone_number"),
      whatsapp_number: optional("whatsapp_number"),
      secondary_whatsapp_number: optional("secondary_whatsapp_number"),
      email: optional("email"),
      google_maps_url: optional("google_maps_url"),
      opening_days: data.getAll("opening_days"),
      opening_time: optional("opening_time"),
      closing_time: optional("closing_time"),
      is_active: data.get("is_active") === "on",
    };

    try {
      await apiFetch<ManagementBranch>("branches/management/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      router.push("/management/branches");
      router.refresh();
    } catch (caught) {
      setErrors(caught instanceof ApiError ? errorMessages(caught) : ["The branch could not be created. Please try again."]);
      setSubmitting(false);
    }
  }

  return (
    <form className="management-form" onSubmit={submit}>
      <ValidationSummary errors={errors} />

      <section className="management-form__section">
        <div className="management-form__section-heading">
          <h2>Branch identity</h2>
          <p>The branch code identifies this location throughout bookings, stock, payments, POS sales, and reports.</p>
        </div>
        <div className="management-form__grid">
          <FormField name="name" label="Branch name" placeholder="Example: East Legon" maxLength={150} required />
          <FormField name="code" label="Branch code" placeholder="Example: EAST-LEGON" maxLength={30} pattern="[A-Za-z0-9_-]+" hint="Letters, numbers, hyphens, and underscores only." required />
          <div className="management-form__wide"><TextAreaField name="address" label="Address" rows={3} required /></div>
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Contact details</h2><p>Email and secondary numbers are optional and remain hidden publicly when empty.</p></div>
        <div className="management-form__grid">
          <FormField name="telephone_number" label="Primary telephone" type="tel" placeholder="+233..." maxLength={30} required />
          <FormField name="secondary_telephone_number" label="Secondary telephone" type="tel" placeholder="+233..." maxLength={30} />
          <FormField name="whatsapp_number" label="Primary WhatsApp" type="tel" placeholder="+233..." maxLength={30} />
          <FormField name="secondary_whatsapp_number" label="Secondary WhatsApp" type="tel" placeholder="+233..." maxLength={30} />
          <FormField name="email" label="Branch email" type="email" placeholder="branch@example.com" />
          <FormField name="google_maps_url" label="Google Maps URL" type="url" placeholder="https://maps.google.com/..." />
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Operating schedule</h2><p>Select every day this branch normally opens.</p></div>
        <fieldset className="management-form__days">
          <legend>Opening days *</legend>
          {DAYS.map((day) => <label key={day}><input type="checkbox" name="opening_days" value={day} defaultChecked={day !== "sunday"} /><span>{day.slice(0, 3)}</span></label>)}
        </fieldset>
        <div className="management-form__grid">
          <FormField name="opening_time" label="Opening time" type="time" defaultValue="07:30" required />
          <FormField name="closing_time" label="Closing time" type="time" defaultValue="17:00" required />
        </div>
        <label className="management-form__toggle"><input type="checkbox" name="is_active" defaultChecked /><span><strong>Active branch</strong><small>Active branches can appear publicly and be used for operations.</small></span></label>
      </section>

      <div className="management-form__actions">
        <ButtonLink href="/management/branches" variant="outline">Cancel</ButtonLink>
        <Button type="submit" loading={submitting} loadingLabel="Creating branch...">Create branch</Button>
      </div>
    </form>
  );
}

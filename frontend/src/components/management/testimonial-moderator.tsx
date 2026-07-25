"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { FormField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import type {
  ManagementTestimonial,
  TestimonialStatus,
} from "@/lib/testimonials";

function errorMessages(error: unknown) {
  if (!(error instanceof ApiError)) {
    return ["The testimonial could not be updated. Please try again."];
  }
  if (!error.details || typeof error.details !== "object") return [error.message];
  const messages = Object.entries(
    error.details as Record<string, unknown>,
  ).flatMap(([field, value]) =>
    (Array.isArray(value) ? value : [value]).map(
      (message) => `${field.replaceAll("_", " ")}: ${String(message)}`,
    ),
  );
  return messages.length ? messages : [error.message];
}

function statusClass(status: TestimonialStatus) {
  if (status === "approved") return "status-badge status-badge--active";
  if (status === "rejected") return "status-badge status-badge--inactive";
  return "status-badge testimonial-moderator__pending";
}

function ModerationCard({ initial }: { initial: ManagementTestimonial }) {
  const [testimonial, setTestimonial] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [success, setSuccess] = useState("");

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setErrors([]);
    setSuccess("");
    const values = new FormData(event.currentTarget);
    try {
      const updated = await apiFetch<ManagementTestimonial>(
        `testimonials/management/${testimonial.id}/`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            consent_confirmed: values.get("consent_confirmed") === "on",
            moderation_status: String(values.get("moderation_status")),
            is_visible: values.get("is_visible") === "on",
            is_featured: values.get("is_featured") === "on",
            display_order: Number(values.get("display_order")),
          }),
        },
      );
      setTestimonial(updated);
      setSuccess(
        updated.is_visible
          ? "Approved testimonial is visible on the public page."
          : "Moderation changes saved. This testimonial remains hidden.",
      );
    } catch (error) {
      setErrors(errorMessages(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="testimonial-moderator__card" onSubmit={save}>
      <header>
        <div>
          <span className="testimonial-moderator__source">{testimonial.source_type_label}</span>
          <h2>{testimonial.client_name}</h2>
          <p>{testimonial.service_context || "No service context supplied"}</p>
        </div>
        <span className={statusClass(testimonial.moderation_status)}>
          {testimonial.moderation_status}
        </span>
      </header>
      <blockquote>“{testimonial.quote}”</blockquote>
      {testimonial.client_attribution ? (
        <p className="testimonial-moderator__attribution">{testimonial.client_attribution}</p>
      ) : null}
      {testimonial.source_type === "development_sample" ? (
        <p className="testimonial-moderator__warning">
          This is invented development copy, not a customer review. Keep it
          hidden and replace it with an accurately recorded, consented
          testimonial before launch.
        </p>
      ) : null}
      <div className="testimonial-moderator__controls">
        <div className="form-field">
          <label className="form-field__label" htmlFor={`status-${testimonial.id}`}>Moderation decision</label>
          <select className="form-field__control" id={`status-${testimonial.id}`} name="moderation_status" defaultValue={testimonial.moderation_status}>
            <option value="pending">Pending review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
        <FormField name="display_order" label="Display order" type="number" min={0} max={32767} defaultValue={testimonial.display_order} required />
      </div>
      <div className="testimonial-moderator__checks">
        <label className="management-form__toggle">
          <input type="checkbox" name="consent_confirmed" defaultChecked={testimonial.consent_confirmed} />
          <span><strong>Consent confirmed</strong><small>Required before approval or publication.</small></span>
        </label>
        <label className="management-form__toggle">
          <input type="checkbox" name="is_visible" defaultChecked={testimonial.is_visible} />
          <span><strong>Visible publicly</strong><small>Only approved, consented testimonials can be shown.</small></span>
        </label>
        <label className="management-form__toggle">
          <input type="checkbox" name="is_featured" defaultChecked={testimonial.is_featured} />
          <span><strong>Featured</strong><small>Marks the testimonial for prominent future placements.</small></span>
        </label>
      </div>
      <ValidationSummary errors={errors} />
      {success ? <p className="content-editor__success" role="status">{success}</p> : null}
      {testimonial.reviewed_by && testimonial.reviewed_at ? (
        <p className="content-editor__audit">
          Last reviewed by {testimonial.reviewed_by.full_name} on{" "}
          {new Intl.DateTimeFormat("en-GH", {
            dateStyle: "medium",
            timeStyle: "short",
          }).format(new Date(testimonial.reviewed_at))}
        </p>
      ) : null}
      <div className="testimonial-moderator__actions">
        <Button type="submit" loading={saving} loadingLabel="Saving review...">Save moderation</Button>
      </div>
    </form>
  );
}

export function TestimonialModerator({
  testimonials,
}: {
  testimonials: ManagementTestimonial[];
}) {
  if (!testimonials.length) {
    return <p className="testimonial-moderator__empty">There are no testimonials awaiting management.</p>;
  }
  return (
    <div className="testimonial-moderator">
      {testimonials.map((testimonial) => (
        <ModerationCard initial={testimonial} key={testimonial.id} />
      ))}
    </div>
  );
}

"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, TextAreaField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import type { BranchManagerOption, ManagementBranch } from "@/lib/management-branches";

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const;

function errorMessages(error: ApiError) {
  if (!error.details || typeof error.details !== "object") return [error.message];
  const messages = Object.entries(error.details as Record<string, unknown>).flatMap(([field, value]) =>
    (Array.isArray(value) ? value : [value]).map((message) => `${field.replaceAll("_", " ")}: ${String(message)}`),
  );
  return messages.length ? messages : [error.message];
}

export function BranchEditForm({ branch, managers }: { branch: ManagementBranch; managers: BranchManagerOption[] }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors([]);
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "").trim();
    const managerId = text("assigned_manager_id");

    try {
      await apiFetch(`branches/management/${branch.id}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: text("name"), code: text("code").toUpperCase(), address: text("address"),
          telephone_number: text("telephone_number"), secondary_telephone_number: text("secondary_telephone_number"),
          whatsapp_number: text("whatsapp_number"), secondary_whatsapp_number: text("secondary_whatsapp_number"),
          email: text("email"), google_maps_url: text("google_maps_url"), opening_days: data.getAll("opening_days"),
          opening_time: text("opening_time"), closing_time: text("closing_time"),
          assigned_manager_id: managerId || null, is_active: data.get("is_active") === "on",
        }),
      });
      router.push("/management/branches");
      router.refresh();
    } catch (caught) {
      setErrors(caught instanceof ApiError ? errorMessages(caught) : ["The branch could not be updated. Please try again."]);
      setSubmitting(false);
    }
  }

  return (
    <form className="management-form" onSubmit={submit}>
      <ValidationSummary errors={errors} />
      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Branch identity</h2><p>The code is used to attribute operational and financial records to this branch.</p></div>
        <div className="management-form__grid">
          <FormField name="name" label="Branch name" defaultValue={branch.name} maxLength={150} required />
          <FormField name="code" label="Branch code" defaultValue={branch.code} maxLength={30} pattern="[A-Za-z0-9_-]+" required />
          <div className="management-form__wide"><TextAreaField name="address" label="Address" defaultValue={branch.address} rows={3} required /></div>
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Contacts and map</h2><p>Empty optional fields are not displayed on the public contact page.</p></div>
        <div className="management-form__grid">
          <FormField name="telephone_number" label="Primary telephone" type="tel" defaultValue={branch.telephone_number} maxLength={30} required />
          <FormField name="secondary_telephone_number" label="Secondary telephone" type="tel" defaultValue={branch.secondary_telephone_number} maxLength={30} />
          <FormField name="whatsapp_number" label="Primary WhatsApp" type="tel" defaultValue={branch.whatsapp_number} maxLength={30} />
          <FormField name="secondary_whatsapp_number" label="Secondary WhatsApp" type="tel" defaultValue={branch.secondary_whatsapp_number} maxLength={30} />
          <FormField name="email" label="Branch email" type="email" defaultValue={branch.email} />
          <FormField name="google_maps_url" label="Google Maps URL" type="url" defaultValue={branch.google_maps_url} />
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Hours and management</h2><p>Changing active status controls public visibility and future operational selection.</p></div>
        <fieldset className="management-form__days">
          <legend>Opening days *</legend>
          {DAYS.map((day) => <label key={day}><input type="checkbox" name="opening_days" value={day} defaultChecked={branch.opening_days.includes(day)} /><span>{day.slice(0, 3)}</span></label>)}
        </fieldset>
        <div className="management-form__grid">
          <FormField name="opening_time" label="Opening time" type="time" defaultValue={branch.opening_time.slice(0, 5)} required />
          <FormField name="closing_time" label="Closing time" type="time" defaultValue={branch.closing_time.slice(0, 5)} required />
          <div className="form-field">
            <label className="form-field__label" htmlFor="assigned_manager_id">Assigned manager</label>
            <select className="form-field__control" id="assigned_manager_id" name="assigned_manager_id" defaultValue={branch.assigned_manager?.id ?? ""}>
              <option value="">Not assigned</option>
              {managers.map((manager) => <option value={manager.id} key={manager.id}>{manager.full_name} — {manager.email}</option>)}
            </select>
            <p className="form-field__hint">Only active staff accounts can manage a branch.</p>
          </div>
        </div>
        <label className="management-form__toggle"><input type="checkbox" name="is_active" defaultChecked={branch.is_active} /><span><strong>Active branch</strong><small>Inactive branches remain in management but are hidden from customer branch choices.</small></span></label>
      </section>

      <div className="management-form__actions">
        <ButtonLink href="/management/branches" variant="outline">Cancel</ButtonLink>
        <Button type="submit" loading={submitting} loadingLabel="Saving changes...">Save changes</Button>
      </div>
    </form>
  );
}

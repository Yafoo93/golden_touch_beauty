"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, TextAreaField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import { ServicePriceOptionsEditor } from "./service-price-options-editor";

export type ServiceCategoryOption = { id: string; name: string };
export type ServiceBranchOption = { id: string; code: string; name: string };

function messagesFrom(error: unknown) {
  if (!(error instanceof ApiError)) return ["The service could not be created. Please try again."];
  if (!error.details || typeof error.details !== "object") return [error.message];
  return Object.entries(error.details as Record<string, unknown>).flatMap(([field, value]) =>
    (Array.isArray(value) ? value : [value]).map((message) => `${field.replaceAll("_", " ")}: ${String(message)}`),
  );
}

const BOOLEAN_FIELDS = ["is_clinic_service", "is_home_service", "requires_full_payment", "allows_pay_at_clinic", "is_consultation", "is_featured", "result_images_approved"] as const;

export function ServiceCreateForm({ categories, branches }: { categories: ServiceCategoryOption[]; branches: ServiceBranchOption[] }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors([]);
    const body = new FormData(event.currentTarget);
    BOOLEAN_FIELDS.forEach((field) => body.set(field, body.get(field) === "on" ? "true" : "false"));
    if (!body.get("maximum_price")) body.delete("maximum_price");
    try {
      await apiFetch<{ id: string }>("services/management/", { method: "POST", body });
      router.push("/management/services");
      router.refresh();
    } catch (error) {
      setErrors(messagesFrom(error));
      setSubmitting(false);
    }
  }

  return (
    <form className="management-form" onSubmit={submit}>
      <ValidationSummary errors={errors} />
      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Service identity</h2><p>The public URL slug is generated automatically from the service name.</p></div>
        <div className="management-form__grid">
          <FormField name="name" label="Service name" maxLength={180} required />
          <div className="form-field"><label className="form-field__label" htmlFor="service-category">Category *</label><select className="form-field__control" id="service-category" name="category_id" defaultValue="" required><option value="" disabled>Select a category</option>{categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select></div>
          <div className="management-form__wide"><FormField name="short_description" label="Short description" maxLength={300} hint="Used on service cards and search results." required /></div>
          <div className="management-form__wide"><TextAreaField name="description" label="Full description" rows={7} hint="Explain what the service includes and what clients should expect." required /></div>
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Pricing and duration</h2><p>Choose the pricing model customers should see. Placeholder values can be revised later.</p></div>
        <div className="management-form__grid">
          <div className="form-field"><label className="form-field__label" htmlFor="service-price-type">Price type *</label><select className="form-field__control" id="service-price-type" name="price_type" defaultValue="starting_from" required><option value="fixed">Fixed price</option><option value="starting_from">Starting from</option><option value="range">Price range</option><option value="options">Price options</option><option value="quotation">Contact for price</option></select></div>
          <FormField name="price" label="Price / starting price (GHS)" type="number" min={0} step="0.01" required />
          <FormField name="maximum_price" label="Maximum price (GHS)" type="number" min={0} step="0.01" hint="Required only for Price range." />
          <FormField name="duration_minutes" label="Duration in minutes" type="number" min={1} max={1440} defaultValue={60} required />
          <div className="management-form__wide"><TextAreaField name="pricing_notes" label="Pricing notes" rows={3} maxLength={300} hint="Required for price options and manual quotations." /></div>
          <ServicePriceOptionsEditor />
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Image and branches</h2><p>Select where this service is initially available.</p></div>
        <FormField name="image" label="Service image" type="file" accept="image/jpeg,image/png,image/webp" hint="JPEG, PNG, or WebP up to 8 MB." required />
        <div className="management-form__grid">
          <FormField name="before_image" label="Before image" type="file" accept="image/jpeg,image/png,image/webp" hint="Optional; upload only with explicit client consent." />
          <FormField name="after_image" label="After image" type="file" accept="image/jpeg,image/png,image/webp" hint="Must be supplied together with the before image." />
          <FormField name="result_photo_customer_email" label="Customer account email (optional)" type="email" maxLength={254} hint="Optional. It may be used to link the result images to an existing customer account." />
        </div>
        <label className="management-form__toggle"><input type="checkbox" name="result_images_approved" /><span><strong>Approve pair for website</strong><small>Publishes the complete before-and-after pair on the service details page.</small></span></label>
        <fieldset className="service-create-form__branches"><legend>Available branches *</legend>{branches.map((branch) => <label key={branch.id}><input type="checkbox" name="branch_ids" value={branch.id} /><span><strong>{branch.name}</strong><small>{branch.code}</small></span></label>)}</fieldset>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Booking and publication</h2><p>Publish only after content, pricing, and branch availability have been reviewed.</p></div>
        <div className="service-create-form__toggles">
          <label className="management-form__toggle"><input type="checkbox" name="is_clinic_service" defaultChecked /><span><strong>Clinic service</strong><small>Delivered at a branch.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="is_home_service" /><span><strong>Home service</strong><small>May be delivered at the customer’s location.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="requires_full_payment" defaultChecked /><span><strong>Full payment required</strong><small>Required to secure booking.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="allows_pay_at_clinic" defaultChecked /><span><strong>Allow payment at clinic</strong><small>Payment may be completed at the branch.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="is_consultation" /><span><strong>Consultation</strong><small>This record represents a consultation.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="is_featured" /><span><strong>Featured service</strong><small>Eligible for homepage placement.</small></span></label>
          <div className="form-field"><label className="form-field__label" htmlFor="service-publication-state">Publication state *</label><select className="form-field__control" id="service-publication-state" name="publication_state" defaultValue="draft" required><option value="draft">Draft — active but hidden from customers</option><option value="published">Published — visible to customers</option><option value="inactive">Inactive — unavailable for public and operational use</option></select></div>
        </div>
      </section>
      <div className="management-form__actions"><ButtonLink href="/management/services" variant="outline">Cancel</ButtonLink><Button type="submit" loading={submitting} loadingLabel="Creating service...">Create service</Button></div>
    </form>
  );
}

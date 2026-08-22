"use client";

import Image from "next/image";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, TextAreaField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import type { ManagementServiceDetail } from "@/lib/management-services";
import type { ServiceBranchOption, ServiceCategoryOption } from "./service-create-form";
import { ServicePriceOptionsEditor } from "./service-price-options-editor";

const BOOLEANS = ["is_clinic_service", "is_home_service", "requires_full_payment", "allows_pay_at_clinic", "is_consultation", "is_featured", "result_images_approved"] as const;
function errorsFrom(error: unknown) {
  if (!(error instanceof ApiError)) return ["The service could not be updated."];
  if (!error.details || typeof error.details !== "object") return [error.message];
  return Object.entries(error.details as Record<string, unknown>).flatMap(([field, value]) => (Array.isArray(value) ? value : [value]).map((message) => `${field.replaceAll("_", " ")}: ${String(message)}`));
}

export function ServiceEditForm({ service, categories, branches }: { service: ManagementServiceDetail; categories: ServiceCategoryOption[]; branches: ServiceBranchOption[] }) {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setErrors([]);
    const body = new FormData(event.currentTarget);
    BOOLEANS.forEach((field) => body.set(field, body.get(field) === "on" ? "true" : "false"));
    if (!body.get("maximum_price")) body.delete("maximum_price");
    const image = body.get("image");
    if (!(image instanceof File) || image.size === 0) body.delete("image");
    for (const field of ["before_image", "after_image"]) {
      const file = body.get(field);
      if (!(file instanceof File) || file.size === 0) body.delete(field);
    }
    try {
      await apiFetch(`services/management/${service.id}/`, { method: "PATCH", body });
      router.push("/management/services");
      router.refresh();
    } catch (error) {
      setErrors(errorsFrom(error));
      setSaving(false);
    }
  }
  return (
    <form className="management-form" onSubmit={submit}>
      <ValidationSummary errors={errors} />
      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Service details</h2><p>The stable public URL remains /services/{service.slug} even if the name changes.</p></div>
        <div className="management-form__grid">
          <FormField name="name" label="Service name" defaultValue={service.name} maxLength={180} required />
          <div className="form-field"><label className="form-field__label" htmlFor="edit-service-category">Category *</label><select className="form-field__control" id="edit-service-category" name="category_id" defaultValue={service.category_id} required>{categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select></div>
          <div className="management-form__wide"><FormField name="short_description" label="Short description" defaultValue={service.short_description} maxLength={300} required /></div>
          <div className="management-form__wide"><TextAreaField name="description" label="Full description" defaultValue={service.description} rows={7} required /></div>
        </div>
      </section>
      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Pricing and duration</h2><p>Range pricing requires a maximum; options and quotations require explanatory notes.</p></div>
        <div className="management-form__grid">
          <div className="form-field"><label className="form-field__label" htmlFor="edit-price-type">Price type *</label><select className="form-field__control" id="edit-price-type" name="price_type" defaultValue={service.price_type}><option value="fixed">Fixed price</option><option value="starting_from">Starting from</option><option value="range">Price range</option><option value="options">Price options</option><option value="quotation">Manual quotation</option></select></div>
          <FormField name="price" label="Price / starting price (GHS)" type="number" min={0} step="0.01" defaultValue={service.price} required />
          <FormField name="maximum_price" label="Maximum price (GHS)" type="number" min={0} step="0.01" defaultValue={service.maximum_price ?? ""} />
          <FormField name="duration_minutes" label="Duration in minutes" type="number" min={1} max={1440} defaultValue={service.duration_minutes} required />
          <div className="management-form__wide"><TextAreaField name="pricing_notes" label="Pricing notes" defaultValue={service.pricing_notes} rows={3} maxLength={300} /></div>
          <ServicePriceOptionsEditor initialOptions={service.price_options} />
        </div>
      </section>
      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Image and branch availability</h2><p>Leave the file empty to keep the current image.</p></div>
        <div className="service-edit-form__image"><Image src={service.image_path || "/images/hero1.jpeg"} alt="" fill sizes="20rem" /></div>
        <FormField name="image" label="Replace service image" type="file" accept="image/jpeg,image/png,image/webp" hint="Optional. JPEG, PNG, or WebP up to 8 MB." />
        <div className="management-form__grid">
          <FormField name="before_image" label="Replace before image" type="file" accept="image/jpeg,image/png,image/webp" />
          <FormField name="after_image" label="Replace after image" type="file" accept="image/jpeg,image/png,image/webp" />
          <FormField name="result_photo_customer_email" label="Customer account email" type="email" defaultValue={service.result_photo_customer_email} maxLength={254} hint="Publication follows this customer's live photograph-consent preference." />
        </div>
        <label className="management-form__toggle"><input type="checkbox" name="result_images_approved" defaultChecked={service.result_images_approved} /><span><strong>Approved for website</strong><small>Only approved pairs are returned by the public API.</small></span></label>
        <fieldset className="service-create-form__branches"><legend>Available branches *</legend>{branches.map((branch) => <label key={branch.id}><input type="checkbox" name="branch_ids" value={branch.id} defaultChecked={service.branch_ids.includes(branch.id)} /><span><strong>{branch.name}</strong><small>{branch.code}</small></span></label>)}</fieldset>
      </section>
      <section className="management-form__section">
        <div className="management-form__section-heading"><h2>Booking eligibility and publication</h2><p>Inactive or unpublished services are removed from customer booking choices.</p></div>
        <div className="service-create-form__toggles">
          <label className="management-form__toggle"><input type="checkbox" name="is_clinic_service" defaultChecked={service.is_clinic_service} /><span><strong>Clinic service</strong><small>Delivered at a branch.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="is_home_service" defaultChecked={service.is_home_service} /><span><strong>Home service</strong><small>May be delivered at the customer’s location.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="requires_full_payment" defaultChecked={service.requires_full_payment} /><span><strong>Full payment required</strong><small>Required to secure booking.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="allows_pay_at_clinic" defaultChecked={service.allows_pay_at_clinic} /><span><strong>Allow payment at clinic</strong><small>Payment may be completed at the branch.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="is_consultation" defaultChecked={service.is_consultation} /><span><strong>Consultation</strong><small>This service is a consultation.</small></span></label>
          <label className="management-form__toggle"><input type="checkbox" name="is_featured" defaultChecked={service.is_featured} /><span><strong>Featured</strong><small>Eligible for homepage placement.</small></span></label>
          <div className="form-field"><label className="form-field__label" htmlFor="edit-publication-state">Publication state *</label><select className="form-field__control" id="edit-publication-state" name="publication_state" defaultValue={service.publication_state} required><option value="draft">Draft — active but hidden from customers</option><option value="published">Published — visible to customers</option><option value="inactive">Inactive — unavailable for public and operational use</option></select></div>
        </div>
      </section>
      <div className="management-form__actions"><ButtonLink href="/management/services" variant="outline">Cancel</ButtonLink><Button type="submit" loading={saving} loadingLabel="Saving changes...">Save changes</Button></div>
    </form>
  );
}

"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { FormField, TextAreaField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";

export type ManagementServiceCategory = {
  id: string;
  name: string;
  slug: string;
  description: string;
  display_order: number;
  is_active: boolean;
  service_count: number;
  created_at: string;
  updated_at: string;
};

function errorMessages(error: unknown) {
  if (!(error instanceof ApiError)) return ["The category request could not be completed."];
  if (!error.details || typeof error.details !== "object") return [error.message];
  return Object.entries(error.details as Record<string, unknown>).flatMap(([field, value]) => (Array.isArray(value) ? value : [value]).map((message) => `${field.replaceAll("_", " ")}: ${String(message)}`));
}

function CategoryEditor({ initial, onUpdated, onDeleted }: { initial: ManagementServiceCategory; onUpdated: (category: ManagementServiceCategory) => void; onDeleted: (id: string) => void }) {
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [success, setSuccess] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true); setErrors([]); setSuccess("");
    const data = new FormData(event.currentTarget);
    try {
      const updated = await apiFetch<ManagementServiceCategory>(`services/management/service-categories/${initial.id}/`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: String(data.get("name")), description: String(data.get("description")), display_order: Number(data.get("display_order")), is_active: data.get("is_active") === "on" }),
      });
      onUpdated(updated); setSuccess("Category saved.");
    } catch (error) { setErrors(errorMessages(error)); } finally { setSaving(false); }
  }
  async function remove() {
    if (!window.confirm(`Delete the empty category “${initial.name}”?`)) return;
    setDeleting(true); setErrors([]);
    try {
      await apiFetch(`services/management/service-categories/${initial.id}/`, { method: "DELETE" });
      onDeleted(initial.id);
    } catch (error) { setErrors(errorMessages(error)); setDeleting(false); }
  }
  return (
    <form className="service-category-card" onSubmit={save}>
      <header><div><span>/{initial.slug}</span><strong>{initial.service_count} {initial.service_count === 1 ? "service" : "services"}</strong></div><span className={`status-badge status-badge--${initial.is_active ? "active" : "inactive"}`}>{initial.is_active ? "Active" : "Inactive"}</span></header>
      <div className="management-form__grid">
        <FormField name="name" label="Category name" defaultValue={initial.name} maxLength={150} required />
        <FormField name="display_order" label="Display order" type="number" min={0} max={32767} defaultValue={initial.display_order} required />
        <div className="management-form__wide"><TextAreaField name="description" label="Description" defaultValue={initial.description} rows={3} /></div>
      </div>
      <label className="management-form__toggle"><input type="checkbox" name="is_active" defaultChecked={initial.is_active} /><span><strong>Active category</strong><small>Inactive categories and their services are hidden publicly.</small></span></label>
      <ValidationSummary errors={errors} />
      {success ? <p className="content-editor__success" role="status">{success}</p> : null}
      <div className="service-category-card__actions">
        {initial.service_count === 0 ? <Button type="button" variant="outline" onClick={remove} loading={deleting} loadingLabel="Deleting...">Delete empty category</Button> : null}
        <Button type="submit" loading={saving} loadingLabel="Saving...">Save category</Button>
      </div>
    </form>
  );
}

export function ServiceCategoryManager({ initialCategories }: { initialCategories: ManagementServiceCategory[] }) {
  const [categories, setCategories] = useState(initialCategories);
  const [creating, setCreating] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setCreating(true); setErrors([]);
    const data = new FormData(form);
    try {
      const created = await apiFetch<ManagementServiceCategory>("services/management/service-categories/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: String(data.get("name")), description: String(data.get("description")), display_order: Number(data.get("display_order")), is_active: data.get("is_active") === "on" }),
      });
      setCategories((current) => [...current, created].sort((a, b) => a.display_order - b.display_order || a.name.localeCompare(b.name)));
      form.reset();
    } catch (error) { setErrors(errorMessages(error)); } finally { setCreating(false); }
  }
  return (
    <div className="service-category-manager">
      <form className="management-form__section" onSubmit={create}>
        <div className="management-form__section-heading"><h2>Add category</h2><p>A stable URL slug is generated automatically from the category name.</p></div>
        <div className="management-form__grid"><FormField name="name" label="Category name" maxLength={150} required /><FormField name="display_order" label="Display order" type="number" min={0} max={32767} defaultValue={categories.length + 1} required /><div className="management-form__wide"><TextAreaField name="description" label="Description" rows={3} /></div></div>
        <label className="management-form__toggle"><input type="checkbox" name="is_active" defaultChecked /><span><strong>Active category</strong><small>Available for service assignment and public filtering.</small></span></label>
        <ValidationSummary errors={errors} />
        <div className="management-form__actions"><Button type="submit" loading={creating} loadingLabel="Creating...">Add category</Button></div>
      </form>
      <section className="service-category-manager__list"><header><h2>Existing categories</h2><span>{categories.length} categories</span></header>{categories.map((category) => <CategoryEditor initial={category} key={`${category.id}-${category.updated_at}`} onUpdated={(updated) => setCategories((current) => current.map((item) => item.id === updated.id ? updated : item))} onDeleted={(id) => setCategories((current) => current.filter((item) => item.id !== id))} />)}</section>
    </div>
  );
}

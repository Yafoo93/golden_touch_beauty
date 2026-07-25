"use client";

import Image from "next/image";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import {
  FormField,
  TextAreaField,
  ValidationSummary,
} from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import type { ManagementGalleryItem } from "@/lib/gallery";

function messagesFrom(error: unknown) {
  if (!(error instanceof ApiError)) {
    return ["The gallery request could not be completed. Please try again."];
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

function appendCommonFields(formData: FormData, form: HTMLFormElement) {
  const values = new FormData(form);
  ["title", "category", "alt_text", "display_size", "display_order"].forEach(
    (field) => formData.set(field, String(values.get(field) ?? "")),
  );
  formData.set(
    "is_published",
    values.get("is_published") === "on" ? "true" : "false",
  );
  const image = values.get("image");
  if (image instanceof File && image.size > 0) formData.set("image", image);
}

function GalleryItemEditor({
  initial,
  onDeleted,
}: {
  initial: ManagementGalleryItem;
  onDeleted: (id: string) => void;
}) {
  const [item, setItem] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [success, setSuccess] = useState("");

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setErrors([]);
    setSuccess("");
    const body = new FormData();
    appendCommonFields(body, event.currentTarget);
    try {
      const updated = await apiFetch<ManagementGalleryItem>(
        `gallery/management/${item.id}/`,
        { method: "PATCH", body },
      );
      setItem(updated);
      setSuccess("Gallery item saved.");
    } catch (error) {
      setErrors(messagesFrom(error));
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Delete “${item.title}” from the gallery?`)) return;
    setDeleting(true);
    setErrors([]);
    try {
      await apiFetch<unknown>(`gallery/management/${item.id}/`, {
        method: "DELETE",
      });
      onDeleted(item.id);
    } catch (error) {
      setErrors(messagesFrom(error));
      setDeleting(false);
    }
  }

  return (
    <form className="gallery-manager__card" onSubmit={save}>
      <div className="gallery-manager__preview">
        <Image src={item.image_url} alt={item.alt_text} fill sizes="18rem" />
        <span className={item.is_published ? "status-badge status-badge--active" : "status-badge status-badge--inactive"}>
          {item.is_published ? "Published" : "Draft"}
        </span>
      </div>
      <div className="gallery-manager__fields">
        <FormField name="title" label="Title" defaultValue={item.title} maxLength={150} required />
        <FormField name="category" label="Category" defaultValue={item.category} maxLength={120} required />
        <TextAreaField name="alt_text" label="Image description" defaultValue={item.alt_text} rows={3} maxLength={250} hint="Describe the image for customers using screen readers." required />
        <div className="management-form__grid">
          <div className="form-field">
            <label className="form-field__label" htmlFor={`size-${item.id}`}>Display size</label>
            <select className="form-field__control" id={`size-${item.id}`} name="display_size" defaultValue={item.display_size}>
              <option value="standard">Standard</option>
              <option value="wide">Wide</option>
              <option value="tall">Tall</option>
            </select>
          </div>
          <FormField name="display_order" label="Display order" type="number" min={0} max={32767} defaultValue={item.display_order} required />
        </div>
        <FormField name="image" label="Replace image" type="file" accept="image/jpeg,image/png,image/webp" hint="Optional. JPEG, PNG, or WebP up to 8 MB." />
        <label className="management-form__toggle">
          <input type="checkbox" name="is_published" defaultChecked={item.is_published} />
          <span><strong>Published</strong><small>Visible on the public gallery.</small></span>
        </label>
        <ValidationSummary errors={errors} />
        {success ? <p className="content-editor__success" role="status">{success}</p> : null}
        <div className="gallery-manager__actions">
          <Button type="button" variant="outline" onClick={remove} loading={deleting} loadingLabel="Deleting...">Delete</Button>
          <Button type="submit" loading={saving} loadingLabel="Saving...">Save changes</Button>
        </div>
      </div>
    </form>
  );
}

export function GalleryManager({
  initialItems,
}: {
  initialItems: ManagementGalleryItem[];
}) {
  const [items, setItems] = useState(initialItems);
  const [creating, setCreating] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setCreating(true);
    setErrors([]);
    const body = new FormData();
    appendCommonFields(body, form);
    try {
      const created = await apiFetch<ManagementGalleryItem>(
        "gallery/management/",
        { method: "POST", body },
      );
      setItems((current) => [...current, created].sort((a, b) => a.display_order - b.display_order));
      form.reset();
    } catch (error) {
      setErrors(messagesFrom(error));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="gallery-manager">
      <form className="management-form__section gallery-manager__create" onSubmit={create}>
        <div className="management-form__section-heading">
          <h2>Add gallery item</h2>
          <p>New items may be saved as drafts and published after review.</p>
        </div>
        <div className="management-form__grid">
          <FormField name="title" label="Title" maxLength={150} required />
          <FormField name="category" label="Category" maxLength={120} required />
          <div className="management-form__wide">
            <TextAreaField name="alt_text" label="Image description" rows={3} maxLength={250} required />
          </div>
          <div className="form-field">
            <label className="form-field__label" htmlFor="new-gallery-size">Display size</label>
            <select className="form-field__control" id="new-gallery-size" name="display_size" defaultValue="standard">
              <option value="standard">Standard</option>
              <option value="wide">Wide</option>
              <option value="tall">Tall</option>
            </select>
          </div>
          <FormField name="display_order" label="Display order" type="number" min={0} max={32767} defaultValue={items.length + 1} required />
          <div className="management-form__wide">
            <FormField name="image" label="Gallery image" type="file" accept="image/jpeg,image/png,image/webp" hint="JPEG, PNG, or WebP up to 8 MB." required />
          </div>
        </div>
        <label className="management-form__toggle">
          <input type="checkbox" name="is_published" />
          <span><strong>Publish immediately</strong><small>Leave off to review it as a draft first.</small></span>
        </label>
        <ValidationSummary errors={errors} />
        <div className="management-form__actions">
          <Button type="submit" loading={creating} loadingLabel="Uploading...">Add gallery item</Button>
        </div>
      </form>

      <section className="gallery-manager__existing" aria-labelledby="gallery-existing-title">
        <header><h2 id="gallery-existing-title">Existing gallery items</h2><span>{items.length} items</span></header>
        {items.length ? (
          <div className="gallery-manager__list">
            {items.map((item) => (
              <GalleryItemEditor
                initial={item}
                key={item.id}
                onDeleted={(id) => setItems((current) => current.filter((entry) => entry.id !== id))}
              />
            ))}
          </div>
        ) : (
          <p className="gallery-manager__empty">No gallery items have been added.</p>
        )}
      </section>
    </div>
  );
}

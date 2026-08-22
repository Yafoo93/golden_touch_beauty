"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Button, ButtonLink } from "@/components/ui/button";
import {
  FormField,
  TextAreaField,
  ValidationSummary,
} from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";

export type ProductCategoryOption = { id: string; name: string };
export type ProductBranchOption = { id: string; code: string; name: string };

function errorsFrom(error: unknown) {
  if (!(error instanceof ApiError)) {
    return ["The product could not be created. Please try again."];
  }
  if (!error.details || typeof error.details !== "object") {
    return [error.message];
  }
  return Object.entries(error.details as Record<string, unknown>).flatMap(
    ([field, value]) =>
      (Array.isArray(value) ? value : [value]).map(
        (message) => `${field.replaceAll("_", " ")}: ${String(message)}`,
      ),
  );
}

export function ProductCreateForm({
  categories,
  branches,
}: {
  categories: ProductCategoryOption[];
  branches: ProductBranchOption[];
}) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [priceType, setPriceType] = useState<"fixed" | "contact">("fixed");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors([]);
    const body = new FormData(event.currentTarget);
    body.set("is_featured", body.get("is_featured") === "on" ? "true" : "false");
    body.set(
      "initial_is_preorder",
      body.get("initial_is_preorder") === "on" ? "true" : "false",
    );
    if (!body.get("initial_estimated_availability_date")) {
      body.delete("initial_estimated_availability_date");
    }
    body.set(
      "branch_stocks",
      JSON.stringify(
        branches.map((branch) => ({
          branch_id: branch.id,
          quantity_on_hand: Number(body.get(`stock_${branch.id}`) || 0),
          reorder_level: Number(body.get(`reorder_${branch.id}`) || 0),
          is_available: body.get(`available_${branch.id}`) === "on",
        })),
      ),
    );
    branches.forEach((branch) => {
      body.delete(`stock_${branch.id}`);
      body.delete(`reorder_${branch.id}`);
      body.delete(`available_${branch.id}`);
    });

    try {
      await apiFetch("products/management/", { method: "POST", body });
      router.push("/management/products");
      router.refresh();
    } catch (error) {
      setErrors(errorsFrom(error));
      setSubmitting(false);
    }
  }

  return (
    <form className="management-form" onSubmit={submit}>
      <ValidationSummary errors={errors} />

      <section className="management-form__section">
        <div className="management-form__section-heading">
          <h2>Product identity</h2>
          <p>The public URL is generated from the product name.</p>
        </div>
        <div className="management-form__grid">
          <FormField name="name" label="Product name" maxLength={180} required />
          <FormField name="brand" label="Brand" maxLength={150} />
          <div className="form-field">
            <label className="form-field__label" htmlFor="product-category">
              Category *
            </label>
            <select
              className="form-field__control"
              id="product-category"
              name="category_id"
              defaultValue=""
              required
            >
              <option value="" disabled>Select a category</option>
              {categories.map((category) => (
                <option value={category.id} key={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field"><label className="form-field__label" htmlFor="product-price-type">Customer pricing *</label><select className="form-field__control" id="product-price-type" name="price_type" value={priceType} onChange={(event) => setPriceType(event.target.value as "fixed" | "contact")} required><option value="fixed">Show selling price</option><option value="contact">Contact for price via branch WhatsApp</option></select></div>
          <div className="form-field">
            <label className="form-field__label" htmlFor="product-state">
              Publication state *
            </label>
            <select
              className="form-field__control"
              id="product-state"
              name="publication_state"
              defaultValue="draft"
              required
            >
              <option value="draft">Draft — hidden from customers</option>
              <option value="published">Published — visible in the shop</option>
              <option value="inactive">Inactive — unavailable operationally</option>
            </select>
          </div>
          <div className="management-form__wide">
            <TextAreaField
              name="description"
              label="Description"
              rows={6}
              required
            />
          </div>
          <div className="management-form__wide">
            <FormField
              name="image"
              label="Product image"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hint="JPEG, PNG, or WebP up to 8 MB."
              required
            />
          </div>
          <label className="management-form__toggle">
            <input type="checkbox" name="is_featured" />
            <span><strong>Featured product</strong><small>Eligible for homepage promotion.</small></span>
          </label>
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading">
          <h2>Initial variant</h2>
          <p>Create the first SKU and pricing record. Additional variants can be added during product editing.</p>
        </div>
        <div className="management-form__grid">
          <FormField name="initial_variant_name" label="Variant name" defaultValue="Standard" maxLength={120} required />
          <FormField name="initial_sku" label="SKU" maxLength={80} required />
          {priceType === "fixed" ? <>
            <FormField name="initial_selling_price" label="Selling price (GHS)" type="number" min={0} step="0.01" required />
            <FormField name="initial_cost_price" label="Cost price (GHS)" type="number" min={0} step="0.01" required />
          </> : <p className="management-form__wide">Selling and cost prices are not required. Customers will request the current price through WhatsApp.</p>}
          <FormField name="initial_estimated_availability_date" label="Estimated availability" type="date" hint="Required when pre-order is enabled." />
          <label className="management-form__toggle">
            <input type="checkbox" name="initial_is_preorder" />
            <span><strong>Allow pre-order</strong><small>Customers may add this variant before live stock is available.</small></span>
          </label>
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading">
          <h2>Opening branch stock</h2>
          <p>Set initial balances and reorder alerts independently for each active branch.</p>
        </div>
        <div className="product-create-stock-grid">
          {branches.map((branch) => (
            <fieldset key={branch.id}>
              <legend>{branch.name}</legend>
              <span>{branch.code}</span>
              <FormField name={`stock_${branch.id}`} label="Quantity on hand" type="number" min={0} defaultValue={0} required />
              <FormField name={`reorder_${branch.id}`} label="Reorder level" type="number" min={0} defaultValue={5} required />
              <label className="management-form__toggle">
                <input type="checkbox" name={`available_${branch.id}`} defaultChecked />
                <span><strong>Available for sale</strong><small>Stock may be used for shop and POS fulfilment.</small></span>
              </label>
            </fieldset>
          ))}
        </div>
      </section>

      <div className="management-form__actions">
        <ButtonLink href="/management/products" variant="outline">Cancel</ButtonLink>
        <Button type="submit" loading={submitting} loadingLabel="Creating product...">
          Create product
        </Button>
      </div>
    </form>
  );
}

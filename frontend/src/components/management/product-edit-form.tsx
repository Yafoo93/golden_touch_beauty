"use client";

import Image from "next/image";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Button, ButtonLink } from "@/components/ui/button";
import { FormField, TextAreaField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch } from "@/lib/api";
import type { ManagementProductDetail } from "@/lib/management-products";
import type { ProductBranchOption, ProductCategoryOption } from "./product-create-form";

type EditableStock = {
  branch_id: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  reorder_level: number;
  is_available: boolean;
};

type EditableVariant = {
  key: string;
  id?: string;
  name: string;
  sku: string;
  selling_price: string;
  cost_price: string;
  is_preorder: boolean;
  estimated_availability_date: string;
  is_active: boolean;
  stocks: EditableStock[];
};

function errorsFrom(error: unknown) {
  if (!(error instanceof ApiError)) return ["The product could not be updated."];
  if (!error.details || typeof error.details !== "object") return [error.message];
  return Object.entries(error.details as Record<string, unknown>).flatMap(
    ([field, value]) =>
      (Array.isArray(value) ? value : [value]).map(
        (message) => `${field.replaceAll("_", " ")}: ${String(message)}`,
      ),
  );
}

function newVariant(branches: ProductBranchOption[]): EditableVariant {
  return {
    key: crypto.randomUUID(),
    name: "",
    sku: "",
    selling_price: "",
    cost_price: "",
    is_preorder: false,
    estimated_availability_date: "",
    is_active: true,
    stocks: branches.map((branch) => ({
      branch_id: branch.id,
      quantity_on_hand: 0,
      quantity_reserved: 0,
      reorder_level: 5,
      is_available: true,
    })),
  };
}

export function ProductEditForm({
  product,
  categories,
  branches,
}: {
  product: ManagementProductDetail;
  categories: ProductCategoryOption[];
  branches: ProductBranchOption[];
}) {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [priceType, setPriceType] = useState<"fixed" | "contact">(product.price_type);
  const [variants, setVariants] = useState<EditableVariant[]>(
    product.variants.map((variant) => ({
      key: variant.id,
      id: variant.id,
      name: variant.name,
      sku: variant.sku,
      selling_price: variant.selling_price,
      cost_price: variant.cost_price,
      is_preorder: variant.is_preorder,
      estimated_availability_date: variant.estimated_availability_date ?? "",
      is_active: variant.is_active,
      stocks: branches.map((branch) => {
        const stock = variant.stocks.find((item) => item.branch_id === branch.id);
        return {
          branch_id: branch.id,
          quantity_on_hand: stock?.quantity_on_hand ?? 0,
          quantity_reserved: stock?.quantity_reserved ?? 0,
          reorder_level: stock?.reorder_level ?? 5,
          is_available: stock?.is_available ?? true,
        };
      }),
    })),
  );

  function updateVariant(key: string, patch: Partial<EditableVariant>) {
    setVariants((current) =>
      current.map((variant) => (variant.key === key ? { ...variant, ...patch } : variant)),
    );
  }

  function updateStock(
    variantKey: string,
    branchId: string,
    patch: Partial<EditableStock>,
  ) {
    setVariants((current) =>
      current.map((variant) =>
        variant.key === variantKey
          ? {
              ...variant,
              stocks: variant.stocks.map((stock) =>
                stock.branch_id === branchId ? { ...stock, ...patch } : stock,
              ),
            }
          : variant,
      ),
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setErrors([]);
    const body = new FormData(event.currentTarget);
    body.set("is_featured", body.get("is_featured") === "on" ? "true" : "false");
    const image = body.get("image");
    if (!(image instanceof File) || image.size === 0) body.delete("image");
    body.set(
      "variants",
      JSON.stringify(
        variants.map(({ key: _key, ...variant }) => ({
          ...variant,
          estimated_availability_date:
            variant.estimated_availability_date || null,
          stocks: variant.stocks.map(
            ({ quantity_reserved: _reserved, ...stock }) => stock,
          ),
        })),
      ),
    );
    try {
      await apiFetch(`products/management/${product.id}/`, {
        method: "PATCH",
        body,
      });
      router.push("/management/products");
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
        <div className="management-form__section-heading">
          <h2>Product details</h2>
          <p>The stable shop URL remains /shop/{product.slug}.</p>
        </div>
        <div className="management-form__grid">
          <FormField name="name" label="Product name" defaultValue={product.name} required />
          <FormField name="brand" label="Brand" defaultValue={product.brand} />
          <div className="form-field">
            <label className="form-field__label" htmlFor="edit-product-category">Category *</label>
            <select className="form-field__control" id="edit-product-category" name="category_id" defaultValue={product.category_id} required>
              {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
          </div>
          <div className="form-field"><label className="form-field__label" htmlFor="edit-product-price-type">Customer pricing *</label><select className="form-field__control" id="edit-product-price-type" name="price_type" value={priceType} onChange={(event) => setPriceType(event.target.value as "fixed" | "contact")} required><option value="fixed">Show selling price</option><option value="contact">Contact for price via branch WhatsApp</option></select></div>
          <div className="form-field">
            <label className="form-field__label" htmlFor="edit-product-state">Publication state *</label>
            <select className="form-field__control" id="edit-product-state" name="publication_state" defaultValue={product.publication_state} required>
              <option value="draft">Draft - hidden from customers</option>
              <option value="published">Published - visible in the shop</option>
              <option value="inactive">Inactive - unavailable operationally</option>
            </select>
          </div>
          <div className="management-form__wide">
            <TextAreaField name="description" label="Description" defaultValue={product.description} rows={6} required />
          </div>
          <label className="management-form__toggle">
            <input type="checkbox" name="is_featured" defaultChecked={product.is_featured} />
            <span><strong>Featured product</strong><small>Eligible for homepage promotion.</small></span>
          </label>
        </div>
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading">
          <h2>Product image</h2>
          <p>Leave the file empty to keep the current image.</p>
        </div>
        <div className="service-edit-form__image">
          <Image src={product.image_path || "/images/hero2.jpeg"} alt="" fill sizes="22rem" />
        </div>
        <FormField name="image" label="Replace product image" type="file" accept="image/jpeg,image/png,image/webp" hint="Optional. JPEG, PNG, or WebP up to 8 MB." />
      </section>

      <section className="management-form__section">
        <div className="management-form__section-heading">
          <h2>Variants, prices, and branch stock</h2>
          <p>Each variant has its own SKU, price, and stock balance at every branch.</p>
        </div>
        <div className="product-variant-editor">
          {variants.map((variant, index) => (
            <fieldset className="product-variant-editor__variant" key={variant.key}>
              <legend>Variant {index + 1}</legend>
              <div className="management-form__grid">
                <FormField label="Variant name" value={variant.name} onChange={(event) => updateVariant(variant.key, { name: event.target.value })} required />
                <FormField label="SKU" value={variant.sku} onChange={(event) => updateVariant(variant.key, { sku: event.target.value })} required />
                {priceType === "fixed" ? <>
                  <FormField label="Selling price (GHS)" type="number" min={0} step="0.01" value={variant.selling_price} onChange={(event) => updateVariant(variant.key, { selling_price: event.target.value })} required />
                  <FormField label="Cost price (GHS)" type="number" min={0} step="0.01" value={variant.cost_price} onChange={(event) => updateVariant(variant.key, { cost_price: event.target.value })} required />
                </> : null}
                <FormField label="Estimated availability" type="date" value={variant.estimated_availability_date} onChange={(event) => updateVariant(variant.key, { estimated_availability_date: event.target.value })} />
                <div className="product-variant-editor__toggles">
                  <label className="management-form__toggle"><input type="checkbox" checked={variant.is_preorder} onChange={(event) => updateVariant(variant.key, { is_preorder: event.target.checked })} /><span><strong>Pre-order</strong><small>May sell before stock arrives.</small></span></label>
                  <label className="management-form__toggle"><input type="checkbox" checked={variant.is_active} onChange={(event) => updateVariant(variant.key, { is_active: event.target.checked })} /><span><strong>Active variant</strong><small>Available for operational use.</small></span></label>
                </div>
              </div>
              <div className="product-create-stock-grid">
                {branches.map((branch) => {
                  const stock = variant.stocks.find((item) => item.branch_id === branch.id)!;
                  return (
                    <fieldset key={branch.id}>
                      <legend>{branch.name}</legend>
                      <span>{branch.code} / {stock.quantity_reserved} reserved</span>
                      <FormField label="Quantity on hand" type="number" min={stock.quantity_reserved} value={stock.quantity_on_hand} onChange={(event) => updateStock(variant.key, branch.id, { quantity_on_hand: Number(event.target.value) })} required />
                      <FormField label="Reorder level" type="number" min={0} value={stock.reorder_level} onChange={(event) => updateStock(variant.key, branch.id, { reorder_level: Number(event.target.value) })} required />
                      <label className="management-form__toggle"><input type="checkbox" checked={stock.is_available} onChange={(event) => updateStock(variant.key, branch.id, { is_available: event.target.checked })} /><span><strong>Available at branch</strong><small>Can fulfil shop and POS sales.</small></span></label>
                    </fieldset>
                  );
                })}
              </div>
              {variants.length > 1 ? (
                <Button type="button" variant="outline" size="small" onClick={() => setVariants((current) => current.filter((item) => item.key !== variant.key))}>Remove variant</Button>
              ) : null}
            </fieldset>
          ))}
        </div>
        <Button type="button" variant="outline" onClick={() => setVariants((current) => [...current, newVariant(branches)])}>Add another variant</Button>
      </section>

      <div className="management-form__actions">
        <ButtonLink href="/management/products" variant="outline">Cancel</ButtonLink>
        <Button type="submit" loading={saving} loadingLabel="Saving changes...">Save changes</Button>
      </div>
    </form>
  );
}

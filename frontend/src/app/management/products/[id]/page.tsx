import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ProductEditForm } from "@/components/management/product-edit-form";
import type { ProductBranchOption, ProductCategoryOption } from "@/components/management/product-create-form";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementProductDetail } from "@/lib/management-products";

export const metadata: Metadata = { title: "Edit Product" };

type LoadResult =
  | { status: "success"; product: ManagementProductDetail; categories: ProductCategoryOption[]; branches: ProductBranchOption[] }
  | { status: "denied" }
  | { status: "missing" }
  | { status: "error" };

async function loadProduct(id: string): Promise<LoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  const init = {
    cache: "no-store" as const,
    headers: { Accept: "application/json", Cookie: cookieHeader },
    signal: AbortSignal.timeout(15_000),
  };
  try {
    const [product, categories, branches] = await Promise.all([
      fetch(`${backendUrl}/api/v1/products/management/${encodeURIComponent(id)}/`, init),
      fetch(`${backendUrl}/api/v1/products/management/category-options/`, init),
      fetch(`${backendUrl}/api/v1/products/management/branch-options/`, init),
    ]);
    if ([product.status, categories.status, branches.status].some((code) => code === 401 || code === 403)) return { status: "denied" };
    if (product.status === 404) return { status: "missing" };
    if (!product.ok || !categories.ok || !branches.ok) return { status: "error" };
    return {
      status: "success",
      product: (await product.json()) as ManagementProductDetail,
      categories: (await categories.json()) as ProductCategoryOption[],
      branches: (await branches.json()) as ProductBranchOption[],
    };
  } catch {
    return { status: "error" };
  }
}

export default async function EditProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await loadProduct(id);
  return (
    <main className="management-page management-page--form">
      <header className="management-page__header">
        <div>
          <p>Management / Shop</p>
          <h1>{result.status === "success" ? result.product.name : "Edit product"}</h1>
          <span>Update product content, image, variants, prices, branch stock, and publication.</span>
        </div>
        <div className="management-page__summary">
          <strong>Inventory-aware editing</strong>
          <span>Existing reservations are protected while stock balances are changed.</span>
          <ButtonLink href="/management/products" variant="outline" size="small">Back to products</ButtonLink>
        </div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Owner access required" description="Sign in with the owner account to edit products." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "missing" ? (
        <EmptyState title="Product not found" description="This product may have been removed or the link is invalid." action={<ButtonLink href="/management/products">View products</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Product could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href={`/management/products/${id}`}>Try again</ButtonLink>} />
      ) : (
        <ProductEditForm product={result.product} categories={result.categories} branches={result.branches} />
      )}
    </main>
  );
}

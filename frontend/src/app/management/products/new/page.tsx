import type { Metadata } from "next";
import { cookies } from "next/headers";

import {
  ProductCreateForm,
  type ProductBranchOption,
  type ProductCategoryOption,
} from "@/components/management/product-create-form";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata: Metadata = { title: "Create Product" };

type LoadResult =
  | {
      status: "success";
      categories: ProductCategoryOption[];
      branches: ProductBranchOption[];
    }
  | { status: "denied" }
  | { status: "error" };

async function loadOptions(): Promise<LoadResult> {
  const backendUrl =
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  const init = {
    cache: "no-store" as const,
    headers: { Accept: "application/json", Cookie: cookieHeader },
    signal: AbortSignal.timeout(15_000),
  };
  try {
    const [categories, branches] = await Promise.all([
      fetch(`${backendUrl}/api/v1/products/management/category-options/`, init),
      fetch(`${backendUrl}/api/v1/products/management/branch-options/`, init),
    ]);
    if (
      [categories.status, branches.status].some(
        (status) => status === 401 || status === 403,
      )
    ) {
      return { status: "denied" };
    }
    if (!categories.ok || !branches.ok) return { status: "error" };
    return {
      status: "success",
      categories: (await categories.json()) as ProductCategoryOption[],
      branches: (await branches.json()) as ProductBranchOption[],
    };
  } catch {
    return { status: "error" };
  }
}

export default async function NewProductPage() {
  const result = await loadOptions();
  return (
    <main className="management-page management-page--form">
      <header className="management-page__header">
        <div>
          <p>Management · Shop</p>
          <h1>Create product</h1>
          <span>Create the catalogue record, first SKU, image, pricing, and opening branch inventory together.</span>
        </div>
        <div className="management-page__summary">
          <strong>Draft recommended</strong>
          <span>Review product copy, pricing, and stock before publishing.</span>
          <ButtonLink href="/management/products" variant="outline" size="small">
            Back to products
          </ButtonLink>
        </div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Owner access required" description="Sign in with the owner account to create products." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Product options could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/products/new">Try again</ButtonLink>} />
      ) : !result.categories.length || !result.branches.length ? (
        <EmptyState title="Product setup is incomplete" description="At least one active product category and branch are required." />
      ) : (
        <ProductCreateForm categories={result.categories} branches={result.branches} />
      )}
    </main>
  );
}

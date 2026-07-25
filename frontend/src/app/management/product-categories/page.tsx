import type { Metadata } from "next";
import { cookies } from "next/headers";

import {
  ProductCategoryManager,
  type ManagementProductCategory,
} from "@/components/management/product-category-manager";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata: Metadata = { title: "Manage Product Categories" };

type Result =
  | { status: "success"; categories: ManagementProductCategory[] }
  | { status: "denied" }
  | { status: "error" };

async function loadCategories(): Promise<Result> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(
      `${backendUrl}/api/v1/products/management/product-categories/`,
      {
        cache: "no-store",
        headers: { Accept: "application/json", Cookie: cookieHeader },
        signal: AbortSignal.timeout(15_000),
      },
    );
    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (!response.ok) return { status: "error" };
    return {
      status: "success",
      categories: (await response.json()) as ManagementProductCategory[],
    };
  } catch {
    return { status: "error" };
  }
}

export default async function ProductCategoriesPage() {
  const result = await loadCategories();
  return (
    <main className="management-page management-page--form">
      <header className="management-page__header">
        <div>
          <p>Management / Shop</p>
          <h1>Product categories</h1>
          <span>Create, order, rename, activate, or safely remove product categories.</span>
        </div>
        <div className="management-page__summary">
          <strong>Safe shop structure</strong>
          <span>Categories containing products cannot be deleted. Deactivate them to hide their products without losing data.</span>
          <ButtonLink href="/management/products" variant="outline" size="small">View products</ButtonLink>
        </div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Owner access required" description="Sign in with the owner account to manage product categories." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Categories could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/product-categories">Try again</ButtonLink>} />
      ) : (
        <ProductCategoryManager initialCategories={result.categories} />
      )}
    </main>
  );
}

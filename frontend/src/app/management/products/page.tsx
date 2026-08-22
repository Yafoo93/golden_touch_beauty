import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ManagementProductList } from "@/components/management/product-list";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementProduct } from "@/lib/management-products";

export const metadata: Metadata = { title: "Manage Products" };

type LoadResult =
  | { status: "success"; products: ManagementProduct[] }
  | { status: "denied" }
  | { status: "error" };

async function loadProducts(): Promise<LoadResult> {
  const backendUrl =
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(
      `${backendUrl}/api/v1/products/management/`,
      {
        cache: "no-store",
        headers: { Accept: "application/json", Cookie: cookieHeader },
        signal: AbortSignal.timeout(15_000),
      },
    );
    if (response.status === 401 || response.status === 403) {
      return { status: "denied" };
    }
    if (!response.ok) return { status: "error" };
    return {
      status: "success",
      products: (await response.json()) as ManagementProduct[],
    };
  } catch {
    return { status: "error" };
  }
}

export default async function ManagementProductsPage() {
  const result = await loadProducts();
  const totals =
    result.status === "success"
      ? {
          published: result.products.filter(
            (product) => product.publication_state === "published",
          ).length,
          draft: result.products.filter(
            (product) => product.publication_state === "draft",
          ).length,
          inactive: result.products.filter(
            (product) => product.publication_state === "inactive",
          ).length,
          available: result.products.reduce(
            (total, product) => total + product.total_available,
            0,
          ),
        }
      : { published: 0, draft: 0, inactive: 0, available: 0 };

  return (
    <main className="management-page management-page--services">
      <header className="management-page__header">
        <div>
          <p>Management · Shop</p>
          <h1>Products</h1>
          <span>
            Review the complete catalogue, publication state, variants, and
            live inventory across every branch.
          </span>
        </div>
        <div className="management-page__summary">
          <strong>Product catalogue</strong>
          <span>
            {result.status === "success"
              ? `${totals.published} published · ${totals.draft} drafts · ${totals.inactive} inactive · ${totals.available} units available`
              : "Catalogue totals appear when the product API is available."}
          </span>
          <ButtonLink href="/management/products/new" size="small">
            Add product
          </ButtonLink>
          <ButtonLink
            href="/management/product-categories"
            variant="outline"
            size="small"
          >
            Manage categories
          </ButtonLink>
          <ButtonLink href="/shop" variant="outline" size="small">
            View public shop
          </ButtonLink>
        </div>
      </header>

      {result.status === "denied" ? (
        <EmptyState
          title="Owner access required"
          description="Sign in with the owner account to view product and stock management."
          action={<ButtonLink href="/login">Sign in</ButtonLink>}
        />
      ) : result.status === "error" ? (
        <EmptyState
          title="Products could not be loaded"
          description="Check that Django is running, then try again."
          action={<ButtonLink href="/management/products">Try again</ButtonLink>}
        />
      ) : result.products.length ? (
        <ManagementProductList products={result.products} />
      ) : (
        <EmptyState
          title="No products yet"
          description="Create the first product during the upcoming product-creation task."
        />
      )}
    </main>
  );
}

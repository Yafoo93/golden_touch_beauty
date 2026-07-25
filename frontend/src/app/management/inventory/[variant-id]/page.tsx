import type { Metadata } from "next";
import { cookies } from "next/headers";

import { StockMovementHistory } from "@/components/management/stock-movement-history";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { VariantStockHistory } from "@/lib/management-inventory";

export const metadata: Metadata = { title: "Stock Movement History" };

type Result =
  | { status: "success"; history: VariantStockHistory }
  | { status: "denied" }
  | { status: "missing" }
  | { status: "error" };

async function loadHistory(variantId: string): Promise<Result> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(
      `${backendUrl}/api/v1/inventory/management/${encodeURIComponent(variantId)}/`,
      {
        cache: "no-store",
        headers: { Accept: "application/json", Cookie: cookieHeader },
        signal: AbortSignal.timeout(15_000),
      },
    );
    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (response.status === 404) return { status: "missing" };
    if (!response.ok) return { status: "error" };
    return { status: "success", history: (await response.json()) as VariantStockHistory };
  } catch {
    return { status: "error" };
  }
}

export default async function StockHistoryPage({
  params,
}: {
  params: Promise<{ "variant-id": string }>;
}) {
  const { "variant-id": variantId } = await params;
  const result = await loadHistory(variantId);
  return (
    <main className="management-page">
      <header className="management-page__header">
        <div>
          <p>Management / Inventory history</p>
          <h1>{result.status === "success" ? result.history.variant.product_name : "Stock history"}</h1>
          <span>{result.status === "success" ? `${result.history.variant.variant_name} / ${result.history.variant.sku}` : "Review stock movements for this product variant."}</span>
        </div>
        <div className="management-page__summary"><strong>Immutable movement ledger</strong><span>Entries record who changed stock, the quantity change, branch, and resulting balance.</span><ButtonLink href="/management/inventory" variant="outline" size="small">Back to inventory</ButtonLink></div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Inventory access required" description="You are not authorized to view this stock history." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "missing" ? (
        <EmptyState title="Variant not found" description="The variant does not exist or is outside your assigned branches." action={<ButtonLink href="/management/inventory">View inventory</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Stock history could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href={`/management/inventory/${variantId}`}>Try again</ButtonLink>} />
      ) : (
        <StockMovementHistory history={result.history} />
      )}
    </main>
  );
}

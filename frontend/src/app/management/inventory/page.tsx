import type { Metadata } from "next";
import { cookies } from "next/headers";

import { InventoryDashboard } from "@/components/management/inventory-dashboard";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementInventoryItem } from "@/lib/management-inventory";

export const metadata: Metadata = { title: "Inventory" };

type Result =
  | { status: "success"; inventory: ManagementInventoryItem[] }
  | { status: "denied" }
  | { status: "error" };

async function loadInventory(): Promise<Result> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(`${backendUrl}/api/v1/inventory/management/`, {
      cache: "no-store",
      headers: { Accept: "application/json", Cookie: cookieHeader },
      signal: AbortSignal.timeout(15_000),
    });
    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (!response.ok) return { status: "error" };
    return { status: "success", inventory: (await response.json()) as ManagementInventoryItem[] };
  } catch {
    return { status: "error" };
  }
}

export default async function InventoryPage() {
  const result = await loadInventory();
  return (
    <main className="management-page">
      <header className="management-page__header">
        <div><p>Management / Stock</p><h1>Inventory</h1><span>View product stock, reservations, availability, and reorder warnings by branch.</span></div>
        <div className="management-page__summary"><strong>Branch-scoped access</strong><span>You only see inventory for branches assigned to your staff account.</span><ButtonLink href="/management/products" variant="outline" size="small">Manage products</ButtonLink></div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Inventory access required" description="You need an owner, branch manager, or stock manager account for an assigned branch." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Inventory could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/inventory">Try again</ButtonLink>} />
      ) : (
        <InventoryDashboard inventory={result.inventory} />
      )}
    </main>
  );
}

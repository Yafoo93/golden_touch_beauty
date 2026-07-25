import type { Metadata } from "next";
import { cookies } from "next/headers";
import { ServiceCategoryManager, type ManagementServiceCategory } from "@/components/management/service-category-manager";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata: Metadata = { title: "Manage Service Categories" };
type Result = { status: "success"; categories: ManagementServiceCategory[] } | { status: "denied" } | { status: "error" };
async function loadCategories(): Promise<Result> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(`${backendUrl}/api/v1/services/management/service-categories/`, { cache: "no-store", headers: { Accept: "application/json", Cookie: cookieHeader }, signal: AbortSignal.timeout(15_000) });
    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (!response.ok) return { status: "error" };
    return { status: "success", categories: (await response.json()) as ManagementServiceCategory[] };
  } catch { return { status: "error" }; }
}

export default async function ServiceCategoriesPage() {
  const result = await loadCategories();
  return (
    <main className="management-page management-page--form">
      <header className="management-page__header"><div><p>Management · Catalogue</p><h1>Service categories</h1><span>Create, order, rename, activate, or safely remove service categories.</span></div><div className="management-page__summary"><strong>Safe catalogue structure</strong><span>Categories containing services cannot be deleted. Deactivate them to hide their services without data loss.</span><ButtonLink href="/management/services" variant="outline" size="small">View services</ButtonLink></div></header>
      {result.status === "denied" ? <EmptyState title="Owner access required" description="Sign in with the owner account to manage categories." action={<ButtonLink href="/login">Sign in</ButtonLink>} /> : result.status === "error" ? <EmptyState title="Categories could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/service-categories">Try again</ButtonLink>} /> : <ServiceCategoryManager initialCategories={result.categories} />}
    </main>
  );
}

import type { Metadata } from "next";
import { cookies } from "next/headers";
import { ServiceCreateForm, type ServiceBranchOption, type ServiceCategoryOption } from "@/components/management/service-create-form";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export const metadata: Metadata = { title: "Create Service" };
type LoadResult = { status: "success"; categories: ServiceCategoryOption[]; branches: ServiceBranchOption[] } | { status: "denied" } | { status: "error" };

async function loadOptions(): Promise<LoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const [categories, branches] = await Promise.all([
      fetch(`${backendUrl}/api/v1/services/management/category-options/`, { cache: "no-store", headers: { Accept: "application/json", Cookie: cookieHeader }, signal: AbortSignal.timeout(15_000) }),
      fetch(`${backendUrl}/api/v1/services/management/branch-options/`, { cache: "no-store", headers: { Accept: "application/json", Cookie: cookieHeader }, signal: AbortSignal.timeout(15_000) }),
    ]);
    if ([categories.status, branches.status].some((status) => status === 401 || status === 403)) return { status: "denied" };
    if (!categories.ok || !branches.ok) return { status: "error" };
    return { status: "success", categories: (await categories.json()) as ServiceCategoryOption[], branches: (await branches.json()) as ServiceBranchOption[] };
  } catch {
    return { status: "error" };
  }
}

export default async function NewServicePage() {
  const result = await loadOptions();
  return (
    <main className="management-page management-page--form">
      <header className="management-page__header"><div><p>Management · Catalogue</p><h1>Create service</h1><span>Add a service, configure pricing and booking behavior, and assign its initial branches.</span></div><div className="management-page__summary"><strong>Draft first</strong><span>Leave Published off until the service has been reviewed.</span><ButtonLink href="/management/services" variant="outline" size="small">Back to services</ButtonLink></div></header>
      {result.status === "denied" ? <EmptyState title="Owner access required" description="Sign in with the owner account to create services." action={<ButtonLink href="/login">Sign in</ButtonLink>} /> : result.status === "error" ? <EmptyState title="Creation options could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/services/new">Try again</ButtonLink>} /> : !result.categories.length || !result.branches.length ? <EmptyState title="Service setup is incomplete" description="At least one active category and active branch are required." /> : <ServiceCreateForm categories={result.categories} branches={result.branches} />}
    </main>
  );
}

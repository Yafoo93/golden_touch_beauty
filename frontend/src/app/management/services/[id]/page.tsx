import type { Metadata } from "next";
import { cookies } from "next/headers";
import { ServiceEditForm } from "@/components/management/service-edit-form";
import type { ServiceBranchOption, ServiceCategoryOption } from "@/components/management/service-create-form";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementServiceDetail } from "@/lib/management-services";

export const metadata: Metadata = { title: "Edit Service" };
type LoadResult = { status: "success"; service: ManagementServiceDetail; categories: ServiceCategoryOption[]; branches: ServiceBranchOption[] } | { status: "denied" } | { status: "missing" } | { status: "error" };

async function loadService(id: string): Promise<LoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  const init = { cache: "no-store" as const, headers: { Accept: "application/json", Cookie: cookieHeader }, signal: AbortSignal.timeout(15_000) };
  try {
    const [service, categories, branches] = await Promise.all([
      fetch(`${backendUrl}/api/v1/services/management/${encodeURIComponent(id)}/`, init),
      fetch(`${backendUrl}/api/v1/services/management/category-options/`, init),
      fetch(`${backendUrl}/api/v1/services/management/branch-options/`, init),
    ]);
    if ([service.status, categories.status, branches.status].some((status) => status === 401 || status === 403)) return { status: "denied" };
    if (service.status === 404) return { status: "missing" };
    if (!service.ok || !categories.ok || !branches.ok) return { status: "error" };
    return { status: "success", service: (await service.json()) as ManagementServiceDetail, categories: (await categories.json()) as ServiceCategoryOption[], branches: (await branches.json()) as ServiceBranchOption[] };
  } catch {
    return { status: "error" };
  }
}

export default async function EditServicePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await loadService(id);
  return (
    <main className="management-page management-page--form">
      <header className="management-page__header"><div><p>Management · Catalogue</p><h1>{result.status === "success" ? result.service.name : "Edit service"}</h1><span>Update service content, pricing, image, branch availability, and booking eligibility.</span></div><div className="management-page__summary"><strong>Stable service URL</strong><span>Editing the service name does not change its existing public URL.</span><ButtonLink href="/management/services" variant="outline" size="small">Back to services</ButtonLink></div></header>
      {result.status === "denied" ? <EmptyState title="Owner access required" description="Sign in with the owner account to edit services." action={<ButtonLink href="/login">Sign in</ButtonLink>} /> : result.status === "missing" ? <EmptyState title="Service not found" description="This service may have been removed or the link is invalid." action={<ButtonLink href="/management/services">View services</ButtonLink>} /> : result.status === "error" ? <EmptyState title="Service could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href={`/management/services/${id}`}>Try again</ButtonLink>} /> : <ServiceEditForm service={result.service} categories={result.categories} branches={result.branches} />}
    </main>
  );
}

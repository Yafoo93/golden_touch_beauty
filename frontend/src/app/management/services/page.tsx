import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ManagementServiceList } from "@/components/management/service-list";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementService } from "@/lib/management-services";

export const metadata: Metadata = { title: "Manage Services" };

type LoadResult =
  | { status: "success"; services: ManagementService[] }
  | { status: "denied" }
  | { status: "error" };

async function loadServices(): Promise<LoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(`${backendUrl}/api/v1/services/management/`, {
      cache: "no-store",
      headers: { Accept: "application/json", Cookie: cookieHeader },
      signal: AbortSignal.timeout(15_000),
    });
    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (!response.ok) return { status: "error" };
    return { status: "success", services: (await response.json()) as ManagementService[] };
  } catch {
    return { status: "error" };
  }
}

export default async function ManagementServicesPage() {
  const result = await loadServices();
  const stateCounts = result.status === "success"
    ? {
        published: result.services.filter((service) => service.publication_state === "published").length,
        draft: result.services.filter((service) => service.publication_state === "draft").length,
        inactive: result.services.filter((service) => service.publication_state === "inactive").length,
      }
    : { published: 0, draft: 0, inactive: 0 };
  return (
    <main className="management-page management-page--services">
      <header className="management-page__header">
        <div>
          <p>Management · Catalogue</p>
          <h1>Services</h1>
          <span>Review every service and its publication, activity, pricing, and branch availability state.</span>
        </div>
        <div className="management-page__summary">
          <strong>Service catalogue</strong>
          <span>
            {result.status === "success"
              ? `${stateCounts.published} published · ${stateCounts.draft} drafts · ${stateCounts.inactive} inactive · ${result.services.length} total`
              : "Publication totals will appear when the service API is available."}
          </span>
          <ButtonLink href="/management/services/new" size="small">Add service</ButtonLink>
          <ButtonLink href="/management/service-categories" variant="outline" size="small">Manage categories</ButtonLink>
          <ButtonLink href="/services" variant="outline" size="small">View public services</ButtonLink>
        </div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Owner access required" description="Sign in with the owner account to manage the complete service catalogue." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Services could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/services">Try again</ButtonLink>} />
      ) : result.services.length ? (
        <ManagementServiceList services={result.services} />
      ) : (
        <EmptyState title="No services yet" description="Create the first service when the service-creation module is available." />
      )}
    </main>
  );
}

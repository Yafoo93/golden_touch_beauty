import type { Metadata } from "next";
import { cookies } from "next/headers";
import { ManagementBranchList } from "@/components/management/branch-list";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { PaginatedResponse } from "@/lib/branches";
import type { ManagementBranch } from "@/lib/management-branches";

export const metadata: Metadata = { title: "Manage Branches" };

type BranchLoadResult =
  | { status: "success"; branches: ManagementBranch[] }
  | { status: "denied" }
  | { status: "error" };

async function getManagementBranches(): Promise<BranchLoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();

  try {
    const response = await fetch(`${backendUrl}/api/v1/branches/management/`, {
      cache: "no-store",
      headers: { Accept: "application/json", Cookie: cookieHeader },
      signal: AbortSignal.timeout(15_000),
    });

    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (!response.ok) return { status: "error" };

    const body = (await response.json()) as PaginatedResponse<ManagementBranch>;
    return { status: "success", branches: body.results };
  } catch {
    return { status: "error" };
  }
}

export default async function ManagementBranchesPage() {
  const result = await getManagementBranches();

  return (
    <main className="management-page">
      <header className="management-page__header">
        <div>
          <p>Management · Locations</p>
          <h1>Branches</h1>
          <span>View every Golden Touch location, including branches that are not publicly active.</span>
        </div>
        <div className="management-page__summary">
          <strong>Branch operations</strong>
          <span>Add new locations now. Editing is delivered in the next branch-management task.</span>
          <ButtonLink href="/management/branches/new" size="small">Add branch</ButtonLink>
        </div>
      </header>

      <section aria-label="Golden Touch branches">
        {result.status === "denied" ? (
          <EmptyState
            title="Owner access required"
            description="Sign in with the Golden Touch owner account to view branch management."
          />
        ) : result.status === "error" ? (
          <EmptyState
            title="Branches could not be loaded"
            description="The branch service is temporarily unavailable. Check that Django is running, then try again."
            action={<ButtonLink href="/management/branches">Try again</ButtonLink>}
          />
        ) : result.branches.length === 0 ? (
          <EmptyState title="No branches yet" description="Create the first Golden Touch location to begin branch operations." />
        ) : (
          <ManagementBranchList branches={result.branches} />
        )}
      </section>
    </main>
  );
}

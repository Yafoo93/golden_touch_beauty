import type { Metadata } from "next";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { BranchEditForm } from "@/components/management/branch-edit-form";
import { EmptyState } from "@/components/ui/empty-state";
import type { BranchManagerOption, ManagementBranch } from "@/lib/management-branches";

export const metadata: Metadata = { title: "Edit Branch" };

type LoadResult =
  | { status: "success"; branch: ManagementBranch; managers: BranchManagerOption[] }
  | { status: "denied" }
  | { status: "error" }
  | { status: "not-found" };

async function loadBranch(id: string): Promise<LoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  const headers = { Accept: "application/json", Cookie: cookieHeader };

  try {
    const [branchResponse, managersResponse] = await Promise.all([
      fetch(`${backendUrl}/api/v1/branches/management/${id}/`, { cache: "no-store", headers, signal: AbortSignal.timeout(15_000) }),
      fetch(`${backendUrl}/api/v1/branches/management/managers/`, { cache: "no-store", headers, signal: AbortSignal.timeout(15_000) }),
    ]);
    if (branchResponse.status === 404) return { status: "not-found" };
    if ([branchResponse.status, managersResponse.status].some((status) => status === 401 || status === 403)) return { status: "denied" };
    if (!branchResponse.ok || !managersResponse.ok) return { status: "error" };
    return { status: "success", branch: await branchResponse.json(), managers: await managersResponse.json() };
  } catch {
    return { status: "error" };
  }
}

export default async function EditBranchPage({ params }: { params: Promise<{ id: string }> }) {
  const result = await loadBranch((await params).id);
  if (result.status === "not-found") notFound();

  let content;
  if (result.status === "denied") {
    content = <EmptyState title="Owner access required" description="Sign in with the Golden Touch owner account to edit branches." />;
  } else if (result.status === "error") {
    content = <EmptyState title="Branch could not be loaded" description="Check that Django is running, then refresh this page." />;
  } else {
    content = <BranchEditForm branch={result.branch} managers={result.managers} />;
  }

  return (
    <main className="management-page management-page--form">
      <header className="management-page__header"><div><p>Management · Locations</p><h1>{result.status === "success" ? result.branch.name : "Edit branch"}</h1><span>Review and update this branch’s operational information.</span></div></header>
      {content}
    </main>
  );
}

import { BranchSelector } from "@/components/booking/branch-selector";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import type { PaginatedResponse, PublicBranch } from "@/lib/branches";


async function getBranches(): Promise<PublicBranch[] | null> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${backendUrl}/api/v1/branches/`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    const body = (await response.json()) as PaginatedResponse<PublicBranch>;
    return body.results;
  } catch {
    return null;
  }
}

export default async function BookPage({
  searchParams,
}: {
  searchParams: Promise<{ branch?: string; step?: string }>;
}) {
  const [branches, params] = await Promise.all([getBranches(), searchParams]);

  return (
    <main className="booking-page">
      <PageHero
        eyebrow="Book an appointment"
        title="Choose Your"
        accentTitle="Golden Touch Branch"
        description="Select where you would like to receive your service. You can review branch-specific services and availability next."
        size="compact"
      />
      <section className="booking-page__content" aria-label="Branch selection">
        {!branches ? (
          <EmptyState
            title="Branches could not be loaded"
            description="Check your connection and try again. No booking information has been lost."
            action={<ButtonLink href="/book">Try again</ButtonLink>}
          />
        ) : branches.length === 0 ? (
          <EmptyState
            title="No branches are currently available"
            description="Please contact Golden Touch for assistance with your appointment."
          />
        ) : (
          <BranchSelector
            branches={branches}
            initialBranchCode={params.branch}
          />
        )}
      </section>
    </main>
  );
}

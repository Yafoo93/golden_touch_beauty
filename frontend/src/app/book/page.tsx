import { BranchSelector } from "@/components/booking/branch-selector";
import { BookingFlow } from "@/components/booking/booking-flow";
import { ServiceSelector } from "@/components/booking/service-selector";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import type { PaginatedResponse, PublicBranch } from "@/lib/branches";
import { requireAuthenticated } from "@/lib/server-auth";
import { getServiceCatalogue } from "@/lib/services";


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
  searchParams: Promise<{
    branch?: string;
    step?: string;
    service?: string;
    services?: string;
  }>;
}) {
  const params = await searchParams;
  const returnQuery = new URLSearchParams();
  if (params.branch) returnQuery.set("branch", params.branch);
  if (params.step) returnQuery.set("step", params.step);
  if (params.service) returnQuery.set("service", params.service);
  if (params.services) returnQuery.set("services", params.services);
  await requireAuthenticated(
    `/book${returnQuery.size ? `?${returnQuery.toString()}` : ""}`,
  );
  const branches = await getBranches();
  const selectedBranch = branches?.find(
    (branch) => branch.code === params.branch,
  );
  const bookingServices = params.step === "schedule" && selectedBranch;
  const selectingServices = params.step === "service" && selectedBranch;
  const catalogue = (selectingServices || bookingServices)
    ? await getServiceCatalogue({ branch: selectedBranch.code })
    : null;
  const initialServiceSlugs = [
    ...(params.services?.split(",") ?? []),
    ...(params.service ? [params.service] : []),
  ].filter(Boolean);

  return (
    <main className="booking-page">
      <PageHero
        eyebrow="Book an appointment"
        title="Choose Your"
        accentTitle={bookingServices ? "Appointment" : selectingServices ? "Services" : "Golden Touch Branch"}
        description={
          bookingServices
            ? `Complete your request for ${selectedBranch.name}.`
            : selectingServices
            ? `Select one or more services available at ${selectedBranch.name}.`
            : "Select where you would like to receive your service. You can review branch-specific services and availability next."
        }
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
        ) : bookingServices && catalogue ? (
          <BookingFlow
            branchCode={selectedBranch.code}
            branchName={selectedBranch.name}
            services={catalogue.services.filter((service) => initialServiceSlugs.includes(service.slug))}
          />
        ) : selectingServices && catalogue ? (
          catalogue.unavailable ? (
            <EmptyState
              title="Services could not be loaded"
              description="Check your connection and try again. Your selected branch has been preserved."
              action={<ButtonLink href={`/book?step=service&branch=${encodeURIComponent(selectedBranch.code)}`}>Try again</ButtonLink>}
            />
          ) : catalogue.services.length ? (
            <ServiceSelector
              services={catalogue.services}
              branchCode={selectedBranch.code}
              branchName={selectedBranch.name}
              initialServiceSlugs={initialServiceSlugs}
            />
          ) : (
            <EmptyState
              title="No services are currently available at this branch"
              description="Choose another branch or contact Golden Touch for assistance."
              action={<ButtonLink href="/book">Choose another branch</ButtonLink>}
            />
          )
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

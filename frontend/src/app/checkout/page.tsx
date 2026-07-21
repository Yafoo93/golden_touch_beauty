import { PickupBranchSelector, type PickupBranchOption } from "@/components/checkout/pickup-branch-selector";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";


async function getPickupOptions(): Promise<PickupBranchOption[] | null> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${backendUrl}/api/v1/branches/pickup-options/`, {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        items: [{ sku: "MRC-FC-STD", quantity: 1 }],
      }),
    });
    if (!response.ok) return null;
    const body = (await response.json()) as { results: PickupBranchOption[] };
    return body.results;
  } catch {
    return null;
  }
}

export default async function CheckoutPage({
  searchParams,
}: {
  searchParams: Promise<{ pickup_branch?: string }>;
}) {
  const [options, params] = await Promise.all([getPickupOptions(), searchParams]);
  return (
    <main className="checkout-page">
      <PageHero
        eyebrow="Clinic pickup"
        title="Choose a"
        accentTitle="Pickup Branch"
        description="Pickup availability is checked against the unreserved stock required for every product in your basket."
        size="compact"
      />
      <section className="checkout-page__content" aria-label="Pickup branch selection">
        {!options ? (
          <EmptyState title="Pickup availability could not be checked" description="Please try again. A branch cannot be selected until stock has been verified." action={<ButtonLink href="/checkout">Try again</ButtonLink>} />
        ) : options.length === 0 ? (
          <EmptyState title="Pickup is currently unavailable" description="No active branch can currently fulfil this basket." />
        ) : (
          <PickupBranchSelector options={options} initialBranchCode={params.pickup_branch} />
        )}
        <p className="checkout-page__development-note">Development preview basket: one Marcelito Face Cream. The full cart will supply these items during the cart and checkout stages.</p>
      </section>
    </main>
  );
}

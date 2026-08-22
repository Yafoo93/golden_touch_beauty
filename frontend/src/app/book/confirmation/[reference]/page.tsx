import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import { formatGhanaCedis } from "@/lib/formatters";
import { requireAuthenticated } from "@/lib/server-auth";

type BookingConfirmation = {
  reference: string;
  branch_name: string;
  status: string;
  preferred_start: string;
  total_duration_minutes: number;
  total_amount: string;
  pricing_status: "final" | "estimate";
  recipient_name: string;
  payment_method: string;
  payment_status: string;
  services: Array<{
    id: string;
    service_name: string;
    option_name: string;
    unit_price: string;
    duration_minutes: number;
  }>;
};

type LoadResult =
  | { status: "success"; booking: BookingConfirmation }
  | { status: "missing" }
  | { status: "error" };

export const metadata: Metadata = {
  title: "Booking Request Received",
  description: "Review your Golden Touch booking request and reference.",
};

async function loadBooking(reference: string): Promise<LoadResult> {
  const backendUrl = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  const cookieHeader = (await cookies()).toString();

  try {
    const response = await fetch(
      `${backendUrl}/api/v1/bookings/${encodeURIComponent(reference)}/`,
      {
        cache: "no-store",
        headers: { Accept: "application/json", Cookie: cookieHeader },
        signal: AbortSignal.timeout(30_000),
      },
    );
    if (response.status === 404) return { status: "missing" };
    if (!response.ok) return { status: "error" };
    return {
      status: "success",
      booking: (await response.json()) as BookingConfirmation,
    };
  } catch {
    return { status: "error" };
  }
}

export default async function BookingConfirmationPage({
  params,
}: {
  params: Promise<{ reference: string }>;
}) {
  const { reference } = await params;
  const returnTo = `/book/confirmation/${encodeURIComponent(reference)}`;
  await requireAuthenticated(returnTo);
  const result = await loadBooking(reference);

  return (
    <main className="booking-confirmation-page">
      <PageHero
        eyebrow="Request received"
        title="Your Booking"
        accentTitle="Is With Us"
        description="Keep your reference safe while the selected branch reviews your preferred appointment time."
        size="compact"
      />
      <section className="booking-confirmation-page__content">
        {result.status === "missing" ? (
          <EmptyState
            title="Booking request not found"
            description="This reference is invalid or does not belong to your account."
            action={<ButtonLink href="/account">View your account</ButtonLink>}
          />
        ) : result.status === "error" ? (
          <EmptyState
            title="Booking request could not be loaded"
            description="Your booking has not been changed. Please try loading the confirmation again."
            action={<ButtonLink href={returnTo}>Try again</ButtonLink>}
          />
        ) : (
          <article className="booking-confirmation">
            <header className="booking-confirmation__header">
              <span aria-hidden="true">✓</span>
              <div>
                <p>Booking reference</p>
                <h1>{result.booking.reference}</h1>
              </div>
              <strong>{result.booking.status.replaceAll("_", " ")}</strong>
            </header>

            <div className="booking-confirmation__notice">
              <h2>Your request is awaiting branch review</h2>
              <p>
                This page confirms that Golden Touch received your request. The
                appointment is not final until the branch confirms the time or
                you accept a proposed alternative.
              </p>
            </div>

            <dl className="booking-flow__summary">
              <div>
                <dt>Branch</dt>
                <dd>{result.booking.branch_name}</dd>
              </div>
              <div>
                <dt>Preferred date and time</dt>
                <dd>
                  {new Intl.DateTimeFormat("en-GH", {
                    dateStyle: "full",
                    timeStyle: "short",
                    timeZone: "Africa/Accra",
                  }).format(new Date(result.booking.preferred_start))}
                </dd>
              </div>
              <div>
                <dt>Recipient</dt>
                <dd>{result.booking.recipient_name}</dd>
              </div>
              {result.booking.services.map((service) => (
                <div key={service.id}>
                  <dt>
                    {service.service_name}
                    {service.option_name ? ` — ${service.option_name}` : ""}
                    <small>
                      {service.duration_minutes} minutes
                    </small>
                  </dt>
                  <dd>{formatGhanaCedis(service.unit_price)}</dd>
                </div>
              ))}
              <div>
                <dt>Total duration</dt>
                <dd>{result.booking.total_duration_minutes} minutes</dd>
              </div>
              <div>
                <dt>{result.booking.pricing_status === "estimate" ? "Starting estimate" : "Total"}</dt>
                <dd>{formatGhanaCedis(result.booking.total_amount)}</dd>
              </div>
              {result.booking.pricing_status === "estimate" ? <div><dt>Final price</dt><dd>Management will confirm it before payment is requested.</dd></div> : null}
              <div>
                <dt>Payment</dt>
                <dd>
                  {result.booking.payment_method === "clinic"
                    ? "Pay at clinic"
                    : "Online payment"}{" "}
                  · {result.booking.payment_status.replaceAll("_", " ")}
                </dd>
              </div>
            </dl>

            <p className="booking-confirmation__email-note">
              A copy of this request is sent to the email address on your
              account when transactional email is configured.
            </p>
            <div className="booking-confirmation__actions">
              <ButtonLink href="/account">View account</ButtonLink>
              <ButtonLink href="/services" variant="outline">
                Browse services
              </ButtonLink>
              <ButtonLink href="/contact" variant="black">
                Contact the branch
              </ButtonLink>
            </div>
          </article>
        )}
      </section>
    </main>
  );
}

import type { Metadata } from "next";
import { cookies } from "next/headers";

import { AppointmentProposalActions } from "@/components/account/appointment-proposal-actions";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementBooking } from "@/lib/management-bookings";
import { requireAuthenticated } from "@/lib/server-auth";


export const metadata: Metadata = { title: "Appointment Details" };

type CustomerAppointment = Omit<ManagementBooking, "history"> & {
  history: {
    id: string;
    action: string;
    from_status: string;
    to_status: string;
    created_at: string;
  }[];
};

type LoadResult =
  | { status: "success"; booking: CustomerAppointment }
  | { status: "missing" }
  | { status: "error" };

async function loadAppointment(reference: string): Promise<LoadResult> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  try {
    const response = await fetch(
      `${base}/api/v1/bookings/${encodeURIComponent(reference)}/`,
      {
        cache: "no-store",
        headers: { Cookie: (await cookies()).toString(), Accept: "application/json" },
        signal: AbortSignal.timeout(20_000),
      },
    );
    if (response.status === 404) return { status: "missing" };
    return response.ok
      ? { status: "success", booking: await response.json() as CustomerAppointment }
      : { status: "error" };
  } catch {
    return { status: "error" };
  }
}

function displayTime(value: string) {
  return new Intl.DateTimeFormat("en-GH", {
    dateStyle: "full",
    timeStyle: "short",
    timeZone: "Africa/Accra",
  }).format(new Date(value));
}

const statusMessages: Record<string, string> = {
  pending: "The selected branch is reviewing this appointment request.",
  proposed: "The branch proposed a different time and is waiting for your response.",
  confirmed: "Your appointment time has been confirmed.",
  rescheduled: "Your appointment is confirmed for its updated time.",
  checked_in: "You have been checked in at the branch.",
  in_progress: "Your service is currently in progress.",
  completed: "This appointment has been completed.",
  cancelled: "This appointment was cancelled.",
  no_show: "This appointment was recorded as a no-show.",
  rejected: "The branch could not accept this appointment request.",
};

export default async function AccountAppointmentDetailPage({
  params,
}: {
  params: Promise<{ reference: string }>;
}) {
  const { reference } = await params;
  const returnTo = `/account/appointments/${encodeURIComponent(reference)}`;
  await requireAuthenticated(returnTo);
  const result = await loadAppointment(reference);

  if (result.status !== "success") {
    return (
      <main className="appointment-detail-page">
        <EmptyState
          title={result.status === "missing" ? "Appointment not found" : "Appointment could not be loaded"}
          description={result.status === "missing" ? "This reference is invalid or does not belong to your account." : "Your appointment has not been changed. Please try again."}
          action={<ButtonLink href={result.status === "missing" ? "/account/appointments" : returnTo}>{result.status === "missing" ? "Back to appointments" : "Try again"}</ButtonLink>}
        />
      </main>
    );
  }

  const booking = result.booking;
  const proposalExpired = booking.proposed_expires_at
    ? new Date(booking.proposed_expires_at).getTime() < Date.now()
    : false;

  return (
    <main className="appointment-detail-page">
      <header className="appointment-detail__header">
        <div><p>Appointment · {booking.status.replaceAll("_", " ")}</p><h1>{booking.reference}</h1><span>{statusMessages[booking.status] ?? "Review the latest appointment information below."}</span></div>
        <div><strong>{formatGhanaCedis(booking.total_amount)}</strong><span className={`booking-status booking-status--${booking.status}`}>{booking.status.replaceAll("_", " ")}</span></div>
      </header>

      {booking.status === "proposed" && booking.proposed_start ? (
        <section className="appointment-detail__proposal">
          <div><p>Action required</p><h2>Alternative appointment time</h2><strong>{displayTime(booking.proposed_start)}</strong><span>{proposalExpired ? "This proposal has expired. Contact the branch for assistance." : booking.proposed_expires_at ? `Respond before ${displayTime(booking.proposed_expires_at)}.` : "Accept or decline this proposed time."}</span></div>
          {!proposalExpired ? <AppointmentProposalActions reference={booking.reference} /> : null}
        </section>
      ) : null}

      <div className="appointment-detail__grid">
        <section>
          <h2>Appointment</h2>
          <dl><div><dt>Branch</dt><dd>{booking.branch_name}</dd></div><div><dt>Date and time</dt><dd>{displayTime(booking.preferred_start)}</dd></div><div><dt>Duration</dt><dd>{booking.total_duration_minutes} minutes</dd></div><div><dt>Recipient</dt><dd>{booking.recipient_name}</dd></div></dl>
        </section>
        <section>
          <h2>Payment</h2>
          <dl><div><dt>Amount</dt><dd>{formatGhanaCedis(booking.total_amount)}</dd></div><div><dt>Method</dt><dd>{booking.payment_method === "clinic" ? "Pay at clinic" : "Online payment"}</dd></div><div><dt>Status</dt><dd>{booking.payment_status.replaceAll("_", " ")}</dd></div></dl>
        </section>
        <section className="appointment-detail__services">
          <h2>Services</h2>
          {booking.services.map((service) => (
            <article key={service.id}><div><strong>{service.service_name}</strong>{service.option_name ? <span>{service.option_name}</span> : null}<small>{service.duration_minutes} minutes</small></div><b>{formatGhanaCedis(service.unit_price)}</b></article>
          ))}
        </section>
        <section className="appointment-detail__history">
          <h2>Appointment history</h2>
          {booking.history.length ? <ol>{booking.history.map((entry) => (
            <li key={entry.id}><span aria-hidden="true" /><div><strong>{entry.action.replaceAll("_", " ")}</strong><p>{entry.from_status ? `${entry.from_status.replaceAll("_", " ")} → ` : ""}{entry.to_status.replaceAll("_", " ")}</p><time dateTime={entry.created_at}>{displayTime(entry.created_at)}</time></div></li>
          ))}</ol> : <p>No history entries are available yet.</p>}
        </section>
      </div>

      <section className="appointment-detail__actions">
        <h2>Available actions</h2>
        <div><ButtonLink href="/account/appointments" variant="outline">All appointments</ButtonLink><ButtonLink href="/book">Book another service</ButtonLink><ButtonLink href="/contact" variant="black">Contact branch</ButtonLink></div>
        <p>For cancellation or changes that are not shown above, contact the branch. This prevents accidental changes outside the approved booking policy.</p>
      </section>
    </main>
  );
}

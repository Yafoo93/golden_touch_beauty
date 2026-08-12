import type { Metadata } from "next";
import { cookies } from "next/headers";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { PaginatedResponse } from "@/lib/branches";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementBooking } from "@/lib/management-bookings";
import { requireAuthenticated } from "@/lib/server-auth";


export const metadata: Metadata = { title: "My Appointments" };

const statuses = [
  "pending", "proposed", "confirmed", "rescheduled", "checked_in",
  "in_progress", "completed", "cancelled", "no_show", "rejected",
] as const;

const statusLabels: Record<string, string> = {
  pending: "Pending",
  proposed: "Proposed changes",
  confirmed: "Confirmed",
  rescheduled: "Rescheduled",
  checked_in: "Checked in",
  in_progress: "In progress",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No-show",
  rejected: "Rejected",
};

type AppointmentFilters = { status?: string; page?: string };
type LoadResult =
  | { status: "success"; page: PaginatedResponse<ManagementBooking> }
  | { status: "error" };

async function loadAppointments(filters: AppointmentFilters): Promise<LoadResult> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  if (filters.status && statuses.includes(filters.status as typeof statuses[number])) {
    query.set("status", filters.status);
  }
  if (filters.page) query.set("page", filters.page);
  try {
    const response = await fetch(`${base}/api/v1/bookings/?${query}`, {
      cache: "no-store",
      headers: { Cookie: (await cookies()).toString(), Accept: "application/json" },
      signal: AbortSignal.timeout(20_000),
    });
    return response.ok
      ? { status: "success", page: await response.json() as PaginatedResponse<ManagementBooking> }
      : { status: "error" };
  } catch {
    return { status: "error" };
  }
}

function appointmentsHref(statusValue: string, page?: number) {
  const query = new URLSearchParams();
  if (statusValue) query.set("status", statusValue);
  if (page && page > 1) query.set("page", String(page));
  return `/account/appointments${query.size ? `?${query}` : ""}`;
}

export default async function AccountAppointmentsPage({
  searchParams,
}: {
  searchParams: Promise<AppointmentFilters>;
}) {
  await requireAuthenticated("/account/appointments");
  const filters = await searchParams;
  const selectedStatus = statuses.includes(filters.status as typeof statuses[number])
    ? filters.status ?? ""
    : "";
  const result = await loadAppointments({ ...filters, status: selectedStatus });
  const page = result.status === "success" ? result.page : null;
  const currentPage = Math.max(1, Number.parseInt(filters.page ?? "1", 10) || 1);
  const grouped = new Map<string, ManagementBooking[]>();
  for (const booking of page?.results ?? []) {
    grouped.set(booking.status, [...(grouped.get(booking.status) ?? []), booking]);
  }

  return (
    <main className="account-appointments-page">
      <header className="account-appointments-page__header">
        <div><p>Customer account</p><h1>My appointments</h1><span>Review every service appointment and its current status.</span></div>
        <div><ButtonLink href="/account" variant="outline" size="small">Account overview</ButtonLink><ButtonLink href="/book" size="small">Book appointment</ButtonLink></div>
      </header>

      <nav className="account-appointment-filters" aria-label="Filter appointments by status">
        <Link href="/account/appointments" aria-current={!selectedStatus ? "page" : undefined}>All</Link>
        {statuses.map((statusValue) => (
          <Link href={appointmentsHref(statusValue)} key={statusValue} aria-current={selectedStatus === statusValue ? "page" : undefined}>{statusLabels[statusValue]}</Link>
        ))}
      </nav>

      {result.status === "error" ? (
        <EmptyState title="Appointments could not be loaded" description="The booking service could not be reached. Please try again." action={<ButtonLink href={appointmentsHref(selectedStatus)}>Try again</ButtonLink>} />
      ) : !page || page.results.length === 0 ? (
        <EmptyState title={selectedStatus ? `No ${statusLabels[selectedStatus].toLowerCase()} appointments` : "No appointments yet"} description={selectedStatus ? "Choose another status to review your other appointments." : "Your bookings will appear here after you request an appointment."} action={selectedStatus ? <ButtonLink href="/account/appointments" variant="outline">View all appointments</ButtonLink> : <ButtonLink href="/book">Book an appointment</ButtonLink>} />
      ) : (
        <div className="account-appointment-groups">
          {statuses.filter((statusValue) => grouped.has(statusValue)).map((statusValue) => (
            <section key={statusValue}>
              <header><h2>{statusLabels[statusValue]}</h2><span>{grouped.get(statusValue)?.length} shown</span></header>
              <div>{grouped.get(statusValue)?.map((booking) => (
                <article key={booking.id}>
                  <div><small>{booking.reference} · {booking.branch_name}</small><h3>{booking.services.map((item) => item.service_name).join(", ")}</h3><p>{new Date(booking.preferred_start).toLocaleString()} · {booking.total_duration_minutes} minutes</p></div>
                  <div><strong>{formatGhanaCedis(booking.total_amount)}</strong><span className={`booking-status booking-status--${booking.status}`}>{statusLabels[booking.status] ?? booking.status.replaceAll("_", " ")}</span><ButtonLink href={`/account/appointments/${booking.reference}`} variant="outline" size="small">View appointment</ButtonLink></div>
                </article>
              ))}</div>
            </section>
          ))}
        </div>
      )}

      {page && (page.previous || page.next) ? (
        <nav className="management-pagination" aria-label="Appointment pages">
          {page.previous ? <ButtonLink href={appointmentsHref(selectedStatus, currentPage - 1)} variant="outline" size="small">Previous</ButtonLink> : <span />}
          <span>Page {currentPage} · {page.count} appointments</span>
          {page.next ? <ButtonLink href={appointmentsHref(selectedStatus, currentPage + 1)} variant="outline" size="small">Next</ButtonLink> : <span />}
        </nav>
      ) : null}
    </main>
  );
}

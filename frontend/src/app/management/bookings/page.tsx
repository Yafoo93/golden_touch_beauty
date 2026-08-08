import { cookies } from "next/headers";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { PaginatedResponse } from "@/lib/branches";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementBooking } from "@/lib/management-bookings";

type BookingFilters = {
  branch?: string;
  status?: string;
  page?: string;
};

type BookingLoadResult =
  | { status: "success"; page: PaginatedResponse<ManagementBooking> }
  | { status: "denied" }
  | { status: "error" };

async function loadBookings(filters: BookingFilters): Promise<BookingLoadResult> {
  const base = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  const query = new URLSearchParams();
  if (filters.branch) query.set("branch", filters.branch);
  if (filters.status) query.set("status", filters.status);
  if (filters.page) query.set("page", filters.page);

  try {
    const response = await fetch(
      `${base}/api/v1/bookings/management/all/?${query.toString()}`,
      {
        cache: "no-store",
        headers: {
          Cookie: (await cookies()).toString(),
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(20_000),
      },
    );
    if (response.status === 401 || response.status === 403) {
      return { status: "denied" };
    }
    if (!response.ok) return { status: "error" };

    return {
      status: "success",
      page: (await response.json()) as PaginatedResponse<ManagementBooking>,
    };
  } catch {
    return { status: "error" };
  }
}

function pageHref(filters: BookingFilters, page: number) {
  const query = new URLSearchParams();
  if (filters.branch) query.set("branch", filters.branch);
  if (filters.status) query.set("status", filters.status);
  query.set("page", String(page));
  return `/management/bookings?${query.toString()}`;
}

export default async function ManagementBookingsPage({
  searchParams,
}: {
  searchParams: Promise<BookingFilters>;
}) {
  const filters = await searchParams;
  const result = await loadBookings(filters);
  const currentPage = Math.max(1, Number.parseInt(filters.page ?? "1", 10) || 1);
  const bookingPage = result.status === "success" ? result.page : null;

  return (
    <main className="management-page">
      <header className="management-page__header">
        <div>
          <p>Management · Appointments</p>
          <h1>Bookings</h1>
          <span>
            Approve requests, propose times, and follow every appointment
            through completion.
          </span>
        </div>
        <div className="management-page__summary">
          <strong>{bookingPage?.count ?? 0} accessible bookings</strong>
          <ButtonLink href="/management/bookings/new" size="small">
            Assisted booking
          </ButtonLink>
          <ButtonLink
            href="/management/booking-blocks"
            variant="outline"
            size="small"
          >
            Manage blocks
          </ButtonLink>
        </div>
      </header>

      <form className="management-booking-filters">
        <label>
          Branch code
          <input
            name="branch"
            defaultValue={filters.branch}
            placeholder="e.g. MAKOLA"
          />
        </label>
        <label>
          Status
          <select name="status" defaultValue={filters.status ?? ""}>
            <option value="">All statuses</option>
            {[
              "pending",
              "proposed",
              "confirmed",
              "checked_in",
              "in_progress",
              "completed",
              "cancelled",
              "rescheduled",
              "no_show",
              "rejected",
            ].map((value) => (
              <option value={value} key={value}>
                {value.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Apply filters</button>
        {filters.branch || filters.status ? (
          <ButtonLink href="/management/bookings" variant="outline" size="small">
            Clear filters
          </ButtonLink>
        ) : null}
      </form>

      {result.status === "denied" ? (
        <EmptyState
          title="Booking access required"
          description="Use the owner account or a staff account assigned to the relevant branch."
        />
      ) : result.status === "error" ? (
        <EmptyState
          title="Bookings could not be loaded"
          description="The booking service could not be reached. Try again rather than assuming the list is empty."
          action={
            <ButtonLink href="/management/bookings">Try again</ButtonLink>
          }
        />
      ) : result.page.results.length === 0 ? (
        <EmptyState
          title={filters.branch || filters.status ? "No matching bookings" : "No bookings yet"}
          description={
            filters.branch || filters.status
              ? "Clear or change the filters to see other bookings available to your account."
              : "New website and assisted bookings will appear here."
          }
          action={
            filters.branch || filters.status ? (
              <ButtonLink href="/management/bookings">Clear filters</ButtonLink>
            ) : undefined
          }
        />
      ) : (
        <>
          <div className="management-booking-list">
            {result.page.results.map((booking) => (
              <Link
                href={`/management/bookings/${booking.reference}`}
                key={booking.id}
              >
                <article>
                  <div>
                    <small>
                      {booking.reference} · {booking.branch_name}
                    </small>
                    <h2>{booking.recipient_name}</h2>
                    <p>
                      {booking.services
                        .map((item) => item.service_name)
                        .join(", ")}
                    </p>
                  </div>
                  <div>
                    <strong>
                      {new Date(booking.preferred_start).toLocaleString()}
                    </strong>
                    <span
                      className={`booking-status booking-status--${booking.status}`}
                    >
                      {booking.status.replaceAll("_", " ")}
                    </span>
                    <b>{formatGhanaCedis(booking.total_amount)}</b>
                  </div>
                </article>
              </Link>
            ))}
          </div>
          {result.page.previous || result.page.next ? (
            <nav className="management-pagination" aria-label="Booking pages">
              {result.page.previous ? (
                <ButtonLink
                  href={pageHref(filters, currentPage - 1)}
                  variant="outline"
                  size="small"
                >
                  Previous
                </ButtonLink>
              ) : <span />}
              <span>Page {currentPage}</span>
              {result.page.next ? (
                <ButtonLink
                  href={pageHref(filters, currentPage + 1)}
                  variant="outline"
                  size="small"
                >
                  Next
                </ButtonLink>
              ) : <span />}
            </nav>
          ) : null}
        </>
      )}
    </main>
  );
}

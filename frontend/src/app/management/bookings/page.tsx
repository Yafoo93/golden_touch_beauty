import { cookies } from "next/headers";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementBooking } from "@/lib/management-bookings";

async function loadBookings(filters: { branch?: string; status?: string }): Promise<ManagementBooking[] | null> {
  try {
    const base = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
    const query = new URLSearchParams();
    if (filters.branch) query.set("branch", filters.branch);
    if (filters.status) query.set("status", filters.status);
    const response = await fetch(`${base}/api/v1/bookings/management/all/?${query.toString()}`, {
      cache: "no-store",
      headers: { Cookie: (await cookies()).toString(), Accept: "application/json" },
    });
    return response.ok ? (await response.json()) as ManagementBooking[] : null;
  } catch { return null; }
}

export default async function ManagementBookingsPage({ searchParams }: { searchParams: Promise<{ branch?: string; status?: string }> }) {
  const filters = await searchParams;
  const bookings = await loadBookings(filters);
  return (
    <main className="management-page">
      <header className="management-page__header">
        <div><p>Management · Appointments</p><h1>Bookings</h1><span>Approve requests, propose times, and follow every appointment through completion.</span></div>
        <div className="management-page__summary"><strong>{bookings?.length ?? 0} visible bookings</strong><ButtonLink href="/management/bookings/new" size="small">Assisted booking</ButtonLink><ButtonLink href="/management/booking-blocks" variant="outline" size="small">Manage blocks</ButtonLink></div>
      </header>
      <form className="management-booking-filters">
        <label>Branch code<input name="branch" defaultValue={filters.branch} placeholder="e.g. MAKOLA" /></label>
        <label>Status<select name="status" defaultValue={filters.status ?? ""}><option value="">All statuses</option>{["pending", "proposed", "confirmed", "checked_in", "in_progress", "completed", "cancelled", "rescheduled", "no_show", "rejected"].map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
        <button type="submit">Apply filters</button>
      </form>
      {!bookings ? <EmptyState title="Bookings could not be loaded" description="Sign in with authorized management access and confirm Django is running." /> :
      !bookings.length ? <EmptyState title="No bookings yet" description="New website and assisted bookings will appear here." /> :
      <div className="management-booking-list">{bookings.map((booking) => (
        <Link href={`/management/bookings/${booking.reference}`} key={booking.id}>
          <article><div><small>{booking.reference} · {booking.branch_name}</small><h2>{booking.recipient_name}</h2><p>{booking.services.map((item) => item.service_name).join(", ")}</p></div><div><strong>{new Date(booking.preferred_start).toLocaleString()}</strong><span>{booking.status.replaceAll("_", " ")}</span><b>{formatGhanaCedis(booking.total_amount)}</b></div></article>
        </Link>
      ))}</div>}
    </main>
  );
}

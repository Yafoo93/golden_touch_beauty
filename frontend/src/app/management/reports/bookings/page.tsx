import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { requirePortalAccess } from "@/lib/server-auth";
import { ReportExportActions } from "@/components/management/report-export-actions";

export const metadata: Metadata = { title: "Bookings Report | Management" };

type Filters = { date_from?: string; date_to?: string; branch?: string; status?: string; source?: string };
type Breakdown = { count: number; value: string };
type Report = {
  filters: Required<Filters>;
  branches: { id: string; code: string; name: string }[];
  choices: { statuses: { value: string; label: string }[]; sources: { value: string; label: string }[] };
  summary: { booking_count: number; active_count: number; completed_count: number; cancelled_count: number; cancellation_rate: string; no_show_count: number; no_show_rate: string; rejected_count: number; booked_value: string; average_value: string; total_duration_minutes: number };
  by_status: ({ status: string } & Breakdown)[];
  by_source: ({ source: string } & Breakdown)[];
  daily: ({ date: string; cancelled_count: number; no_show_count: number } & Breakdown)[];
  by_branch: ({ branch_id: string; branch_name: string } & Breakdown)[];
  bookings: { reference: string; branch_name: string; customer_name: string; preferred_start: string; status: string; source: string; payment_status: string; service_names: string[]; duration_minutes: number; amount: string }[];
};

const label = (value: string) => value.replaceAll("_", " ");

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  try {
    const response = await fetch(`${base}/api/v1/reports/bookings/?${query}`, {
      cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000),
    });
    if (!response.ok) return null;
    return await response.json() as Report;
  } catch { return null; }
}

export default async function ManagementBookingsReportPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const user = await requirePortalAccess("management", "/management/reports/bookings");
  if (!user.management_modules.includes("reports")) redirect("/management");
  const report = await loadReport(await searchParams);

  return <main className="management-sales-report">
    <header><div><p>Management / Reports</p><h1>Bookings report</h1><span>Appointment demand and operational activity within your permitted branches.</span></div><ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink></header>
    {!report ? <EmptyState title="Bookings report unavailable" description="The report could not be loaded. Check the selected filters and try again." action={<ButtonLink href="/management/reports/bookings">Reset report</ButtonLink>} /> : <>
      <form className="management-sales-report__filters management-bookings-report__filters">
        <label>From<input type="date" name="date_from" defaultValue={report.filters.date_from} /></label>
        <label>To<input type="date" name="date_to" defaultValue={report.filters.date_to} /></label>
        <label>Branch<select name="branch" defaultValue={report.filters.branch}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
        <label>Status<select name="status" defaultValue={report.filters.status}><option value="">All statuses</option>{report.choices.statuses.map((choice) => <option value={choice.value} key={choice.value}>{choice.label}</option>)}</select></label>
        <label>Source<select name="source" defaultValue={report.filters.source}><option value="">All sources</option>{report.choices.sources.map((choice) => <option value={choice.value} key={choice.value}>{choice.label}</option>)}</select></label>
        <button type="submit">Apply filters</button><ButtonLink href="/management/reports/bookings" variant="outline" size="small">Reset</ButtonLink>
      </form>
      <ReportExportActions report="bookings" filters={report.filters} />
      <p className="management-report-note"><strong>Rate formulas:</strong> cancellation rate = cancelled appointments / total appointments × 100; no-show rate = no-show appointments / total appointments × 100. All figures respect the selected filters and permitted branches.</p>
      <section className="management-sales-report__metrics" aria-label="Bookings summary">
        <article><span>Appointment volume</span><strong>{report.summary.booking_count}</strong></article>
        <article><span>Active bookings</span><strong>{report.summary.active_count}</strong></article>
        <article><span>Completed</span><strong>{report.summary.completed_count}</strong></article>
        <article><span>Cancelled</span><strong>{report.summary.cancelled_count}</strong><small>{report.summary.cancellation_rate}% cancellation rate</small></article>
        <article><span>No-shows</span><strong>{report.summary.no_show_count}</strong><small>{report.summary.no_show_rate}% no-show rate</small></article>
        <article><span>Rejected</span><strong>{report.summary.rejected_count}</strong></article>
        <article><span>Booked value</span><strong>{formatGhanaCedis(report.summary.booked_value)}</strong></article>
        <article><span>Average booking</span><strong>{formatGhanaCedis(report.summary.average_value)}</strong></article>
        <article><span>Scheduled hours</span><strong>{(report.summary.total_duration_minutes / 60).toFixed(1)}</strong></article>
      </section>
      <div className="management-sales-report__breakdowns">
        <section><h2>By status</h2>{report.by_status.length ? report.by_status.map((item) => <article key={item.status}><div><strong>{label(item.status)}</strong><small>{item.count} booking{item.count === 1 ? "" : "s"}</small></div><b>{formatGhanaCedis(item.value)}</b></article>) : <p>No status activity in this period.</p>}</section>
        <section><h2>By source</h2>{report.by_source.length ? report.by_source.map((item) => <article key={item.source}><div><strong>{label(item.source)}</strong><small>{item.count} booking{item.count === 1 ? "" : "s"}</small></div><b>{formatGhanaCedis(item.value)}</b></article>) : <p>No source activity in this period.</p>}</section>
      </div>
      <section className="management-sales-report__daily"><h2>Daily appointments</h2>{report.daily.length ? <div>{report.daily.map((day) => <article key={day.date}><time dateTime={day.date}>{new Date(`${day.date}T00:00:00`).toLocaleDateString()}</time><span>{day.count} appointment{day.count === 1 ? "" : "s"}</span><small>{day.cancelled_count} cancelled / {day.no_show_count} no-show</small><strong>{formatGhanaCedis(day.value)}</strong></article>)}</div> : <p>No bookings fall within this period.</p>}</section>
      <section className="management-sales-report__transactions"><h2>Booking details</h2>{report.bookings.length ? <div className="management-table-wrap"><table><thead><tr><th>Date</th><th>Reference</th><th>Customer / service</th><th>Branch</th><th>Source</th><th>Status</th><th>Payment</th><th>Amount</th></tr></thead><tbody>{report.bookings.map((booking) => <tr key={booking.reference}><td>{new Date(booking.preferred_start).toLocaleString()}</td><td><ButtonLink href={`/management/bookings/${booking.reference}`} variant="outline" size="small">{booking.reference}</ButtonLink></td><td><strong>{booking.customer_name}</strong><small>{booking.service_names.join(", ") || "Service not recorded"} / {booking.duration_minutes} min</small></td><td>{booking.branch_name}</td><td>{label(booking.source)}</td><td>{label(booking.status)}</td><td>{label(booking.payment_status)}</td><td>{formatGhanaCedis(booking.amount)}</td></tr>)}</tbody></table></div> : <p>No bookings match the selected filters.</p>}</section>
    </>}
  </main>;
}

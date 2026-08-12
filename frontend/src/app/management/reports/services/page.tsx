import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { requirePortalAccess } from "@/lib/server-auth";
import { ReportExportActions } from "@/components/management/report-export-actions";

export const metadata: Metadata = { title: "Services Report | Management" };
type Filters = { date_from?: string; date_to?: string; branch?: string; source?: string; status?: string; service?: string };
type Report = {
  filters: Required<Filters>;
  branches: { id: string; name: string }[];
  services: { id: string; name: string }[];
  statuses: { value: string; label: string }[];
  summary: { service_count: number; distinct_services: number; revenue: string; average_value: string; completed_bookings: number; duration_minutes: number };
  popular_services: { rank: number; id: string; name: string; service_count: number; booking_count: number; pos_count: number; revenue: string }[];
  daily: { date: string; booking_count: number; pos_count: number; revenue: string }[];
  performance: { id: string; name: string; booking_count: number; pos_count: number; service_count: number; booking_revenue: string; pos_revenue: string; revenue: string; average_value: string; duration_minutes: number; completed_count: number }[];
};

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  try {
    const response = await fetch(`${base}/api/v1/reports/services/?${query}`, { cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000) });
    if (!response.ok) return null;
    return await response.json() as Report;
  } catch { return null; }
}

export default async function ManagementServicesReportPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const user = await requirePortalAccess("management", "/management/reports/services");
  if (!user.management_modules.includes("reports")) redirect("/management");
  const report = await loadReport(await searchParams);
  return <main className="management-sales-report">
    <header><div><p>Management / Reports</p><h1>Services report</h1><span>Appointment demand and recognized service revenue within your permitted branches.</span></div><ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink></header>
    {!report ? <EmptyState title="Services report unavailable" description="The report could not be loaded. Check the selected filters and try again." action={<ButtonLink href="/management/reports/services">Reset report</ButtonLink>} /> : <>
      <form className="management-sales-report__filters management-services-report__filters">
        <label>From<input type="date" name="date_from" defaultValue={report.filters.date_from} /></label><label>To<input type="date" name="date_to" defaultValue={report.filters.date_to} /></label>
        <label>Branch<select name="branch" defaultValue={report.filters.branch}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
        <label>Source<select name="source" defaultValue={report.filters.source}><option value="all">Bookings and POS</option><option value="booking">Bookings only</option><option value="pos">POS only</option></select></label>
        <label>Booking status<select name="status" defaultValue={report.filters.status}><option value="">All statuses</option>{report.statuses.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
        <label>Service<select name="service" defaultValue={report.filters.service}><option value="">All available services</option>{report.services.map((service) => <option key={service.id} value={service.id}>{service.name}</option>)}</select></label>
        <button type="submit">Apply filters</button><ButtonLink href="/management/reports/services" variant="outline" size="small">Reset</ButtonLink>
      </form>
      <ReportExportActions report="services" filters={report.filters} />
      {report.filters.status ? <p className="management-report-note">A booking status is selected, so POS-only service lines are excluded from these results.</p> : null}
      <p className="management-report-note"><strong>Revenue formula:</strong> fully paid, non-cancelled booking service prices plus service lines from completed POS sales. Unpaid booking prices remain in demand counts but are not reported as revenue.</p>
      <section className="management-sales-report__metrics" aria-label="Service report summary"><article><span>Services delivered/booked</span><strong>{report.summary.service_count}</strong></article><article><span>Distinct services</span><strong>{report.summary.distinct_services}</strong></article><article><span>Service revenue</span><strong>{formatGhanaCedis(report.summary.revenue)}</strong></article><article><span>Revenue per service activity</span><strong>{formatGhanaCedis(report.summary.average_value)}</strong></article><article><span>Completed bookings</span><strong>{report.summary.completed_bookings}</strong></article><article><span>Scheduled hours</span><strong>{(report.summary.duration_minutes / 60).toFixed(1)}</strong></article></section>
      <section className="management-sales-report__transactions"><h2>Popular services</h2><p className="management-report-note">Ranked by total booking and POS service occurrences; revenue breaks ties.</p>{report.popular_services.length ? <div className="management-table-wrap"><table><thead><tr><th>Rank</th><th>Service</th><th>Bookings</th><th>POS</th><th>Total activity</th><th>Revenue</th></tr></thead><tbody>{report.popular_services.map((service) => <tr key={service.id}><td>#{service.rank}</td><td><strong>{service.name}</strong></td><td>{service.booking_count}</td><td>{service.pos_count}</td><td>{service.service_count}</td><td>{formatGhanaCedis(service.revenue)}</td></tr>)}</tbody></table></div> : <p>No service activity falls within this period.</p>}</section>
      <section className="management-sales-report__daily"><h2>Daily service activity</h2>{report.daily.length ? <div>{report.daily.map((day) => <article key={day.date}><time dateTime={day.date}>{new Date(`${day.date}T00:00:00`).toLocaleDateString()}</time><span>{day.booking_count} booked / {day.pos_count} POS</span><small>Recognized service revenue</small><strong>{formatGhanaCedis(day.revenue)}</strong></article>)}</div> : <p>No service activity falls within this period.</p>}</section>
      <section className="management-sales-report__transactions"><h2>Service performance</h2>{report.performance.length ? <div className="management-table-wrap"><table><thead><tr><th>Service</th><th>Bookings</th><th>POS</th><th>Total</th><th>Booking revenue</th><th>POS revenue</th><th>Total revenue</th><th>Average</th><th>Hours booked</th><th>Completed</th></tr></thead><tbody>{report.performance.map((service) => <tr key={service.id}><td><strong>{service.name}</strong></td><td>{service.booking_count}</td><td>{service.pos_count}</td><td>{service.service_count}</td><td>{formatGhanaCedis(service.booking_revenue)}</td><td>{formatGhanaCedis(service.pos_revenue)}</td><td>{formatGhanaCedis(service.revenue)}</td><td>{formatGhanaCedis(service.average_value)}</td><td>{(service.duration_minutes / 60).toFixed(1)}</td><td>{service.completed_count}</td></tr>)}</tbody></table></div> : <p>No services match the selected filters.</p>}</section>
    </>}
  </main>;
}

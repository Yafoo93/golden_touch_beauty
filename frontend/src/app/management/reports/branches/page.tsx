import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { requirePortalAccess } from "@/lib/server-auth";
import { ReportExportActions } from "@/components/management/report-export-actions";

export const metadata: Metadata = { title: "Branches Report | Management" };
type Filters = { date_from?: string; date_to?: string; branch?: string; sort?: string };
type Report = {
  filters: Required<Filters>;
  branches: { id: string; name: string }[];
  summary: { branch_count: number; total_sales: string; booking_count: number; booking_value: string; payments_collected: string; product_revenue: string; product_gross_profit: string; service_revenue: string; estimated_operating_result: string; stock_available: number };
  performance: { branch_id: string; branch_code: string; branch_name: string; online_sales: string; pos_sales: string; total_sales: string; sales_share_percent: string; booking_count: number; booking_value: string; completed_bookings: number; cancelled_bookings: number; cancellation_rate: string; no_show_bookings: number; no_show_rate: string; product_units: number; product_revenue: string; product_cost: string; product_gross_profit: string; service_count: number; service_revenue: string; estimated_operating_result: string; payments_collected: string; stock_available: number; low_stock_count: number; out_of_stock_count: number }[];
};

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  try {
    const response = await fetch(`${base}/api/v1/reports/branches/?${query}`, { cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000) });
    if (!response.ok) return null;
    return await response.json() as Report;
  } catch { return null; }
}

export default async function ManagementBranchesReportPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const user = await requirePortalAccess("management", "/management/reports/branches");
  if (!user.management_modules.includes("reports")) redirect("/management");
  const report = await loadReport(await searchParams);
  return <main className="management-sales-report">
    <header><div><p>Management / Reports</p><h1>Branches report</h1><span>Cross-operational performance within your permitted branch scope.</span></div><ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink></header>
    {!report ? <EmptyState title="Branches report unavailable" description="The report could not be loaded. Check the selected filters and try again." action={<ButtonLink href="/management/reports/branches">Reset report</ButtonLink>} /> : <>
      <form className="management-sales-report__filters">
        <label>From<input type="date" name="date_from" defaultValue={report.filters.date_from} /></label><label>To<input type="date" name="date_to" defaultValue={report.filters.date_to} /></label>
        <label>Branch<select name="branch" defaultValue={report.filters.branch}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
        <label>Sort by<select name="sort" defaultValue={report.filters.sort}><option value="revenue">Sales revenue</option><option value="bookings">Booking volume</option><option value="payments">Collected payments</option><option value="name">Branch name</option></select></label>
        <button type="submit">Apply filters</button><ButtonLink href="/management/reports/branches" variant="outline" size="small">Reset</ButtonLink>
      </form>
      <ReportExportActions report="branches" filters={report.filters} />
      <p className="management-report-note">Activity values use the selected dates. Service revenue includes fully paid, non-cancelled bookings and completed POS service lines. Product profit uses sale-time costs. Available and low-stock figures show the current inventory position.</p>
      <p className="management-report-note"><strong>Estimate warning:</strong> Estimated operating result = product gross profit + recognized service revenue. It is not net profit because service consumables, labour, commissions, delivery costs, rent, utilities, taxes, and other operating expenses are not yet captured.</p>
      <section className="management-sales-report__metrics" aria-label="Branch report summary"><article><span>Branches shown</span><strong>{report.summary.branch_count}</strong></article><article><span>Total sales</span><strong>{formatGhanaCedis(report.summary.total_sales)}</strong></article><article><span>Bookings</span><strong>{report.summary.booking_count}</strong></article><article><span>Booking value</span><strong>{formatGhanaCedis(report.summary.booking_value)}</strong></article><article><span>Payments collected</span><strong>{formatGhanaCedis(report.summary.payments_collected)}</strong></article><article><span>Product revenue</span><strong>{formatGhanaCedis(report.summary.product_revenue)}</strong></article><article><span>Product gross profit</span><strong>{formatGhanaCedis(report.summary.product_gross_profit)}</strong></article><article><span>Service revenue</span><strong>{formatGhanaCedis(report.summary.service_revenue)}</strong></article><article><span>Estimated operating result</span><strong>{formatGhanaCedis(report.summary.estimated_operating_result)}</strong><small>Estimate — incomplete service and operating costs</small></article><article><span>Available stock</span><strong>{report.summary.stock_available}</strong></article></section>
      <section className="management-branch-comparison" aria-label="Branch comparison">{report.performance.length ? report.performance.map((branch) => <article key={branch.branch_id}>
        <header><div><p>{branch.branch_code}</p><h2>{branch.branch_name}</h2></div><ButtonLink href={`/management/branches/${branch.branch_id}`} variant="outline" size="small">View branch</ButtonLink></header>
        <dl><div><dt>Total sales</dt><dd>{formatGhanaCedis(branch.total_sales)}</dd><small>{branch.sales_share_percent}% of compared sales · Online {formatGhanaCedis(branch.online_sales)} / POS {formatGhanaCedis(branch.pos_sales)}</small></div><div><dt>Bookings</dt><dd>{branch.booking_count}</dd><small>{branch.completed_bookings} completed · {branch.cancelled_bookings} cancelled ({branch.cancellation_rate}%) · {branch.no_show_bookings} no-show ({branch.no_show_rate}%)</small></div><div><dt>Products</dt><dd>{branch.product_units} units</dd><small>Revenue {formatGhanaCedis(branch.product_revenue)} · GP {formatGhanaCedis(branch.product_gross_profit)}</small></div><div><dt>Services</dt><dd>{branch.service_count}</dd><small>Revenue {formatGhanaCedis(branch.service_revenue)}</small></div><div><dt>Estimated operating result</dt><dd>{formatGhanaCedis(branch.estimated_operating_result)}</dd><small>Estimate — service and operating costs incomplete</small></div><div><dt>Payments collected</dt><dd>{formatGhanaCedis(branch.payments_collected)}</dd></div><div><dt>Available stock</dt><dd>{branch.stock_available}</dd><small>{branch.low_stock_count} low / {branch.out_of_stock_count} out</small></div></dl>
      </article>) : <EmptyState title="No branch activity" description="No permitted branches match the selected filters." />}</section>
    </>}
  </main>;
}

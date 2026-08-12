import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { requirePortalAccess } from "@/lib/server-auth";
import { ReportExportActions } from "@/components/management/report-export-actions";

export const metadata: Metadata = { title: "Sales Report | Management" };

type Filters = { date_from?: string; date_to?: string; branch?: string; source?: string; interval?: string };
type Report = {
  filters: { date_from: string; date_to: string; branch: string; source: string; interval: "daily" | "weekly" | "monthly" };
  branches: { id: string; code: string; name: string }[];
  summary: { total_revenue: string; online_revenue: string; pos_revenue: string; transaction_count: number; online_count: number; pos_count: number; online_share_percent: string; pos_share_percent: string; online_average_sale: string; pos_average_sale: string; average_sale: string };
  daily: { date: string; online: string; pos: string; total: string; count: number }[];
  trend: { period_start: string; interval: "daily" | "weekly" | "monthly"; online: string; pos: string; total: string; count: number }[];
  by_branch: { branch_id: string; branch_name: string; online: string; pos: string; total: string; count: number }[];
  payment_methods: { method: string; amount: string; count: number }[];
  transactions: { reference: string; source: "online" | "pos"; branch_name: string; customer_name: string; occurred_at: string; status: string; amount: string; cashier_name?: string }[];
};

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  try {
    const response = await fetch(`${base}/api/v1/reports/sales/?${query}`, {
      cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000),
    });
    if (!response.ok) return null;
    return await response.json() as Report;
  } catch { return null; }
}

export default async function ManagementSalesReportPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const user = await requirePortalAccess("management", "/management/reports/sales");
  if (!user.management_modules.includes("reports")) redirect("/management");
  const report = await loadReport(await searchParams);
  return <main className="management-sales-report">
    <header><div><p>Management / Reports</p><h1>Sales report</h1><span>Paid online orders and completed POS sales within your permitted branches.</span></div><ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink></header>
    {!report ? <EmptyState title="Sales report unavailable" description="The report could not be loaded. Check the selected filters and try again." action={<ButtonLink href="/management/reports/sales">Reset report</ButtonLink>} /> : <>
      <form className="management-sales-report__filters management-sales-interval__filters">
        <label>From<input type="date" name="date_from" defaultValue={report.filters.date_from} /></label><label>To<input type="date" name="date_to" defaultValue={report.filters.date_to} /></label>
        <label>Branch<select name="branch" defaultValue={report.filters.branch}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
        <label>Source<select name="source" defaultValue={report.filters.source}><option value="all">Online and POS</option><option value="online">Online orders</option><option value="pos">POS sales</option></select></label>
        <label>Interval<select name="interval" defaultValue={report.filters.interval}><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></label>
        <button type="submit">Apply filters</button><ButtonLink href="/management/reports/sales" variant="outline" size="small">Reset</ButtonLink>
      </form>
      <ReportExportActions report="sales" filters={report.filters} />
      <p className="management-report-note"><strong>Sales formula:</strong> paid, non-cancelled online orders plus completed POS sales. Online orders use their payment date; POS sales use their completion date.</p>
      <section className="management-sales-report__metrics" aria-label="Sales summary"><article><span>Total revenue</span><strong>{formatGhanaCedis(report.summary.total_revenue)}</strong></article><article><span>Online revenue</span><strong>{formatGhanaCedis(report.summary.online_revenue)}</strong><small>{report.summary.online_count} orders · {report.summary.online_share_percent}% share</small></article><article><span>POS revenue</span><strong>{formatGhanaCedis(report.summary.pos_revenue)}</strong><small>{report.summary.pos_count} sales · {report.summary.pos_share_percent}% share</small></article><article><span>Transactions</span><strong>{report.summary.transaction_count}</strong></article><article><span>Average sale</span><strong>{formatGhanaCedis(report.summary.average_sale)}</strong></article><article><span>Average online order</span><strong>{formatGhanaCedis(report.summary.online_average_sale)}</strong></article><article><span>Average POS sale</span><strong>{formatGhanaCedis(report.summary.pos_average_sale)}</strong></article></section>
      <div className="management-sales-report__breakdowns">
        <section><h2>Revenue by branch</h2>{report.by_branch.length ? report.by_branch.map((branch) => <article key={branch.branch_id}><div><strong>{branch.branch_name}</strong><small>{branch.count} transaction{branch.count === 1 ? "" : "s"} / Online {formatGhanaCedis(branch.online)} / POS {formatGhanaCedis(branch.pos)}</small></div><b>{formatGhanaCedis(branch.total)}</b></article>) : <p>No branch revenue in this period.</p>}</section>
        <section><h2>Payment methods</h2>{report.payment_methods.length ? report.payment_methods.map((method) => <article key={method.method}><div><strong>{method.method.replaceAll("_", " ")}</strong><small>{method.count} payment entr{method.count === 1 ? "y" : "ies"}</small></div><b>{formatGhanaCedis(method.amount)}</b></article>) : <p>No successful payment entries in this period.</p>}</section>
      </div>
      <section className="management-sales-report__daily"><h2>{report.filters.interval[0].toUpperCase() + report.filters.interval.slice(1)} sales</h2>{report.trend.length ? <div>{report.trend.map((period) => <article key={period.period_start}><time dateTime={period.period_start}>{report.filters.interval === "monthly" ? new Date(`${period.period_start}T00:00:00`).toLocaleDateString(undefined, { month: "long", year: "numeric" }) : report.filters.interval === "weekly" ? `Week of ${new Date(`${period.period_start}T00:00:00`).toLocaleDateString()}` : new Date(`${period.period_start}T00:00:00`).toLocaleDateString()}</time><span>{period.count} sale{period.count === 1 ? "" : "s"}</span><small>Online {formatGhanaCedis(period.online)} / POS {formatGhanaCedis(period.pos)}</small><strong>{formatGhanaCedis(period.total)}</strong></article>)}</div> : <p>No sales occurred in this period.</p>}</section>
      <section className="management-sales-report__transactions"><h2>Transactions</h2>{report.transactions.length ? <div className="management-table-wrap"><table><thead><tr><th>Date</th><th>Reference</th><th>Source</th><th>Branch</th><th>Customer</th><th>Status</th><th>Amount</th></tr></thead><tbody>{report.transactions.map((sale) => <tr key={`${sale.source}:${sale.reference}`}><td>{new Date(sale.occurred_at).toLocaleString()}</td><td><strong>{sale.reference}</strong></td><td>{sale.source === "pos" ? "POS" : "Online"}</td><td>{sale.branch_name}</td><td>{sale.customer_name}{sale.cashier_name ? <small>Cashier: {sale.cashier_name}</small> : null}</td><td>{sale.status.replaceAll("_", " ")}</td><td>{formatGhanaCedis(sale.amount)}</td></tr>)}</tbody></table></div> : <p>No transactions match the selected filters.</p>}</section>
    </>}
  </main>;
}

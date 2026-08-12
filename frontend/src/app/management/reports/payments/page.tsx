import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { requirePortalAccess } from "@/lib/server-auth";
import { ReportExportActions } from "@/components/management/report-export-actions";

export const metadata: Metadata = { title: "Payments Report | Management" };
type Filters = { date_from?: string; date_to?: string; branch?: string; source?: string; status?: string; method?: string; provider?: string };
type Report = {
  filters: Required<Filters>;
  branches: { id: string; name: string }[];
  choices: { statuses: string[]; methods: string[]; providers: string[] };
  summary: { payment_count: number; successful_count: number; successful_amount: string; pending_count: number; failed_count: number; refunded_count: number; refunded_amount: string; net_collected: string };
  by_status: { status: string; count: number; amount: string }[];
  by_method: { method: string; attempted_count: number; successful_count: number; collected_amount: string; refunded_amount: string; net_collected: string; online_amount: string; pos_amount: string }[];
  daily: { date: string; online: string; pos: string; total: string; count: number }[];
  payments: { reference: string; source: string; source_type: string; source_reference: string; branch_name: string; customer_name: string; provider: string; method: string; status: string; amount: string; occurred_at: string; cashier_name?: string }[];
};
const label = (value: string) => value.replaceAll("_", " ");

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  try {
    const response = await fetch(`${base}/api/v1/reports/payments/?${query}`, { cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000) });
    if (!response.ok) return null;
    return await response.json() as Report;
  } catch { return null; }
}

export default async function ManagementPaymentsReportPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const user = await requirePortalAccess("management", "/management/reports/payments");
  if (!user.management_modules.includes("reports")) redirect("/management");
  const report = await loadReport(await searchParams);
  return <main className="management-sales-report">
    <header><div><p>Management / Reports</p><h1>Payments report</h1><span>Online and POS payment reconciliation within your permitted branches.</span></div><ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink></header>
    {!report ? <EmptyState title="Payments report unavailable" description="The report could not be loaded. Check the selected filters and try again." action={<ButtonLink href="/management/reports/payments">Reset report</ButtonLink>} /> : <>
      <form className="management-sales-report__filters management-payments-report__filters">
        <label>From<input type="date" name="date_from" defaultValue={report.filters.date_from} /></label><label>To<input type="date" name="date_to" defaultValue={report.filters.date_to} /></label>
        <label>Branch<select name="branch" defaultValue={report.filters.branch}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
        <label>Source<select name="source" defaultValue={report.filters.source}><option value="all">Online and POS</option><option value="online">Online</option><option value="pos">POS</option></select></label>
        <label>Status<select name="status" defaultValue={report.filters.status}><option value="">All statuses</option>{report.choices.statuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}</select></label>
        <label>Method<select name="method" defaultValue={report.filters.method}><option value="">All methods</option>{report.choices.methods.map((value) => <option value={value} key={value}>{label(value)}</option>)}</select></label>
        <label>Provider<select name="provider" defaultValue={report.filters.provider}><option value="">All providers</option>{report.choices.providers.map((value) => <option value={value} key={value}>{label(value)}</option>)}</select></label>
        <button type="submit">Apply filters</button><ButtonLink href="/management/reports/payments" variant="outline" size="small">Reset</ButtonLink>
      </form>
      <ReportExportActions report="payments" filters={report.filters} />
      <p className="management-report-note"><strong>Method-total formula:</strong> net collected = successful payment amounts − refunded payment amounts. Pending, failed, and cancelled attempts are counted but never included in collected totals.</p>
      <section className="management-sales-report__metrics" aria-label="Payment report summary"><article><span>Payment entries</span><strong>{report.summary.payment_count}</strong></article><article><span>Successful</span><strong>{report.summary.successful_count}</strong></article><article><span>Gross collected</span><strong>{formatGhanaCedis(report.summary.successful_amount)}</strong></article><article><span>Pending</span><strong>{report.summary.pending_count}</strong></article><article><span>Failed / cancelled</span><strong>{report.summary.failed_count}</strong></article><article><span>Refunded</span><strong>{formatGhanaCedis(report.summary.refunded_amount)}</strong></article><article><span>Net collected</span><strong>{formatGhanaCedis(report.summary.net_collected)}</strong></article></section>
      <div className="management-sales-report__breakdowns">
        <section><h2>By status</h2>{report.by_status.length ? report.by_status.map((item) => <article key={item.status}><div><strong>{label(item.status)}</strong><small>{item.count} entr{item.count === 1 ? "y" : "ies"}</small></div><b>{formatGhanaCedis(item.amount)}</b></article>) : <p>No status activity in this period.</p>}</section>
        <section><h2>Payment-method totals</h2>{report.by_method.length ? report.by_method.map((item) => <article key={item.method}><div><strong>{label(item.method)}</strong><small>{item.successful_count} successful / {item.attempted_count} attempted</small><small>Online {formatGhanaCedis(item.online_amount)} / POS {formatGhanaCedis(item.pos_amount)}</small>{Number(item.refunded_amount) ? <small>Refunded {formatGhanaCedis(item.refunded_amount)}</small> : null}</div><b>{formatGhanaCedis(item.net_collected)}</b></article>) : <p>No payment methods in this period.</p>}</section>
      </div>
      <section className="management-sales-report__daily"><h2>Daily collected payments</h2>{report.daily.length ? <div>{report.daily.map((day) => <article key={day.date}><time dateTime={day.date}>{new Date(`${day.date}T00:00:00`).toLocaleDateString()}</time><span>{day.count} payment entr{day.count === 1 ? "y" : "ies"}</span><small>Online {formatGhanaCedis(day.online)} / POS {formatGhanaCedis(day.pos)}</small><strong>{formatGhanaCedis(day.total)}</strong></article>)}</div> : <p>No payment activity falls within this period.</p>}</section>
      <section className="management-sales-report__transactions"><h2>Payment activity</h2>{report.payments.length ? <div className="management-table-wrap"><table><thead><tr><th>Date</th><th>Payment reference</th><th>Source reference</th><th>Customer</th><th>Branch</th><th>Provider / method</th><th>Status</th><th>Amount</th></tr></thead><tbody>{report.payments.map((payment) => <tr key={`${payment.source}:${payment.reference}`}><td>{new Date(payment.occurred_at).toLocaleString()}</td><td><strong>{payment.reference}</strong><small>{payment.source}</small></td><td>{payment.source_reference}<small>{label(payment.source_type)}</small></td><td>{payment.customer_name}{payment.cashier_name ? <small>Cashier: {payment.cashier_name}</small> : null}</td><td>{payment.branch_name}</td><td>{label(payment.provider)}<small>{label(payment.method)}</small></td><td><span className={`payment-report-status payment-report-status--${payment.status}`}>{label(payment.status)}</span></td><td>{formatGhanaCedis(payment.amount)}</td></tr>)}</tbody></table></div> : <p>No payments match the selected filters.</p>}</section>
    </>}
  </main>;
}

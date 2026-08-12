import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";

export const metadata: Metadata = { title: "End of Day | POS" };
type Filters = { date?: string; branch?: string };
type Report = { date: string; scope: "team" | "cashier"; branches: { id: string; code: string; name: string }[]; selected_branch: string | null; summary: { sale_count: number; item_count: number; gross_total: string; payment_total: string; difference: string }; payment_methods: { method: string; sale_count: number; amount: string }[]; cashiers: { cashier_id: string | null; cashier_name: string; sale_count: number; item_count: number; amount: string }[] };

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  if (filters.date) query.set("date", filters.date);
  if (filters.branch) query.set("branch", filters.branch);
  try {
    const response = await fetch(`${base}/api/v1/pos/end-of-day/?${query}`, { cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000) });
    return response.ok ? await response.json() as Report : null;
  } catch { return null; }
}

export default async function POSEndOfDayPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const filters = await searchParams;
  const report = await loadReport(filters);
  return <main className="pos-end-of-day">
    <header><div><p>Point of sale · Reconciliation</p><h1>End of day</h1><span>Completed-sale totals and successful payment methods for the selected trading day.</span></div><div><ButtonLink href="/pos/sales" variant="outline">Sale history</ButtonLink><ButtonLink href="/pos">New sale</ButtonLink></div></header>
    {!report ? <EmptyState title="End-of-day report unavailable" description="The POS reconciliation data could not be reached. Please try again." action={<ButtonLink href="/pos/end-of-day">Try again</ButtonLink>} /> : <>
      <form className="pos-end-of-day__filters"><label>Trading date<input type="date" name="date" defaultValue={filters.date ?? report.date} /></label><label>Branch<select name="branch" defaultValue={filters.branch ?? ""}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label><button type="submit">View totals</button></form>
      <p className="pos-end-of-day__scope">Showing {report.scope === "team" ? "all permitted cashier activity" : "only your cashier activity"} for {report.date}.</p>
      <section className="pos-end-of-day__metrics" aria-label="End-of-day totals"><article><span>Completed sales</span><strong>{report.summary.sale_count}</strong></article><article><span>Items sold</span><strong>{report.summary.item_count}</strong></article><article><span>Gross sales</span><strong>{formatGhanaCedis(report.summary.gross_total)}</strong></article><article><span>Payments recorded</span><strong>{formatGhanaCedis(report.summary.payment_total)}</strong></article><article className={Number(report.summary.difference) === 0 ? "is-balanced" : "is-warning"}><span>Reconciliation difference</span><strong>{formatGhanaCedis(report.summary.difference)}</strong></article></section>
      <div className="pos-end-of-day__tables">
        <section><header><h2>Payment methods</h2></header>{report.payment_methods.length ? <div>{report.payment_methods.map((method) => <article key={method.method}><div><strong>{method.method.replaceAll("_", " ")}</strong><small>{method.sale_count} sale{method.sale_count === 1 ? "" : "s"}</small></div><b>{formatGhanaCedis(method.amount)}</b></article>)}</div> : <EmptyState title="No payments" description="No successful POS payments were recorded for this selection." />}</section>
        <section><header><h2>Cashier totals</h2></header>{report.cashiers.length ? <div>{report.cashiers.map((cashier) => <article key={cashier.cashier_id ?? "unassigned"}><div><strong>{cashier.cashier_name}</strong><small>{cashier.sale_count} sales · {cashier.item_count} items</small></div><b>{formatGhanaCedis(cashier.amount)}</b></article>)}</div> : <EmptyState title="No completed sales" description="No completed POS sales were recorded for this selection." />}</section>
      </div>
    </>}
  </main>;
}

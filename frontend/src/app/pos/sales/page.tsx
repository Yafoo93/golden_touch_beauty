import type { Metadata } from "next";
import { cookies } from "next/headers";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";

export const metadata: Metadata = { title: "Sale History | POS" };

type Filters = { branch?: string; status?: string; date_from?: string; date_to?: string; search?: string; page?: string };
type Sale = { id: string; reference: string; branch_id: string; branch_code: string; branch_name: string; cashier_name: string; customer_name: string; status: string; status_label: string; payment_status: string; currency: string; total_amount: string; item_count: number; completed_at: string | null; created_at: string };
type Page = { count: number; next: string | null; previous: string | null; results: Sale[] };
type Branch = { id: string; code: string; name: string };

async function load(filters: Filters): Promise<{ sales: Page; branches: Branch[] } | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  const headers = { Accept: "application/json", Cookie: (await cookies()).toString() };
  try {
    const [salesResponse, workspaceResponse] = await Promise.all([
      fetch(`${base}/api/v1/pos/sales/?${query}`, { cache: "no-store", headers, signal: AbortSignal.timeout(20_000) }),
      fetch(`${base}/api/v1/pos/workspace/`, { cache: "no-store", headers, signal: AbortSignal.timeout(20_000) }),
    ]);
    if (!salesResponse.ok || !workspaceResponse.ok) return null;
    return { sales: await salesResponse.json() as Page, branches: (await workspaceResponse.json() as { branches: Branch[] }).branches };
  } catch { return null; }
}

export default async function POSSalesPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const filters = await searchParams;
  const result = await load(filters);
  const hasFilters = Object.values(filters).some(Boolean);
  return <main className="pos-history">
    <header><div><p>Point of sale · Records</p><h1>Sale history</h1><span>Review sales from branches available to your staff account.</span></div><ButtonLink href="/pos">New sale</ButtonLink></header>
    <form className="pos-history__filters">
      <label>Search<input type="search" name="search" defaultValue={filters.search ?? ""} placeholder="Reference, cashier or customer" /></label>
      <label>Branch<select name="branch" defaultValue={filters.branch ?? ""}><option value="">All permitted branches</option>{result?.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
      <label>Status<select name="status" defaultValue={filters.status ?? ""}><option value="">All statuses</option>{["draft", "completed", "voided", "refunded"].map((status) => <option value={status} key={status}>{status}</option>)}</select></label>
      <label>From<input type="date" name="date_from" defaultValue={filters.date_from ?? ""} /></label>
      <label>To<input type="date" name="date_to" defaultValue={filters.date_to ?? ""} /></label>
      <button type="submit">Apply</button>{hasFilters ? <ButtonLink href="/pos/sales" variant="outline" size="small">Clear</ButtonLink> : null}
    </form>
    {!result ? <EmptyState title="Sale history unavailable" description="The POS records could not be reached. Please try again." action={<ButtonLink href="/pos/sales">Try again</ButtonLink>} /> : result.sales.results.length === 0 ? <EmptyState title={hasFilters ? "No matching sales" : "No POS sales yet"} description={hasFilters ? "Change or clear the filters to review other sales." : "Completed in-clinic sales will appear here."} /> : <>
      <div className="pos-history__list">{result.sales.results.map((sale) => sale.status === "draft" ? <article key={sale.id}>
        <div><small>{sale.reference} · {sale.branch_name}</small><h2>{sale.customer_name}</h2><p>{sale.item_count} item{sale.item_count === 1 ? "" : "s"} · {sale.cashier_name}</p></div>
        <div><strong>{formatGhanaCedis(sale.total_amount)}</strong><span className={`booking-status booking-status--${sale.status}`}>{sale.status_label}</span><small>{new Date(sale.completed_at ?? sale.created_at).toLocaleString()}</small></div>
      </article> : <Link href={`/pos/sales/${sale.reference}`} key={sale.id}><article>
        <div><small>{sale.reference} · {sale.branch_name}</small><h2>{sale.customer_name}</h2><p>{sale.item_count} item{sale.item_count === 1 ? "" : "s"} · {sale.cashier_name}</p></div>
        <div><strong>{formatGhanaCedis(sale.total_amount)}</strong><span className={`booking-status booking-status--${sale.status}`}>{sale.status_label}</span><small>{new Date(sale.completed_at ?? sale.created_at).toLocaleString()}</small></div>
      </article></Link>)}</div>
      <p className="pos-history__count">{result.sales.count} permitted sale{result.sales.count === 1 ? "" : "s"}</p>
    </>}
  </main>;
}

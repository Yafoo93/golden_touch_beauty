import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { requirePortalAccess } from "@/lib/server-auth";
import { ReportExportActions } from "@/components/management/report-export-actions";

export const metadata: Metadata = { title: "Inventory Report | Management" };
type Filters = { date_from?: string; date_to?: string; branch?: string; category?: string; stock?: string; search?: string };
type Report = {
  filters: Required<Filters>;
  branches: { id: string; name: string }[];
  categories: { id: string; name: string }[];
  summary: { inventory_count: number; quantity_on_hand: number; quantity_reserved: number; quantity_available: number; cost_value: string; retail_value: string; low_stock_count: number; out_of_stock_count: number; movement_count: number; on_hand_change: number };
  movements_by_type: { type: string; count: number; on_hand_change: number; reserved_change: number }[];
  movements: { id: string; occurred_at: string; type: string; branch_name: string; product_name: string; variant_name: string; sku: string; on_hand_change: number; reserved_change: number; on_hand_after: number; reserved_after: number; reference_type: string; reference_id: string; note: string; performed_by: string }[];
  inventory: { variant_id: string; branch_name: string; product_name: string; variant_name: string; category_name: string; sku: string; quantity_on_hand: number; quantity_reserved: number; quantity_available: number; reorder_level: number; stock_state: string; cost_value: string; retail_value: string; movement_count: number; on_hand_change: number; reserved_change: number }[];
};
const label = (value: string) => value.replaceAll("_", " ");

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  try {
    const response = await fetch(`${base}/api/v1/reports/inventory/?${query}`, { cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000) });
    if (!response.ok) return null;
    return await response.json() as Report;
  } catch { return null; }
}

export default async function ManagementInventoryReportPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const user = await requirePortalAccess("management", "/management/reports/inventory");
  if (!user.management_modules.includes("reports")) redirect("/management");
  const report = await loadReport(await searchParams);
  return <main className="management-sales-report">
    <header><div><p>Management / Reports</p><h1>Inventory report</h1><span>Current stock position and dated movement activity within your permitted branches.</span></div><ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink></header>
    {!report ? <EmptyState title="Inventory report unavailable" description="The report could not be loaded. Check the selected filters and try again." action={<ButtonLink href="/management/reports/inventory">Reset report</ButtonLink>} /> : <>
      <form className="management-sales-report__filters management-services-report__filters">
        <label>Movement from<input type="date" name="date_from" defaultValue={report.filters.date_from} /></label><label>Movement to<input type="date" name="date_to" defaultValue={report.filters.date_to} /></label>
        <label>Branch<select name="branch" defaultValue={report.filters.branch}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
        <label>Category<select name="category" defaultValue={report.filters.category}><option value="">All categories</option>{report.categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select></label>
        <label>Stock health<select name="stock" defaultValue={report.filters.stock}><option value="all">All stock levels</option><option value="healthy">Healthy</option><option value="low">Low stock</option><option value="out">Out of stock</option></select></label>
        <label>Product or SKU<input name="search" defaultValue={report.filters.search} placeholder="Search inventory" /></label>
        <button type="submit">Apply filters</button><ButtonLink href="/management/reports/inventory" variant="outline" size="small">Reset</ButtonLink>
      </form>
      <ReportExportActions report="inventory" filters={report.filters} />
      <p className="management-report-note">Stock quantities and valuation show the current position. Movement totals use the selected date range.</p>
      <section className="management-sales-report__metrics" aria-label="Inventory report summary"><article><span>Inventory lines</span><strong>{report.summary.inventory_count}</strong></article><article><span>On hand</span><strong>{report.summary.quantity_on_hand}</strong></article><article><span>Reserved</span><strong>{report.summary.quantity_reserved}</strong></article><article><span>Available</span><strong>{report.summary.quantity_available}</strong></article><article><span>Available cost value</span><strong>{formatGhanaCedis(report.summary.cost_value)}</strong></article><article><span>Available retail value</span><strong>{formatGhanaCedis(report.summary.retail_value)}</strong></article><article><span>Low / out</span><strong>{report.summary.low_stock_count} / {report.summary.out_of_stock_count}</strong></article><article><span>Movement net change</span><strong>{report.summary.on_hand_change > 0 ? "+" : ""}{report.summary.on_hand_change}</strong></article></section>
      <section className="management-sales-report__daily"><h2>Movements by type</h2>{report.movements_by_type.length ? <div>{report.movements_by_type.map((movement) => <article key={movement.type}><strong>{label(movement.type)}</strong><span>{movement.count} movement{movement.count === 1 ? "" : "s"}</span><small>Reserved change: {movement.reserved_change > 0 ? "+" : ""}{movement.reserved_change}</small><strong>{movement.on_hand_change > 0 ? "+" : ""}{movement.on_hand_change}</strong></article>)}</div> : <p>No stock movements occurred in this period.</p>}</section>
      <section className="management-sales-report__transactions"><h2>Stock movement ledger</h2>{report.movements.length ? <div className="management-table-wrap"><table><thead><tr><th>Date</th><th>Product / SKU</th><th>Branch</th><th>Type</th><th>On-hand change</th><th>Reserved change</th><th>Balance after</th><th>Reference / note</th><th>Recorded by</th></tr></thead><tbody>{report.movements.map((movement) => <tr key={movement.id}><td>{new Date(movement.occurred_at).toLocaleString()}</td><td><strong>{movement.product_name}</strong><small>{movement.variant_name} / {movement.sku}</small></td><td>{movement.branch_name}</td><td>{label(movement.type)}</td><td>{movement.on_hand_change > 0 ? "+" : ""}{movement.on_hand_change}</td><td>{movement.reserved_change > 0 ? "+" : ""}{movement.reserved_change}</td><td>{movement.on_hand_after} on hand<small>{movement.reserved_after} reserved</small></td><td>{movement.reference_id || "—"}<small>{movement.reference_type ? `${label(movement.reference_type)} · ` : ""}{movement.note || "No note"}</small></td><td>{movement.performed_by}</td></tr>)}</tbody></table></div> : <p>No stock movements occurred in this period.</p>}</section>
      <section className="management-sales-report__transactions"><h2>Current inventory position</h2>{report.inventory.length ? <div className="management-table-wrap"><table><thead><tr><th>Product / SKU</th><th>Branch</th><th>Category</th><th>On hand</th><th>Reserved</th><th>Available</th><th>Reorder level</th><th>Cost value</th><th>Retail value</th><th>Period movement</th><th>Health</th></tr></thead><tbody>{report.inventory.map((item) => <tr key={`${item.branch_name}:${item.variant_id}`}><td><ButtonLink href={`/management/inventory/${item.variant_id}`} variant="outline" size="small">{item.product_name}</ButtonLink><small>{item.variant_name} / {item.sku}</small></td><td>{item.branch_name}</td><td>{item.category_name}</td><td>{item.quantity_on_hand}</td><td>{item.quantity_reserved}</td><td>{item.quantity_available}</td><td>{item.reorder_level}</td><td>{formatGhanaCedis(item.cost_value)}</td><td>{formatGhanaCedis(item.retail_value)}</td><td>{item.on_hand_change > 0 ? "+" : ""}{item.on_hand_change}<small>{item.movement_count} movement{item.movement_count === 1 ? "" : "s"}</small></td><td><span className={`report-stock-state report-stock-state--${item.stock_state}`}>{item.stock_state}</span></td></tr>)}</tbody></table></div> : <p>No inventory matches the selected filters.</p>}</section>
    </>}
  </main>;
}

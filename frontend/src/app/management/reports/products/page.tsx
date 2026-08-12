import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import { requirePortalAccess } from "@/lib/server-auth";
import { ReportExportActions } from "@/components/management/report-export-actions";

export const metadata: Metadata = { title: "Products Report | Management" };
type Filters = { date_from?: string; date_to?: string; branch?: string; source?: string; stock?: string };
type Report = {
  filters: Required<Filters>;
  branches: { id: string; name: string }[];
  summary: { product_count: number; units_sold: number; revenue: string; cost_of_goods: string; gross_profit: string; gross_margin_percent: string; average_unit_revenue: string; low_stock_count: number; out_of_stock_count: number };
  best_selling_products: { rank: number; name: string; variant: string; sku: string; units_sold: number; revenue: string }[];
  products: { name: string; variant: string; sku: string; online_units: number; pos_units: number; units_sold: number; online_revenue: string; pos_revenue: string; revenue: string; cost_of_goods: string; gross_profit: string; gross_margin_percent: string; stock_on_hand: number; stock_reserved: number; stock_available: number; reorder_level: number; stock_state: string }[];
};

async function loadReport(filters: Filters): Promise<Report | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
  try {
    const response = await fetch(`${base}/api/v1/reports/products/?${query}`, { cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000) });
    if (!response.ok) return null;
    return await response.json() as Report;
  } catch { return null; }
}

export default async function ManagementProductsReportPage({ searchParams }: { searchParams: Promise<Filters> }) {
  const user = await requirePortalAccess("management", "/management/reports/products");
  if (!user.management_modules.includes("reports")) redirect("/management");
  const report = await loadReport(await searchParams);
  return <main className="management-sales-report">
    <header><div><p>Management / Reports</p><h1>Products report</h1><span>Product sales performance and current inventory within your permitted branches.</span></div><ButtonLink href="/management/reports" variant="outline">All reports</ButtonLink></header>
    {!report ? <EmptyState title="Products report unavailable" description="The report could not be loaded. Check the selected filters and try again." action={<ButtonLink href="/management/reports/products">Reset report</ButtonLink>} /> : <>
      <form className="management-sales-report__filters management-bookings-report__filters">
        <label>From<input type="date" name="date_from" defaultValue={report.filters.date_from} /></label><label>To<input type="date" name="date_to" defaultValue={report.filters.date_to} /></label>
        <label>Branch<select name="branch" defaultValue={report.filters.branch}><option value="">All permitted branches</option>{report.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></label>
        <label>Sales source<select name="source" defaultValue={report.filters.source}><option value="all">Online and POS</option><option value="online">Online only</option><option value="pos">POS only</option></select></label>
        <label>Stock health<select name="stock" defaultValue={report.filters.stock}><option value="all">All stock levels</option><option value="low">Low stock</option><option value="out">Out of stock</option></select></label>
        <button type="submit">Apply filters</button><ButtonLink href="/management/reports/products" variant="outline" size="small">Reset</ButtonLink>
      </form>
      <ReportExportActions report="products" filters={report.filters} />
      <p className="management-report-note">Gross profit = product revenue minus sale-time product cost. Gross margin = gross profit divided by product revenue.</p>
      <section className="management-sales-report__metrics" aria-label="Products summary"><article><span>Products shown</span><strong>{report.summary.product_count}</strong></article><article><span>Units sold</span><strong>{report.summary.units_sold}</strong></article><article><span>Product revenue</span><strong>{formatGhanaCedis(report.summary.revenue)}</strong></article><article><span>Cost of goods sold</span><strong>{formatGhanaCedis(report.summary.cost_of_goods)}</strong></article><article><span>Gross profit</span><strong>{formatGhanaCedis(report.summary.gross_profit)}</strong></article><article><span>Gross margin</span><strong>{report.summary.gross_margin_percent}%</strong></article><article><span>Average per unit</span><strong>{formatGhanaCedis(report.summary.average_unit_revenue)}</strong></article><article><span>Low / out stock</span><strong>{report.summary.low_stock_count} / {report.summary.out_of_stock_count}</strong></article></section>
      <section className="management-sales-report__transactions"><h2>Best-selling products</h2><p className="management-report-note">Ranked by units sold across online orders and POS sales; revenue breaks ties.</p>{report.best_selling_products.length ? <div className="management-table-wrap"><table><thead><tr><th>Rank</th><th>Product</th><th>SKU</th><th>Units sold</th><th>Revenue</th></tr></thead><tbody>{report.best_selling_products.map((product) => <tr key={product.sku}><td>#{product.rank}</td><td><strong>{product.name}</strong><small>{product.variant}</small></td><td>{product.sku}</td><td>{product.units_sold}</td><td>{formatGhanaCedis(product.revenue)}</td></tr>)}</tbody></table></div> : <p>No product sales fall within this period.</p>}</section>
      <section className="management-sales-report__transactions"><h2>Product performance and stock</h2>{report.products.length ? <div className="management-table-wrap"><table><thead><tr><th>Product / SKU</th><th>Online</th><th>POS</th><th>Total units</th><th>Revenue</th><th>COGS</th><th>Gross profit</th><th>Margin</th><th>Available stock</th><th>Stock health</th></tr></thead><tbody>{report.products.map((product) => <tr key={product.sku}><td><strong>{product.name}</strong><small>{product.variant} / {product.sku}</small></td><td>{product.online_units}<small>{formatGhanaCedis(product.online_revenue)}</small></td><td>{product.pos_units}<small>{formatGhanaCedis(product.pos_revenue)}</small></td><td>{product.units_sold}</td><td>{formatGhanaCedis(product.revenue)}</td><td>{formatGhanaCedis(product.cost_of_goods)}</td><td>{formatGhanaCedis(product.gross_profit)}</td><td>{product.gross_margin_percent}%</td><td>{product.stock_available}<small>{product.stock_on_hand} on hand / {product.stock_reserved} reserved</small></td><td><span className={`report-stock-state report-stock-state--${product.stock_state}`}>{product.stock_state}</span></td></tr>)}</tbody></table></div> : <p>No products match the selected filters.</p>}</section>
    </>}
  </main>;
}

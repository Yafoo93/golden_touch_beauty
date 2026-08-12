import type { Metadata } from "next";
import { cookies } from "next/headers";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { PaginatedResponse } from "@/lib/branches";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CustomerOrder } from "@/lib/orders";
import { requireAuthenticated } from "@/lib/server-auth";

export const metadata: Metadata = { title: "My Orders" };

const statuses = [
  "awaiting_payment", "payment_under_review", "paid", "processing",
  "ready_for_pickup", "shipped", "delivered", "cancelled", "returned", "refunded",
] as const;

const statusLabels: Record<string, string> = {
  awaiting_payment: "Awaiting payment",
  payment_under_review: "Payment under review",
  paid: "Paid",
  processing: "Processing",
  ready_for_pickup: "Ready for pickup",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
  returned: "Returned",
  refunded: "Refunded",
};

type OrderFilters = { status?: string; page?: string };
type LoadResult =
  | { status: "success"; page: PaginatedResponse<CustomerOrder> }
  | { status: "error" };

async function loadOrders(filters: OrderFilters): Promise<LoadResult> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const query = new URLSearchParams();
  if (filters.status && statuses.includes(filters.status as typeof statuses[number])) query.set("status", filters.status);
  if (filters.page) query.set("page", filters.page);
  try {
    const response = await fetch(`${base}/api/v1/orders/?${query}`, {
      cache: "no-store",
      headers: { Cookie: (await cookies()).toString(), Accept: "application/json" },
      signal: AbortSignal.timeout(20_000),
    });
    return response.ok
      ? { status: "success", page: await response.json() as PaginatedResponse<CustomerOrder> }
      : { status: "error" };
  } catch {
    return { status: "error" };
  }
}

function ordersHref(statusValue: string, page?: number) {
  const query = new URLSearchParams();
  if (statusValue) query.set("status", statusValue);
  if (page && page > 1) query.set("page", String(page));
  return `/account/orders${query.size ? `?${query}` : ""}`;
}

export default async function AccountOrdersPage({ searchParams }: { searchParams: Promise<OrderFilters> }) {
  await requireAuthenticated("/account/orders");
  const filters = await searchParams;
  const selectedStatus = statuses.includes(filters.status as typeof statuses[number]) ? filters.status ?? "" : "";
  const result = await loadOrders({ ...filters, status: selectedStatus });
  const page = result.status === "success" ? result.page : null;
  const currentPage = Math.max(1, Number.parseInt(filters.page ?? "1", 10) || 1);
  const grouped = new Map<string, CustomerOrder[]>();
  for (const order of page?.results ?? []) grouped.set(order.status, [...(grouped.get(order.status) ?? []), order]);

  return (
    <main className="account-orders-page">
      <header className="account-orders-page__header">
        <div><p>Customer account</p><h1>My orders</h1><span>Review your product purchases, payments, and fulfilment progress.</span></div>
        <div><ButtonLink href="/account" variant="outline" size="small">Account overview</ButtonLink><ButtonLink href="/shop" size="small">Shop products</ButtonLink></div>
      </header>

      <nav className="account-order-filters" aria-label="Filter orders by status">
        <Link href="/account/orders" aria-current={!selectedStatus ? "page" : undefined}>All</Link>
        {statuses.map((value) => <Link href={ordersHref(value)} key={value} aria-current={selectedStatus === value ? "page" : undefined}>{statusLabels[value]}</Link>)}
      </nav>

      {result.status === "error" ? (
        <EmptyState title="Orders could not be loaded" description="The order service could not be reached. Please try again." action={<ButtonLink href={ordersHref(selectedStatus)}>Try again</ButtonLink>} />
      ) : !page || page.results.length === 0 ? (
        <EmptyState title={selectedStatus ? `No orders marked ${statusLabels[selectedStatus].toLowerCase()}` : "No product orders yet"} description={selectedStatus ? "Choose another status to review your other orders." : "Orders will appear here after you complete checkout."} action={selectedStatus ? <ButtonLink href="/account/orders" variant="outline">View all orders</ButtonLink> : <ButtonLink href="/shop">Shop products</ButtonLink>} />
      ) : (
        <div className="account-order-groups">
          {statuses.filter((value) => grouped.has(value)).map((value) => (
            <section key={value}>
              <header><h2>{statusLabels[value]}</h2><span>{grouped.get(value)?.length} shown</span></header>
              <div>{grouped.get(value)?.map((order) => (
                <article key={order.id}>
                  <div>
                    <small>{order.reference} · {order.branch_name} · {new Date(order.created_at).toLocaleDateString()}</small>
                    <h3>{order.items.map((item) => `${item.product_name} (${item.variant_name}) ×${item.quantity}`).join(", ")}</h3>
                    <p>{order.fulfillment_method === "pickup" ? "Clinic pickup" : "Delivery"} · Payment {order.payment_status.replaceAll("_", " ")}</p>
                  </div>
                  <div><strong>{formatGhanaCedis(order.total_amount)}</strong><span className={`order-status order-status--${order.status}`}>{statusLabels[order.status] ?? order.status.replaceAll("_", " ")}</span><ButtonLink href={`/account/orders/${encodeURIComponent(order.reference)}`} variant="outline" size="small">View order</ButtonLink></div>
                </article>
              ))}</div>
            </section>
          ))}
        </div>
      )}

      {page && (page.previous || page.next) ? (
        <nav className="management-pagination" aria-label="Order pages">
          {page.previous ? <ButtonLink href={ordersHref(selectedStatus, currentPage - 1)} variant="outline" size="small">Previous</ButtonLink> : <span />}
          <span>Page {currentPage} · {page.count} orders</span>
          {page.next ? <ButtonLink href={ordersHref(selectedStatus, currentPage + 1)} variant="outline" size="small">Next</ButtonLink> : <span />}
        </nav>
      ) : null}
    </main>
  );
}

import type { Metadata } from "next";
import { cookies } from "next/headers";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CustomerOrderDetail } from "@/lib/orders";
import { requireAuthenticated } from "@/lib/server-auth";

export const metadata: Metadata = { title: "Order Details" };

const labels: Record<string, string> = {
  awaiting_payment: "Awaiting payment", payment_under_review: "Payment under review",
  paid: "Paid", processing: "Processing", ready_for_pickup: "Ready for pickup",
  shipped: "Shipped", delivered: "Delivered", cancelled: "Cancelled",
  returned: "Returned", refunded: "Refunded",
};

async function loadOrder(reference: string): Promise<CustomerOrderDetail | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  try {
    const response = await fetch(`${base}/api/v1/orders/${encodeURIComponent(reference)}/`, {
      cache: "no-store",
      headers: { Cookie: (await cookies()).toString(), Accept: "application/json" },
      signal: AbortSignal.timeout(20_000),
    });
    return response.ok ? await response.json() as CustomerOrderDetail : null;
  } catch { return null; }
}

function trackingSteps(order: CustomerOrderDetail) {
  const delivery = order.fulfillment_method === "delivery";
  const normal = [
    ["awaiting_payment", "Order received"], ["paid", "Payment confirmed"],
    ["processing", "Preparing order"],
    [delivery ? "shipped" : "ready_for_pickup", delivery ? "Shipped" : "Ready for pickup"],
    ["delivered", delivery ? "Delivered" : "Collected"],
  ];
  const rank: Record<string, number> = { awaiting_payment: 0, payment_under_review: 0, paid: 1, processing: 2, ready_for_pickup: 3, shipped: 3, delivered: 4 };
  const current = rank[order.status] ?? -1;
  return normal.map(([key, label], index) => ({ key, label, reached: index <= current, current: index === current }));
}

export default async function AccountOrderDetailPage({ params }: { params: Promise<{ reference: string }> }) {
  const { reference } = await params;
  await requireAuthenticated(`/account/orders/${encodeURIComponent(reference)}`);
  const order = await loadOrder(reference);
  if (!order) return <main className="order-detail-page"><EmptyState title="Order not found" description="This order is unavailable or does not belong to your account." action={<ButtonLink href="/account/orders">Return to orders</ButtonLink>} /></main>;
  const receipt = order.payments.find((payment) => payment.receipt_reference)?.receipt_reference;
  const exceptional = ["cancelled", "returned", "refunded"].includes(order.status);

  return (
    <main className="order-detail-page">
      <header className="order-detail__header">
        <div><p>Product order</p><h1>{order.reference}</h1><span>Placed {new Date(order.created_at).toLocaleString()} at {order.branch_name}</span></div>
        <div><strong>{formatGhanaCedis(order.total_amount)}</strong><span className={`order-status order-status--${order.status}`}>{labels[order.status] ?? order.status.replaceAll("_", " ")}</span><ButtonLink href="/account/orders" variant="outline" size="small">All orders</ButtonLink></div>
      </header>

      <div className="order-detail__grid">
        <section className="order-detail__items"><h2>Items</h2>{order.items.map((item) => <article key={item.id ?? item.variant_id}><div><strong>{item.product_name}</strong><span>{item.variant_name} · SKU {item.sku} · Quantity {item.quantity}</span></div><strong>{formatGhanaCedis(item.line_total)}</strong></article>)}<dl><div><dt>Subtotal</dt><dd>{formatGhanaCedis(order.subtotal)}</dd></div><div><dt>Delivery fee</dt><dd>{formatGhanaCedis(order.delivery_fee)}</dd></div><div><dt>Total</dt><dd>{formatGhanaCedis(order.total_amount)}</dd></div></dl></section>

        <section><h2>Payment</h2><dl><div><dt>Status</dt><dd>{order.payment_status.replaceAll("_", " ")}</dd></div>{order.invoice_reference ? <div><dt>Invoice</dt><dd>{order.invoice_reference}</dd></div> : null}{order.payments.map((payment) => <div key={payment.reference}><dt>{payment.provider} · {payment.method || "Payment"}</dt><dd>{formatGhanaCedis(payment.amount)} · {payment.status}</dd></div>)}</dl>{receipt ? <ButtonLink href={`/account/receipts/${receipt}`} size="small">View payment receipt</ButtonLink> : <p>A payment receipt will appear after payment is verified.</p>}</section>

        <section><h2>Fulfilment</h2><dl><div><dt>Method</dt><dd>{order.fulfillment_method === "pickup" ? "Clinic pickup" : "Delivery"}</dd></div><div><dt>Branch</dt><dd>{order.branch_name}</dd></div><div><dt>Recipient</dt><dd>{order.recipient_name} · {order.recipient_phone}</dd></div>{order.delivery_address ? <div><dt>Address</dt><dd>{order.delivery_address}{order.delivery_city ? `, ${order.delivery_city}` : ""}</dd></div> : null}</dl>{order.delivery_notes ? <p>{order.delivery_notes}</p> : null}</section>

        <section className="order-detail__tracking"><h2>Tracking</h2>{exceptional ? <p className="order-detail__exception">This order is {labels[order.status]?.toLowerCase()}. Contact the branch if you need assistance.</p> : <ol>{trackingSteps(order).map((step) => <li key={step.key} data-reached={step.reached || undefined} aria-current={step.current ? "step" : undefined}><span aria-hidden="true" /><div><strong>{step.label}</strong>{step.current ? <small>Current status · updated {new Date(order.updated_at).toLocaleString()}</small> : null}</div></li>)}</ol>}</section>
      </div>
    </main>
  );
}

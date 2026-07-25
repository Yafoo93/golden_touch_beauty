"use client";

import { useEffect, useState } from "react";

import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { apiFetch } from "@/lib/api";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CustomerOrder } from "@/lib/orders";

export function OrderResult({ reference }: { reference: string }) {
  const [order, setOrder] = useState<CustomerOrder | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    apiFetch<CustomerOrder>(`orders/${encodeURIComponent(reference)}/`)
      .then(setOrder)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Order could not be loaded."));
  }, [reference]);
  if (error) return <EmptyState title="Order could not be loaded" description={error} action={<ButtonLink href="/account">Go to account</ButtonLink>} />;
  if (!order) return <p className="checkout-loading">Loading your order receipt…</p>;
  return <section className="order-result">
    <div className="order-result__mark" aria-hidden="true">✓</div>
    <p>Order reserved</p><h1>{order.reference}</h1>
    <span>Your order is awaiting secure payment. Its stock is held until {order.reservation_expires_at ? new Date(order.reservation_expires_at).toLocaleString() : "the reservation deadline"}.</span>
    <div className="order-result__receipt">
      <header><div><strong>Golden Touch Beauty Centre</strong><span>Order receipt / reservation</span></div><div><strong>{order.status.replaceAll("_", " ")}</strong><span>{new Date(order.created_at).toLocaleString()}</span></div></header>
      <dl><div><dt>Fulfillment</dt><dd>{order.fulfillment_method === "pickup" ? `Pickup at ${order.branch_name}` : `Delivery from ${order.branch_name}`}</dd></div><div><dt>Recipient</dt><dd>{order.recipient_name} · {order.recipient_phone}</dd></div>{order.delivery_address ? <div><dt>Address</dt><dd>{order.delivery_address}, {order.delivery_city}</dd></div> : null}</dl>
      {order.items.map((item) => <article key={item.id ?? item.variant_id}><span>{item.product_name} · {item.variant_name} × {item.quantity}</span><strong>{formatGhanaCedis(item.line_total)}</strong></article>)}
      <footer><span>Total</span><strong>{formatGhanaCedis(order.total_amount)}</strong></footer>
    </div>
    <div className="order-result__actions">
      <Button onClick={() => window.print()}>Print receipt</Button>
      <ButtonLink href="/shop" variant="outline">Continue shopping</ButtonLink>
      <ButtonLink href="/account" variant="black">View account</ButtonLink>
    </div>
    <small>The KoraPay hosted-payment action will be connected in Stage 11. Your reservation is not a completed sale until verified payment succeeds.</small>
  </section>;
}

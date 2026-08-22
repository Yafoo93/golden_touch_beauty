"use client";

import { useEffect, useState } from "react";

import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { apiFetch } from "@/lib/api";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CustomerOrder } from "@/lib/orders";

function readableStatus(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function OrderResult({ reference }: { reference: string }) {
  const [order, setOrder] = useState<CustomerOrder | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<CustomerOrder>(`orders/${encodeURIComponent(reference)}/`)
      .then(setOrder)
      .catch((caught) =>
        setError(
          caught instanceof Error ? caught.message : "Order could not be loaded.",
        ),
      );
  }, [reference]);

  if (error) {
    return (
      <EmptyState
        title="Order could not be loaded"
        description={error}
        action={<ButtonLink href="/account">Go to account</ButtonLink>}
      />
    );
  }

  if (!order) {
    return <p className="checkout-loading">Loading your order confirmation...</p>;
  }

  const reservationDeadline = order.reservation_expires_at
    ? new Date(order.reservation_expires_at).toLocaleString()
    : "the reservation deadline shown in your account";
  const isPaid = order.payment_status === "paid" || Boolean(order.paid_at);
  const preorderOnly = order.items.length > 0 && order.items.every((item) => item.is_preorder);

  return (
    <section className="order-result" aria-labelledby="order-confirmation-title">
      <div className="order-result__mark" aria-hidden="true">
        ✓
      </div>
      <p className="order-result__eyebrow">Order received</p>
      <h1 id="order-confirmation-title">{order.reference}</h1>
      <p>
        {isPaid
          ? "Your payment has been verified and your order is being processed."
          : preorderOnly
            ? "Your pre-order was received. Full payment is required before it is confirmed for future fulfillment."
            : `Your in-stock products are reserved until ${reservationDeadline}. Complete payment before then to keep the reservation.`}
      </p>

      <div className="order-result__receipt">
        <header>
          <div>
            <strong>Golden Touch Beauty Centre</strong>
            <span>Order confirmation</span>
          </div>
          <div>
            <strong>{readableStatus(order.status)}</strong>
            <span>{new Date(order.created_at).toLocaleString()}</span>
          </div>
        </header>
        <dl>
          <div>
            <dt>Payment</dt>
            <dd>{readableStatus(order.payment_status)}</dd>
          </div>
          <div>
            <dt>Fulfillment</dt>
            <dd>
              {order.fulfillment_method === "pickup"
                ? `Pickup at ${order.branch_name}`
                : `Delivery from ${order.branch_name}`}
            </dd>
          </div>
          <div>
            <dt>Recipient</dt>
            <dd>
              {order.recipient_name} · {order.recipient_phone}
            </dd>
          </div>
          {order.delivery_address ? (
            <div>
              <dt>Delivery address</dt>
              <dd>
                {order.delivery_address}
                {order.delivery_city ? `, ${order.delivery_city}` : ""}
              </dd>
            </div>
          ) : null}
        </dl>

        <div className="order-result__items" aria-label="Order items">
          {order.items.map((item) => (
            <article key={item.id ?? item.variant_id}>
              <span>
                {item.product_name} · {item.variant_name} × {item.quantity}
              </span>
              <strong>{formatGhanaCedis(item.line_total)}</strong>
            </article>
          ))}
        </div>
        <dl className="order-result__totals">
          <div>
            <dt>Subtotal</dt>
            <dd>{formatGhanaCedis(order.subtotal)}</dd>
          </div>
          <div>
            <dt>Delivery fee</dt>
            <dd>{formatGhanaCedis(order.delivery_fee)}</dd>
          </div>
        </dl>
        <footer>
          <span>Total</span>
          <strong>{formatGhanaCedis(order.total_amount)}</strong>
        </footer>
      </div>

      <div className="order-result__actions">
        <Button onClick={() => window.print()}>Print confirmation</Button>
        <ButtonLink href="/shop" variant="outline">
          Continue shopping
        </ButtonLink>
        <ButtonLink href="/account" variant="black">
          View my orders
        </ButtonLink>
      </div>
      {!isPaid ? (
        <small>
          This confirms that your order was received. It is not a payment
          receipt; a receipt is issued only after payment is verified.
        </small>
      ) : null}
    </section>
  );
}

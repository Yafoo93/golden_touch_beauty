"use client";

import { useEffect, useState } from "react";

import { ButtonLink } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import type { PaginatedResponse } from "@/lib/branches";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CustomerOrder } from "@/lib/orders";

export function AccountOrders() {
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiFetch<CustomerOrder[] | PaginatedResponse<CustomerOrder>>("orders/")
      .then((response) =>
        setOrders(Array.isArray(response) ? response : response.results),
      )
      .catch((error) =>
        setMessage(
          error instanceof Error ? error.message : "Orders could not be loaded.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="account-section-status">Loading orders...</p>;
  }

  return (
    <section className="account-bookings" aria-labelledby="account-orders-title">
      <header>
        <div>
          <p>Purchases</p>
          <h2 id="account-orders-title">Your orders</h2>
        </div>
        <ButtonLink href="/account/orders" size="small">
          View all orders
        </ButtonLink>
      </header>
      {message ? <p aria-live="polite">{message}</p> : null}
      {!orders.length ? (
        <p>You have not placed any product orders yet.</p>
      ) : (
        orders.map((order) => (
          <article key={order.id}>
            <div>
              <small>
                {order.reference} · {order.branch_name} ·{" "}
                {new Date(order.created_at).toLocaleDateString()}
              </small>
              <h3>
                {order.items
                  .map(
                    (item) =>
                      `${item.product_name} (${item.variant_name}) ×${item.quantity}`,
                  )
                  .join(", ")}
              </h3>
              <p>
                {formatGhanaCedis(order.total_amount)} · Payment{" "}
                {order.payment_status.replaceAll("_", " ")}
              </p>
              <ButtonLink
                href={`/account/orders/${encodeURIComponent(order.reference)}`}
                size="small"
                variant="outline"
              >
                View order
              </ButtonLink>
            </div>
            <strong>{order.status.replaceAll("_", " ")}</strong>
          </article>
        ))
      )}
    </section>
  );
}

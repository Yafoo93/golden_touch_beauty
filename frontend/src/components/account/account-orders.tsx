"use client";

import { useEffect, useState } from "react";

import { ButtonLink } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { formatGhanaCedis } from "@/lib/formatters";

type CustomerOrder = {
  id: string;
  reference: string;
  status: string;
  payment_status: string;
  branch_name: string;
  total_amount: string;
  created_at: string;
  items: Array<{
    id: string;
    product_name: string;
    variant_name: string;
    quantity: number;
  }>;
};

export function AccountOrders() {
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiFetch<CustomerOrder[]>("orders/")
      .then(setOrders)
      .catch((error) =>
        setMessage(
          error instanceof Error ? error.message : "Orders could not be loaded.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="account-section-status">Loading orders…</p>;

  return (
    <section className="account-bookings" aria-labelledby="account-orders-title">
      <header>
        <div>
          <p>Purchases</p>
          <h2 id="account-orders-title">Your orders</h2>
        </div>
        <ButtonLink href="/shop" size="small">
          Browse products
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
            </div>
            <strong>{order.status.replaceAll("_", " ")}</strong>
          </article>
        ))
      )}
    </section>
  );
}

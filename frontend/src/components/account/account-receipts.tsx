"use client";

import { useEffect, useState } from "react";

import { ButtonLink } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import type { PaginatedResponse } from "@/lib/branches";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CustomerReceipt } from "@/lib/receipts";


export function AccountReceipts() {
  const [receipts, setReceipts] = useState<CustomerReceipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiFetch<PaginatedResponse<CustomerReceipt>>("payments/receipts/")
      .then((page) => setReceipts(page.results))
      .catch((error) =>
        setMessage(
          error instanceof Error
            ? error.message
            : "Receipts could not be loaded.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="account-section-status">Loading receipts...</p>;
  }

  return (
    <section className="account-bookings" aria-labelledby="account-receipts-title">
      <header>
        <div>
          <p>Payments</p>
          <h2 id="account-receipts-title">Your receipts</h2>
        </div>
      </header>
      {message ? <p aria-live="polite">{message}</p> : null}
      {!receipts.length ? (
        <p>Verified payment receipts will appear here.</p>
      ) : (
        receipts.map((receipt) => (
          <article key={receipt.id}>
            <div>
              <small>
                {receipt.reference} · {receipt.branch_name} ·{" "}
                {new Date(receipt.issued_at).toLocaleDateString()}
              </small>
              <h3>
                {receipt.source_type} {receipt.source_reference}
              </h3>
              <p>{formatGhanaCedis(receipt.amount)}</p>
              <ButtonLink
                href={`/account/receipts/${receipt.reference}`}
                size="small"
                variant="outline"
              >
                View receipt
              </ButtonLink>
            </div>
            <strong>paid</strong>
          </article>
        ))
      )}
    </section>
  );
}

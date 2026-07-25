"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button, ButtonLink } from "@/components/ui/button";
import { apiFetch, ensureCsrfCookie } from "@/lib/api";

export function CheckoutFailure({ reference }: { reference?: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function releaseAndRetry() {
    if (!reference) {
      router.push("/cart");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await ensureCsrfCookie();
      await apiFetch(`orders/${encodeURIComponent(reference)}/cancel/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      router.push("/cart");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The reservation could not be released.");
    } finally { setBusy(false); }
  }
  return <section className="checkout-failure">
    <div aria-hidden="true">!</div><p>Checkout interrupted</p><h1>Your payment was not completed</h1>
    <span>No successful payment has been recorded. You can safely release this reservation, restore its products to the cart, and try again with live prices and stock.</span>
    {error ? <div className="form-alert form-alert--error">{error}</div> : null}
    <div><Button loading={busy} loadingLabel="Releasing reservation…" onClick={() => void releaseAndRetry()}>Restore cart and retry</Button><ButtonLink href="/shop" variant="outline">Return to shop</ButtonLink></div>
  </section>;
}

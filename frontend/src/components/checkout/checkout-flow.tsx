"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { useCartCount } from "@/components/cart/cart-count-context";
import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CheckoutOptions, CustomerOrder } from "@/lib/orders";

export function CheckoutFlow() {
  const router = useRouter();
  const { clearCart } = useCartCount();
  const requestId = useRef(globalThis.crypto?.randomUUID?.() ?? `${Date.now()}`);
  const [options, setOptions] = useState<CheckoutOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [fulfillment, setFulfillment] = useState<"pickup" | "delivery">("pickup");
  const [branch, setBranch] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiFetch<CheckoutOptions>("orders/checkout/options/")
      .then((result) => {
        setOptions(result);
        setName(result.customer.name);
        setPhone(result.customer.phone);
        setBranch(result.pickup_branches[0]?.code ?? "");
      })
      .catch((caught) => {
        if (caught instanceof ApiError && [401, 403].includes(caught.status)) {
          window.location.assign(`/login?next=${encodeURIComponent("/checkout")}`);
          return;
        }
        setError(caught instanceof Error ? caught.message : "Checkout could not be loaded.");
      })
      .finally(() => setLoading(false));
  }, []);

  async function submit() {
    if (!options || submitting) return;
    setSubmitting(true);
    setError("");
    try {
      await ensureCsrfCookie();
      const order = await apiFetch<CustomerOrder>("orders/checkout/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_request_id: requestId.current,
          fulfillment_method: fulfillment,
          pickup_branch_code: fulfillment === "pickup" ? branch : "",
          recipient_name: name,
          recipient_phone: phone,
          delivery_address: fulfillment === "delivery" ? address : "",
          delivery_city: fulfillment === "delivery" ? city : "",
          delivery_notes: notes,
        }),
      });
      await clearCart();
      router.push(`/checkout/success?order=${encodeURIComponent(order.reference)}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The order could not be created.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="checkout-loading">Checking your cart and branch stock…</div>;
  if (error && !options) return <EmptyState title="Checkout could not be loaded" description={error} action={<ButtonLink href="/cart">Return to cart</ButtonLink>} />;
  if (!options?.items.length) return <EmptyState title="Your cart is empty" description="Add an available product before starting checkout." action={<ButtonLink href="/shop">Browse products</ButtonLink>} />;

  const valid =
    name.trim() &&
    phone.trim() &&
    (fulfillment === "pickup" ? branch : address.trim() && city.trim());

  return <div className="checkout-flow">
    <section className="checkout-flow__form">
      {error ? <div className="form-alert form-alert--error">{error}</div> : null}
      <div className="checkout-flow__section">
        <p>1 · Fulfillment</p><h2>How should you receive the order?</h2>
        <div className="checkout-flow__choices">
          <label data-selected={fulfillment === "pickup" || undefined}><input type="radio" checked={fulfillment === "pickup"} onChange={() => setFulfillment("pickup")} /> Clinic pickup</label>
          <label data-selected={fulfillment === "delivery" || undefined}><input type="radio" checked={fulfillment === "delivery"} disabled={!options.delivery_available} onChange={() => setFulfillment("delivery")} /> Delivery</label>
        </div>
        {fulfillment === "pickup" ? <label className="checkout-flow__field"><span>Pickup branch</span><select value={branch} onChange={(event) => setBranch(event.target.value)}>{options.pickup_branches.map((item) => <option value={item.code} key={item.id}>{item.name}</option>)}</select><small>Only branches that can fulfil every cart item are shown.</small></label> : <><label className="checkout-flow__field"><span>Delivery address</span><textarea value={address} onChange={(event) => setAddress(event.target.value)} /></label><label className="checkout-flow__field"><span>City or area</span><input value={city} onChange={(event) => setCity(event.target.value)} /></label><p>The fulfillment branch is selected internally from branches with enough stock.</p></>}
      </div>
      <div className="checkout-flow__section">
        <p>2 · Recipient</p><h2>Contact information</h2>
        <label className="checkout-flow__field"><span>Full name</span><input value={name} onChange={(event) => setName(event.target.value)} /></label>
        <label className="checkout-flow__field"><span>Phone number</span><input value={phone} onChange={(event) => setPhone(event.target.value)} /></label>
        <label className="checkout-flow__field"><span>Delivery or pickup notes</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
      </div>
      <div className="checkout-flow__section">
        <p>3 · Payment</p><h2>Secure online payment</h2>
        <label className="checkout-flow__payment"><input type="radio" checked readOnly /> Online payment · payment link follows after the order is reserved</label>
        <small>Stage 10 creates the traceable order and reserves stock. KoraPay hosted payment is connected in Stage 11; no card details are collected here.</small>
      </div>
    </section>
    <aside className="checkout-flow__summary">
      <p>Order summary</p><h2>{options.items.length} product {options.items.length === 1 ? "line" : "lines"}</h2>
      {options.items.map((item) => <article key={item.variant_id}><div className="checkout-flow__image">{item.image_path ? <Image src={item.image_path} alt="" fill sizes="4rem" /> : null}</div><div><strong>{item.product_name}</strong><span>{item.variant_name} · Qty {item.quantity}</span><small>{item.sku}</small></div><b>{formatGhanaCedis(item.line_total)}</b></article>)}
      <dl><div><dt>Subtotal</dt><dd>{formatGhanaCedis(options.subtotal)}</dd></div><div><dt>Delivery</dt><dd>{Number(options.delivery_fee) ? formatGhanaCedis(options.delivery_fee) : "Calculated/confirmed later"}</dd></div><div><dt>Total now</dt><dd>{formatGhanaCedis(options.total_amount)}</dd></div></dl>
      <p className="checkout-flow__reservation">Stock will be reserved for {options.reservation_minutes} minutes after submission.</p>
      <Button fullWidth size="large" loading={submitting} loadingLabel="Reserving stock once…" disabled={!valid} onClick={() => void submit()}>Reserve order and continue</Button>
      <small>By continuing, you accept the delivery, returns, privacy, and terms policies.</small>
    </aside>
  </div>;
}

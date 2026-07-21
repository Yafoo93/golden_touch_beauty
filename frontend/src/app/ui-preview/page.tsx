"use client";

import { useState, type FormEvent } from "react";
import { useCartCount } from "@/components/cart/cart-count-context";
import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { FormField, TextAreaField, ValidationSummary } from "@/components/ui/form-field";
import { LoadingIndicator } from "@/components/ui/loading-indicator";
import { CardSkeleton, ListSkeleton } from "@/components/ui/skeleton";

export default function UiPreviewPage() {
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const { itemCount, incrementItemCount, decrementItemCount, resetItemCount } = useCartCount();
  function validate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); const next: string[] = [];
    if (!String(form.get("name") ?? "").trim()) next.push("Full name is required.");
    if (!String(form.get("email") ?? "").includes("@")) next.push("Enter a valid email address.");
    setErrors(next);
  }
  return <main className="ui-preview"><header className="ui-preview__heading"><p>Development preview</p><h1>Reusable form and interface states</h1><span>This route is for visual testing during development.</span></header><div className="ui-preview__grid">
    <section className="ui-preview__panel"><h2>Form fields and validation</h2><form onSubmit={validate} noValidate><ValidationSummary errors={errors} /><FormField name="name" label="Full name" placeholder="Enter your full name" required error={errors.includes("Full name is required.") ? "Full name is required." : undefined} /><FormField name="email" type="email" label="Email address" placeholder="name@example.com" hint="We will use this for confirmations and receipts." required error={errors.includes("Enter a valid email address.") ? "Enter a valid email address." : undefined} /><TextAreaField name="notes" label="Notes" placeholder="Optional appointment information" hint="Do not include payment-card information." rows={4} /><Button type="submit">Validate form</Button></form></section>
    <section className="ui-preview__panel"><h2>Loading indicators</h2><LoadingIndicator label="Checking availability" /><LoadingIndicator label="Loading appointments" size="large" presentation="panel" /><Button variant="black" loading={loading} loadingLabel="Saving changes" onClick={() => setLoading(true)}>Test button loading</Button>{loading ? <Button variant="outline" onClick={() => setLoading(false)}>Stop preview</Button> : null}</section>
    <section className="ui-preview__panel ui-preview__panel--wide"><h2>Empty state</h2><EmptyState title="No appointments yet" description="When a customer books a service, upcoming appointments will appear here." action={<ButtonLink href="/book">Book an appointment</ButtonLink>} /></section>
    <section className="ui-preview__panel ui-preview__panel--wide"><h2>Cart item-count indicator</h2><p className="ui-preview__copy">Current cart quantity: <strong>{itemCount}</strong>. The global header badge updates at the same time.</p><div className="ui-preview__actions"><Button onClick={() => incrementItemCount()}>Add one item</Button><Button variant="black" onClick={() => decrementItemCount()} disabled={itemCount === 0}>Remove one</Button><Button variant="outline" onClick={resetItemCount} disabled={itemCount === 0}>Reset count</Button><Button variant="outline" onClick={() => incrementItemCount(100)}>Test 99+ cap</Button></div></section>
    <section className="ui-preview__panel ui-preview__panel--wide"><h2>Loading skeletons</h2><p className="ui-preview__copy">These placeholders preserve layout while catalogue or account data is loading.</p><div className="ui-preview__skeletons"><CardSkeleton /><ListSkeleton rows={3} /></div></section>
  </div></main>;
}

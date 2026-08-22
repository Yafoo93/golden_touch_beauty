"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { apiFetch, ensureCsrfCookie } from "@/lib/api";

export function BookingActions({ reference, pricingStatus }: { reference: string; pricingStatus: "final" | "estimate" }) {
  const router = useRouter();
  const [reason, setReason] = useState("");
  const [proposedStart, setProposedStart] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [finalAmount, setFinalAmount] = useState("");

  async function act(action: string) {
    setBusy(action);
    setMessage("");
    try {
      await ensureCsrfCookie();
      await apiFetch(`bookings/management/${reference}/action/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          reason,
          proposed_start: proposedStart ? new Date(proposedStart).toISOString() : undefined,
          final_amount: action === "confirm_price" ? finalAmount : undefined,
        }),
      });
      setMessage("Booking updated successfully.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Booking could not be updated.");
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="management-booking-actions">
      <h2>Booking actions</h2>
      <label>Reason / internal note<textarea value={reason} onChange={(event) => setReason(event.target.value)} /></label>
      <label>Alternative date and time<input type="datetime-local" value={proposedStart} onChange={(event) => setProposedStart(event.target.value)} /></label>
      {pricingStatus === "estimate" ? <label>Confirmed final price (GHS)<input type="number" min="0" step="0.01" value={finalAmount} onChange={(event) => setFinalAmount(event.target.value)} /></label> : null}
      <div>
        {pricingStatus === "estimate" ? <Button size="small" disabled={!finalAmount || Boolean(busy)} onClick={() => void act("confirm_price")}>Confirm final price</Button> : null}
        <Button size="small" disabled={Boolean(busy)} onClick={() => void act("confirm")}>Approve</Button>
        <Button size="small" variant="outline" disabled={!proposedStart || Boolean(busy)} onClick={() => void act("propose_time")}>Propose time</Button>
        <Button size="small" variant="outline" disabled={Boolean(busy)} onClick={() => void act("check_in")}>Check in</Button>
        <Button size="small" variant="outline" disabled={Boolean(busy)} onClick={() => void act("start")}>Start</Button>
        <Button size="small" variant="outline" disabled={Boolean(busy)} onClick={() => void act("complete")}>Complete</Button>
        <Button size="small" variant="black" disabled={!reason || Boolean(busy)} onClick={() => void act("cancel")}>Cancel</Button>
        <Button size="small" variant="black" disabled={!reason || Boolean(busy)} onClick={() => void act("reject")}>Reject</Button>
        <Button size="small" variant="black" disabled={!reason || Boolean(busy)} onClick={() => void act("no_show")}>No-show</Button>
      </div>
      {message ? <p aria-live="polite">{message}</p> : null}
    </section>
  );
}

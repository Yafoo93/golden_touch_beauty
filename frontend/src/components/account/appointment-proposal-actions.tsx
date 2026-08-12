"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch, ensureCsrfCookie } from "@/lib/api";


export function AppointmentProposalActions({ reference }: { reference: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState<"accept" | "decline" | "">("");
  const [message, setMessage] = useState("");

  async function respond(accepted: boolean) {
    setBusy(accepted ? "accept" : "decline");
    setMessage("");
    try {
      await ensureCsrfCookie();
      await apiFetch(`bookings/${reference}/proposal/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accepted }),
      });
      setMessage(
        accepted
          ? "The proposed appointment time has been accepted."
          : "The proposed time was declined and the booking returned for review.",
      );
      router.refresh();
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Your response could not be saved.",
      );
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="appointment-detail__proposal-actions">
      <Button
        size="small"
        loading={busy === "accept"}
        disabled={Boolean(busy)}
        onClick={() => void respond(true)}
      >
        Accept proposed time
      </Button>
      <Button
        size="small"
        variant="outline"
        loading={busy === "decline"}
        disabled={Boolean(busy)}
        onClick={() => void respond(false)}
      >
        Decline proposed time
      </Button>
      {message ? <p aria-live="polite">{message}</p> : null}
    </div>
  );
}

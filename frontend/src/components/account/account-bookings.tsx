"use client";

import { useEffect, useState } from "react";

import { Button, ButtonLink } from "@/components/ui/button";
import { apiFetch, ensureCsrfCookie } from "@/lib/api";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementBooking } from "@/lib/management-bookings";

export function AccountBookings() {
  const [bookings, setBookings] = useState<ManagementBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  async function refresh() {
    setBookings(await apiFetch<ManagementBooking[]>("bookings/"));
  }
  useEffect(() => { refresh().catch((error) => setMessage(error.message)).finally(() => setLoading(false)); }, []);
  async function respond(reference: string, accepted: boolean) {
    try {
      await ensureCsrfCookie();
      await apiFetch(`bookings/${reference}/proposal/`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accepted }),
      });
      setMessage(accepted ? "The proposed time was accepted." : "The proposed time was declined.");
      await refresh();
    } catch (error) { setMessage(error instanceof Error ? error.message : "Your response could not be saved."); }
  }
  if (loading) return <p>Loading appointments…</p>;
  return <section className="account-bookings">
    <header><div><p>Appointments</p><h2>Your bookings</h2></div><ButtonLink href="/book" size="small">Book an appointment</ButtonLink></header>
    {message ? <p aria-live="polite">{message}</p> : null}
    {!bookings.length ? <p>You do not have any booking requests yet.</p> : bookings.map((booking) => <article key={booking.id}>
      <div><small>{booking.reference} · {booking.branch_name}</small><h3>{booking.services.map((item) => item.service_name).join(", ")}</h3><p>{new Date(booking.preferred_start).toLocaleString()} · {formatGhanaCedis(booking.total_amount)}</p></div>
      <strong>{booking.status.replaceAll("_", " ")}</strong>
      {booking.status === "proposed" && booking.proposed_start ? <div className="account-bookings__proposal"><p>Management proposed {new Date(booking.proposed_start).toLocaleString()}.</p><Button size="small" onClick={() => void respond(booking.reference, true)}>Accept time</Button><Button size="small" variant="outline" onClick={() => void respond(booking.reference, false)}>Decline</Button></div> : null}
    </article>)}
  </section>;
}

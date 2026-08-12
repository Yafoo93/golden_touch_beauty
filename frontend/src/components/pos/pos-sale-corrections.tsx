"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

export type POSCorrection = {
  action: string;
  reason: string;
  actor_name: string;
  created_at: string;
};

export function POSSaleCorrections({
  reference,
  canCorrect,
  corrections,
}: {
  reference: string;
  canCorrect: boolean;
  corrections: POSCorrection[];
}) {
  const router = useRouter();
  const [correctionType, setCorrectionType] = useState<"reversal" | "refund">("reversal");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!window.confirm(`Confirm this ${correctionType}? It will restore product stock and cannot be repeated.`)) return;
    setSaving(true); setError("");
    try {
      await apiFetch(`pos/sales/${encodeURIComponent(reference)}/corrections/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correction_type: correctionType, reason }),
      });
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The correction could not be completed.");
    } finally {
      setSaving(false);
    }
  }

  return <section className="pos-corrections" aria-labelledby="pos-corrections-title">
    <h2 id="pos-corrections-title">Corrections and audit history</h2>
    {canCorrect ? <form onSubmit={(event) => void submit(event)}>
      <label>Correction type<select value={correctionType} onChange={(event) => setCorrectionType(event.target.value as "reversal" | "refund")}>
        <option value="reversal">Reverse incorrect sale</option>
        <option value="refund">Record customer refund</option>
      </select></label>
      <label>Required reason<textarea minLength={10} maxLength={1000} required value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Explain why this correction is authorized (minimum 10 characters)." /></label>
      {error ? <p role="alert">{error}</p> : null}
      <button type="submit" disabled={saving || reason.trim().length < 10}>{saving ? "Processing…" : `Authorize ${correctionType}`}</button>
    </form> : null}
    {corrections.length ? <div className="pos-corrections__history">{corrections.map((correction) => <article key={`${correction.action}:${correction.created_at}`}>
      <div><strong>{correction.action === "pos.sale_refunded" ? "Refunded" : "Reversed"}</strong><span>{new Date(correction.created_at).toLocaleString()}</span></div>
      <p>{correction.reason}</p><small>Authorized by {correction.actor_name}</small>
    </article>)}</div> : <p className="pos-corrections__empty">No corrections have been recorded for this sale.</p>}
  </section>;
}

"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { ValidationSummary } from "@/components/ui/form-field";
import { apiFetch, ensureCsrfCookie } from "@/lib/api";
import type { CustomerConsent } from "@/lib/consent";

export function ConsentSettings() {
  const [consent, setConsent] = useState<CustomerConsent | null>(null);
  const [marketing, setMarketing] = useState(false);
  const [photographs, setPhotographs] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiFetch<CustomerConsent>("account/consent/")
      .then((value) => { setConsent(value); setMarketing(value.marketing_consent); setPhotographs(value.photograph_consent); })
      .catch((error) => setErrors([error instanceof Error ? error.message : "Consent settings could not be loaded."]))
      .finally(() => setLoading(false));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setErrors([]); setMessage("");
    try {
      await ensureCsrfCookie();
      const updated = await apiFetch<CustomerConsent>("account/consent/", {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ marketing_consent: marketing, photograph_consent: photographs }),
      });
      setConsent(updated); setMessage("Your consent preferences have been saved.");
    } catch (error) { setErrors([error instanceof Error ? error.message : "Consent preferences could not be saved."]); }
    finally { setSaving(false); }
  }

  if (loading) return <section className="consent-settings consent-settings--loading"><p>Loading consent settings...</p></section>;
  return <form className="consent-settings" onSubmit={submit}>
    <ValidationSummary errors={errors} />
    {message ? <p className="account-profile__success" role="status">{message}</p> : null}
    <article>
      <div><p>Optional communications</p><h2>Marketing consent</h2><span>Allow Golden Touch to send promotions, service announcements, beauty tips, and product offers. Operational messages about your bookings, orders, payments, and account are still sent when this is disabled.</span>{consent?.marketing_consent_updated_at ? <small>Last updated {new Date(consent.marketing_consent_updated_at).toLocaleString()}</small> : null}</div>
      <label className="consent-switch"><input type="checkbox" checked={marketing} onChange={(event) => setMarketing(event.target.checked)} /><span aria-hidden="true" /><b>{marketing ? "Allowed" : "Not allowed"}</b></label>
    </article>
    <article>
      <div><p>Images and media</p><h2>Photograph consent</h2><span>Allow photographs or videos taken during approved services to be used for Golden Touch marketing, portfolio, training, or social-media content. Declining does not prevent you from receiving a service.</span>{consent?.photograph_consent_updated_at ? <small>Last updated {new Date(consent.photograph_consent_updated_at).toLocaleString()}</small> : null}</div>
      <label className="consent-switch"><input type="checkbox" checked={photographs} onChange={(event) => setPhotographs(event.target.checked)} /><span aria-hidden="true" /><b>{photographs ? "Allowed" : "Not allowed"}</b></label>
    </article>
    <section className="consent-settings__legal"><h2>Legal agreements</h2><p>Your accepted terms version is <strong>{consent?.terms_version}</strong> and privacy version is <strong>{consent?.privacy_version}</strong>.</p>{consent?.terms_privacy_accepted_at ? <small>Accepted {new Date(consent.terms_privacy_accepted_at).toLocaleString()}</small> : null}<div><Link href="/terms">Read terms</Link><Link href="/privacy">Read privacy policy</Link></div></section>
    <footer><Button type="submit" loading={saving} loadingLabel="Saving preferences...">Save consent preferences</Button><p>You may return here to withdraw optional consent at any time.</p></footer>
  </form>;
}

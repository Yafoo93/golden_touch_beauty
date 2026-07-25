"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { apiFetch, ensureCsrfCookie } from "@/lib/api";

type Options = {
  branches: { id: string; code: string; name: string }[];
  services: { id: string; name: string; price: string; duration_minutes: number; branch_codes: string[] }[];
  customers: { id: string; name: string; email: string; phone: string }[];
};

export function AssistedBookingForm() {
  const router = useRouter();
  const requestId = useRef(globalThis.crypto?.randomUUID?.() ?? `${Date.now()}`);
  const [options, setOptions] = useState<Options>({ branches: [], services: [], customers: [] });
  const [branch, setBranch] = useState("");
  const [customer, setCustomer] = useState("");
  const [services, setServices] = useState<string[]>([]);
  const [preferredStart, setPreferredStart] = useState("");
  const [source, setSource] = useState("phone");
  const [overrideDuplicate, setOverrideDuplicate] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => { apiFetch<Options>("bookings/management/options/").then((value) => { setOptions(value); setBranch(value.branches[0]?.code || ""); setCustomer(value.customers[0]?.id || ""); }).catch((error) => setMessage(error.message)); }, []);
  const selectedCustomer = options.customers.find((item) => item.id === customer);
  const availableServices = useMemo(() => options.services.filter((service) => service.branch_codes.includes(branch)), [options.services, branch]);

  async function submit() {
    try {
      await ensureCsrfCookie();
      const result = await apiFetch<{ reference: string }>("bookings/management/all/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_request_id: requestId.current, branch_code: branch,
          preferred_start: new Date(preferredStart).toISOString(),
          service_selections: services.map((service_id) => ({ service_id })),
          customer_id: customer, recipient_is_customer: true,
          recipient_name: selectedCustomer?.name, recipient_phone: selectedCustomer?.phone,
          payment_method: "clinic", source, duplicate_override: overrideDuplicate,
          duplicate_override_reason: overrideReason,
        }),
      });
      router.push(`/management/bookings/${result.reference}`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Booking could not be created."); }
  }

  return <section className="management-form assisted-booking-form">
    {message ? <div className="form-alert form-alert--error">{message}</div> : null}
    <label>Branch<select value={branch} onChange={(event) => { setBranch(event.target.value); setServices([]); }}>{options.branches.map((item) => <option value={item.code} key={item.id}>{item.name}</option>)}</select></label>
    <label>Customer<select value={customer} onChange={(event) => setCustomer(event.target.value)}>{options.customers.map((item) => <option value={item.id} key={item.id}>{item.name} · {item.phone}</option>)}</select></label>
    <fieldset><legend>Services</legend>{availableServices.map((service) => <label key={service.id}><input type="checkbox" checked={services.includes(service.id)} onChange={(event) => setServices((current) => event.target.checked ? [...current, service.id] : current.filter((id) => id !== service.id))} /> {service.name} · GHS {service.price} · {service.duration_minutes} minutes</label>)}</fieldset>
    <label>Preferred date and time<input type="datetime-local" value={preferredStart} onChange={(event) => setPreferredStart(event.target.value)} /></label>
    <label>Source<select value={source} onChange={(event) => setSource(event.target.value)}><option value="phone">Phone</option><option value="whatsapp">WhatsApp</option><option value="walk_in">Walk-in</option></select></label>
    <label><input type="checkbox" checked={overrideDuplicate} onChange={(event) => setOverrideDuplicate(event.target.checked)} /> Authorized duplicate-booking override</label>
    {overrideDuplicate ? <label>Required override reason<textarea value={overrideReason} onChange={(event) => setOverrideReason(event.target.value)} /></label> : null}
    <Button disabled={!branch || !customer || !services.length || !preferredStart || (overrideDuplicate && !overrideReason)} onClick={() => void submit()}>Create assisted booking</Button>
  </section>;
}

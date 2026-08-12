"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { FormField, ValidationSummary } from "@/components/ui/form-field";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";
import type { PaginatedResponse } from "@/lib/branches";
import type { CustomerAddress } from "@/lib/addresses";

const emptyAddress = { label: "", address_type: "delivery", recipient_name: "", recipient_phone: "", address_line_1: "", address_line_2: "", city: "", region: "", landmark: "", country: "Ghana", is_default_billing: false, is_default_delivery: false };

export function AddressManager({ customerName, customerPhone }: { customerName: string; customerPhone: string }) {
  const [addresses, setAddresses] = useState<CustomerAddress[]>([]);
  const [editing, setEditing] = useState<CustomerAddress | null>(null);
  const [formKey, setFormKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try { const page = await apiFetch<PaginatedResponse<CustomerAddress>>("account/addresses/"); setAddresses(page.results); setErrors([]); }
    catch (error) { setErrors([error instanceof Error ? error.message : "Addresses could not be loaded."]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  function reset() { setEditing(null); setFormKey((value) => value + 1); setErrors([]); }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSubmitting(true); setErrors([]); setMessage("");
    const form = new FormData(event.currentTarget);
    const payload = {
      label: String(form.get("label") ?? "").trim(), address_type: String(form.get("address_type") ?? "delivery"),
      recipient_name: String(form.get("recipient_name") ?? "").trim(), recipient_phone: String(form.get("recipient_phone") ?? "").trim(),
      address_line_1: String(form.get("address_line_1") ?? "").trim(), address_line_2: String(form.get("address_line_2") ?? "").trim(),
      city: String(form.get("city") ?? "").trim(), region: String(form.get("region") ?? "").trim(), landmark: String(form.get("landmark") ?? "").trim(),
      country: String(form.get("country") ?? "Ghana").trim(), is_default_billing: form.get("is_default_billing") === "on", is_default_delivery: form.get("is_default_delivery") === "on",
    };
    try {
      await ensureCsrfCookie();
      await apiFetch(`account/addresses/${editing ? `${editing.id}/` : ""}`, { method: editing ? "PATCH" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      setMessage(editing ? "Address updated." : "Address saved."); reset(); await load();
    } catch (error) {
      if (error instanceof ApiError && error.details && typeof error.details === "object") setErrors(Object.values(error.details as Record<string, unknown>).flatMap((value) => Array.isArray(value) ? value.map(String) : [String(value)]));
      else setErrors([error instanceof Error ? error.message : "Address could not be saved."]);
    } finally { setSubmitting(false); }
  }

  async function remove(address: CustomerAddress) {
    if (!window.confirm(`Delete ${address.label}?`)) return;
    try { await ensureCsrfCookie(); await apiFetch(`account/addresses/${address.id}/`, { method: "DELETE" }); if (editing?.id === address.id) reset(); setMessage("Address deleted."); await load(); }
    catch (error) { setErrors([error instanceof Error ? error.message : "Address could not be deleted."]); }
  }

  const values = editing ?? { ...emptyAddress, recipient_name: customerName, recipient_phone: customerPhone };
  return <div className="address-manager">
    <section className="address-manager__list" aria-labelledby="saved-addresses-title">
      <header><div><p>Address book</p><h2 id="saved-addresses-title">Saved addresses</h2></div><span>{addresses.length} saved</span></header>
      {loading ? <p>Loading addresses...</p> : addresses.length === 0 ? <p>No saved addresses yet. Add your first billing or delivery address.</p> : <div>{addresses.map((address) => <article key={address.id}>
        <header><div><h3>{address.label}</h3><span>{address.address_type === "both" ? "Billing and delivery" : address.address_type}</span></div><div>{address.is_default_billing ? <small>Default billing</small> : null}{address.is_default_delivery ? <small>Default delivery</small> : null}</div></header>
        <p>{address.recipient_name} · {address.recipient_phone}</p><address>{address.address_line_1}{address.address_line_2 ? `, ${address.address_line_2}` : ""}<br />{address.city}, {address.region}, {address.country}{address.landmark ? <><br />Landmark: {address.landmark}</> : null}</address>
        <footer><Button size="small" variant="outline" onClick={() => { setEditing(address); setFormKey((v) => v + 1); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Edit</Button><Button size="small" variant="black" onClick={() => void remove(address)}>Delete</Button></footer>
      </article>)}</div>}
    </section>
    <section className="address-manager__form"><header><p>{editing ? "Update address" : "New address"}</p><h2>{editing ? editing.label : "Add an address"}</h2></header>
      <form key={formKey} onSubmit={submit}><ValidationSummary errors={errors} />{message ? <p className="account-profile__success" role="status">{message}</p> : null}<div className="address-manager__fields">
        <FormField name="label" label="Address label" defaultValue={values.label} placeholder="Home or Office" required maxLength={80} />
        <div className="form-field"><label className="form-field__label" htmlFor="address-type">Address type *</label><select className="form-field__control" id="address-type" name="address_type" defaultValue={values.address_type} required><option value="delivery">Delivery</option><option value="billing">Billing</option><option value="both">Billing and delivery</option></select></div>
        <FormField name="recipient_name" label="Recipient name" defaultValue={values.recipient_name} required maxLength={200} /><FormField name="recipient_phone" label="Recipient phone" type="tel" defaultValue={values.recipient_phone} required maxLength={20} />
        <FormField name="address_line_1" label="Address line 1" defaultValue={values.address_line_1} required maxLength={250} /><FormField name="address_line_2" label="Address line 2" defaultValue={values.address_line_2} maxLength={250} />
        <FormField name="city" label="City or town" defaultValue={values.city} required maxLength={120} /><FormField name="region" label="Region" defaultValue={values.region} required maxLength={120} />
        <FormField name="landmark" label="Nearest landmark" defaultValue={values.landmark} maxLength={250} /><FormField name="country" label="Country" defaultValue={values.country} required maxLength={80} />
      </div><div className="address-manager__defaults"><label><input type="checkbox" name="is_default_billing" defaultChecked={values.is_default_billing} /> Default billing address</label><label><input type="checkbox" name="is_default_delivery" defaultChecked={values.is_default_delivery} /> Default delivery address</label></div>
      <div className="address-manager__actions"><Button type="submit" loading={submitting} loadingLabel="Saving address...">{editing ? "Update address" : "Save address"}</Button>{editing ? <Button type="button" variant="outline" onClick={reset}>Cancel editing</Button> : null}</div></form>
    </section>
  </div>;
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import type { ServiceCardProps } from "@/components/catalogue/service-card";
import { Button } from "@/components/ui/button";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";
import { formatGhanaCedis } from "@/lib/formatters";

type Slot = { value: string; label: string; would_finish_after_closing: boolean };
type Availability = {
  slots: Slot[];
  message: string;
  management_may_propose_another_time: boolean;
};
type CurrentUser = {
  user: { full_name: string; email: string; phone_number: string };
};
type CreatedBooking = { reference: string; status: string };

export function BookingFlow({
  branchCode,
  branchName,
  services,
}: {
  branchCode: string;
  branchName: string;
  services: ServiceCardProps[];
}) {
  const router = useRouter();
  const [stage, setStage] = useState<"schedule" | "details" | "review">("schedule");
  const [date, setDate] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [time, setTime] = useState("");
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [recipientIsCustomer, setRecipientIsCustomer] = useState(true);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [allergies, setAllergies] = useState("");
  const [conditions, setConditions] = useState("");
  const [previousTreatments, setPreviousTreatments] = useState("");
  const [notes, setNotes] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [marketingConsent, setMarketingConsent] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<"online" | "clinic">("online");
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      services
        .filter((service) => service.priceType === "options" && service.priceOptions?.[0])
        .map((service) => [service.slug, service.priceOptions![0].id]),
    ),
  );
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const requestId = useRef(globalThis.crypto?.randomUUID?.() ?? `${Date.now()}`);

  function selectedOption(service: ServiceCardProps) {
    return service.priceOptions?.find((option) => option.id === selectedOptions[service.slug]);
  }
  function serviceDuration(service: ServiceCardProps) {
    return selectedOption(service)?.duration_minutes ?? service.durationMinutes;
  }
  function servicePrice(service: ServiceCardProps) {
    return selectedOption(service)?.price ?? service.price;
  }
  const totalDuration = services.reduce((sum, service) => sum + serviceDuration(service), 0);
  const total = services.reduce((sum, service) => sum + Number(servicePrice(service)), 0);
  const clinicAllowed = services.every((service) => service.allowsPayAtClinic);
  const minDate = useMemo(() => {
    const value = new Date();
    value.setDate(value.getDate() + 1);
    return value.toISOString().slice(0, 10);
  }, []);

  useEffect(() => {
    apiFetch<CurrentUser>("auth/me/")
      .then(({ user }) => {
        setName(user.full_name);
        setPhone(user.phone_number);
      })
      .catch((caught) => {
        if (caught instanceof ApiError && [401, 403].includes(caught.status)) {
          const next = `${window.location.pathname}${window.location.search}`;
          window.location.assign(`/login?next=${encodeURIComponent(next)}`);
        }
      });
  }, []);

  useEffect(() => {
    if (!date) return;
    setLoadingSlots(true);
    setTime("");
    apiFetch<Availability>(
      `bookings/availability/?branch=${encodeURIComponent(branchCode)}&date=${date}&duration=${totalDuration}`,
    )
      .then((response) => setSlots(response.slots))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Availability could not be loaded."))
      .finally(() => setLoadingSlots(false));
  }, [branchCode, date, totalDuration]);

  function move(next: typeof stage) {
    setError("");
    setStage(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submitBooking() {
    if (submitting) return;
    setSubmitting(true);
    setError("");
    try {
      await ensureCsrfCookie();
      const data = new FormData();
      data.set("client_request_id", requestId.current);
      data.set("branch_code", branchCode);
      data.set("preferred_start", time);
      data.set(
        "service_selections",
        JSON.stringify(
          services.map((service) => ({
            service_id: service.id,
            price_option_id: selectedOptions[service.slug] || undefined,
          })),
        ),
      );
      data.set("recipient_is_customer", String(recipientIsCustomer));
      data.set("recipient_name", name);
      data.set("recipient_phone", phone);
      data.set("allergies", allergies);
      data.set("conditions", conditions);
      data.set("previous_treatments", previousTreatments);
      data.set("notes", notes);
      data.set("photo_marketing_consent", String(marketingConsent));
      data.set("payment_method", paymentMethod);
      if (photo) data.set("treatment_photo", photo);
      const created = await apiFetch<CreatedBooking>("bookings/", { method: "POST", body: data });
      router.push(
        `/book/confirmation/${encodeURIComponent(created.reference)}`,
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Your appointment could not be submitted.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="booking-flow">
      <ol className="booking-flow__steps" aria-label="Booking progress">
        {["Date & time", "Your details", "Review & payment"].map((label, index) => (
          <li data-active={index === ["schedule", "details", "review"].indexOf(stage) || undefined} key={label}>
            {index + 1}. {label}
          </li>
        ))}
      </ol>

      {error ? <div className="form-alert form-alert--error">{error}</div> : null}

      {stage === "schedule" ? (
        <div className="booking-flow__panel">
          <h2>Choose a preferred date and time</h2>
          <p>
            Available times are in 30-minute intervals. This is a request: management may approve it
            or propose another suitable time.
          </p>
          <div className="booking-flow__selected-services">
            {services.map((service) => (
              <div key={service.slug}>
                <span><strong>{service.name}</strong><small>{serviceDuration(service)} minutes</small></span>
                {service.priceType === "options" && service.priceOptions?.length ? (
                  <label>
                    <span className="sr-only">Price option for {service.name}</span>
                    <select value={selectedOptions[service.slug]} onChange={(event) => setSelectedOptions((current) => ({ ...current, [service.slug]: event.target.value }))}>
                      {service.priceOptions.map((option) => <option value={option.id} key={option.id}>{option.name} · {formatGhanaCedis(option.price)}</option>)}
                    </select>
                  </label>
                ) : <strong>{formatGhanaCedis(service.price)}</strong>}
              </div>
            ))}
          </div>
          <label className="booking-flow__field">
            <span>Date</span>
            <input type="date" min={minDate} value={date} onChange={(event) => setDate(event.target.value)} />
          </label>
          <div className="booking-flow__slots" aria-live="polite">
            {loadingSlots ? <p>Checking branch availability…</p> : null}
            {!loadingSlots && date && !slots.length ? <p>No available times remain for this date.</p> : null}
            {slots.map((slot) => (
              <button type="button" data-selected={time === slot.value || undefined} key={slot.value} onClick={() => setTime(slot.value)}>
                {slot.label}
                {slot.would_finish_after_closing ? <small>May finish after closing</small> : null}
              </button>
            ))}
          </div>
          <div className="booking-flow__actions">
            <Button type="button" disabled={!time} onClick={() => move("details")}>Continue</Button>
          </div>
        </div>
      ) : null}

      {stage === "details" ? (
        <div className="booking-flow__panel">
          <h2>Who is receiving the treatment?</h2>
          <div className="booking-flow__choice">
            <label><input type="radio" checked={recipientIsCustomer} onChange={() => setRecipientIsCustomer(true)} /> Myself</label>
            <label><input type="radio" checked={!recipientIsCustomer} onChange={() => setRecipientIsCustomer(false)} /> Someone else</label>
          </div>
          <div className="booking-flow__grid">
            <label className="booking-flow__field"><span>Recipient full name</span><input required value={name} onChange={(event) => setName(event.target.value)} /></label>
            <label className="booking-flow__field"><span>Recipient phone</span><input required value={phone} onChange={(event) => setPhone(event.target.value)} /></label>
            <label className="booking-flow__field"><span>Allergies</span><textarea value={allergies} onChange={(event) => setAllergies(event.target.value)} /></label>
            <label className="booking-flow__field"><span>Medical or skin conditions</span><textarea value={conditions} onChange={(event) => setConditions(event.target.value)} /></label>
            <label className="booking-flow__field"><span>Previous treatments</span><textarea value={previousTreatments} onChange={(event) => setPreviousTreatments(event.target.value)} /></label>
            <label className="booking-flow__field"><span>Additional notes</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
          </div>
          <label className="booking-flow__field"><span>Optional consultation photo</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setPhoto(event.target.files?.[0] ?? null)} /></label>
          <label className="booking-flow__consent"><input type="checkbox" checked={marketingConsent} onChange={(event) => setMarketingConsent(event.target.checked)} /> I separately consent to this photo being considered for approved marketing use.</label>
          <div className="booking-flow__actions"><Button type="button" variant="outline" onClick={() => move("schedule")}>Back</Button><Button type="button" disabled={!name.trim() || !phone.trim()} onClick={() => move("review")}>Review booking</Button></div>
        </div>
      ) : null}

      {stage === "review" ? (
        <div className="booking-flow__panel">
          <h2>Review your booking request</h2>
          <dl className="booking-flow__summary">
            <div><dt>Branch</dt><dd>{branchName}</dd></div>
            <div><dt>Preferred time</dt><dd>{new Date(time).toLocaleString()}</dd></div>
            <div><dt>Recipient</dt><dd>{name} · {phone}</dd></div>
            {services.map((service) => <div key={service.slug}><dt>{service.name}{selectedOption(service) ? ` — ${selectedOption(service)!.name}` : ""} · {serviceDuration(service)} min</dt><dd>{formatGhanaCedis(servicePrice(service))}</dd></div>)}
            <div><dt>Total</dt><dd>{formatGhanaCedis(total)}</dd></div>
          </dl>
          <h3>Payment method</h3>
          <div className="booking-flow__choice">
            <label><input type="radio" checked={paymentMethod === "online"} onChange={() => setPaymentMethod("online")} /> Pay online after approval</label>
            {clinicAllowed ? <label><input type="radio" checked={paymentMethod === "clinic"} onChange={() => setPaymentMethod("clinic")} /> Pay in full at the clinic</label> : null}
          </div>
          <p className="booking-flow__policy">
            By submitting, you accept the <Link href="/terms">terms</Link>,{" "}
            <Link href="/privacy">privacy policy</Link>, and{" "}
            <Link href="/cancellation-refunds">cancellation and refund policy</Link>.
          </p>
          <div className="booking-flow__actions"><Button type="button" variant="outline" onClick={() => move("details")}>Back</Button><Button type="button" disabled={submitting} onClick={() => void submitBooking()}>{submitting ? "Submitting once…" : "Submit booking request"}</Button></div>
        </div>
      ) : null}
    </section>
  );
}

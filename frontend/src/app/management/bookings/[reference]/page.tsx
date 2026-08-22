import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { BookingActions } from "@/components/management/booking-actions";
import {
  StaffWhatsAppActions,
  type StaffWhatsAppAction,
} from "@/components/management/staff-whatsapp-actions";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ManagementBooking } from "@/lib/management-bookings";

async function loadBooking(reference: string) {
  const base = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(
    `${base}/api/v1/bookings/management/${encodeURIComponent(reference)}/`,
    {
      cache: "no-store",
      headers: {
        Cookie: (await cookies()).toString(),
        Accept: "application/json",
      },
    },
  );
  return response.ok
    ? ((await response.json()) as ManagementBooking)
    : null;
}

function whatsappActions(booking: ManagementBooking): StaffWhatsAppAction[] {
  const appointment = new Intl.DateTimeFormat("en-GH", {
    dateStyle: "full",
    timeStyle: "short",
    timeZone: "Africa/Accra",
  }).format(new Date(booking.preferred_start));
  const greeting = `Hello ${booking.recipient_name},`;
  const signature = "Golden Touch Beauty Centre";
  const context = `booking ${booking.reference} at our ${booking.branch_name} branch`;
  const actions: StaffWhatsAppAction[] = [
    {
      label: "Contact customer",
      message: `${greeting}\n\nThis is ${signature}. We are contacting you about ${context}. How may we assist you?`,
    },
    {
      label: "Send appointment details",
      message: `${greeting}\n\nThis is a reminder about ${context}, scheduled for ${appointment}. Please reply if you need assistance before your appointment.\n\n${signature}`,
    },
  ];

  if (booking.payment_status !== "paid") {
    actions.push({
      label: "Follow up payment",
      message: `${greeting}\n\nWe are following up on payment for ${context}. The amount is ${formatGhanaCedis(booking.total_amount)}. Please contact us if you need help completing payment.\n\n${signature}`,
    });
  }
  return actions;
}

export default async function ManagementBookingDetailPage({
  params,
}: {
  params: Promise<{ reference: string }>;
}) {
  const { reference } = await params;
  const booking = await loadBooking(reference);
  if (!booking) notFound();

  return (
    <main className="management-page">
      <header className="management-page__header">
        <div>
          <p>Booking · {booking.status}</p>
          <h1>{booking.reference}</h1>
          <span>
            {booking.branch_name} · {new Date(booking.preferred_start).toLocaleString()}
          </span>
        </div>
        <div className="management-page__summary">
          <strong>{booking.pricing_status === "estimate" ? `Starting estimate ${formatGhanaCedis(booking.total_amount)}` : formatGhanaCedis(booking.total_amount)}</strong>
          <span>{booking.payment_method} · {booking.payment_status}</span>
          {booking.finishes_after_branch_closing ? (
            <b>Warning: this appointment may finish after branch closing.</b>
          ) : null}
        </div>
      </header>

      <div className="management-booking-detail">
        <section>
          <h2>Services and recipient</h2>
          {booking.services.map((item) => (
            <p key={item.id}>
              {item.service_name} {item.option_name ? `— ${item.option_name}` : ""} · {item.duration_minutes} minutes · {formatGhanaCedis(item.unit_price)}
            </p>
          ))}
          <p>
            <strong>{booking.recipient_name}</strong><br />
            {booking.recipient_phone}<br />
            {booking.customer_email}
          </p>
        </section>

        <StaffWhatsAppActions
          phoneNumber={booking.recipient_phone}
          recipientName={booking.recipient_name}
          actions={whatsappActions(booking)}
        />

        {booking.can_view_sensitive_intake ? <section>
          <h2>Consultation details</h2>
          <p><strong>Allergies:</strong> {booking.allergies || "None supplied"}</p>
          <p><strong>Conditions:</strong> {booking.conditions || "None supplied"}</p>
          <p><strong>Previous treatments:</strong> {booking.previous_treatments || "None supplied"}</p>
          <p><strong>Notes:</strong> {booking.notes || "None supplied"}</p>
        </section> : null}

        <BookingActions reference={booking.reference} pricingStatus={booking.pricing_status} />

        <section>
          <h2>History</h2>
          {booking.history.map((entry) => (
            <p key={entry.id}>
              <strong>{entry.action.replaceAll("_", " ")}</strong> · {new Date(entry.created_at).toLocaleString()} · {entry.actor_name || "System"} {entry.reason ? `— ${entry.reason}` : ""}
            </p>
          ))}
        </section>
      </div>
    </main>
  );
}

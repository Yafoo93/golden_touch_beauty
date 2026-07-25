import { AssistedBookingForm } from "@/components/management/assisted-booking-form";

export default function AssistedBookingPage() {
  return <main className="management-page"><header className="management-page__header"><div><p>Management · Assisted booking</p><h1>Create booking</h1><span>Record phone, WhatsApp, or walk-in requests against the correct customer, services, and branch.</span></div></header><AssistedBookingForm /></main>;
}

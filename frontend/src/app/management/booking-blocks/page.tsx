import { BookingBlockManager } from "@/components/management/booking-block-manager";

export default function ManagementBookingBlocksPage() {
  return <main className="management-page"><header className="management-page__header"><div><p>Management · Availability</p><h1>Booking blocks</h1><span>Exclude meetings, maintenance, leave, and other unavailable periods from customer time choices.</span></div></header><BookingBlockManager /></main>;
}

import type { Metadata } from "next";
import { cookies } from "next/headers";
import { AccountOverview } from "@/components/account/account-overview";
import { AccountOrders } from "@/components/account/account-orders";
import { ButtonLink } from "@/components/ui/button";
import { AccountBookings } from "@/components/account/account-bookings";
import { AccountReceipts } from "@/components/account/account-receipts";
import { requireAuthenticated } from "@/lib/server-auth";
import type { AccountOverview as AccountOverviewData } from "@/lib/account-overview";

export const metadata: Metadata = { title: "My Account" };

async function loadOverview(): Promise<AccountOverviewData | null> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  try {
    const response = await fetch(`${base}/api/v1/account/overview/`, {
      cache: "no-store",
      headers: { Cookie: (await cookies()).toString(), Accept: "application/json" },
      signal: AbortSignal.timeout(20_000),
    });
    return response.ok ? await response.json() as AccountOverviewData : null;
  } catch {
    return null;
  }
}

export default async function AccountPage() {
  const user = await requireAuthenticated("/account");
  const overview = await loadOverview();
  const firstName = user.full_name.trim().split(/\s+/)[0] || "Customer";
  return (
    <main className="account-landing">
      <header className="account-landing__header">
        <p>Customer account</p>
        <h1>My account</h1>
        <span>Manage your Golden Touch experience from one place.</span>
      </header>

      <section className="account-landing__panel">
        <div>
          <p>Account dashboard</p>
          <h2>Welcome, {firstName}</h2>
          <span>Review your booking requests and product orders, or continue shopping and managing saved products.</span>
        </div>
        <div className="account-landing__actions">
          <ButtonLink href="/book">Book an appointment</ButtonLink>
          <ButtonLink href="/account/appointments" variant="outline">All appointments</ButtonLink>
          <ButtonLink href="/account/orders" variant="outline">All orders</ButtonLink>
          <ButtonLink href="/account/profile" variant="outline">Edit profile</ButtonLink>
          <ButtonLink href="/account/addresses" variant="outline">Saved addresses</ButtonLink>
          <ButtonLink href="/account/consent" variant="outline">Consent settings</ButtonLink>
          <ButtonLink href="/shop" variant="outline">Browse products</ButtonLink>
          <ButtonLink href="/account/wishlist" variant="outline">Wishlist</ButtonLink>
          <ButtonLink href="/cart" variant="outline">Cart</ButtonLink>
          <ButtonLink href="/account/notifications" variant="outline">Notifications</ButtonLink>
          <ButtonLink href="/contact" variant="outline">Contact a branch</ButtonLink>
          <ButtonLink href="/logout" variant="black">Sign out</ButtonLink>
        </div>
      </section>
      {overview ? (
        <AccountOverview data={overview} />
      ) : (
        <section className="account-overview account-overview--unavailable">
          <h2>Overview temporarily unavailable</h2>
          <p>Your detailed bookings, orders, receipts, and profile remain available below.</p>
        </section>
      )}
      <AccountBookings />
      <AccountOrders />
      <AccountReceipts />
    </main>
  );
}

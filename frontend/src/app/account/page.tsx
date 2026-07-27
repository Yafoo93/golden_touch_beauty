import type { Metadata } from "next";
import { AccountOrders } from "@/components/account/account-orders";
import { ButtonLink } from "@/components/ui/button";
import { AccountBookings } from "@/components/account/account-bookings";

export const metadata: Metadata = { title: "My Account" };

export default function AccountPage() {
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
          <h2>Welcome to Golden Touch</h2>
          <span>Review your booking requests and product orders, or continue shopping and managing saved products.</span>
        </div>
        <div className="account-landing__actions">
          <ButtonLink href="/book">Book an appointment</ButtonLink>
          <ButtonLink href="/shop" variant="outline">Browse products</ButtonLink>
          <ButtonLink href="/wishlist" variant="outline">Wishlist</ButtonLink>
          <ButtonLink href="/cart" variant="outline">Cart</ButtonLink>
          <ButtonLink href="/contact" variant="outline">Contact a branch</ButtonLink>
          <ButtonLink href="/logout" variant="black">Sign out</ButtonLink>
        </div>
      </section>
      <AccountBookings />
      <AccountOrders />
    </main>
  );
}

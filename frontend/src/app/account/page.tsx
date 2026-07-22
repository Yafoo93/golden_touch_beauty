import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button";

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
          <span>Your appointments, orders, profile, receipts, and notifications will appear here as those customer modules are completed.</span>
        </div>
        <div className="account-landing__actions">
          <ButtonLink href="/book">Book an appointment</ButtonLink>
          <ButtonLink href="/shop" variant="outline">Browse products</ButtonLink>
          <ButtonLink href="/logout" variant="black">Sign out</ButtonLink>
        </div>
      </section>
    </main>
  );
}

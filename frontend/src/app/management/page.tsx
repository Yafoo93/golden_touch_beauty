import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Management" };

export default function ManagementPage() {
  return (
    <main className="portal-landing">
      <header><p>Staff portal</p><h1>Management</h1><span>Manage the Golden Touch operation within your assigned branches and permissions.</span></header>
      <section className="portal-landing__panel">
        <h2>Management workspace</h2>
        <p>Service, product, booking, inventory, payment, staffing, and reporting tools will appear here as their individual modules are completed.</p>
        <div><ButtonLink href="/" variant="outline">Return home</ButtonLink><ButtonLink href="/logout" variant="black">Sign out</ButtonLink></div>
      </section>
    </main>
  );
}

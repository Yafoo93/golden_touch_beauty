import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Management" };

export default function ManagementPage() {
  return (
    <main className="portal-landing">
      <header><p>Staff portal</p><h1>Management</h1><span>Manage the Golden Touch operation within your assigned branches and permissions.</span></header>
      <section className="portal-landing__panel">
        <h2>Management workspace</h2>
        <p>Manage approved website copy, branches, and the operational modules available to your account.</p>
        <div><ButtonLink href="/management/services">Services</ButtonLink><ButtonLink href="/management/products">Products</ButtonLink><ButtonLink href="/management/inventory">Inventory</ButtonLink><ButtonLink href="/management/service-categories">Service categories</ButtonLink><ButtonLink href="/management/product-categories">Product categories</ButtonLink><ButtonLink href="/management/content">Website content</ButtonLink><ButtonLink href="/management/gallery">Gallery</ButtonLink><ButtonLink href="/management/testimonials">Testimonials</ButtonLink><ButtonLink href="/management/branches" variant="outline">Branches</ButtonLink><ButtonLink href="/logout" variant="black">Sign out</ButtonLink></div>
      </section>
    </main>
  );
}

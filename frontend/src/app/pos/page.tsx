import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Point of Sale" };

export default function PosPage() {
  return (
    <main className="portal-landing">
      <header><p>Staff portal</p><h1>Point of sale</h1><span>Process permitted in-branch sales from the Golden Touch POS workspace.</span></header>
      <section className="portal-landing__panel">
        <h2>POS workspace</h2>
        <p>Product and service search, the current sale, payment collection, and receipts will be added during the dedicated POS stage.</p>
        <div><ButtonLink href="/" variant="outline">Return home</ButtonLink><ButtonLink href="/logout" variant="black">Sign out</ButtonLink></div>
      </section>
    </main>
  );
}

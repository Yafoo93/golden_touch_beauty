import type { Metadata } from "next";

import { CartPageContent } from "@/components/cart/cart-page-content";
import { PageHero } from "@/components/ui/page-hero";

export const metadata: Metadata = { title: "Your Cart" };

export default function CartPage() {
  return (
    <main className="cart-page">
      <PageHero
        eyebrow="Your selection"
        title="Shopping"
        accentTitle="Cart"
        description="Review your products, variants, quantities, and subtotal before checkout."
        size="compact"
      />
      <section className="cart-page__content">
        <CartPageContent />
      </section>
    </main>
  );
}

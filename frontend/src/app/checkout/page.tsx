import { CheckoutFlow } from "@/components/checkout/checkout-flow";
import { PageHero } from "@/components/ui/page-hero";

export default function CheckoutPage() {
  return <main className="checkout-page">
    <PageHero eyebrow="Secure checkout" title="Review and" accentTitle="Reserve Your Order" description="Live prices and branch stock are checked again before one traceable order is created." size="compact" />
    <section className="checkout-page__content"><CheckoutFlow /></section>
  </main>;
}

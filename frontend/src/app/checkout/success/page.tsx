import { OrderResult } from "@/components/checkout/order-result";
import { EmptyState } from "@/components/ui/empty-state";
import { ButtonLink } from "@/components/ui/button";
import { requireAuthenticated } from "@/lib/server-auth";

export default async function CheckoutSuccessPage({ searchParams }: { searchParams: Promise<{ order?: string }> }) {
  const { order } = await searchParams;
  const returnTo = order
    ? `/checkout/success?order=${encodeURIComponent(order)}`
    : "/checkout/success";
  await requireAuthenticated(returnTo);
  return <main className="checkout-result-page">{order ? <OrderResult reference={order} /> : <EmptyState title="Order reference missing" description="Return to your cart to begin a safe checkout." action={<ButtonLink href="/cart">Return to cart</ButtonLink>} />}</main>;
}

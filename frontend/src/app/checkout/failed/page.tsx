import { CheckoutFailure } from "@/components/checkout/checkout-failure";

export default async function CheckoutFailedPage({ searchParams }: { searchParams: Promise<{ order?: string }> }) {
  const { order } = await searchParams;
  return <main className="checkout-result-page"><CheckoutFailure reference={order} /></main>;
}

import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { PrintReceiptButton } from "@/components/account/print-receipt-button";
import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";
import type { CustomerReceipt } from "@/lib/receipts";
import { requireAuthenticated } from "@/lib/server-auth";


async function loadReceipt(reference: string) {
  const base = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  const response = await fetch(
    `${base}/api/v1/payments/receipts/${encodeURIComponent(reference)}/`,
    {
      cache: "no-store",
      headers: {
        Cookie: (await cookies()).toString(),
        Accept: "application/json",
      },
    },
  );
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error("Receipt could not be loaded.");
  return (await response.json()) as CustomerReceipt;
}

export default async function CustomerReceiptPage({
  params,
}: {
  params: Promise<{ reference: string }>;
}) {
  const { reference } = await params;
  await requireAuthenticated(`/account/receipts/${reference}`);
  const receipt = await loadReceipt(reference);

  return (
    <main className="receipt-page">
      <section className="payment-receipt" aria-labelledby="receipt-title">
        <header>
          <div>
            <p>Golden Touch Beauty Centre</p>
            <h1 id="receipt-title">Payment receipt</h1>
          </div>
          <strong>PAID</strong>
        </header>

        <dl className="payment-receipt__metadata">
          <div><dt>Receipt number</dt><dd>{receipt.reference}</dd></div>
          <div><dt>Payment reference</dt><dd>{receipt.payment_reference}</dd></div>
          <div><dt>Issued</dt><dd>{new Date(receipt.issued_at).toLocaleString()}</dd></div>
          <div><dt>Customer</dt><dd>{receipt.recipient_name}</dd></div>
          <div><dt>Branch</dt><dd>{receipt.branch_name}</dd></div>
          <div><dt>Branch address</dt><dd>{receipt.branch_address}</dd></div>
          <div><dt>Payment method</dt><dd>{receipt.payment_method.replaceAll("_", " ") || receipt.provider}</dd></div>
          <div><dt>For</dt><dd>{receipt.source_type} {receipt.source_reference}</dd></div>
        </dl>

        <div className="payment-receipt__items">
          {receipt.line_items.map((item, index) => (
            <article key={`${item.description}-${index}`}>
              <span>{item.description} × {item.quantity}</span>
              <strong>{formatGhanaCedis(item.line_total)}</strong>
            </article>
          ))}
        </div>
        <footer>
          <span>Amount paid</span>
          <strong>{formatGhanaCedis(receipt.amount)}</strong>
        </footer>
        <small>This receipt was generated from a verified payment record.</small>
      </section>
      <div className="receipt-page__actions">
        <PrintReceiptButton />
        <ButtonLink href="/account" variant="outline">Back to account</ButtonLink>
      </div>
    </main>
  );
}

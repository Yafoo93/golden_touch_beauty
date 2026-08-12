import type { Metadata } from "next";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { PrintReceiptButton } from "@/components/account/print-receipt-button";
import { POSSaleCorrections } from "@/components/pos/pos-sale-corrections";
import type { POSCorrection } from "@/components/pos/pos-sale-corrections";
import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";

export const metadata: Metadata = { title: "POS Sale Receipt" };

type SaleDetail = {
  reference: string; receipt_reference: string; branch_name: string; branch_address: string;
  cashier_name: string; customer_name: string; status: string; status_label: string;
  payment_status: string; total_amount: string; item_count: number;
  completed_at: string | null; created_at: string;
  lines: { id: string; item_type: string; name: string; option_name: string; sku: string; quantity: number; unit_price: string; line_total: string }[];
  payments: { id: string; method: string; reference: string; amount: string; status: string; created_at: string }[];
  can_correct: boolean; corrections: POSCorrection[];
};

async function loadSale(reference: string): Promise<SaleDetail> {
  const base = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
  const response = await fetch(`${base}/api/v1/pos/sales/${encodeURIComponent(reference)}/`, {
    cache: "no-store", headers: { Accept: "application/json", Cookie: (await cookies()).toString() }, signal: AbortSignal.timeout(20_000),
  });
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error("The POS receipt could not be loaded.");
  return await response.json() as SaleDetail;
}

export default async function POSSaleReceiptPage({ params }: { params: Promise<{ reference: string }> }) {
  const { reference } = await params;
  const sale = await loadSale(reference);
  const issued = sale.completed_at ?? sale.created_at;
  return <main className="receipt-page pos-receipt-page">
    <section className="payment-receipt" aria-labelledby="pos-receipt-title">
      <header><div><p>Golden Touch Beauty Centre</p><h1 id="pos-receipt-title">POS sale receipt</h1></div><strong>{sale.status_label.toUpperCase()}</strong></header>
      <dl className="payment-receipt__metadata">
        <div><dt>Receipt number</dt><dd>{sale.receipt_reference}</dd></div>
        <div><dt>Sale reference</dt><dd>{sale.reference}</dd></div>
        <div><dt>Issued</dt><dd>{new Date(issued).toLocaleString()}</dd></div>
        <div><dt>Branch</dt><dd>{sale.branch_name}</dd></div>
        <div><dt>Branch address</dt><dd>{sale.branch_address}</dd></div>
        <div><dt>Cashier</dt><dd>{sale.cashier_name}</dd></div>
        <div><dt>Customer</dt><dd>{sale.customer_name}</dd></div>
        <div><dt>Payment status</dt><dd>{sale.payment_status.replaceAll("_", " ")}</dd></div>
      </dl>
      <div className="payment-receipt__items">
        {sale.lines.map((line) => <article key={line.id}><span>{line.name}{line.option_name ? ` — ${line.option_name}` : ""} × {line.quantity}<small>{line.sku ? ` ${line.sku} ·` : ""} {formatGhanaCedis(line.unit_price)} each</small></span><strong>{formatGhanaCedis(line.line_total)}</strong></article>)}
      </div>
      {sale.payments.length ? <section className="pos-receipt__payments"><h2>Payments</h2>{sale.payments.map((payment) => <div key={payment.id}><span>{payment.method.replaceAll("_", " ")}{payment.reference ? ` · ${payment.reference}` : ""}</span><strong>{formatGhanaCedis(payment.amount)}</strong></div>)}</section> : null}
      <footer><span>Total</span><strong>{formatGhanaCedis(sale.total_amount)}</strong></footer>
      <small>This receipt is an immutable snapshot of the completed in-clinic sale.</small>
    </section>
    <POSSaleCorrections reference={sale.reference} canCorrect={sale.can_correct} corrections={sale.corrections} />
    <div className="receipt-page__actions"><PrintReceiptButton /><ButtonLink href="/pos/sales" variant="outline">Back to sale history</ButtonLink></div>
  </main>;
}

import type { Metadata } from "next";

import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Reports | Management" };

export default function ManagementReportsPage() {
  return (
    <main className="portal-landing">
      <header>
        <div><p>Management / Analytics</p><h1>Reports</h1><span>Open branch-scoped operational and financial reports.</span></div>
        <ButtonLink href="/management/reports/methodology" variant="outline">Metric formulas</ButtonLink>
      </header>
      <section className="portal-landing__panel">
        <h2>Sales and revenue</h2>
        <p>Review paid online orders and completed POS sales by date, source, branch, and payment method.</p>
        <div><ButtonLink href="/management/reports/sales">Open sales report</ButtonLink></div>
      </section>
      <section className="portal-landing__panel">
        <h2>Branch performance</h2>
        <p>Compare sales, bookings, products, services, payments, and current stock across permitted branches.</p>
        <div><ButtonLink href="/management/reports/branches">Open branches report</ButtonLink></div>
      </section>
      <section className="portal-landing__panel">
        <h2>Payments and reconciliation</h2>
        <p>Reconcile online and POS payments by status, method, provider, source, and branch.</p>
        <div><ButtonLink href="/management/reports/payments">Open payments report</ButtonLink></div>
      </section>
      <section className="portal-landing__panel">
        <h2>Inventory and stock movements</h2>
        <p>Review current stock, valuation, stock risks, and movement activity by branch.</p>
        <div><ButtonLink href="/management/reports/inventory">Open inventory report</ButtonLink></div>
      </section>
      <section className="portal-landing__panel">
        <h2>Services and treatments</h2>
        <p>Review appointment and POS service demand, revenue, completion, and scheduled duration.</p>
        <div><ButtonLink href="/management/reports/services">Open services report</ButtonLink></div>
      </section>
      <section className="portal-landing__panel">
        <h2>Products and stock</h2>
        <p>Compare online and POS product sales with current branch stock health.</p>
        <div><ButtonLink href="/management/reports/products">Open products report</ButtonLink></div>
      </section>
      <section className="portal-landing__panel">
        <h2>Bookings and appointments</h2>
        <p>Monitor booking volume, status, source, scheduled value, duration, and branch performance.</p>
        <div><ButtonLink href="/management/reports/bookings">Open bookings report</ButtonLink></div>
      </section>
    </main>
  );
}

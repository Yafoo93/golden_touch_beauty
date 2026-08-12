import type { Metadata } from "next";
import { ManagementModuleLanding } from "@/components/management/module-landing";

export const metadata: Metadata = { title: "Payments | Management" };

export default function ManagementPaymentsPage() {
  return <ManagementModuleLanding eyebrow="Finance" title="Payments" description="Review permitted payment records, balances, receipts, and reconciliation status." stage="the payment-management stage" />;
}

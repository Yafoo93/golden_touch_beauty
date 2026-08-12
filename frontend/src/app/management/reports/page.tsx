import type { Metadata } from "next";
import { ManagementModuleLanding } from "@/components/management/module-landing";

export const metadata: Metadata = { title: "Reports | Management" };

export default function ManagementReportsPage() {
  return <ManagementModuleLanding eyebrow="Analytics" title="Reports" description="Open branch-scoped sales, booking, product, service, inventory, and payment reports." stage="Stage 16 — reports and analytics" />;
}

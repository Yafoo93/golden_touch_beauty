import type { Metadata } from "next";
import { ManagementModuleLanding } from "@/components/management/module-landing";

export const metadata: Metadata = { title: "Customers | Management" };

export default function ManagementCustomersPage() {
  return <ManagementModuleLanding eyebrow="Customers" title="Customers" description="Find customers and review the operational information staff are permitted to access." stage="the customer-management stage" />;
}

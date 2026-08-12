import type { Metadata } from "next";
import { ManagementModuleLanding } from "@/components/management/module-landing";

export const metadata: Metadata = { title: "Orders | Management" };

export default function ManagementOrdersPage() {
  return <ManagementModuleLanding eyebrow="Commerce" title="Orders" description="Track online product orders and their fulfilment status across authorized branches." stage="the order-management stage" />;
}

import type { Metadata } from "next";
import { ManagementModuleLanding } from "@/components/management/module-landing";

export const metadata: Metadata = { title: "Audit Log | Management" };

export default function ManagementAuditLogPage() {
  return <ManagementModuleLanding eyebrow="Governance" title="Audit log" description="Review immutable records of sensitive and operational changes within authorized branches." stage="the audit and reporting stage" />;
}

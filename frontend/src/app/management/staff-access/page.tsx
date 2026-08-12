import type { Metadata } from "next";
import { ManagementModuleLanding } from "@/components/management/module-landing";

export const metadata: Metadata = { title: "Staff Access | Management" };

export default function ManagementStaffAccessPage() {
  return <ManagementModuleLanding eyebrow="Security" title="Staff access" description="Manage staff-to-branch assignments and role-based access to operational workspaces." stage="the staff-access management stage" />;
}

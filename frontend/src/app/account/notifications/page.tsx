import type { Metadata } from "next";

import { AccountNotifications } from "@/components/account/account-notifications";
import { requireAuthenticated } from "@/lib/server-auth";

export const metadata: Metadata = { title: "Notifications" };

export default async function NotificationsPage() {
  await requireAuthenticated("/account/notifications");
  return (
    <main className="account-notifications-page">
      <AccountNotifications />
    </main>
  );
}

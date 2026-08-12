import type { Metadata } from "next";

import { ProfileForm } from "@/components/account/profile-form";
import { ButtonLink } from "@/components/ui/button";
import { requireAuthenticated } from "@/lib/server-auth";

export const metadata: Metadata = { title: "My Profile" };

export default async function AccountProfilePage() {
  const user = await requireAuthenticated("/account/profile");
  return (
    <main className="account-profile-page">
      <header className="account-profile-page__header">
        <div><p>Customer account</p><h1>My profile</h1><span>Keep your contact and personal information accurate for bookings, orders, and receipts.</span></div>
        <ButtonLink href="/account" variant="outline" size="small">Account overview</ButtonLink>
      </header>
      <ProfileForm profile={user} />
    </main>
  );
}

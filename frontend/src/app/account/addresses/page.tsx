import type { Metadata } from "next";
import { AddressManager } from "@/components/account/address-manager";
import { ButtonLink } from "@/components/ui/button";
import { requireAuthenticated } from "@/lib/server-auth";

export const metadata: Metadata = { title: "Saved Addresses" };

export default async function AccountAddressesPage() {
  const user = await requireAuthenticated("/account/addresses");
  return <main className="account-addresses-page"><header><div><p>Customer account</p><h1>Saved addresses</h1><span>Manage reusable billing and delivery details for faster checkout.</span></div><ButtonLink href="/account" variant="outline" size="small">Account overview</ButtonLink></header><AddressManager customerName={user.full_name} customerPhone={user.phone_number} /></main>;
}

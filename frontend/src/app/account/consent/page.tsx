import type { Metadata } from "next";
import { ConsentSettings } from "@/components/account/consent-settings";
import { ButtonLink } from "@/components/ui/button";
import { requireAuthenticated } from "@/lib/server-auth";

export const metadata: Metadata = { title: "Consent Settings" };

export default async function AccountConsentPage() {
  await requireAuthenticated("/account/consent");
  return <main className="account-consent-page"><header><div><p>Customer account</p><h1>Consent settings</h1><span>Control optional marketing communications and the use of photographs or videos.</span></div><ButtonLink href="/account" variant="outline" size="small">Account overview</ButtonLink></header><ConsentSettings /></main>;
}

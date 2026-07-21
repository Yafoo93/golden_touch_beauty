import type { Metadata } from "next";

import { BranchContactCard } from "@/components/branches/branch-contact-card";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import type { PaginatedResponse, PublicBranch } from "@/lib/branches";


export const metadata: Metadata = { title: "Contact Us" };

async function getBranches(): Promise<PublicBranch[] | null> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${backendUrl}/api/v1/branches/`, { cache: "no-store" });
    if (!response.ok) return null;
    return ((await response.json()) as PaginatedResponse<PublicBranch>).results;
  } catch { return null; }
}

export default async function ContactPage() {
  const branches = await getBranches();
  return <main className="contact-page"><PageHero eyebrow="Visit Golden Touch" title="Contact Our" accentTitle="Ghana Branches" description="Call, WhatsApp, or visit Makola and Tse Addo during their branch opening hours." backgroundImage="/images/hero2.jpeg" size="compact" /><section className="contact-page__content" aria-labelledby="branch-contact-heading"><div className="contact-page__heading"><p>Our locations</p><h2 id="branch-contact-heading">Makola and Tse Addo</h2></div>{!branches ? <EmptyState title="Branch contacts could not be loaded" description="Please try again to retrieve the latest branch information." action={<ButtonLink href="/contact">Try again</ButtonLink>} /> : branches.length === 0 ? <EmptyState title="No active branches" description="Branch contact information is temporarily unavailable." /> : <div className="contact-page__grid">{branches.map((branch) => <BranchContactCard branch={branch} key={branch.id} />)}</div>}</section></main>;
}

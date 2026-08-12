import type { Metadata } from "next";
import { AccountWishlistContent } from "@/components/account/wishlist-content";
import { ButtonLink } from "@/components/ui/button";
import { requireAuthenticated } from "@/lib/server-auth";

export const metadata: Metadata = { title: "My Wishlist" };

export default async function AccountWishlistPage() {
  await requireAuthenticated("/account/wishlist");
  return <main className="account-wishlist-page"><header><div><p>Customer account</p><h1>Saved products</h1><span>Keep your preferred Golden Touch products together until you are ready to purchase.</span></div><div><ButtonLink href="/account" variant="outline" size="small">Account overview</ButtonLink><ButtonLink href="/shop" size="small">Browse products</ButtonLink></div></header><AccountWishlistContent /></main>;
}

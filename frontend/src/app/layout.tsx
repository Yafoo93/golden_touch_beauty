import type { Metadata } from "next";
import { CartCountProvider } from "@/components/cart/cart-count-context";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { WishlistProvider } from "@/components/wishlist/wishlist-context";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  title: {
    default: "Golden Touch Beauty Centre",
    template: "%s | Golden Touch Beauty Centre",
  },
  description:
    "Beauty services, appointment booking, and premium products in Accra.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <body className="min-h-full flex flex-col">
        <CartCountProvider>
          <WishlistProvider>
            <SiteHeader />
            <div className="site-content">{children}</div>
            <SiteFooter />
          </WishlistProvider>
        </CartCountProvider>
      </body>
    </html>
  );
}

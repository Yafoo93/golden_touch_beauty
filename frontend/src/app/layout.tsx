import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
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
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

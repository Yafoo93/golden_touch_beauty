"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { PortalAccess } from "@/lib/server-auth";

const managementLinks = [
  { href: "/management", label: "Dashboard", exact: true },
  { href: "/management/bookings", label: "Bookings" },
  { href: "/management/services", label: "Services" },
  { href: "/management/products", label: "Products" },
  { href: "/management/inventory", label: "Inventory" },
  { href: "/management/branches", label: "Branches" },
  { href: "/management/content", label: "Website" },
];

export function PortalNavigation({
  portalAccess,
}: {
  portalAccess: PortalAccess[];
}) {
  const pathname = usePathname();
  const inManagement = pathname.startsWith("/management");

  return (
    <nav className="portal-navigation" aria-label="Staff portal navigation">
      <div className="portal-navigation__inner">
        {inManagement
          ? managementLinks.map((item) => {
              const active = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);
              return (
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  key={item.href}
                >
                  {item.label}
                </Link>
              );
            })
          : null}
        <span className="portal-navigation__spacer" />
        {portalAccess.includes("management") && !inManagement ? (
          <Link href="/management">Management</Link>
        ) : null}
        {portalAccess.includes("pos") ? (
          <Link
            href="/pos"
            aria-current={pathname.startsWith("/pos") ? "page" : undefined}
          >
            POS
          </Link>
        ) : null}
        <Link href="/">Website</Link>
      </div>
    </nav>
  );
}

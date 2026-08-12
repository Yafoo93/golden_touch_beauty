"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { ManagementModule, PortalAccess } from "@/lib/server-auth";

const managementLinks = [
  { href: "/management", label: "Dashboard", module: "dashboard", exact: true },
  { href: "/management/branches", label: "Branches", module: "branches" },
  { href: "/management/services", label: "Services", module: "services" },
  { href: "/management/products", label: "Products", module: "products" },
  { href: "/management/inventory", label: "Inventory", module: "inventory" },
  { href: "/management/bookings", label: "Bookings", module: "bookings" },
  { href: "/management/customers", label: "Customers", module: "customers" },
  { href: "/management/orders", label: "Orders", module: "orders" },
  { href: "/management/payments", label: "Payments", module: "payments" },
  { href: "/management/reports", label: "Reports", module: "reports" },
  { href: "/management/staff-access", label: "Staff access", module: "staff_access" },
  { href: "/management/audit-log", label: "Audit log", module: "audit_log" },
] satisfies Array<{ href: string; label: string; module: ManagementModule; exact?: boolean }>;

export function PortalNavigation({
  portalAccess,
  managementModules,
}: {
  portalAccess: PortalAccess[];
  managementModules: ManagementModule[];
}) {
  const pathname = usePathname();
  const inManagement = pathname.startsWith("/management");

  return (
    <nav className="portal-navigation" aria-label="Management navigation">
      <div className="portal-navigation__inner">
        {inManagement
          ? managementLinks.filter((item) => managementModules.includes(item.module)).map((item) => {
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
          <><Link href="/pos" aria-current={pathname === "/pos" ? "page" : undefined}>POS</Link>{pathname.startsWith("/pos") ? <><Link href="/pos/sales" aria-current={pathname.startsWith("/pos/sales") ? "page" : undefined}>Sale history</Link><Link href="/pos/end-of-day" aria-current={pathname.startsWith("/pos/end-of-day") ? "page" : undefined}>End of day</Link></> : null}</>
        ) : null}
        {inManagement && managementModules.includes("content") ? (
          <Link
            href="/management/content"
            aria-current={
              pathname.startsWith("/management/content") ||
              pathname.startsWith("/management/gallery") ||
              pathname.startsWith("/management/testimonials")
                ? "page"
                : undefined
            }
          >
            Website content
          </Link>
        ) : null}
        <Link href="/">Website</Link>
      </div>
    </nav>
  );
}

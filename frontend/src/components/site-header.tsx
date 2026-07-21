"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useCartCount } from "@/components/cart/cart-count-context";
import { CartItemCount } from "@/components/cart/cart-item-count";
import { ButtonLink } from "@/components/ui/button";

const navigation = [
  { href: "/", label: "Home" },
  { href: "/services", label: "Services" },
  { href: "/shop", label: "Shop" },
];

function isCurrentRoute(pathname: string, href: string) {
  return href === "/" ? pathname === href : pathname.startsWith(href);
}

function CartIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 4h2l2.1 10.1a2 2 0 0 0 2 1.6h7.8a2 2 0 0 0 2-1.6L20 7H6" />
      <circle cx="9" cy="20" r="1" />
      <circle cx="18" cy="20" r="1" />
    </svg>
  );
}

function AccountIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="8" r="3.25" />
      <path d="M5.5 20a6.5 6.5 0 0 1 13 0" />
    </svg>
  );
}

export function SiteHeader() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { itemCount: cartItemCount } = useCartCount();

  useEffect(() => {
    if (!isMenuOpen) return;

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsMenuOpen(false);
    };

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isMenuOpen]);

  // Authentication is implemented in Stage 4. Until then this control points
  // to Login; it will become Account when the session endpoint is connected.
  const isAuthenticated = false;
  const accountHref = isAuthenticated ? "/account" : "/login";
  const accountLabel = isAuthenticated ? "Account" : "Login";

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link
          className="brand"
          href="/"
          aria-label="Golden Touch Beauty Centre home"
        >
          <Image
            className="brand__logo"
            src="/images/logo.png"
            alt=""
            width={52}
            height={52}
            priority
          />
          <span className="brand__words">
            <span className="brand__name">Golden Touch</span>
            <span className="brand__tagline">Beauty Centre</span>
          </span>
        </Link>

        <nav className="primary-nav" aria-label="Primary navigation">
          {navigation.map((item) => {
            const isActive = isCurrentRoute(pathname, item.href);
            return (
              <Link
                key={item.href}
                className="primary-nav__link"
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                data-active={isActive || undefined}
              >
                {item.label}
              </Link>
            );
          })}
          <ButtonLink
            className="primary-nav__book"
            href="/book"
            size="small"
            aria-current={pathname.startsWith("/book") ? "page" : undefined}
          >
            Book Now
          </ButtonLink>
        </nav>

        <div className="header-actions">
          <Link
            className="cart-link"
            href="/cart"
            aria-label={`Cart, ${cartItemCount} ${cartItemCount === 1 ? "item" : "items"}`}
          >
            <CartIcon />
            <CartItemCount count={cartItemCount} />
          </Link>
          <Link className="account-link" href={accountHref}>
            <AccountIcon />
            <span>{accountLabel}</span>
          </Link>
          <button
            className="mobile-menu-toggle"
            type="button"
            aria-expanded={isMenuOpen}
            aria-controls="mobile-navigation"
            aria-label={isMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            onClick={() => setIsMenuOpen((current) => !current)}
          >
            <span className="mobile-menu-toggle__lines" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
          </button>
        </div>
      </div>

      {isMenuOpen ? (
        <nav
          className="mobile-nav"
          id="mobile-navigation"
          aria-label="Mobile navigation"
        >
          <div className="mobile-nav__inner">
            {navigation.map((item) => {
              const isActive = isCurrentRoute(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  className="mobile-nav__link"
                  href={item.href}
                  aria-current={isActive ? "page" : undefined}
                  data-active={isActive || undefined}
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.label}
                </Link>
              );
            })}
            <Link
              className="mobile-nav__link"
              href="/cart"
              aria-label={`Cart, ${cartItemCount} ${cartItemCount === 1 ? "item" : "items"}`}
              aria-current={pathname.startsWith("/cart") ? "page" : undefined}
              onClick={() => setIsMenuOpen(false)}
            >
              Cart
              <CartItemCount count={cartItemCount} className="mobile-nav__count" />
            </Link>
            <Link
              className="mobile-nav__link"
              href={accountHref}
              aria-current={pathname.startsWith(accountHref) ? "page" : undefined}
              onClick={() => setIsMenuOpen(false)}
            >
              {accountLabel}
            </Link>
            <ButtonLink
              className="mobile-nav__book"
              href="/book"
              fullWidth
              aria-current={pathname.startsWith("/book") ? "page" : undefined}
              onClick={() => setIsMenuOpen(false)}
            >
              Book Now
            </ButtonLink>
          </div>
        </nav>
      ) : null}
    </header>
  );
}

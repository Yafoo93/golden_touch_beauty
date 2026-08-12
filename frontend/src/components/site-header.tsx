"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useCartCount } from "@/components/cart/cart-count-context";
import { CartItemCount } from "@/components/cart/cart-item-count";
import { CartDrawer } from "@/components/cart/cart-drawer";
import { ButtonLink } from "@/components/ui/button";
import { NotificationCentre } from "@/components/notifications/notification-centre";
import { useWishlist } from "@/components/wishlist/wishlist-context";
import { ApiError, apiFetch } from "@/lib/api";

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

function WishlistIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m12 2.8 2.8 5.7 6.3.9-4.55 4.43 1.07 6.27L12 17.14 6.38 20.1l1.07-6.27L2.9 9.4l6.3-.9L12 2.8Z" />
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

type CurrentUserResponse = {
  user: {
    portal_access: Array<"management" | "pos">;
  };
};

export function SiteHeader() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [portalAccess, setPortalAccess] = useState<
    Array<"management" | "pos">
  >([]);
  const [headerAuthenticated, setHeaderAuthenticated] = useState<boolean | null>(
    null,
  );
  const closeCart = useCallback(() => setIsCartOpen(false), []);
  const { itemCount: cartItemCount } = useCartCount();
  const {
    itemCount: wishlistItemCount,
    authenticated,
    loading: authenticationLoading,
  } = useWishlist();

  useEffect(() => {
    if (!isMenuOpen) return;

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsMenuOpen(false);
    };

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isMenuOpen]);

  useEffect(() => {
    setIsCartOpen(false);
  }, [pathname]);

  useEffect(() => {
    let cancelled = false;

    async function loadPortalAccess() {
      try {
        const response = await apiFetch<CurrentUserResponse>("auth/me/");
        if (!cancelled) {
          setPortalAccess(response.user.portal_access);
          setHeaderAuthenticated(true);
        }
      } catch (error) {
        if (
          !cancelled &&
          error instanceof ApiError &&
          [401, 403].includes(error.status)
        ) {
          setPortalAccess([]);
          setHeaderAuthenticated(false);
        }
      }
    }

    void loadPortalAccess();
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  // Authentication belongs to the session endpoint. Wishlist availability is
  // only a fallback while that request is still resolving; a temporary
  // wishlist failure must never hide authenticated header controls.
  const isAuthenticated =
    headerAuthenticated === true ||
    (headerAuthenticated === null && authenticated === true);
  const hasManagementAccess = portalAccess.includes("management");
  const hasPosAccess = portalAccess.includes("pos");
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
          {hasManagementAccess ? (
            <Link
              className="management-link"
              href="/management"
              aria-current={pathname.startsWith("/management") ? "page" : undefined}
            >
              Management
            </Link>
          ) : null}
          {hasPosAccess ? (
            <Link
              className="management-link"
              href="/pos"
              aria-current={pathname.startsWith("/pos") ? "page" : undefined}
            >
              POS
            </Link>
          ) : null}
          <NotificationCentre enabled={isAuthenticated} />
          <Link
            className="wishlist-link"
            href={
              isAuthenticated
                ? "/account/wishlist"
                : `/login?next=${encodeURIComponent("/account/wishlist")}`
            }
            aria-label={`Wishlist, ${wishlistItemCount} ${wishlistItemCount === 1 ? "item" : "items"}`}
          >
            <WishlistIcon />
            <CartItemCount count={wishlistItemCount} className="wishlist-link__count" />
          </Link>
          <button
            className="cart-link"
            type="button"
            aria-label={`Cart, ${cartItemCount} ${cartItemCount === 1 ? "item" : "items"}`}
            aria-haspopup="dialog"
            aria-expanded={isCartOpen}
            onClick={() => {
              setIsMenuOpen(false);
              if (authenticationLoading) return;
              if (!isAuthenticated) {
                window.location.assign(
                  `/login?next=${encodeURIComponent("/shop")}`,
                );
                return;
              }
              setIsCartOpen(true);
            }}
          >
            <CartIcon />
            <CartItemCount count={cartItemCount} />
          </button>
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
            {hasManagementAccess ? (
              <Link
                className="mobile-nav__link"
                href="/management"
                aria-current={
                  pathname.startsWith("/management") ? "page" : undefined
                }
                onClick={() => setIsMenuOpen(false)}
              >
                Management portal
              </Link>
            ) : null}
            {hasPosAccess ? (
              <Link
                className="mobile-nav__link"
                href="/pos"
                aria-current={pathname.startsWith("/pos") ? "page" : undefined}
                onClick={() => setIsMenuOpen(false)}
              >
                Point of sale
              </Link>
            ) : null}
            <Link
              className="mobile-nav__link"
              href={
                isAuthenticated
                  ? "/account/wishlist"
                  : `/login?next=${encodeURIComponent("/account/wishlist")}`
              }
              aria-label={`Wishlist, ${wishlistItemCount} ${wishlistItemCount === 1 ? "item" : "items"}`}
              aria-current={pathname.startsWith("/account/wishlist") ? "page" : undefined}
              onClick={() => setIsMenuOpen(false)}
            >
              Wishlist
              <CartItemCount count={wishlistItemCount} className="mobile-nav__count" />
            </Link>
            <Link
              className="mobile-nav__link"
              href={
                isAuthenticated
                  ? "/cart"
                  : `/login?next=${encodeURIComponent("/cart")}`
              }
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
      <CartDrawer open={isCartOpen} onClose={closeCart} />
    </header>
  );
}

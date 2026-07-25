"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useRef } from "react";

import { useCartCount } from "@/components/cart/cart-count-context";
import { ButtonLink } from "@/components/ui/button";
import { formatGhanaCedis } from "@/lib/formatters";

export function CartDrawer({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const drawer = useRef<HTMLElement>(null);
  const { isHydrated, cartItems, itemCount, cartNotice, removeCartItem } = useCartCount();
  const subtotal = useMemo(
    () =>
      cartItems.reduce(
        (total, item) => total + Number(item.unitPrice) * item.quantity,
        0,
      ),
    [cartItems],
  );

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    document.body.style.overflow = "hidden";
    closeButton.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") {
        const focusable = Array.from(
          drawer.current?.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
          ) ?? [],
        );
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
      previouslyFocused?.focus();
    };
  }, [onClose, open]);

  if (!open) return null;

  return (
    <div className="cart-drawer-layer">
      <button
        className="cart-drawer__backdrop"
        type="button"
        aria-label="Close cart preview"
        onClick={onClose}
      />
      <aside
        ref={drawer}
        className="cart-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cart-drawer-title"
      >
        <header>
          <div>
            <p>Your cart</p>
            <h2 id="cart-drawer-title">Cart preview</h2>
          </div>
          <button
            ref={closeButton}
            className="cart-drawer__close"
            type="button"
            aria-label="Close cart preview"
            onClick={onClose}
          >
            ×
          </button>
        </header>

        <div className="cart-drawer__body">
          {cartNotice ? <p className="cart-drawer__message" role="status">{cartNotice}</p> : null}
          {!isHydrated ? (
            <p className="cart-drawer__message">Loading your cart...</p>
          ) : !cartItems.length ? (
            <div className="cart-drawer__empty">
              <span aria-hidden="true">🛍</span>
              <h3>Your cart is empty</h3>
              <p>Add products from the shop to see them here.</p>
              <ButtonLink href="/shop" onClick={onClose}>Browse products</ButtonLink>
            </div>
          ) : (
            <div className="cart-drawer__items">
              {cartItems.map((item) => (
                <article key={item.variantId}>
                  <Link
                    className="cart-drawer__image"
                    href={`/shop/${item.productSlug}`}
                    onClick={onClose}
                  >
                    <Image src={item.imageSrc || "/images/hero2.jpeg"} alt="" fill sizes="5rem" />
                  </Link>
                  <div>
                    <Link href={`/shop/${item.productSlug}`} onClick={onClose}>
                      <h3>{item.productName}</h3>
                    </Link>
                    <p>{item.variantName} / {item.sku}</p>
                    <span>{item.quantity} × {formatGhanaCedis(item.unitPrice)}</span>
                    <button type="button" onClick={() => removeCartItem(item.variantId)}>Remove</button>
                  </div>
                  <strong>{formatGhanaCedis(Number(item.unitPrice) * item.quantity)}</strong>
                </article>
              ))}
            </div>
          )}
        </div>

        {isHydrated && cartItems.length ? (
          <footer>
            <div><span>Subtotal ({itemCount} {itemCount === 1 ? "item" : "items"})</span><strong>{formatGhanaCedis(subtotal)}</strong></div>
            <ButtonLink href="/checkout" fullWidth onClick={onClose}>Continue to Checkout</ButtonLink>
            <ButtonLink href="/cart" variant="outline" fullWidth onClick={onClose}>View full cart</ButtonLink>
            <small>Delivery and final availability are confirmed at checkout.</small>
          </footer>
        ) : null}
      </aside>
    </div>
  );
}

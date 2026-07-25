"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo } from "react";

import { useCartCount } from "@/components/cart/cart-count-context";
import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingIndicator } from "@/components/ui/loading-indicator";
import { formatGhanaCedis } from "@/lib/formatters";
import { useWishlist } from "@/components/wishlist/wishlist-context";

export function CartPageContent() {
  const { authenticated, loading: authenticationLoading } = useWishlist();
  const {
    isHydrated,
    cartItems,
    cartNotice,
    updateCartItemQuantity,
    removeCartItem,
    clearCart,
  } = useCartCount();
  const subtotal = useMemo(
    () =>
      cartItems.reduce(
        (total, item) => total + Number(item.unitPrice) * item.quantity,
        0,
      ),
    [cartItems],
  );

  useEffect(() => {
    if (!authenticationLoading && authenticated === false) {
      window.location.replace(`/login?next=${encodeURIComponent("/cart")}`);
    }
  }, [authenticated, authenticationLoading]);

  if (!isHydrated || authenticationLoading || authenticated !== true) {
    return <LoadingIndicator label="Loading your cart" presentation="panel" size="large" />;
  }

  if (!cartItems.length) {
    return (
      <EmptyState
        title="Your cart is empty"
        description="Browse the beauty shop and add products before continuing to checkout."
        action={<ButtonLink href="/shop">Browse products</ButtonLink>}
      />
    );
  }

  return (
    <div className="cart-layout">
      <section className="cart-items" aria-label="Cart items">
        {cartNotice ? <p className="product-card__action-message" role="status">{cartNotice}</p> : null}
        <header>
          <h2>{cartItems.length} {cartItems.length === 1 ? "product" : "products"}</h2>
          <Button type="button" variant="outline" size="small" onClick={clearCart}>Clear cart</Button>
        </header>
        <div className="cart-items__list">
          {cartItems.map((item) => {
            const lineSubtotal = Number(item.unitPrice) * item.quantity;
            return (
              <article className="cart-line" key={item.variantId}>
                <Link className="cart-line__image" href={`/shop/${item.productSlug}`} aria-label={`View ${item.productName}`}>
                  <Image src={item.imageSrc || "/images/hero2.jpeg"} alt="" fill sizes="8rem" />
                </Link>
                <div className="cart-line__details">
                  <div>
                    <Link href={`/shop/${item.productSlug}`}><h3>{item.productName}</h3></Link>
                    <p>{item.variantName}</p>
                    <small>SKU: {item.sku}</small>
                  </div>
                  <div className="cart-line__price"><span>Unit price</span><strong>{formatGhanaCedis(item.unitPrice)}</strong></div>
                  <div className="cart-line__quantity">
                    <span>Quantity</span>
                    <div className="quantity-control">
                      <button type="button" aria-label={`Decrease ${item.productName} quantity`} disabled={item.quantity === 1} onClick={() => updateCartItemQuantity(item.variantId, item.quantity - 1)}>−</button>
                      <input type="number" min={1} max={20} value={item.quantity} aria-label={`${item.productName} quantity`} onChange={(event) => updateCartItemQuantity(item.variantId, Number(event.target.value) || 1)} />
                      <button type="button" aria-label={`Increase ${item.productName} quantity`} disabled={item.quantity === 20} onClick={() => updateCartItemQuantity(item.variantId, item.quantity + 1)}>+</button>
                    </div>
                  </div>
                  <div className="cart-line__subtotal"><span>Subtotal</span><strong>{formatGhanaCedis(lineSubtotal)}</strong></div>
                  <button className="cart-line__remove" type="button" onClick={() => removeCartItem(item.variantId)}>Remove</button>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <aside className="cart-summary" aria-label="Order summary">
        <p>Order summary</p>
        <h2>Cart total</h2>
        <dl>
          <div><dt>Items</dt><dd>{cartItems.reduce((sum, item) => sum + item.quantity, 0)}</dd></div>
          <div><dt>Subtotal</dt><dd>{formatGhanaCedis(subtotal)}</dd></div>
          <div><dt>Delivery</dt><dd>Calculated at checkout</dd></div>
        </dl>
        <div className="cart-summary__total"><span>Total before delivery</span><strong>{formatGhanaCedis(subtotal)}</strong></div>
        <ButtonLink href="/checkout" fullWidth size="large">Continue to Checkout</ButtonLink>
        <ButtonLink href="/shop" variant="outline" fullWidth>Continue shopping</ButtonLink>
        <small>Stock and pickup availability will be checked again during checkout.</small>
      </aside>
    </div>
  );
}

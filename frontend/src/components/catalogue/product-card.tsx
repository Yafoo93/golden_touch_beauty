"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { useCartCount } from "@/components/cart/cart-count-context";
import { ButtonLink } from "@/components/ui/button";
import { useWishlist } from "@/components/wishlist/wishlist-context";
import { formatGhanaCedis } from "@/lib/formatters";

export type ProductCardProps = {
  name: string;
  slug: string;
  category: string;
  description: string;
  price: number | string;
  imageSrc: string;
  variantLabel?: string;
  variantId?: string;
  sku?: string;
  inStock: boolean;
  badge?: string;
};

export function ProductCard({
  name,
  slug,
  category,
  description,
  price,
  imageSrc,
  variantLabel,
  variantId,
  sku,
  inStock,
  badge,
}: ProductCardProps) {
  const detailsHref = `/shop/${slug}`;
  const { cartItems, addCartItem, removeCartItem } = useCartCount();
  const { addFavorite, removeFavorite, isFavorite, authenticated, loading } = useWishlist();
  const [message, setMessage] = useState("");
  const [wishlistSaving, setWishlistSaving] = useState(false);
  const favorite = isFavorite(slug);
  const canQuickAdd = Boolean(
    variantId && sku && (inStock || badge === "Pre-order"),
  );
  const isInCart = Boolean(
    variantId &&
      cartItems.some((cartItem) => cartItem.variantId === variantId),
  );

  async function toggleDefaultVariantInCart() {
    if (!variantId || !sku || !canQuickAdd) return;
    if (loading) return;
    if (!authenticated) {
      window.location.assign(`/login?next=${encodeURIComponent(detailsHref)}`);
      return;
    }
    try {
      if (isInCart) {
        await removeCartItem(variantId);
        setMessage("Removed from cart.");
        return;
      }
      const result = await addCartItem({
        variantId,
        sku,
        productSlug: slug,
        productName: name,
        variantName: variantLabel || "Standard",
        unitPrice: String(price),
        quantity: 1,
        imageSrc,
      });
      setMessage(
        result.accepted
          ? result.message || "Added to cart at the current price."
          : result.message || "This product is no longer available.",
      );
    } catch {
      setMessage("The cart could not be updated. Please try again.");
    }
  }

  async function toggleWishlist() {
    if (loading) return;
    if (!authenticated) {
      window.location.assign(`/login?next=${encodeURIComponent(detailsHref)}`);
      return;
    }
    setWishlistSaving(true);
    try {
      if (favorite) {
        await removeFavorite(slug);
        setMessage("Removed from wishlist.");
      } else {
        const result = await addFavorite(slug);
        setMessage(result === "signin" ? "Redirecting to sign in..." : "Saved to wishlist.");
      }
    } catch {
      setMessage("Wishlist could not be updated.");
    } finally {
      setWishlistSaving(false);
    }
  }

  return (
    <article className="catalogue-card product-card">
      <Link
        href={detailsHref}
        className="catalogue-card__media"
        aria-label={`View ${name}`}
      >
        <Image
          src={imageSrc}
          alt=""
          fill
          sizes="(max-width: 48rem) 100vw, (max-width: 75rem) 50vw, 33vw"
          className="catalogue-card__image"
        />
        {badge ? <span className="catalogue-card__badge">{badge}</span> : null}
      </Link>
      <div className="catalogue-card__body">
        <p className="catalogue-card__category">{category}</p>
        <h3>
          <Link href={detailsHref}>{name}</Link>
        </h3>
        <p className="catalogue-card__description">{description}</p>
        <div className="product-card__meta">
          {variantLabel ? <span>{variantLabel}</span> : null}
          <span
            className={
              inStock ? "stock stock--available" : "stock stock--unavailable"
            }
          >
            {inStock ? "In stock" : "Out of stock"}
          </span>
        </div>
        <div className="catalogue-card__footer">
          <p className="catalogue-card__price">{formatGhanaCedis(price)}</p>
          <div className="product-card__actions">
            <ButtonLink
              href={detailsHref}
              variant={inStock ? "gold" : "black"}
              size="small"
              aria-label={`View ${name}`}
            >
              View product
            </ButtonLink>
            <button
              type="button"
              className={
                isInCart
                  ? "product-card__icon-action product-card__icon-action--in-cart"
                  : "product-card__icon-action"
              }
              onClick={toggleDefaultVariantInCart}
              disabled={!canQuickAdd}
              aria-label={
                isInCart
                  ? `Remove ${name} from cart`
                  : `Add ${name} to cart`
              }
              aria-pressed={isInCart}
              title={
                canQuickAdd
                  ? isInCart
                    ? "Remove from cart"
                    : badge === "Pre-order"
                      ? "Add pre-order to cart"
                      : "Add to cart"
                  : "Currently out of stock"
              }
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 4h2l2.1 10.1a2 2 0 0 0 2 1.6h7.8a2 2 0 0 0 2-1.6L20 7H6" />
                <path d="M12 9v5M9.5 11.5h5" />
                <circle cx="9" cy="20" r="1" />
                <circle cx="18" cy="20" r="1" />
              </svg>
            </button>
            <button
              type="button"
              className={
                favorite
                  ? "product-card__icon-action product-card__icon-action--favorite"
                  : "product-card__icon-action"
              }
              onClick={toggleWishlist}
              disabled={wishlistSaving}
              aria-label={
                favorite
                  ? `Remove ${name} from wishlist`
                  : `Add ${name} to wishlist`
              }
              aria-pressed={favorite}
              title={favorite ? "Remove from wishlist" : "Add to wishlist"}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m12 2.8 2.8 5.7 6.3.9-4.55 4.43 1.07 6.27L12 17.14 6.38 20.1l1.07-6.27L2.9 9.4l6.3-.9L12 2.8Z" />
              </svg>
            </button>
          </div>
        </div>
        {message ? (
          <p className="product-card__action-message" role="status">
            {message}
          </p>
        ) : null}
      </div>
    </article>
  );
}

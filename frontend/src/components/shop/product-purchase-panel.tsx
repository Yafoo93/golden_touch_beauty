"use client";

import { useMemo, useState } from "react";

import { useCartCount } from "@/components/cart/cart-count-context";
import { Button } from "@/components/ui/button";
import { useWishlist } from "@/components/wishlist/wishlist-context";
import { formatGhanaCedis } from "@/lib/formatters";
import type { ProductDetail, ProductVariant } from "@/lib/products";

function availabilityLabel(variant: ProductVariant) {
  if (variant.availability === "in_stock") return "In stock";
  if (variant.availability === "preorder") return "Available for pre-order";
  return "Out of stock";
}

export function ProductPurchasePanel({ product }: { product: ProductDetail }) {
  const initialVariant =
    product.variants.find((variant) => variant.availability === "in_stock") ??
    product.variants.find((variant) => variant.availability === "preorder") ??
    product.variants[0];
  const [variantId, setVariantId] = useState(initialVariant?.id ?? "");
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState("");
  const [favoriteSaving, setFavoriteSaving] = useState(false);
  const { addCartItem } = useCartCount();
  const { addFavorite, removeFavorite, isFavorite, authenticated, loading } = useWishlist();
  const favorite = isFavorite(product.slug);
  const selected = useMemo(
    () => product.variants.find((variant) => variant.id === variantId),
    [product.variants, variantId],
  );
  const canAdd = selected && selected.availability !== "out_of_stock";

  async function addToCart() {
    if (!selected || !canAdd) return;
    if (loading) return;
    if (!authenticated) {
      window.location.assign(
        `/login?next=${encodeURIComponent(`/shop/${product.slug}`)}`,
      );
      return;
    }
    try {
      const result = await addCartItem({
        variantId: selected.id,
        sku: selected.sku,
        productSlug: product.slug,
        productName: product.name,
        variantName: selected.name,
        unitPrice: selected.selling_price,
        quantity,
        imageSrc: product.image_path || "/images/hero2.jpeg",
      });
      setMessage(
        result.accepted
          ? result.message || `${quantity} ${quantity === 1 ? "item" : "items"} added at the current price.`
          : result.message || "This product is no longer available.",
      );
    } catch {
      setMessage("The cart could not be updated. Please try again.");
    }
  }

  if (!selected) {
    return (
      <p className="product-purchase-panel__unavailable">
        This product currently has no available variants.
      </p>
    );
  }

  return (
    <div className="product-purchase-panel">
      <div className="product-purchase-panel__price">
        <span>Selected price</span>
        <strong>{formatGhanaCedis(selected.selling_price)}</strong>
      </div>

      <fieldset className="product-variant-picker">
        <legend>Choose a variant</legend>
        <div>
          {product.variants.map((variant) => (
            <label
              className={
                variant.id === selected.id
                  ? "product-variant-option product-variant-option--selected"
                  : "product-variant-option"
              }
              key={variant.id}
            >
              <input
                type="radio"
                name="product-variant"
                value={variant.id}
                checked={variant.id === selected.id}
                onChange={() => {
                  setVariantId(variant.id);
                  setMessage("");
                }}
              />
              <span>
                <strong>{variant.name}</strong>
                <small>{formatGhanaCedis(variant.selling_price)}</small>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="product-purchase-panel__availability">
        <strong
          className={`stock stock--${selected.availability === "in_stock" ? "available" : "unavailable"}`}
        >
          {availabilityLabel(selected)}
        </strong>
        {selected.available_at.length ? (
          <span>
            Available at{" "}
            {selected.available_at.map((branch) => branch.branch_name).join(" and ")}
          </span>
        ) : selected.is_preorder && selected.estimated_availability_date ? (
          <span>
            Estimated availability:{" "}
            {new Intl.DateTimeFormat("en-GH", { dateStyle: "medium" }).format(
              new Date(`${selected.estimated_availability_date}T00:00:00`),
            )}
          </span>
        ) : (
          <span>Contact Golden Touch for restock information.</span>
        )}
      </div>

      <div className="product-purchase-panel__controls">
        <label htmlFor="product-quantity">Quantity</label>
        <div className="quantity-control">
          <button
            type="button"
            aria-label="Decrease quantity"
            disabled={quantity === 1}
            onClick={() => setQuantity((current) => Math.max(1, current - 1))}
          >
            −
          </button>
          <input
            id="product-quantity"
            type="number"
            min={1}
            max={20}
            value={quantity}
            onChange={(event) =>
              setQuantity(Math.min(20, Math.max(1, Number(event.target.value) || 1)))
            }
          />
          <button
            type="button"
            aria-label="Increase quantity"
            disabled={quantity === 20}
            onClick={() => setQuantity((current) => Math.min(20, current + 1))}
          >
            +
          </button>
        </div>
      </div>

      <div className="product-purchase-panel__actions">
        <Button type="button" onClick={addToCart} disabled={!canAdd}>
          {selected.availability === "preorder" ? "Add pre-order to cart" : "Add to cart"}
        </Button>
        <Button
          type="button"
          variant="outline"
          aria-pressed={favorite}
          loading={favoriteSaving}
          loadingLabel="Saving..."
          onClick={async () => {
            if (loading) return;
            if (!authenticated) {
              window.location.assign(
                `/login?next=${encodeURIComponent(`/shop/${product.slug}`)}`,
              );
              return;
            }
            setFavoriteSaving(true);
            try {
              if (favorite) {
                await removeFavorite(product.slug);
                setMessage("Removed from your wishlist.");
              } else {
                const result = await addFavorite(product.slug);
                setMessage(
                  result === "signin"
                    ? "Sign in to save products to your wishlist."
                    : "Saved to your wishlist.",
                );
              }
            } catch {
              setMessage("Your wishlist could not be updated. Please try again.");
            } finally {
              setFavoriteSaving(false);
            }
          }}
        >
          {favorite ? "♥ Favorited" : "♡ Favorite"}
        </Button>
      </div>
      {message ? (
        <p className="product-purchase-panel__message" role="status">
          {message}
        </p>
      ) : null}
      <p className="product-purchase-panel__note">
        Final stock and pickup eligibility are rechecked during checkout.
      </p>
    </div>
  );
}

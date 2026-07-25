"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError, apiFetch } from "@/lib/api";

type CartCountContextValue = {
  isHydrated: boolean;
  itemCount: number;
  cartItems: CartItem[];
  cartNotice: string;
  addCartItem: (item: CartItem) => Promise<CartChangeResult>;
  updateCartItemQuantity: (variantId: string, quantity: number) => Promise<CartChangeResult>;
  removeCartItem: (variantId: string) => Promise<CartChangeResult>;
  clearCart: () => Promise<CartChangeResult>;
  setItemCount: (count: number) => void;
  incrementItemCount: (amount?: number) => void;
  decrementItemCount: (amount?: number) => void;
  resetItemCount: () => void;
};

export type CartItem = {
  variantId: string;
  sku: string;
  productSlug: string;
  productName: string;
  variantName: string;
  unitPrice: string;
  quantity: number;
  imageSrc: string;
};

type ServerCartItem = {
  variant_id: string;
  sku: string;
  product_slug: string;
  product_name: string;
  variant_name: string;
  unit_price: string;
  quantity: number;
  image_src: string;
};

type CartAdjustment = {
  variant_id: string;
  code: "out_of_stock" | "quantity_reduced" | "unavailable";
  message: string;
};

type CartValidationResponse = {
  items: ServerCartItem[];
  adjustments: CartAdjustment[];
};

export type CartChangeResult = {
  accepted: boolean;
  message: string;
};

const CartCountContext = createContext<CartCountContextValue | null>(null);
const normalizeCount = (count: number) => Math.max(0, Math.floor(Number.isFinite(count) ? count : 0));
function serverItemsToCart(items: ServerCartItem[]): CartItem[] {
  return items.map((item) => ({
    variantId: item.variant_id,
    sku: item.sku,
    productSlug: item.product_slug,
    productName: item.product_name,
    variantName: item.variant_name,
    unitPrice: item.unit_price,
    quantity: item.quantity,
    imageSrc: item.image_src,
  }));
}

export function CartCountProvider({ children }: { children: ReactNode }) {
  const [itemCount, updateItemCount] = useState(0);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartNotice, setCartNotice] = useState("");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    let active = true;
    apiFetch<ServerCartItem[]>("products/cart/")
      .then((saved) => {
        if (!active) return;
        const canonicalItems = serverItemsToCart(saved);
        setCartItems(canonicalItems);
        updateItemCount(
          canonicalItems.reduce((total, item) => total + normalizeCount(item.quantity), 0),
        );
      })
      .catch((error) => {
        if (
          active &&
          error instanceof ApiError &&
          [401, 403].includes(error.status)
        ) {
          setCartItems([]);
          updateItemCount(0);
        }
      })
      .finally(() => {
        if (active) setHydrated(true);
      });
    return () => {
      active = false;
    };
  }, []);

  async function validateAndInstall(
    proposedItems: CartItem[],
    targetVariantId?: string,
  ): Promise<CartChangeResult> {
    let response: CartValidationResponse;
    try {
      response = await apiFetch<CartValidationResponse>(
        "products/cart/validate/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            items: proposedItems.map((item) => ({
              variant_id: item.variantId,
              quantity: item.quantity,
            })),
          }),
        },
      );
    } catch (error) {
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        const returnTo = `${window.location.pathname}${window.location.search}`;
        window.location.assign(`/login?next=${encodeURIComponent(returnTo)}`);
      }
      throw error;
    }
    return installCartResponse(response, targetVariantId);
  }

  function installCartResponse(
    response: CartValidationResponse,
    targetVariantId?: string,
  ): CartChangeResult {
    const canonicalItems = serverItemsToCart(response.items);
    const message = response.adjustments.map((item) => item.message).join(" ");
    setCartItems(canonicalItems);
    updateItemCount(
      canonicalItems.reduce(
        (total, item) => total + normalizeCount(item.quantity),
        0,
      ),
    );
    setCartNotice(message);
    return {
      accepted:
        !targetVariantId ||
        canonicalItems.some((item) => item.variantId === targetVariantId),
      message,
    };
  }

  const value = useMemo<CartCountContextValue>(() => ({
    isHydrated: hydrated,
    itemCount,
    cartItems,
    cartNotice,
    addCartItem: async (item) => {
      const quantity = Math.max(1, Math.floor(item.quantity));
      try {
        const response = await apiFetch<CartValidationResponse>(
          "products/cart/items/",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              variant_id: item.variantId,
              quantity: Math.min(20, quantity),
            }),
          },
        );
        return installCartResponse(response, item.variantId);
      } catch (error) {
        if (error instanceof ApiError && [401, 403].includes(error.status)) {
          const returnTo = `${window.location.pathname}${window.location.search}`;
          window.location.assign(`/login?next=${encodeURIComponent(returnTo)}`);
        }
        throw error;
      }
    },
    updateCartItemQuantity: async (variantId, requestedQuantity) => {
      const quantity = Math.min(20, Math.max(1, Math.floor(requestedQuantity)));
      const existing = cartItems.find((item) => item.variantId === variantId);
      if (!existing) return { accepted: false, message: "That item is no longer in your cart." };
      try {
        const response = await apiFetch<CartValidationResponse>(
          `products/cart/items/${encodeURIComponent(variantId)}/`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity }),
          },
        );
        return installCartResponse(response, variantId);
      } catch (error) {
        if (error instanceof ApiError && [401, 403].includes(error.status)) {
          const returnTo = `${window.location.pathname}${window.location.search}`;
          window.location.assign(`/login?next=${encodeURIComponent(returnTo)}`);
        }
        throw error;
      }
    },
    removeCartItem: async (variantId) => {
      const removed = cartItems.find((item) => item.variantId === variantId);
      if (!removed) return { accepted: false, message: "That item is no longer in your cart." };
      try {
        const response = await apiFetch<CartValidationResponse>(
          `products/cart/items/${encodeURIComponent(variantId)}/`,
          { method: "DELETE" },
        );
        return installCartResponse(response);
      } catch (error) {
        if (error instanceof ApiError && [401, 403].includes(error.status)) {
          const returnTo = `${window.location.pathname}${window.location.search}`;
          window.location.assign(`/login?next=${encodeURIComponent(returnTo)}`);
        }
        throw error;
      }
    },
    clearCart: async () => validateAndInstall([]),
    setItemCount: (count) => updateItemCount(normalizeCount(count)),
    incrementItemCount: (amount = 1) => updateItemCount((current) => current + normalizeCount(amount)),
    decrementItemCount: (amount = 1) => updateItemCount((current) => Math.max(0, current - normalizeCount(amount))),
    resetItemCount: () => {
      setCartItems([]);
      updateItemCount(0);
    },
  }), [cartItems, cartNotice, hydrated, itemCount]);
  return <CartCountContext.Provider value={value}>{children}</CartCountContext.Provider>;
}

export function useCartCount() {
  const context = useContext(CartCountContext);
  if (!context) throw new Error("useCartCount must be used inside CartCountProvider.");
  return context;
}

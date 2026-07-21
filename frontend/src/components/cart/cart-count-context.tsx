"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type CartCountContextValue = {
  itemCount: number;
  setItemCount: (count: number) => void;
  incrementItemCount: (amount?: number) => void;
  decrementItemCount: (amount?: number) => void;
  resetItemCount: () => void;
};

const CartCountContext = createContext<CartCountContextValue | null>(null);
const normalizeCount = (count: number) => Math.max(0, Math.floor(Number.isFinite(count) ? count : 0));

export function CartCountProvider({ children }: { children: ReactNode }) {
  const [itemCount, updateItemCount] = useState(0);
  const value = useMemo<CartCountContextValue>(() => ({
    itemCount,
    setItemCount: (count) => updateItemCount(normalizeCount(count)),
    incrementItemCount: (amount = 1) => updateItemCount((current) => current + normalizeCount(amount)),
    decrementItemCount: (amount = 1) => updateItemCount((current) => Math.max(0, current - normalizeCount(amount))),
    resetItemCount: () => updateItemCount(0),
  }), [itemCount]);
  return <CartCountContext.Provider value={value}>{children}</CartCountContext.Provider>;
}

export function useCartCount() {
  const context = useContext(CartCountContext);
  if (!context) throw new Error("useCartCount must be used inside CartCountProvider.");
  return context;
}

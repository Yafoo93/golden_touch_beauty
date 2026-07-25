"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";

import type { ProductCardProps } from "@/components/catalogue/product-card";
import { ApiError, apiFetch, ensureCsrfCookie } from "@/lib/api";
import {
  productSummaryToCard,
  type PublicProductSummary,
} from "@/lib/products";

type WishlistContextValue = {
  products: ProductCardProps[];
  itemCount: number;
  authenticated: boolean | null;
  loading: boolean;
  isFavorite: (slug: string) => boolean;
  addFavorite: (slug: string) => Promise<"added" | "signin">;
  removeFavorite: (slug: string) => Promise<void>;
};

const WishlistContext = createContext<WishlistContextValue | null>(null);

export function WishlistProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [products, setProducts] = useState<ProductCardProps[]>([]);
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const response = await apiFetch<PublicProductSummary[]>("products/wishlist/");
      setProducts(
        response
          .map(productSummaryToCard)
          .filter((product): product is ProductCardProps => product !== null),
      );
      setAuthenticated(true);
    } catch (error) {
      if (error instanceof ApiError && [401, 403].includes(error.status)) {
        setProducts([]);
        setAuthenticated(false);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeout = window.setTimeout(() => void refresh(), 0);
    return () => window.clearTimeout(timeout);
  }, [pathname, refresh]);

  const value = useMemo<WishlistContextValue>(
    () => ({
      products,
      itemCount: products.length,
      authenticated,
      loading,
      isFavorite: (slug) => products.some((product) => product.slug === slug),
      addFavorite: async (slug) => {
        try {
          await ensureCsrfCookie();
          const response = await apiFetch<PublicProductSummary>(
            "products/wishlist/",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ product_slug: slug }),
            },
          );
          const product = productSummaryToCard(response);
          if (product) {
            setProducts((current) =>
              current.some((item) => item.slug === product.slug)
                ? current
                : [product, ...current],
            );
          }
          setAuthenticated(true);
          return "added";
        } catch (error) {
          if (error instanceof ApiError && [401, 403].includes(error.status)) {
            setAuthenticated(false);
            const returnTo = `${window.location.pathname}${window.location.search}`;
            window.location.assign(`/login?next=${encodeURIComponent(returnTo)}`);
            return "signin";
          }
          throw error;
        }
      },
      removeFavorite: async (slug) => {
        try {
          await ensureCsrfCookie();
          await apiFetch(`products/wishlist/${encodeURIComponent(slug)}/`, {
            method: "DELETE",
          });
          setProducts((current) =>
            current.filter((product) => product.slug !== slug),
          );
        } catch (error) {
          if (error instanceof ApiError && [401, 403].includes(error.status)) {
            setAuthenticated(false);
            const returnTo = `${window.location.pathname}${window.location.search}`;
            window.location.assign(`/login?next=${encodeURIComponent(returnTo)}`);
          }
          throw error;
        }
      },
    }),
    [authenticated, loading, products],
  );

  return (
    <WishlistContext.Provider value={value}>
      {children}
    </WishlistContext.Provider>
  );
}

export function useWishlist() {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error("useWishlist must be used inside WishlistProvider.");
  }
  return context;
}

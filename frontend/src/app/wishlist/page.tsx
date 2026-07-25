"use client";

import { useEffect } from "react";
import { ProductCard } from "@/components/catalogue/product-card";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import { useWishlist } from "@/components/wishlist/wishlist-context";

export default function WishlistPage() {
  const { products, authenticated, loading } = useWishlist();

  useEffect(() => {
    if (!loading && authenticated === false) {
      window.location.replace(`/login?next=${encodeURIComponent("/wishlist")}`);
    }
  }, [authenticated, loading]);

  if (loading || authenticated !== true) {
    return (
      <main className="wishlist-page">
        <div className="wishlist-page__loading" role="status">
          <span aria-hidden="true" />
          {authenticated === false ? "Redirecting to sign in..." : "Loading your wishlist..."}
        </div>
      </main>
    );
  }

  return (
    <main className="wishlist-page">
      <PageHero
        eyebrow="Your saved products"
        title="My"
        accentTitle="Wishlist"
        description="Keep your preferred Golden Touch products together and return when you are ready to purchase."
        size="compact"
      />
      <section className="wishlist-page__content" aria-labelledby="wishlist-title">
        <header>
          <div>
            <p>Customer account</p>
            <h2 id="wishlist-title">Saved products</h2>
          </div>
          {authenticated && products.length ? (
            <span>
              {products.length} {products.length === 1 ? "product" : "products"}
            </span>
          ) : null}
        </header>

        {products.length ? (
          <div className="catalogue-grid">
            {products.map((product) => (
              <ProductCard key={product.slug} {...product} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="Your wishlist is empty"
            description="Select the star or Favorite button on any product to save it here."
            action={<ButtonLink href="/shop">Browse products</ButtonLink>}
          />
        )}
      </section>
    </main>
  );
}

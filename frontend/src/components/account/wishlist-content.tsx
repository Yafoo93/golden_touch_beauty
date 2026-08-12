"use client";

import { ProductCard } from "@/components/catalogue/product-card";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { useWishlist } from "@/components/wishlist/wishlist-context";

export function AccountWishlistContent() {
  const { products, authenticated, loading } = useWishlist();

  if (loading || authenticated !== true) {
    return <div className="wishlist-page__loading" role="status"><span aria-hidden="true" />Loading your wishlist...</div>;
  }

  return <section className="wishlist-page__content" aria-labelledby="wishlist-title">
    <header><div><p>Saved products</p><h2 id="wishlist-title">My wishlist</h2></div>{products.length ? <span>{products.length} {products.length === 1 ? "product" : "products"}</span> : null}</header>
    {products.length ? <div className="catalogue-grid">{products.map((product) => <ProductCard key={product.slug} {...product} />)}</div> : <EmptyState title="Your wishlist is empty" description="Select the star or Favorite button on any product to save it here." action={<ButtonLink href="/shop">Browse products</ButtonLink>} />}
  </section>;
}

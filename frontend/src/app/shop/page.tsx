import type { Metadata } from "next";
import Link from "next/link";

import { ProductCard } from "@/components/catalogue/product-card";
import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import {
  getProductCatalogue,
  type ProductAvailability,
} from "@/lib/products";

export const metadata: Metadata = {
  title: "Beauty Shop",
  description:
    "Shop published Golden Touch face, body, hair, and beauty products available from our Ghana branches.",
};

const availabilityFilters: {
  value: ProductAvailability;
  label: string;
}[] = [
  { value: "", label: "All availability" },
  { value: "in_stock", label: "In stock" },
  { value: "preorder", label: "Pre-order" },
  { value: "out_of_stock", label: "Out of stock" },
];

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function shopHref({
  category,
  search,
  availability,
}: {
  category?: string;
  search?: string;
  availability?: string;
}) {
  const query = new URLSearchParams();
  if (category) query.set("category", category);
  if (search) query.set("search", search);
  if (availability) query.set("availability", availability);
  return `/shop${query.size ? `?${query.toString()}` : ""}`;
}

export default async function ShopPage({
  searchParams,
}: {
  searchParams: Promise<{
    category?: string | string[];
    search?: string | string[];
    availability?: string | string[];
  }>;
}) {
  const params = await searchParams;
  const category = first(params.category).trim();
  const search = first(params.search).trim();
  const requestedAvailability = first(params.availability).trim();
  const availability = availabilityFilters.some(
    (item) => item.value === requestedAvailability,
  )
    ? (requestedAvailability as ProductAvailability)
    : "";
  const catalogue = await getProductCatalogue({
    category,
    search,
    availability,
  });
  const activeCategory = catalogue.categories.find(
    (item) => item.slug === category,
  );
  const activeAvailability = availabilityFilters.find(
    (item) => item.value === availability,
  );

  return (
    <main className="shop-page">
      <PageHero
        eyebrow="Golden Touch shop"
        title="Care For Your Skin"
        accentTitle="Beyond The Clinic"
        description="Explore approved face, body, hair, and beauty products currently offered through Golden Touch."
        backgroundImage="/images/hero1.jpeg"
        backgroundPosition="center 42%"
        size="compact"
      />

      <section className="services-catalogue" aria-labelledby="shop-title">
        <header className="services-catalogue__header">
          <div>
            <p>Find your products</p>
            <h2 id="shop-title">Published products</h2>
            <span>
              Search the catalogue and check current branch stock or pre-order
              availability.
            </span>
          </div>
          <form className="services-search" action="/shop" method="get" role="search">
            {category ? <input type="hidden" name="category" value={category} /> : null}
            {availability ? (
              <input type="hidden" name="availability" value={availability} />
            ) : null}
            <label htmlFor="product-search">Search products</label>
            <div>
              <input
                id="product-search"
                name="search"
                type="search"
                defaultValue={search}
                placeholder="Try cream, serum, soap..."
              />
              <Button type="submit" size="small">Search</Button>
            </div>
          </form>
        </header>

        <nav className="service-filters" aria-label="Filter products by category">
          <Link
            href={shopHref({ search, availability })}
            className={!category ? "service-filter service-filter--active" : "service-filter"}
            aria-current={!category ? "page" : undefined}
          >
            All products
          </Link>
          {catalogue.categories.map((item) => (
            <Link
              href={shopHref({ category: item.slug, search, availability })}
              className={category === item.slug ? "service-filter service-filter--active" : "service-filter"}
              aria-current={category === item.slug ? "page" : undefined}
              key={item.slug}
            >
              {item.name}
            </Link>
          ))}
        </nav>

        <nav className="shop-availability-filters" aria-label="Filter products by availability">
          {availabilityFilters.map((item) => (
            <Link
              href={shopHref({
                category,
                search,
                availability: item.value,
              })}
              className={availability === item.value ? "shop-availability-filter shop-availability-filter--active" : "shop-availability-filter"}
              aria-current={availability === item.value ? "page" : undefined}
              key={item.value || "all"}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="services-catalogue__result-summary" role="status">
          <span>
            {catalogue.products.length}{" "}
            {catalogue.products.length === 1 ? "product" : "products"}
            {activeCategory ? ` in ${activeCategory.name}` : ""}
            {availability && activeAvailability
              ? ` marked ${activeAvailability.label.toLowerCase()}`
              : ""}
            {search ? ` matching “${search}”` : ""}
          </span>
          {category || search || availability ? (
            <ButtonLink href="/shop" variant="outline" size="small">
              Clear filters
            </ButtonLink>
          ) : null}
        </div>

        {catalogue.unavailable ? (
          <EmptyState
            title="Products are temporarily unavailable"
            description="The product catalogue could not be reached. Check that Django is running, then try again."
            action={<ButtonLink href="/shop">Try again</ButtonLink>}
          />
        ) : catalogue.products.length ? (
          <div className="catalogue-grid">
            {catalogue.products.map((product) => (
              <ProductCard key={product.slug} {...product} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No products match these filters"
            description="Try another search term, availability, or category."
            action={<ButtonLink href="/shop">View all products</ButtonLink>}
          />
        )}
      </section>
    </main>
  );
}

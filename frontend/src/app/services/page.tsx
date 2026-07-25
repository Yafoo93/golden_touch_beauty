import type { Metadata } from "next";
import Link from "next/link";

import { ServiceCard } from "@/components/catalogue/service-card";
import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import { getServiceCatalogue } from "@/lib/services";

export const metadata: Metadata = {
  title: "Beauty Services",
  description:
    "Search and explore published Golden Touch beauty services available at our Ghana branches.",
};

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function filterHref(category: string, search: string) {
  const query = new URLSearchParams();
  if (category) query.set("category", category);
  if (search) query.set("search", search);
  return `/services${query.size ? `?${query.toString()}` : ""}`;
}

export default async function ServicesPage({
  searchParams,
}: {
  searchParams: Promise<{
    category?: string | string[];
    search?: string | string[];
  }>;
}) {
  const params = await searchParams;
  const category = first(params.category).trim();
  const search = first(params.search).trim();
  const catalogue = await getServiceCatalogue({ category, search });
  const activeCategory = catalogue.categories.find(
    (item) => item.slug === category,
  );

  return (
    <main className="services-page">
      <PageHero
        eyebrow="Golden Touch services"
        title="Professional Care"
        accentTitle="For Every Journey"
        description="Explore skin, hair, bridal, body, and personal-care services currently available across our branches."
        backgroundImage="/images/hero2.jpeg"
        backgroundPosition="center 46%"
        size="compact"
      />

      <section className="services-catalogue" aria-labelledby="services-title">
        <header className="services-catalogue__header">
          <div>
            <p>Find your treatment</p>
            <h2 id="services-title">Published services</h2>
            <span>
              Search by treatment, concern, or category, then choose a service
              to begin booking.
            </span>
          </div>
          <form className="services-search" action="/services" method="get" role="search">
            {category ? <input type="hidden" name="category" value={category} /> : null}
            <label htmlFor="service-search">Search services</label>
            <div>
              <input
                id="service-search"
                name="search"
                type="search"
                defaultValue={search}
                placeholder="Try facial, acne, hair..."
              />
              <Button type="submit" size="small">Search</Button>
            </div>
          </form>
        </header>

        <nav className="service-filters" aria-label="Filter services by category">
          <Link
            href={filterHref("", search)}
            className={!category ? "service-filter service-filter--active" : "service-filter"}
            aria-current={!category ? "page" : undefined}
          >
            All services
          </Link>
          {catalogue.categories.map((item) => (
            <Link
              href={filterHref(item.slug, search)}
              className={category === item.slug ? "service-filter service-filter--active" : "service-filter"}
              aria-current={category === item.slug ? "page" : undefined}
              key={item.slug}
            >
              {item.name}
            </Link>
          ))}
        </nav>

        <div className="services-catalogue__result-summary" role="status">
          <span>
            {catalogue.services.length}{" "}
            {catalogue.services.length === 1 ? "service" : "services"}
            {activeCategory ? ` in ${activeCategory.name}` : ""}
            {search ? ` matching “${search}”` : ""}
          </span>
          {category || search ? (
            <ButtonLink href="/services" variant="outline" size="small">
              Clear filters
            </ButtonLink>
          ) : null}
        </div>

        {catalogue.unavailable ? (
          <EmptyState
            title="Services are temporarily unavailable"
            description="The service catalogue could not be reached. Check that Django is running, then try again."
            action={<ButtonLink href="/services">Try again</ButtonLink>}
          />
        ) : catalogue.services.length ? (
          <div className="catalogue-grid">
            {catalogue.services.map((service) => (
              <ServiceCard key={service.slug} {...service} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No services match these filters"
            description="Try another search term or clear the selected category."
            action={<ButtonLink href="/services">View all services</ButtonLink>}
          />
        )}
      </section>
    </main>
  );
}

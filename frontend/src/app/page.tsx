import { ProductCard } from "@/components/catalogue/product-card";
import { ServiceCard } from "@/components/catalogue/service-card";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import {
  getFeaturedProducts,
  getFeaturedServices,
} from "@/lib/featured-catalogue";
import { getWebsiteContent } from "@/lib/website-content";

const contentDefaults = {
  "home-hero-eyebrow": "Premium beauty and wellness",
  "home-hero-title": "Where Beauty",
  "home-hero-accent-title": "Meets Excellence",
  "home-hero-description":
    "Discover professional beauty treatments and personal-care products at our Makola and Tse Addo branches.",
  "home-cta-title": "Ready to book your next visit?",
  "home-cta-description":
    "Choose a service, pick your nearest branch, and secure your appointment in minutes.",
};

const benefits = [
  {
    title: "Experienced professionals",
    description:
      "Trained beauty specialists across skin, hair, and body treatments, delivering consistent, careful service.",
  },
  {
    title: "Premium products",
    description:
      "Treatments and retail products including Marcelito, our own Golden Touch house-brand skincare range.",
  },
  {
    title: "Two Accra locations",
    description:
      "Visit us at Makola or Tse Addo, both open six days a week, so care fits around your schedule.",
  },
  {
    title: "Personalized care",
    description:
      "Every appointment is tailored to your skin, hair, and goals rather than a one-size-fits-all routine.",
  },
];

export default async function Home() {
  const [services, products, content] = await Promise.all([
    getFeaturedServices(),
    getFeaturedProducts(),
    getWebsiteContent(contentDefaults),
  ]);

  return (
    <main className="home-page">
      <PageHero
        eyebrow={content["home-hero-eyebrow"]}
        title={content["home-hero-title"]}
        accentTitle={content["home-hero-accent-title"]}
        description={content["home-hero-description"]}
        backgroundImage="/images/hero1.jpeg"
        backgroundPosition="center 42%"
        size="large"
        actions={
          <>
            <ButtonLink href="/book" size="large">
              Book an appointment
            </ButtonLink>
            <ButtonLink href="/shop" variant="outline" size="large">
              Shop products
            </ButtonLink>
          </>
        }
      />

      <div className="home-page__content">
        <section
          className="catalogue-preview"
          aria-labelledby="featured-services-title"
        >
          <div className="catalogue-preview__heading">
            <p>What we offer</p>
            <h2 id="featured-services-title">Featured services</h2>
          </div>
          {services.items.length ? (
            <div className="catalogue-grid">
              {services.items.map((service) => (
                <ServiceCard key={service.slug} {...service} />
              ))}
            </div>
          ) : (
            <EmptyState
              title={
                services.unavailable
                  ? "Services are temporarily unavailable"
                  : "No featured services yet"
              }
              description={
                services.unavailable
                  ? "Please refresh the page shortly or view the full service catalogue."
                  : "Featured services selected by management will appear here."
              }
              action={<ButtonLink href="/services">View services</ButtonLink>}
            />
          )}
        </section>
        <section
          className="catalogue-preview"
          aria-labelledby="featured-products-title"
        >
          <div className="catalogue-preview__heading">
            <p>Golden Touch store</p>
            <h2 id="featured-products-title">Featured products</h2>
          </div>
          {products.items.length ? (
            <div className="catalogue-grid">
              {products.items.map((product) => (
                <ProductCard key={product.slug} {...product} />
              ))}
            </div>
          ) : (
            <EmptyState
              title={
                products.unavailable
                  ? "Products are temporarily unavailable"
                  : "No featured products yet"
              }
              description={
                products.unavailable
                  ? "Please refresh the page shortly or continue to the shop."
                  : "Featured products selected by management will appear here."
              }
              action={<ButtonLink href="/shop">Visit the shop</ButtonLink>}
            />
          )}
        </section>

        <section className="home-benefits" aria-labelledby="home-benefits-title">
          <div className="catalogue-preview__heading">
            <p>The Golden Touch difference</p>
            <h2 id="home-benefits-title">Why clients choose us</h2>
          </div>
          <div className="home-benefits__grid">
            {benefits.map((benefit) => (
              <div className="benefit-card" key={benefit.title}>
                <h3>{benefit.title}</h3>
                <p>{benefit.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="home-cta-band" aria-labelledby="home-cta-title">
          <h2 id="home-cta-title">{content["home-cta-title"]}</h2>
          <p>{content["home-cta-description"]}</p>
          <div className="home-cta-band__actions">
            <ButtonLink href="/book" size="large">
              Book an appointment
            </ButtonLink>
            <ButtonLink href="/shop" variant="outline" size="large">
              Shop products
            </ButtonLink>
          </div>
        </section>
      </div>
    </main>
  );
}

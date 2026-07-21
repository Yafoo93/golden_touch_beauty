import {
  ProductCard,
  type ProductCardProps,
} from "@/components/catalogue/product-card";
import {
  ServiceCard,
  type ServiceCardProps,
} from "@/components/catalogue/service-card";
import { ButtonLink } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";

const featuredServices = [
  {
    name: "Facial Treatment",
    slug: "facial-treatment",
    category: "Skin & Clinical Aesthetics",
    description: "A personalized facial designed to cleanse, exfoliate, hydrate, and refresh the skin.",
    price: 250,
    durationMinutes: 60,
    imageSrc: "/images/facial_treatment.jpeg",
    availableAt: ["Makola", "Tse Addo"],
    badge: "Featured",
  },
  {
    name: "Sunburn Treatment",
    slug: "sunburn-treatment",
    category: "Skin & Clinical Aesthetics",
    description: "A soothing skin-care treatment intended to calm sun-stressed skin and support hydration.",
    price: 220,
    durationMinutes: 60,
    imageSrc: "/images/sunburn.jpeg",
    availableAt: ["Makola", "Tse Addo"],
  },
] satisfies ServiceCardProps[];

const featuredProducts = [
  {
    name: "Marcelito Face Cream",
    slug: "marcelito-face-cream",
    category: "Marcelito Face & Body",
    description: "A daily face moisturizer from the Golden Touch house range for soft, hydrated-looking skin.",
    price: 180,
    imageSrc: "/images/face_cream.jpeg",
    variantLabel: "Standard",
    inStock: true,
    badge: "House brand",
  },
  {
    name: "Marcelito Face Serum & Oil",
    slug: "marcelito-face-serum-and-oil",
    category: "Face Serums & Oils",
    description: "A concentrated face-care blend designed to complement a daily moisturizing routine.",
    price: 160,
    imageSrc: "/images/syrum_n_oil.jpeg",
    variantLabel: "Standard",
    inStock: true,
  },
] satisfies ProductCardProps[];

type HealthResponse = {
  application: string;
  status: string;
  database: string;
};

async function getBackendHealth(): Promise<HealthResponse | null> {
  const baseUrl = process.env.BACKEND_INTERNAL_URL;

  if (!baseUrl) {
    return null;
  }

  try {
    const response = await fetch(`${baseUrl}/api/v1/health/`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export default async function Home() {
  const backend = await getBackendHealth();

  return (
    <main className="home-page">
      <PageHero
        eyebrow="Premium beauty and wellness"
        title="Where Beauty"
        accentTitle="Meets Excellence"
        description="Discover professional beauty treatments and personal-care products at our Makola and Tse Addo branches."
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
        <div className="system-status">
          <p className="text-sm uppercase tracking-wider text-neutral-400">
            System connection
          </p>

          <p className="mt-3 text-xl font-medium">
            Backend:{" "}
            <span
              className={
                backend?.status === "ok"
                  ? "text-green-400"
                  : "text-red-400"
              }
            >
              {backend?.status === "ok"
                ? "Connected"
                : "Unavailable"}
            </span>
          </p>

          <p className="mt-2 text-neutral-400">
            Database: {backend?.database ?? "Unknown"}
          </p>
        </div>
        <section
          className="catalogue-preview"
          aria-labelledby="featured-services-title"
        >
          <div className="catalogue-preview__heading">
            <p>What we offer</p>
            <h2 id="featured-services-title">Featured services</h2>
          </div>
          <div className="catalogue-grid">
            {featuredServices.map((service) => (
              <ServiceCard key={service.slug} {...service} />
            ))}
          </div>
        </section>
        <section
          className="catalogue-preview"
          aria-labelledby="featured-products-title"
        >
          <div className="catalogue-preview__heading">
            <p>Golden Touch store</p>
            <h2 id="featured-products-title">Featured products</h2>
          </div>
          <div className="catalogue-grid">
            {featuredProducts.map((product) => (
              <ProductCard key={product.slug} {...product} />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

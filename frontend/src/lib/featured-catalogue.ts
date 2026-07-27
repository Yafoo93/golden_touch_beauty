import type { ProductCardProps } from "@/components/catalogue/product-card";
import type { ServiceCardProps } from "@/components/catalogue/service-card";
import { fetchBackendJson } from "@/lib/backend-fetch";

type FeaturedServiceResponse = {
  name: string;
  slug: string;
  category: string;
  short_description: string;
  price: string;
  duration_minutes: number;
  image_path: string;
  available_at: string[];
};

type FeaturedProductResponse = {
  name: string;
  slug: string;
  category: string;
  description: string;
  price: string | null;
  image_path: string;
  variant_label: string | null;
  variant_id: string | null;
  sku: string | null;
  in_stock: boolean;
};

export type FeaturedCatalogueResult<T> = {
  items: T[];
  unavailable: boolean;
};

function apiUrl(path: string) {
  const base = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  return `${base}/api/v1/${path.replace(/^\/+/, "")}`;
}

async function fetchPublicList<T>(path: string): Promise<FeaturedCatalogueResult<T>> {
  const items = await fetchBackendJson<T[]>(apiUrl(path));
  return items === null
    ? { items: [], unavailable: true }
    : { items, unavailable: false };
}

export async function getFeaturedServices(): Promise<
  FeaturedCatalogueResult<ServiceCardProps>
> {
  const result = await fetchPublicList<FeaturedServiceResponse>(
    "services/featured/",
  );
  return {
    unavailable: result.unavailable,
    items: result.items.map((service) => ({
      name: service.name,
      slug: service.slug,
      category: service.category,
      description: service.short_description,
      price: service.price,
      durationMinutes: service.duration_minutes,
      imageSrc: service.image_path || "/images/hero1.jpeg",
      availableAt: service.available_at,
      badge: "Featured",
    })),
  };
}

export async function getFeaturedProducts(): Promise<
  FeaturedCatalogueResult<ProductCardProps>
> {
  const result = await fetchPublicList<FeaturedProductResponse>(
    "products/featured/",
  );
  return {
    unavailable: result.unavailable,
    items: result.items
      .filter((product) => product.price !== null)
      .map((product) => ({
        name: product.name,
        slug: product.slug,
        category: product.category,
        description: product.description,
        price: product.price as string,
        imageSrc: product.image_path || "/images/hero2.jpeg",
        variantLabel: product.variant_label ?? undefined,
        variantId: product.variant_id ?? undefined,
        sku: product.sku ?? undefined,
        inStock: product.in_stock,
        badge: "Featured",
      })),
  };
}

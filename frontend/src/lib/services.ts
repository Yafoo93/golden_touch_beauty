import type { ServiceCardProps } from "@/components/catalogue/service-card";
import type { PublicBranch } from "@/lib/branches";

export type ServiceCategory = { name: string; slug: string };
export type ServicePriceOption = {
  id: string;
  name: string;
  description: string;
  price: string;
  duration_minutes: number | null;
  display_order: number;
};

type ServiceResponse = {
  name: string;
  slug: string;
  category: string;
  category_slug: string;
  short_description: string;
  price: string;
  price_type: string;
  pricing_notes: string;
  duration_minutes: number;
  image_path: string;
  available_at: string[];
};

export type ServiceCatalogueResult = {
  services: ServiceCardProps[];
  categories: ServiceCategory[];
  unavailable: boolean;
};

export type ServiceDetail = ServiceResponse & {
  description: string;
  maximum_price: string | null;
  price_type_label: string;
  is_clinic_service: boolean;
  is_home_service: boolean;
  requires_full_payment: boolean;
  allows_pay_at_clinic: boolean;
  is_consultation: boolean;
  available_branches: PublicBranch[];
  price_options: ServicePriceOption[];
};

function apiUrl(path: string) {
  const base = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  return `${base}/api/v1/services/${path}`;
}

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const response = await fetch(url, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function getServiceCatalogue(filters: {
  category?: string;
  search?: string;
}): Promise<ServiceCatalogueResult> {
  const query = new URLSearchParams();
  if (filters.category) query.set("category", filters.category);
  if (filters.search) query.set("search", filters.search);
  const [services, categories] = await Promise.all([
    fetchJson<ServiceResponse[]>(
      apiUrl(`${query.size ? `?${query.toString()}` : ""}`),
    ),
    fetchJson<ServiceCategory[]>(apiUrl("categories/")),
  ]);

  return {
    unavailable: services === null || categories === null,
    categories: categories ?? [],
    services: (services ?? []).map((service) => ({
      name: service.name,
      slug: service.slug,
      category: service.category,
      description: service.short_description,
      price: service.price,
      durationMinutes: service.duration_minutes,
      imageSrc: service.image_path || "/images/hero1.jpeg",
      availableAt: service.available_at,
      badge:
        service.price_type === "starting_from"
          ? "Starting from"
          : service.price_type === "options"
            ? "Price options"
            : service.price_type === "quotation"
              ? "Quotation"
          : service.pricing_notes || undefined,
    })),
  };
}

export async function getServiceDetail(
  slug: string,
): Promise<ServiceDetail | null> {
  return fetchJson<ServiceDetail>(
    apiUrl(`${encodeURIComponent(slug)}/`),
  );
}

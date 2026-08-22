import type { ServiceCardProps } from "@/components/catalogue/service-card";
import { fetchBackendJson } from "@/lib/backend-fetch";
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
  id: string;
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
  has_result_images: boolean;
  available_at: string[];
  available_branches: PublicBranch[];
  allows_pay_at_clinic: boolean;
  price_options: ServicePriceOption[];
};

function serviceResponseToCard(service: ServiceResponse): ServiceCardProps {
  return {
    id: service.id,
    name: service.name,
    slug: service.slug,
    category: service.category,
    description: service.short_description,
    price: service.price,
    durationMinutes: service.duration_minutes,
    imageSrc: service.image_path || "/images/hero1.jpeg",
    availableAt: service.available_at,
    priceType: service.price_type,
    allowsPayAtClinic: service.allows_pay_at_clinic,
    priceOptions: service.price_options,
    hasResultImages: service.has_result_images,
    enquiryBranches: service.available_branches.map((branch) => ({ code: branch.code, name: branch.name, whatsapp_number: branch.whatsapp_number || branch.secondary_whatsapp_number || branch.telephone_number })),
    badge:
      service.price_type === "starting_from"
        ? "Starting from"
        : service.price_type === "options"
          ? "Price options"
          : service.price_type === "quotation"
            ? "Quotation"
            : service.pricing_notes || undefined,
  };
}

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
  before_image_url: string | null;
  after_image_url: string | null;
  price_options: ServicePriceOption[];
};

function apiUrl(path: string) {
  const base = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  return `${base}/api/v1/services/${path}`;
}

export async function getServiceCatalogue(filters: {
  category?: string;
  search?: string;
  branch?: string;
}): Promise<ServiceCatalogueResult> {
  const query = new URLSearchParams();
  if (filters.category) query.set("category", filters.category);
  if (filters.search) query.set("search", filters.search);
  if (filters.branch) query.set("branch", filters.branch);
  const [services, categories] = await Promise.all([
    fetchBackendJson<ServiceResponse[]>(
      apiUrl(`${query.size ? `?${query.toString()}` : ""}`),
    ),
    fetchBackendJson<ServiceCategory[]>(apiUrl("categories/")),
  ]);

  return {
    unavailable: services === null || categories === null,
    categories: categories ?? [],
    services: (services ?? []).map(serviceResponseToCard),
  };
}

export async function getServiceDetail(
  slug: string,
): Promise<ServiceDetail | null> {
  return fetchBackendJson<ServiceDetail>(
    apiUrl(`${encodeURIComponent(slug)}/`),
  );
}

export async function getRelatedServices(
  service: Pick<ServiceDetail, "slug" | "category_slug">,
  limit = 3,
): Promise<ServiceCardProps[]> {
  const catalogue = await getServiceCatalogue({
    category: service.category_slug,
  });
  const sameCategory = catalogue.services
    .filter((candidate) => candidate.slug !== service.slug)
    .slice(0, limit);
  if (sameCategory.length >= limit) return sameCategory;

  const fallback = await getServiceCatalogue({});
  return [
    ...sameCategory,
    ...fallback.services.filter(
      (candidate) =>
        candidate.slug !== service.slug &&
        !sameCategory.some((related) => related.slug === candidate.slug),
    ),
  ].slice(0, limit);
}

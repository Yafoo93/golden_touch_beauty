import type { ProductCardProps } from "@/components/catalogue/product-card";
import { fetchBackendJson } from "@/lib/backend-fetch";

export type ProductCategory = { name: string; slug: string };
export type ProductAvailability = "" | "in_stock" | "preorder" | "out_of_stock";
export type ProductVariant = {
  id: string;
  name: string;
  sku: string;
  selling_price: string;
  is_preorder: boolean;
  estimated_availability_date: string | null;
  availability: "in_stock" | "preorder" | "out_of_stock";
  available_at: {
    branch_id: string;
    branch_code: string;
    branch_name: string;
    whatsapp_number: string;
  }[];
};
export type ProductDetail = {
  name: string;
  slug: string;
  brand: string;
  category: string;
  category_slug: string;
  description: string;
  image_path: string;
  images: string[];
  variants: ProductVariant[];
  price_type: "fixed" | "contact";
};

export type PublicProductSummary = {
  name: string;
  slug: string;
  category: string;
  category_slug: string;
  description: string;
  price: string | null;
  image_path: string;
  variant_label: string | null;
  variant_id: string | null;
  sku: string | null;
  in_stock: boolean;
  availability: "in_stock" | "preorder" | "out_of_stock";
  price_type: "fixed" | "contact";
  contact_branches: { code: string; name: string; whatsapp_number: string }[];
};

export function productSummaryToCard(
  product: PublicProductSummary,
): ProductCardProps | null {
  if (product.price === null) return null;
  return {
    name: product.name,
    slug: product.slug,
    category: product.category,
    description: product.description,
    price: product.price,
    imageSrc: product.image_path || "/images/hero2.jpeg",
    variantLabel: product.variant_label ?? undefined,
    variantId: product.variant_id ?? undefined,
    sku: product.sku ?? undefined,
    inStock: product.in_stock,
    badge:
      product.availability === "preorder"
        ? "Pre-order"
        : product.availability === "out_of_stock"
          ? "Unavailable"
          : undefined,
    priceType: product.price_type,
    contactBranches: product.contact_branches,
  };
}

export type ProductCatalogueResult = {
  products: ProductCardProps[];
  categories: ProductCategory[];
  unavailable: boolean;
};

function apiUrl(path: string) {
  const base = (
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  return `${base}/api/v1/products/${path}`;
}

export async function getProductCatalogue(filters: {
  category?: string;
  search?: string;
  availability?: ProductAvailability;
}): Promise<ProductCatalogueResult> {
  const query = new URLSearchParams();
  if (filters.category) query.set("category", filters.category);
  if (filters.search) query.set("search", filters.search);
  if (filters.availability) query.set("availability", filters.availability);
  const [products, categories] = await Promise.all([
    fetchBackendJson<PublicProductSummary[]>(
      apiUrl(query.size ? `?${query.toString()}` : ""),
    ),
    fetchBackendJson<ProductCategory[]>(apiUrl("categories/")),
  ]);

  return {
    unavailable: products === null || categories === null,
    categories: categories ?? [],
    products: (products ?? [])
      .map(productSummaryToCard)
      .filter((product): product is ProductCardProps => product !== null),
  };
}

export async function getProductDetail(
  slug: string,
): Promise<ProductDetail | null> {
  return fetchBackendJson<ProductDetail>(
    apiUrl(`${encodeURIComponent(slug)}/`),
  );
}

export async function getRelatedProducts(
  product: Pick<ProductDetail, "slug" | "category_slug">,
  limit = 4,
): Promise<ProductCardProps[]> {
  const catalogue = await getProductCatalogue({
    category: product.category_slug,
  });
  const sameCategory = catalogue.products
    .filter((candidate) => candidate.slug !== product.slug)
    .slice(0, limit);
  if (sameCategory.length >= limit) return sameCategory;

  const fallback = await getProductCatalogue({});
  return [
    ...sameCategory,
    ...fallback.products.filter(
      (candidate) =>
        candidate.slug !== product.slug &&
        !sameCategory.some((related) => related.slug === candidate.slug),
    ),
  ].slice(0, limit);
}

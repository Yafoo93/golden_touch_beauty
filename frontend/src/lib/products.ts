import type { ProductCardProps } from "@/components/catalogue/product-card";

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
    fetchJson<PublicProductSummary[]>(
      apiUrl(query.size ? `?${query.toString()}` : ""),
    ),
    fetchJson<ProductCategory[]>(apiUrl("categories/")),
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
  return fetchJson<ProductDetail>(apiUrl(`${encodeURIComponent(slug)}/`));
}

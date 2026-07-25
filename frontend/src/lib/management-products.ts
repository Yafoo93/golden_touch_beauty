export type ManagementProductBranchStock = {
  branch_id: string;
  branch_code: string;
  branch_name: string;
  branch_is_active: boolean;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
};

export type ManagementProduct = {
  id: string;
  name: string;
  slug: string;
  brand: string;
  category: string;
  image_path: string;
  is_featured: boolean;
  is_active: boolean;
  is_published: boolean;
  publication_state: "draft" | "published" | "inactive";
  active_variant_count: number;
  variant_count: number;
  minimum_price: string | null;
  maximum_price: string | null;
  total_on_hand: number;
  total_reserved: number;
  total_available: number;
  low_stock_count: number;
  branch_stock: ManagementProductBranchStock[];
  updated_at: string;
};

export type ManagementProductVariantStock = {
  branch_id: string;
  branch_code: string;
  branch_name: string;
  branch_is_active: boolean;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  reorder_level: number;
  is_available: boolean;
};

export type ManagementProductVariant = {
  id: string;
  name: string;
  sku: string;
  selling_price: string;
  cost_price: string;
  is_preorder: boolean;
  estimated_availability_date: string | null;
  is_active: boolean;
  stocks: ManagementProductVariantStock[];
};

export type ManagementProductDetail = {
  id: string;
  name: string;
  slug: string;
  brand: string;
  category_id: string;
  category_name: string;
  description: string;
  image_path: string;
  is_featured: boolean;
  is_active: boolean;
  is_published: boolean;
  publication_state: "draft" | "published" | "inactive";
  variants: ManagementProductVariant[];
  created_at: string;
  updated_at: string;
};

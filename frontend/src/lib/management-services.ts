export type ManagementServiceBranchAvailability = {
  branch_id: string;
  branch_code: string;
  branch_name: string;
  branch_is_active: boolean;
  is_available: boolean;
};

export type ServicePriceOption = {
  id?: string;
  name: string;
  description: string;
  price: string;
  duration_minutes: number | null;
  display_order: number;
};

export type ManagementService = {
  id: string;
  name: string;
  slug: string;
  category: string;
  price_type: string;
  price: string;
  maximum_price: string | null;
  pricing_notes: string;
  duration_minutes: number;
  image_path: string;
  is_featured: boolean;
  is_active: boolean;
  is_published: boolean;
  publication_state: "draft" | "published" | "inactive";
  requires_full_payment: boolean;
  allows_pay_at_clinic: boolean;
  branch_availability: ManagementServiceBranchAvailability[];
  updated_at: string;
};

export type ManagementServiceDetail = ManagementService & {
  category_id: string;
  category_name: string;
  short_description: string;
  description: string;
  is_clinic_service: boolean;
  is_home_service: boolean;
  is_consultation: boolean;
  branch_ids: string[];
  price_options: ServicePriceOption[];
  created_at: string;
};

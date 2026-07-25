export type ManagementInventoryItem = {
  id: string;
  branch_id: string;
  branch_code: string;
  branch_name: string;
  branch_is_active: boolean;
  product_id: string;
  product_name: string;
  product_slug: string;
  category_name: string;
  variant_id: string;
  variant_name: string;
  sku: string;
  variant_is_active: boolean;
  selling_price: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  reorder_level: number;
  is_available: boolean;
  is_low_stock: boolean;
  updated_at: string;
};

export type StockMovement = {
  id: string;
  branch_id: string;
  branch_code: string;
  branch_name: string;
  movement_type: string;
  movement_label: string;
  quantity_on_hand_change: number;
  quantity_reserved_change: number;
  quantity_on_hand_after: number;
  quantity_reserved_after: number;
  reference_type: string;
  reference_id: string;
  note: string;
  performed_by_name: string;
  created_at: string;
};

export type VariantStockHistory = {
  variant: {
    id: string;
    product_name: string;
    product_slug: string;
    category_name: string;
    variant_name: string;
    sku: string;
    is_active: boolean;
  };
  current_stock: ManagementInventoryItem[];
  movements: StockMovement[];
};

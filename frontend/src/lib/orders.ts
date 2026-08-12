export type CheckoutItem = {
  id?: string;
  variant_id: string;
  product_name: string;
  variant_name: string;
  sku: string;
  image_path: string;
  unit_price: string;
  quantity: number;
  line_total: string;
};

export type CheckoutOptions = {
  customer: { name: string; phone: string; email: string };
  items: CheckoutItem[];
  subtotal: string;
  delivery_fee: string;
  total_amount: string;
  pickup_branches: { id: string; code: string; name: string }[];
  delivery_available: boolean;
  reservation_minutes: number;
};

export type CustomerOrder = {
  id: string;
  reference: string;
  status: string;
  payment_status: string;
  fulfillment_method: "pickup" | "delivery";
  branch_code: string;
  branch_name: string;
  currency: string;
  subtotal: string;
  delivery_fee: string;
  total_amount: string;
  recipient_name: string;
  recipient_phone: string;
  delivery_address: string;
  delivery_city: string;
  delivery_notes: string;
  reservation_expires_at: string | null;
  paid_at: string | null;
  cancelled_at: string | null;
  items: CheckoutItem[];
  created_at: string;
};

export type CustomerOrderPayment = {
  reference: string;
  provider: string;
  method: string;
  status: string;
  currency: string;
  amount: string;
  paid_at: string | null;
  receipt_reference: string | null;
  created_at: string;
};

export type CustomerOrderDetail = CustomerOrder & {
  payments: CustomerOrderPayment[];
  invoice_reference: string | null;
  updated_at: string;
};

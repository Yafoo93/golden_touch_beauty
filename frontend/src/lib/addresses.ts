export type CustomerAddress = {
  id: string;
  label: string;
  address_type: "billing" | "delivery" | "both";
  recipient_name: string;
  recipient_phone: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  region: string;
  landmark: string;
  country: string;
  is_default_billing: boolean;
  is_default_delivery: boolean;
  created_at: string;
  updated_at: string;
};

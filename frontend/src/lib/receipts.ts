export type ReceiptLineItem = {
  description: string;
  quantity: number;
  unit_price: string;
  line_total: string;
};

export type CustomerReceipt = {
  id: string;
  reference: string;
  payment_reference: string;
  payment_method: string;
  provider: string;
  source_type: "booking" | "order";
  source_reference: string;
  branch_code: string;
  branch_name: string;
  branch_address: string;
  recipient_name: string;
  currency: string;
  amount: string;
  line_items: ReceiptLineItem[];
  issued_at: string;
  created_at: string;
};

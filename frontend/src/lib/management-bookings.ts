export type BookingServiceItem = {
  id: string;
  service_name: string;
  option_name: string;
  unit_price: string;
  duration_minutes: number;
};

export type ManagementBooking = {
  id: string;
  reference: string;
  status: string;
  branch_code: string;
  branch_name: string;
  customer_name: string;
  customer_email: string;
  preferred_start: string;
  proposed_start: string | null;
  proposed_expires_at: string | null;
  total_amount: string;
  total_duration_minutes: number;
  recipient_name: string;
  recipient_phone: string;
  payment_method: string;
  payment_status: string;
  finishes_after_branch_closing: boolean;
  source: string;
  allergies?: string;
  conditions?: string;
  previous_treatments?: string;
  notes?: string;
  can_view_sensitive_intake: boolean;
  services: BookingServiceItem[];
  history: {
    id: string;
    action: string;
    from_status: string;
    to_status: string;
    reason: string;
    actor_name: string;
    created_at: string;
  }[];
};

export type BookingBlock = {
  id: string;
  branch_code: string;
  branch_name: string;
  starts_at: string;
  ends_at: string;
  block_type: string;
  reason: string;
  is_active: boolean;
};

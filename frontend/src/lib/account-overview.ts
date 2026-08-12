export type AccountOverview = {
  summary: {
    upcoming_appointments: number;
    completed_services: number;
    orders: number;
    outstanding_balance: string;
    currency: string;
  };
  upcoming_appointments: {
    reference: string;
    branch_name: string;
    preferred_start: string;
    status: string;
    services: string[];
    total_amount: string;
  }[];
  recent_orders: {
    reference: string;
    branch_name: string;
    status: string;
    payment_status: string;
    total_amount: string;
    item_count: number;
    created_at: string;
  }[];
  recent_activity: {
    id: string;
    type: "booking" | "order";
    reference: string;
    title: string;
    description: string;
    status: string;
    timestamp: string;
    action_url: string;
  }[];
};

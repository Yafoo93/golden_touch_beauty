export type PublicBranch = {
  id: string;
  code: string;
  name: string;
  address: string;
  telephone_number: string;
  secondary_telephone_number: string;
  whatsapp_number: string;
  secondary_whatsapp_number: string;
  email: string;
  google_maps_url: string;
  opening_days: string[];
  opening_time: string;
  closing_time: string;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

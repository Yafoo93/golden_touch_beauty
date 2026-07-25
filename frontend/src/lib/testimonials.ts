export type TestimonialStatus = "pending" | "approved" | "rejected";

export type Testimonial = {
  id: string;
  client_name: string;
  client_attribution: string;
  service_context: string;
  quote: string;
  is_featured: boolean;
};

export type ManagementTestimonial = Testimonial & {
  source_type: "written" | "video" | "development_sample";
  source_type_label: string;
  consent_confirmed: boolean;
  moderation_status: TestimonialStatus;
  is_visible: boolean;
  display_order: number;
  reviewed_by: { id: string; full_name: string } | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
};

export async function getTestimonials(): Promise<Testimonial[]> {
  const backendUrl =
    process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${backendUrl}/api/v1/testimonials/`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) return [];
    return (await response.json()) as Testimonial[];
  } catch {
    return [];
  }
}

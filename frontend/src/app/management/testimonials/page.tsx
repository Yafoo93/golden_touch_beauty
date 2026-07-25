import type { Metadata } from "next";
import { cookies } from "next/headers";

import { TestimonialModerator } from "@/components/management/testimonial-moderator";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { ManagementTestimonial } from "@/lib/testimonials";

export const metadata: Metadata = { title: "Moderate Testimonials" };

type LoadResult =
  | { status: "success"; testimonials: ManagementTestimonial[] }
  | { status: "denied" }
  | { status: "error" };

async function loadTestimonials(): Promise<LoadResult> {
  const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const cookieHeader = (await cookies()).toString();
  try {
    const response = await fetch(`${backendUrl}/api/v1/testimonials/management/`, {
      cache: "no-store",
      headers: { Accept: "application/json", Cookie: cookieHeader },
      signal: AbortSignal.timeout(15_000),
    });
    if (response.status === 401 || response.status === 403) return { status: "denied" };
    if (!response.ok) return { status: "error" };
    return { status: "success", testimonials: (await response.json()) as ManagementTestimonial[] };
  } catch {
    return { status: "error" };
  }
}

export default async function ManagementTestimonialsPage() {
  const result = await loadTestimonials();
  return (
    <main className="management-page management-page--testimonials">
      <header className="management-page__header">
        <div>
          <p>Management · Website</p>
          <h1>Testimonials</h1>
          <span>Review consent, approve or reject client stories, and control public visibility.</span>
        </div>
        <div className="management-page__summary">
          <strong>Consent before publication</strong>
          <span>A testimonial cannot be approved or shown publicly until client consent has been explicitly confirmed.</span>
          <ButtonLink href="/testimonials" variant="outline" size="small">View public testimonials</ButtonLink>
        </div>
      </header>
      {result.status === "denied" ? (
        <EmptyState title="Owner access required" description="Sign in with the owner account to moderate testimonials." action={<ButtonLink href="/login">Sign in</ButtonLink>} />
      ) : result.status === "error" ? (
        <EmptyState title="Testimonials could not be loaded" description="Check that Django is running, then try again." action={<ButtonLink href="/management/testimonials">Try again</ButtonLink>} />
      ) : (
        <TestimonialModerator testimonials={result.testimonials} />
      )}
    </main>
  );
}

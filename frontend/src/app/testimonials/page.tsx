import type { Metadata } from "next";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHero } from "@/components/ui/page-hero";
import { getTestimonials } from "@/lib/testimonials";

export const metadata: Metadata = {
  title: "Client Testimonials",
  description:
    "Read approved client experiences from Golden Touch Beauty Centre.",
};

function QuoteIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M8 27c0-9 4-15 12-18l2 4c-5 2-7 5-8 9h7v16H8V27Zm21 0c0-9 4-15 12-18l2 4c-5 2-7 5-8 9h7v16H29V27Z" />
    </svg>
  );
}

export default async function TestimonialsPage() {
  const testimonials = await getTestimonials();
  return (
    <main className="testimonials-page">
      <PageHero
        eyebrow="Client experiences"
        title="Care Worth"
        accentTitle="Talking About"
        description="Read approved stories from clients who have chosen Golden Touch for their beauty and personal-care journey."
        backgroundImage="/images/hero1.jpeg"
        backgroundPosition="center 44%"
        size="compact"
      />

      <section
        className="testimonials-page__content"
        aria-labelledby="testimonials-title"
      >
        <div className="testimonials-page__heading">
          <p>Approved client experiences</p>
          <h2 id="testimonials-title">What our clients share</h2>
          <span>
            Only testimonials reviewed for consent and approved by Golden Touch
            management are published here.
          </span>
        </div>

        {testimonials.length ? (
          <div className="testimonial-grid">
            {testimonials.map((testimonial) => (
              <figure className="testimonial-card" key={testimonial.id}>
                <div className="testimonial-card__top">
                  <QuoteIcon />
                  <span>{testimonial.is_featured ? "Featured" : "Approved"}</span>
                </div>
                <blockquote>
                  <p>“{testimonial.quote}”</p>
                </blockquote>
                <figcaption>
                  <strong>{testimonial.client_name}</strong>
                  <span>
                    {[
                      testimonial.service_context,
                      testimonial.client_attribution,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                </figcaption>
              </figure>
            ))}
          </div>
        ) : (
          <EmptyState
            title="Client stories are being reviewed"
            description="Testimonials will appear here after consent and management approval are confirmed."
          />
        )}
      </section>

      <section
        className="testimonial-feature"
        aria-labelledby="video-testimonial-title"
      >
        <div className="testimonial-feature__marker" aria-hidden="true">
          <svg viewBox="0 0 48 48">
            <rect x="5" y="9" width="38" height="30" rx="4" />
            <path d="m21 18 10 6-10 6V18Z" />
          </svg>
        </div>
        <div className="testimonial-feature__content">
          <p>Coming later</p>
          <h2 id="video-testimonial-title">Verified video testimonial</h2>
          <span>
            This section is reserved for an approved Golden Touch video
            testimonial. The speaker’s consent, preferred name, service
            context, and final wording will be confirmed before publication.
          </span>
        </div>
      </section>

      <section className="testimonial-cta" aria-labelledby="testimonial-cta-title">
        <div>
          <p>Experience Golden Touch</p>
          <h2 id="testimonial-cta-title">Start your own beauty journey</h2>
        </div>
        <div className="testimonial-cta__actions">
          <ButtonLink href="/services" variant="outline">
            Explore services
          </ButtonLink>
          <ButtonLink href="/book">Book an appointment</ButtonLink>
        </div>
      </section>
    </main>
  );
}

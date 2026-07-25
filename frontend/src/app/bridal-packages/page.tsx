import type { Metadata } from "next";
import Image from "next/image";

import { ButtonLink } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";

export const metadata: Metadata = {
  title: "Bridal Packages",
  description:
    "Explore bridal beauty preparation at Golden Touch Beauty Centre. Final package details and pricing are confirmed during consultation.",
};

const packageFeatures = [
  "Pre-event beauty consultation",
  "Bridal skin preparation guidance",
  "Bridal makeup application",
  "Hair preparation and styling",
  "Gele or headpiece styling where required",
  "Final-look finishing and touch-up guidance",
];

export default function BridalPackagesPage() {
  return (
    <main className="bridal-page">
      <PageHero
        eyebrow="Golden Touch bridal"
        title="Your Day,"
        accentTitle="Beautifully Prepared"
        description="A thoughtful bridal beauty experience shaped around your look, ceremony, and personal style."
        backgroundImage="/images/bridal.jpeg"
        backgroundPosition="center 28%"
        size="large"
        actions={
          <>
            <ButtonLink href="/book" size="large">
              Request a consultation
            </ButtonLink>
            <ButtonLink href="/contact" variant="outline" size="large">
              Contact a branch
            </ButtonLink>
          </>
        }
      />

      <section
        className="bridal-package-section"
        aria-labelledby="bridal-package-title"
      >
        <div className="bridal-package-section__heading">
          <p>Development package preview</p>
          <h2 id="bridal-package-title">The Golden Bride Experience</h2>
          <span>
            This is placeholder content for development. Final package name,
            inclusions, availability, terms, and pricing require business
            approval before launch.
          </span>
        </div>

        <article className="bridal-package-card">
          <div className="bridal-package-card__image">
            <Image
              src="/images/makeup.jpeg"
              alt="Beauty products prepared for a bridal makeup appointment"
              fill
              sizes="(max-width: 800px) 100vw, 45vw"
            />
          </div>

          <div className="bridal-package-card__content">
            <div className="bridal-package-card__label">
              <span>Placeholder package</span>
              <p>Bridal & Glam</p>
            </div>
            <h3>The Golden Bride Experience</h3>
            <p className="bridal-package-card__summary">
              A coordinated bridal preparation service combining consultation,
              makeup, hair, and traditional styling options for the bride.
            </p>

            <h4>Provisional inclusions</h4>
            <ul>
              {packageFeatures.map((feature) => (
                <li key={feature}>
                  <span aria-hidden="true">✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            <div className="bridal-package-card__price">
              <span>Package price</span>
              <strong>Confirmed after consultation</strong>
            </div>

            <div className="bridal-package-card__actions">
              <ButtonLink href="/book">Request a consultation</ButtonLink>
              <ButtonLink href="/gallery" variant="outline">
                View gallery
              </ButtonLink>
            </div>
          </div>
        </article>
      </section>

      <section className="bridal-note" aria-labelledby="bridal-note-title">
        <div>
          <p>Planning note</p>
          <h2 id="bridal-note-title">Every bridal booking starts with a conversation</h2>
        </div>
        <p>
          Final timing, location, styling requirements, additional participants,
          travel, and payment terms should be agreed with Golden Touch before
          the booking is confirmed.
        </p>
      </section>
    </main>
  );
}
